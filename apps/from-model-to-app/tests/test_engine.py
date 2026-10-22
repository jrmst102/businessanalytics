"""Engine-contract and metric checks (fast; no model fitting beyond one small tree)."""
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.preprocessing import StandardScaler

import models


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------
def test_dataset_snapshot_is_the_approved_one(data):
    assert models.dataset_checksum() == models.DATA_SHA256
    description = models.describe_data(data['df'])
    assert (description['Observations'], description['Stores'], description['Categories']) == (
        models.EXPECTED_ROWS, models.EXPECTED_STORES, models.EXPECTED_CATEGORIES)
    assert str(description['First date']) == '2025-01-01'
    assert str(description['Last date']) == '2025-11-01'


def test_partitions_are_chronological_and_complete(data):
    train, validation, test = data['train'], data['validation'], data['test']
    assert [len(train), len(validation), len(test)] == [13725, 4575, 4575]
    assert train.date.max() < validation.date.min() <= validation.date.max() < test.date.min()
    for a, b in [(train, validation), (validation, test), (train, test)]:
        assert not set(a.date.unique()) & set(b.date.unique())
    assert len(train) + len(validation) + len(test) == len(data['df'])
    assert str(data['train_end'].date()) == '2025-07-02' and str(data['validation_end'].date()) == '2025-09-01'


def test_feature_contract(data):
    assert list(data['X_train'].columns) == ['store_id', 'category', 'weekday', 'day_of_year'] == models.FEATURES
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


# ---------------------------------------------------------------------------
# Classroom constructors and presets
# ---------------------------------------------------------------------------
def numeric_step(pipeline):
    return {name: trans for name, trans, _ in pipeline.named_steps['prepare'].transformers}['numeric']


def test_knn_constructor_preserves_classroom_settings():
    pipeline, _ = models.build_model('KNN regression', 15)
    knn = pipeline.named_steps['model']
    assert (knn.n_neighbors, knn.weights, knn.n_jobs) == (15, 'uniform', -1)
    assert isinstance(numeric_step(pipeline), StandardScaler)


def test_tree_constructor_preserves_classroom_settings():
    pipeline, _ = models.build_model('Regression tree', 6)
    tree = pipeline.named_steps['model']
    assert (tree.max_depth, tree.min_samples_leaf, tree.random_state) == (6, 30, 42)
    assert numeric_step(pipeline) == 'passthrough'


def test_forest_constructor_preserves_classroom_settings():
    pipeline, _ = models.build_model('Random forest', 200)
    forest = pipeline.named_steps['model']
    assert (forest.n_estimators, forest.max_depth, forest.min_samples_leaf,
            forest.max_features, forest.bootstrap, forest.random_state, forest.n_jobs) == (
        200, 12, 30, 0.8, True, 42, -1)
    assert numeric_step(pipeline) == 'passthrough'


def test_network_constructor_preserves_classroom_settings():
    pipeline, _ = models.build_model('Neural network', (32, 16))
    wrapped = pipeline.named_steps['model']
    assert isinstance(wrapped, TransformedTargetRegressor)
    assert isinstance(wrapped.transformer, StandardScaler)
    net = wrapped.regressor
    assert net.hidden_layer_sizes == (32, 16)
    assert (net.activation, net.solver, net.alpha, net.batch_size, net.learning_rate_init,
            net.max_iter, net.early_stopping, net.validation_fraction, net.n_iter_no_change,
            net.random_state) == ('relu', 'adam', 0.01, 256, 0.001, 300, True, 0.15, 20, 42)
    assert isinstance(numeric_step(pipeline), StandardScaler)


def test_ensemble_uses_fixed_classroom_members():
    for method, expected_weights in [('Equal weights', None), ('Weighted average', [1, 1, 2, 2])]:
        ensemble, _ = models.build_model('Ensemble regression', method)
        assert isinstance(ensemble, VotingRegressor)
        assert ensemble.n_jobs == 1 and ensemble.weights == expected_weights
        names = [name for name, _ in ensemble.estimators]
        assert names == ['model_0', 'model_1', 'model_2', 'model_3']
        knn, tree, forest, network = [est.named_steps['model'] for _, est in ensemble.estimators]
        assert knn.n_neighbors == 50 and knn.weights == 'uniform'
        assert (tree.max_depth, tree.min_samples_leaf) == (12, 30)
        assert (forest.n_estimators, forest.max_depth, forest.min_samples_leaf,
                forest.max_features) == (100, 12, 30, 0.8)
        assert network.regressor.hidden_layer_sizes == (16,)
    assert list(models.normalized_weights(models.ENSEMBLE_WEIGHTS)) == pytest.approx(
        [1 / 6, 1 / 6, 1 / 3, 1 / 3])


def test_build_model_rejects_values_outside_classroom_presets():
    for choice, bad in [('KNN regression', 7), ('Regression tree', 99), ('Random forest', 10),
                        ('Neural network', (64,)), ('Ensemble regression', 'Optimized weights')]:
        with pytest.raises(ValueError, match='classroom preset'):
            models.build_model(choice, bad)
    with pytest.raises(ValueError):
        models.build_model('Mean baseline', None)


# ---------------------------------------------------------------------------
# Metric definitions: hand-calculable examples (spec section 14)
# ---------------------------------------------------------------------------
def test_perfect_predictions_give_zero_errors():
    scores = models.evaluate_model([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert scores['MSE'] == 0 and scores['RMSE'] == 0 and scores['MAPE'] == 0
    assert scores['R2'] == pytest.approx(1.0)


def test_mse_and_rmse_hand_example():
    # Errors 1 and -2: MSE = (1 + 4) / 2 = 2.5; RMSE = sqrt(2.5).
    scores = models.evaluate_model([2.0, 4.0], [1.0, 6.0])
    assert scores['MSE'] == pytest.approx(2.5)
    assert scores['RMSE'] == pytest.approx(np.sqrt(2.5))


def test_mape_hand_example_in_percent():
    # APEs 0.1 and 0.2 -> mean 0.15 -> 15%.
    scores = models.evaluate_model([10.0, 20.0], [9.0, 24.0])
    assert scores['MAPE'] == pytest.approx(15.0)
    assert scores['positive_observations'] == 2 and scores['zero_excluded_from_mape'] == 0


def test_mixed_zero_actuals_excluded_from_mape_only():
    scores = models.evaluate_model([0.0, 10.0], [5.0, 12.0])
    assert scores['MAPE'] == pytest.approx(20.0)  # only the positive row
    assert scores['zero_excluded_from_mape'] == 1 and scores['positive_observations'] == 1
    assert scores['MSE'] == pytest.approx((25 + 4) / 2)  # both rows
    assert scores['observations'] == 2


def test_all_zero_actuals_give_mape_na():
    scores = models.evaluate_model([0.0, 0.0], [1.0, 2.0])
    assert scores['MAPE'] is None
    assert 'no positive actual sales' in scores['MAPE_note']
    assert scores['MSE'] == pytest.approx(2.5) and scores['RMSE'] == pytest.approx(np.sqrt(2.5))


def test_constant_actuals_give_r2_undefined():
    scores = models.evaluate_model([5.0, 5.0], [4.0, 6.0])
    assert scores['R2'] is None and 'undefined' in scores['R2_note']
    assert scores['MSE'] == pytest.approx(1.0)


def test_metrics_use_raw_unrounded_values():
    scores = models.evaluate_model([3.0], [2.0])
    assert scores['MAPE'] == pytest.approx(100 / 3)  # not rounded to 33.33


# ---------------------------------------------------------------------------
# Fitting workflow and typed prediction
# ---------------------------------------------------------------------------
def test_fit_selected_model_refits_on_development_and_scores_test(data, fit_once):
    result = fit_once('Regression tree', 3)
    assert result['development_rows'] == 18300 and result['test_rows'] == 4575
    assert result['development_end'] == data['validation_end']
    assert result['test_start'] > data['validation_end']
    assert len(result['test_predictions']) == 4575
    # The retained pipeline is the exact object whose metrics are displayed.
    again = result['pipeline'].predict(data['X_test'])
    np.testing.assert_allclose(again, result['test_predictions'], rtol=1e-7, atol=1e-7)
    assert set(result['scores']) >= {'R2', 'MSE', 'RMSE', 'MAPE'}
    assert result['scores']['RMSE'] == pytest.approx(np.sqrt(result['scores']['MSE']))


def test_prediction_row_and_predict_one(data, fit_once):
    row = models.make_prediction_row('3', 'Bakery', '2025-10-15')
    assert list(row.columns) == models.FEATURES
    assert row.iloc[0]['weekday'] == 'Wednesday' and row.iloc[0]['day_of_year'] == 288
    pipeline = fit_once('Regression tree', 3)['pipeline']
    assert models.predict_one(pipeline, row) == float(pipeline.predict(row)[0])


def test_run_identity_records_development_and_test_periods(data):
    record = models.run_identity('KNN regression', 'n_neighbors=15', data)
    assert 'Training + validation (development): 2025-01-01 to 2025-09-01' in record['Fitting period']
    assert 'Test: 2025-09-02 to 2025-11-01' in record['Evaluation period']
    assert record['Dataset SHA-256'] == models.DATA_SHA256 and record['Seed'] == 42
