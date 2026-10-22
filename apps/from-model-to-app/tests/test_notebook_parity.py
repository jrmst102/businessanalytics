"""Release gate: the engine reproduces the reference notebook's numbers."""
import numpy as np
import pandas as pd
from numpy.testing import assert_allclose

import models

TOL = dict(rtol=1e-7, atol=1e-7)


def test_data_preparation_matches_notebook(data, notebook_ns):
    pd.testing.assert_frame_equal(data['df'], notebook_ns['df'])
    assert notebook_ns['FEATURES'] == models.FEATURES
    assert notebook_ns['TARGET'] == models.TARGET
    for key in ['X_train', 'y_train', 'X_val', 'y_val', 'X_test', 'y_test']:
        getattr(pd.testing, 'assert_frame_equal' if key.startswith('X') else 'assert_series_equal')(
            data[key], notebook_ns[key])
    assert data['train_end'] == pd.Timestamp(notebook_ns['train_end'])
    assert data['validation_end'] == pd.Timestamp(notebook_ns['validation_end'])


def test_preprocessing_matches_notebook(data, candidates, notebook_ns):
    for name in ['KNN (k=5)', 'Tree (depth=3)']:
        ours = candidates[name]['model'].named_steps['prepare']
        theirs = notebook_ns['models'][name].named_steps['prepare']
        assert list(ours.get_feature_names_out()) == list(theirs.get_feature_names_out())
        assert_allclose(ours.transform(data['X_val'].head(50)), theirs.transform(data['X_val'].head(50)), **TOL)


def test_all_fifteen_candidates_match_notebook(candidates, notebook_ns):
    results, predictions = notebook_ns['results'], notebook_ns['validation_predictions']
    assert list(results) == models.CANDIDATE_ORDER == list(models.results_table(candidates))
    for name in models.CANDIDATE_ORDER:
        assert_allclose(candidates[name]['validation_predictions'], predictions[name], **TOL, err_msg=name)
        for metric in ['Train MAE', 'Validation MAE', 'Validation RMSE', 'Validation R2']:
            assert_allclose(candidates[name]['result'][metric], results[name][metric], **TOL, err_msg=f'{name} {metric}')
        assert candidates[name]['family'] == results[name]['Family']


def test_ensemble_members_and_selection_match_notebook(candidates, notebook_ns):
    assert models.family_winners(candidates) == notebook_ns['family_winners']
    assert models.select_model(candidates) == notebook_ns['selected_name']
    gain = models.ensemble_gain(candidates)
    assert gain['best_individual'] == notebook_ns['best_individual']
    assert gain['best_ensemble'] == notebook_ns['best_ensemble']
    assert_allclose(gain['ensemble_gain_units'], notebook_ns['ensemble_gain_units'], **TOL)
    weighted = candidates[models.WEIGHTED_ENSEMBLE_NAME]['model']
    assert weighted.weights == models.ENSEMBLE_WEIGHTS == notebook_ns['ENSEMBLE_WEIGHTS']
    assert [n for n, _ in weighted.estimators] == ['model_0', 'model_1', 'model_2', 'model_3']


def test_ensemble_arithmetic_on_rows(candidates, data):
    rows = data['X_val'].iloc[[0, 7, 123, 999, 4000]]
    for name, weights in [(models.EQUAL_ENSEMBLE_NAME, None), (models.WEIGHTED_ENSEMBLE_NAME, models.ENSEMBLE_WEIGHTS)]:
        fitted = candidates[name]['model']
        member_predictions = np.column_stack([m.predict(rows) for m in fitted.estimators_])
        expected = np.average(member_predictions, axis=1, weights=weights)
        assert_allclose(fitted.predict(rows), expected, **TOL, err_msg=name)
    members = candidates[models.WEIGHTED_ENSEMBLE_NAME]['model'].estimators_
    assert len(members) == 4
    assert_allclose(models.normalized_weights(models.ENSEMBLE_WEIGHTS), [1 / 6, 1 / 6, 1 / 3, 1 / 3])


def test_final_refit_matches_notebook(final, notebook_ns):
    assert final['selected_name'] == notebook_ns['selected_name']
    assert_allclose(final['test_predictions'], notebook_ns['test_predictions'], **TOL)
    assert_allclose(final['baseline_predictions'], notebook_ns['baseline_predictions'], **TOL)
    for metric in ['MAE', 'RMSE', 'R2']:
        assert_allclose(final['selected_test_metrics'][metric], notebook_ns['selected_test_metrics'][metric], **TOL)
        assert_allclose(final['baseline_test_metrics'][metric], notebook_ns['baseline_test_metrics'][metric], **TOL)
    assert_allclose(final['mean_bias'], notebook_ns['mean_bias'], **TOL)
    assert_allclose(final['underprediction_rate'], notebook_ns['underprediction_rate'], **TOL)
    pd.testing.assert_frame_equal(final['store_diagnostics'], notebook_ns['store_diagnostics'])
    pd.testing.assert_frame_equal(final['category_diagnostics'], notebook_ns['category_diagnostics'])


def test_typed_example_equals_direct_predict(candidates, final):
    row = models.make_prediction_row('3', 'Bakery', '2025-10-15')
    assert list(row.columns) == models.FEATURES
    assert row.iloc[0]['weekday'] == 'Wednesday' and row.iloc[0]['day_of_year'] == 288
    for pipeline in [candidates['KNN (k=15)']['model'], final['final_model']]:
        assert models.predict_one(pipeline, row) == float(pipeline.predict(row)[0])
