"""Dashboard behavior test with Streamlit's headless AppTest.

Drives the real app: checks the three-tab layout and footer, trains one
configuration, verifies the four metric cards, makes a typed prediction equal
to the engine's direct ``.predict`` on the same fitted pipeline, and checks
that model/parameter changes clear stale results and disable prediction.
"""
import pytest
from streamlit.testing.v1 import AppTest

import models
from conftest import APP_DIR

pytest.importorskip('streamlit')

FOOTER = 'Business Analytics and Data Visualization Fall 2026 - Prof. Jose Mendoza'
METRIC_LABELS = ['R²', 'MSE', 'RMSE', 'MAPE']


def _app():
    at = AppTest.from_file(str(APP_DIR / 'app.py'), default_timeout=600)
    return at.run()


def _button(at, label):
    matches = [b for b in at.button if b.label == label]
    assert matches, f'Button {label!r} not found'
    return matches[0]


def test_initial_launch_three_tabs_footer_no_results():
    at = _app()
    assert not at.exception
    assert at.title[0].value == 'Business Analytics in Action: From Model to App'
    # Exactly three tabs, in order.
    assert [tab.label for tab in at.tabs] == ['Data', 'Model', 'Test']
    # The exact footer on every tab.
    assert [c.value for c in at.caption].count(FOOTER) == 3
    # Exactly the five allowed model choices; KNN default; no result yet.
    selector = at.selectbox(key='model_choice')
    assert selector.options == models.MODEL_CHOICES and selector.value == 'KNN regression'
    assert len(at.metric) == 0 and at.session_state['active'] is None
    assert any('Train a model in the Model tab' in i.value for i in at.info)
    # None of the removed version-1 actions exist.
    labels = {b.label for b in at.button}
    assert labels <= {'Train model', 'Use example', 'Predict'}
    assert 'Run classroom comparison' not in labels and 'Predict' not in labels


def test_parameter_control_follows_the_selected_model():
    at = _app()
    def visible_param_keys():
        return [s.key for s in at.selectbox if s.key and s.key.startswith('param_')]
    assert visible_param_keys() == ['param_KNN regression']
    assert at.selectbox(key='param_KNN regression').value == 15
    at.selectbox(key='model_choice').set_value('Ensemble regression').run()
    assert visible_param_keys() == ['param_Ensemble regression']
    assert at.selectbox(key='param_Ensemble regression').value == 'Equal weights'
    assert not at.exception


def test_train_predict_and_invalidation_flow(data):
    at = _app()
    # Train the default KNN (k=15).
    _button(at, 'Train model').click().run()
    assert not at.exception
    active = at.session_state['active']
    assert active is not None and active['config'] == ('KNN regression', 15)
    # Exactly four model-performance cards, in order.
    assert [m.label for m in at.metric] == METRIC_LABELS
    # Displayed metrics come from the retained fitted pipeline on the test rows.
    scores = models.evaluate_model(data['y_test'], active['pipeline'].predict(data['X_test']))
    assert scores['RMSE'] == pytest.approx(active['scores']['RMSE'])

    # Typed prediction equals direct engine .predict on the same fitted object.
    at.session_state['store_text'] = '3'
    at.session_state['category_text'] = ' bakery '
    at.session_state['date_text'] = '2025-10-15'
    at.session_state['actual_text'] = '20'
    _button(at, 'Predict').click().run()
    assert not at.exception
    p = at.session_state['last_prediction']
    row = models.make_prediction_row('3', 'Bakery', '2025-10-15')
    assert p['values']['category'] == 'Bakery'
    assert p['predicted'] == models.predict_one(at.session_state['active']['pipeline'], row)
    shown = [m.value for m in at.markdown if 'Predicted daily sales' in m.value]
    assert shown and f"{p['predicted']:.2f}" in shown[0]

    # Invalid typed inputs never reach .predict and give helpful errors.
    at.session_state['store_text'] = '9'
    at.session_state['date_text'] = '15/10/2025'
    _button(at, 'Predict').click().run()
    assert any('Valid stores' in e.value for e in at.error)
    assert any('YYYY-MM-DD' in e.value for e in at.error)

    # A parameter change clears the fit, metrics and prediction.
    at.selectbox(key='param_KNN regression').set_value(5).run()
    assert not at.exception
    assert at.session_state['active'] is None and at.session_state['last_prediction'] is None
    assert len(at.metric) == 0
    assert any('Train a model in the Model tab' in i.value for i in at.info)
