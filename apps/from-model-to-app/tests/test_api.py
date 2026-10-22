"""Interface checks for the engine API and the static dashboard.

Replaces the former Streamlit AppTest smoke test: drives the real Flask API
(the layer every dashboard number comes through) and checks the served HTML
for the three-tab structure, the exact footer and the absence of removed
version-1 actions.
"""
import numpy as np
import pytest

import engine_api
import models
from conftest import APP_DIR

FOOTER = 'Business Analytics and Data Visualization Fall 2026 - Prof. Jose Mendoza'
SESSION = {'X-Session-Id': 'test-session'}


@pytest.fixture()
def client():
    engine_api.app.config['TESTING'] = True
    with engine_api.app.test_client() as test_client:
        yield test_client
    with engine_api.SESSIONS_LOCK:
        engine_api.SESSIONS.clear()


def train(client, choice='Regression tree', parameter_id='3', headers=SESSION):
    return client.post('/api/train', json={'choice': choice, 'parameter_id': parameter_id},
                       headers=headers)


# ---------------------------------------------------------------------------
# Metadata and dataset
# ---------------------------------------------------------------------------
def test_meta_lists_exactly_the_five_choices_and_the_footer(client):
    meta = client.get('/api/meta').get_json()
    assert [c['name'] for c in meta['choices']] == models.MODEL_CHOICES
    assert meta['footer'] == FOOTER
    for choice in meta['choices']:
        assert choice['default_id'] in [o['id'] for o in choice['options']]
    ensemble = meta['choices'][-1]
    assert [o['id'] for o in ensemble['options']] == ['Equal weights', 'Weighted average']
    assert 'never searches' in ensemble['ensemble_notes']['Equal weights']


def test_dataset_returns_the_approved_snapshot(client):
    dataset = client.get('/api/dataset').get_json()
    assert len(dataset['rows']) == models.EXPECTED_ROWS
    assert {'date', 'store_id', 'category', 'weekday', 'units_sold'} <= set(dataset['columns'])


def test_source_endpoint_reads_the_engine(client):
    source = client.get('/api/source?choice=KNN regression').get_json()['source']
    assert 'def make_knn' in source and 'def make_pipeline' in source
    assert client.get('/api/source?choice=Baseline').status_code == 400


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------
def test_train_returns_the_four_metrics_matching_the_engine(client, fit_once):
    body = train(client).get_json()
    engine = fit_once('Regression tree', 3)
    for metric in ['R2', 'MSE', 'RMSE', 'MAPE']:
        assert body['scores'][metric] == pytest.approx(engine['scores'][metric])
    assert body['development_rows'] == 18300 and body['test_rows'] == 4575
    assert 'classroom exploration' in body['historical_note']


def test_train_rejects_values_outside_classroom_presets(client):
    assert train(client, parameter_id='99').status_code == 400
    assert train(client, choice='Mean baseline', parameter_id='5').status_code == 400
    assert train(client, headers={}).status_code == 400  # no session


# ---------------------------------------------------------------------------
# Predict
# ---------------------------------------------------------------------------
def test_predict_before_training_is_blocked(client):
    response = client.post('/api/predict', json={
        'choice': 'Regression tree', 'parameter_id': '3',
        'store': '3', 'category': 'Bakery', 'date': '2025-10-15', 'actual': ''}, headers=SESSION)
    assert response.status_code == 409
    assert 'Train a model in the Model tab' in response.get_json()['error']


def test_predict_equals_direct_engine_predict(client, fit_once):
    train(client)
    response = client.post('/api/predict', json={
        'choice': 'Regression tree', 'parameter_id': '3',
        'store': '3', 'category': ' bakery ', 'date': '2025-10-15', 'actual': '20'},
        headers=SESSION)
    body = response.get_json()
    row = models.make_prediction_row('3', 'Bakery', '2025-10-15')
    expected = models.predict_one(fit_once('Regression tree', 3)['pipeline'], row)
    assert body['predicted'] == pytest.approx(expected)  # deterministic tree: same fit, same value
    assert body['canonical'] == {'store_id': '3', 'category': 'Bakery', 'date': '2025-10-15',
                                 'weekday': 'Wednesday', 'day_of_year': 288}
    assert body['actual_eval']['signed_error'] == pytest.approx(20 - body['predicted'])
    assert body['actual_eval']['ape_percent'] == pytest.approx(
        100 * abs(20 - body['predicted']) / 20)
    assert [body['scores'][m] is not None for m in ['R2', 'MSE', 'RMSE', 'MAPE']]


def test_invalid_typed_inputs_get_helpful_errors(client):
    train(client)
    response = client.post('/api/predict', json={
        'choice': 'Regression tree', 'parameter_id': '3',
        'store': '9', 'category': 'Toys', 'date': '15/10/2025', 'actual': '-2'}, headers=SESSION)
    assert response.status_code == 400
    errors = ' '.join(response.get_json()['errors'])
    assert 'Valid stores' in errors and 'YYYY-MM-DD' in errors
    assert 'not in the dataset' in errors and 'nonnegative' in errors


def test_changed_configuration_requires_retraining(client):
    train(client, parameter_id='3')
    response = client.post('/api/predict', json={
        'choice': 'Regression tree', 'parameter_id': '6',
        'store': '3', 'category': 'Bakery', 'date': '2025-10-15', 'actual': ''}, headers=SESSION)
    assert response.status_code == 409
    assert 'Train the new configuration' in response.get_json()['error']


def test_sessions_are_isolated(client):
    train(client, headers={'X-Session-Id': 'student-a'})
    response = client.post('/api/predict', json={
        'choice': 'Regression tree', 'parameter_id': '3',
        'store': '3', 'category': 'Bakery', 'date': '2025-10-15', 'actual': ''},
        headers={'X-Session-Id': 'student-b'})
    assert response.status_code == 409  # student B has no trained model


# ---------------------------------------------------------------------------
# Static dashboard structure
# ---------------------------------------------------------------------------
def test_frontend_three_tabs_footer_and_no_removed_actions():
    html = (APP_DIR / 'server' / 'static' / 'index.html').read_text()
    tabs = [part.split('"')[0] for part in html.split('data-tab="')[1:]]
    assert tabs == ['data', 'model', 'test']
    assert html.count(FOOTER) == 1  # one shared footer element, visible under every tab
    assert html.count('metric-card"') == 4  # exactly the four performance cards
    for removed in ['Run classroom comparison', 'leaderboard', 'baseline', 'Compare and select',
                    'Finalize']:
        assert removed not in html
    javascript = (APP_DIR / 'server' / 'static' / 'app.js').read_text()
    assert 'invalidateIfChanged' in javascript  # model/parameter changes clear stale results
