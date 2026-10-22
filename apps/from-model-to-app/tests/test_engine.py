"""Evaluation-process and engine-contract checks (fast; no notebook execution)."""
import numpy as np
import pandas as pd
import pytest

import models


def test_dataset_snapshot_is_the_approved_one(data):
    assert models.dataset_checksum() == models.DATA_SHA256
    description = models.describe_data(data['df'])
    assert (description['Rows'], description['Stores'], description['Categories']) == (
        models.EXPECTED_ROWS, models.EXPECTED_STORES, models.EXPECTED_CATEGORIES)


def test_partitions_are_chronological_and_complete(data):
    train, validation, test = data['train'], data['validation'], data['test']
    assert [len(train), len(validation), len(test)] == [13725, 4575, 4575]
    assert train.date.max() < validation.date.min() <= validation.date.max() < test.date.min()
    for a, b in [(train, validation), (validation, test), (train, test)]:
        assert not set(a.date.unique()) & set(b.date.unique())
    assert len(train) + len(validation) + len(test) == len(data['df'])
    assert str(data['train_end'].date()) == '2025-07-02' and str(data['validation_end'].date()) == '2025-09-01'


def test_feature_contract(data):
    assert list(data['X_train'].columns) == ['store_id', 'category', 'weekday', 'day_of_year']
    assert data['X_train']['store_id'].dtype == object
    assert 'revenue' not in data['X_train'] and 'avg_price' not in data['X_train']
    assert (data['df']['weekday'] == data['df']['date'].dt.day_name()).all()


def test_load_data_rejects_invalid_files(tmp_path):
    good = pd.read_csv(models.DATA_PATH).head(20)
    cases = {
        'missing column': good.drop(columns=['units_sold']),
        'duplicate rows': pd.concat([good, good.head(1)]),
        'negative target': good.assign(units_sold=good.units_sold - 100),
        'bad date': good.assign(date=['not-a-date'] + list(good.date[1:])),
        'missing value': good.assign(category=[None] + list(good.category[1:])),
    }
    for label, frame in cases.items():
        path = tmp_path / f'{label}.csv'
        frame.to_csv(path, index=False)
        with pytest.raises(ValueError, match='.'):
            models.load_data(path)
    with pytest.raises(FileNotFoundError):
        models.load_data(tmp_path / 'absent.csv')


def _fake(name, family, mae):
    return {'name': name, 'family': family, 'settings': '', 'specification': None, 'model': None,
            'validation_predictions': None, 'warnings': [],
            'result': {'Model': name, 'Family': family, 'Settings': '', 'Train MAE': mae,
                       'Validation MAE': mae, 'Validation RMSE': mae, 'Validation R2': 0.0, 'Fit seconds': 0.0}}


def test_selection_breaks_ties_by_notebook_order():
    fakes = {
        'Tree (depth=3)': _fake('Tree (depth=3)', 'Regression tree', 5.0),
        models.BASELINE_NAME: _fake(models.BASELINE_NAME, 'Baseline', 5.0),
        'KNN (k=5)': _fake('KNN (k=5)', 'KNN', 5.0),
    }
    assert models.select_model(fakes) == models.BASELINE_NAME
    fakes['KNN (k=5)']['result']['Validation MAE'] = 4.9999999999
    assert models.select_model(fakes) == 'KNN (k=5)'


def test_leaderboard_handles_zero_baseline_mae():
    fakes = {models.BASELINE_NAME: _fake(models.BASELINE_NAME, 'Baseline', 0.0),
             'KNN (k=5)': _fake('KNN (k=5)', 'KNN', 1.0)}
    board = models.leaderboard(fakes)
    assert board['MAE improvement vs baseline (%)'].isna().all()


def test_family_winners_refuses_partial_comparison():
    fakes = {'KNN (k=5)': _fake('KNN (k=5)', 'KNN', 1.0)}
    with pytest.raises(ValueError, match='All 12 individual presets'):
        models.family_winners(fakes)


def test_clear_family_drops_dependent_ensembles():
    fakes = {'KNN (k=5)': _fake('KNN (k=5)', 'KNN', 1.0),
             'Tree (depth=3)': _fake('Tree (depth=3)', 'Regression tree', 1.0),
             models.EQUAL_ENSEMBLE_NAME: _fake(models.EQUAL_ENSEMBLE_NAME, 'Ensemble', 1.0)}
    models.clear_family(fakes, 'KNN')
    assert list(fakes) == ['Tree (depth=3)']


def test_segment_errors_leaves_zero_sales_wape_undefined():
    diagnostics = pd.DataFrame({'store_id': ['1', '1', '2'], 'units_sold': [0, 0, 10],
                                'error': [1.0, -1.0, 2.0], 'absolute_error': [1.0, 1.0, 2.0]})
    table = models.segment_errors(diagnostics, 'store_id')
    assert np.isnan(table.loc['1', 'WAPE_percent'])
    assert table.loc['2', 'WAPE_percent'] == pytest.approx(20.0)


def test_finalize_uses_development_period_and_frozen_spec(data):
    spec = models.candidate_by_name('Tree (depth=3)')['estimator']
    final = models.finalize_model('Tree (depth=3)', models.clone(spec), data)
    assert final['final_baseline'].constant_[0][0] == pytest.approx(
        pd.concat([data['y_train'], data['y_val']]).mean())
    assert len(final['test_predictions']) == len(data['X_test']) == 4575
    assert final['development_end'] == data['validation_end']
    assert final['test_start'] > data['validation_end']
    assert set(final['diagnostics'].columns) >= {'predicted_units', 'error', 'absolute_error', 'underpredicted'}
    briefing = models.managerial_briefing(final, 'Regression tree')
    assert 'Test MAE was' in briefing and 'Student recommendation' in briefing


def test_run_identity_distinguishes_stages(data):
    experiment = models.run_identity('KNN (k=5)', 'k=5', data, 'experiment')
    final = models.run_identity('KNN (k=5)', 'k=5', data, 'final')
    assert experiment['Run key'] != final['Run key']
    assert 'Training: 2025-01-01 to 2025-07-02' in experiment['Fitting period']
    assert 'Test: 2025-09-02 to 2025-11-01' in final['Evaluation period']
