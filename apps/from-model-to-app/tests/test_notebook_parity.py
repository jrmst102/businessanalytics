"""Release gate: each allowed configuration reproduces its direct classroom implementation.

For every preset the engine's development-set refit is compared against the
same specification written out verbatim with scikit-learn (the classroom
constructors from the Mancino notebooks), fitted on the same development data
and scored on the same test rows, at rtol=1e-7, atol=1e-7. Data preparation is
compared against the final notebook's own cells executed verbatim.
"""
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

import models

TOL = dict(rtol=1e-7, atol=1e-7)
SEED = 42

ALL_CONFIGS = [(choice, value)
               for choice in models.MODEL_CHOICES
               for value in models.PRESETS[choice]['values']]


# --- Direct classroom implementations, written out from the notebooks -------
def reference_pipeline(estimator, scale_numeric=False):
    preparation = ColumnTransformer([
        ('categories', OneHotEncoder(handle_unknown='ignore', sparse_output=False),
         ['store_id', 'category', 'weekday']),
        ('numeric', StandardScaler() if scale_numeric else 'passthrough', ['day_of_year'])
    ])
    return Pipeline([('prepare', preparation), ('model', estimator)])


def reference_network(layers):
    return TransformedTargetRegressor(
        regressor=MLPRegressor(hidden_layer_sizes=layers, activation='relu', solver='adam',
                               alpha=0.01, batch_size=256, learning_rate_init=0.001,
                               max_iter=300, early_stopping=True, validation_fraction=0.15,
                               n_iter_no_change=20, random_state=SEED),
        transformer=StandardScaler())


def reference_estimator(choice, parameter):
    if choice == 'KNN regression':
        return reference_pipeline(
            KNeighborsRegressor(n_neighbors=parameter, weights='uniform', n_jobs=-1), True)
    if choice == 'Regression tree':
        return reference_pipeline(DecisionTreeRegressor(
            max_depth=parameter, min_samples_leaf=30, random_state=SEED))
    if choice == 'Random forest':
        return reference_pipeline(RandomForestRegressor(
            n_estimators=parameter, max_depth=12, min_samples_leaf=30,
            max_features=0.8, bootstrap=True, random_state=SEED, n_jobs=-1))
    if choice == 'Neural network':
        return reference_pipeline(reference_network(parameter), True)
    # Fixed members from Mancino_Ensemble_Complete.ipynb, in the notebook's order.
    base_estimators = {
        'KNN': reference_pipeline(
            KNeighborsRegressor(n_neighbors=50, weights='uniform', n_jobs=-1), True),
        'Regression tree': reference_pipeline(DecisionTreeRegressor(
            max_depth=12, min_samples_leaf=30, random_state=SEED)),
        'Random forest': reference_pipeline(RandomForestRegressor(
            n_estimators=100, max_depth=12, min_samples_leaf=30,
            max_features=0.8, bootstrap=True, random_state=SEED, n_jobs=-1)),
        'Neural network': reference_pipeline(reference_network((16,)), True),
    }
    members = [(f'model_{i}', estimator) for i, estimator in enumerate(base_estimators.values())]
    weights = [1, 1, 2, 2] if parameter == 'Weighted average' else None
    return VotingRegressor(estimators=members, weights=weights, n_jobs=1)


# --- Data preparation parity against the final notebook's own cells ---------
def test_data_preparation_matches_notebook(data, notebook_ns):
    pd.testing.assert_frame_equal(data['df'], notebook_ns['df'])
    assert notebook_ns['FEATURES'] == models.FEATURES
    assert notebook_ns['TARGET'] == models.TARGET
    for key in ['X_train', 'y_train', 'X_val', 'y_val', 'X_test', 'y_test']:
        getattr(pd.testing, 'assert_frame_equal' if key.startswith('X') else 'assert_series_equal')(
            data[key], notebook_ns[key])
    assert data['train_end'] == pd.Timestamp(notebook_ns['train_end'])
    assert data['validation_end'] == pd.Timestamp(notebook_ns['validation_end'])


# --- Prediction parity, one configuration at a time --------------------------
@pytest.mark.parametrize('choice,parameter', ALL_CONFIGS,
                         ids=[f'{c} | {p}' for c, p in ALL_CONFIGS])
def test_each_configuration_matches_direct_classroom_refit(choice, parameter, data, fit_once):
    engine = fit_once(choice, parameter)
    X_development = pd.concat([data['X_train'], data['X_val']])
    y_development = pd.concat([data['y_train'], data['y_val']])
    reference = reference_estimator(choice, parameter).fit(X_development, y_development)
    reference_predictions = reference.predict(data['X_test'])
    assert_allclose(engine['test_predictions'], reference_predictions, **TOL,
                    err_msg=f'{choice} | {parameter}')
    # The displayed metrics follow from the same predictions.
    reference_scores = models.evaluate_model(data['y_test'], reference_predictions)
    for metric in ['R2', 'MSE', 'RMSE', 'MAPE']:
        assert_allclose(engine['scores'][metric], reference_scores[metric], **TOL,
                        err_msg=f'{choice} | {parameter} | {metric}')


def test_encoded_columns_and_scaling(data, fit_once):
    scaled = fit_once('KNN regression', 15)['pipeline'].named_steps['prepare']
    passthrough = fit_once('Regression tree', 3)['pipeline'].named_steps['prepare']
    names = list(scaled.get_feature_names_out())
    assert names == list(passthrough.get_feature_names_out())
    assert sum(n.startswith('categories__') for n in names) == 5 + 15 + 7
    assert names[-1] == 'numeric__day_of_year'
    sample = data['X_test'].head(50)
    day = sample[['day_of_year']].to_numpy(dtype=float)
    assert_allclose(passthrough.transform(sample)[:, -1], day[:, 0], **TOL)
    assert not np.allclose(scaled.transform(sample)[:, -1], day[:, 0])  # standardized for KNN


def test_ensemble_combines_members_as_weighted_average(data, fit_once):
    rows = data['X_test'].iloc[[0, 7, 123, 999, 4000]]
    for method, weights in [('Equal weights', None), ('Weighted average', models.ENSEMBLE_WEIGHTS)]:
        fitted = fit_once('Ensemble regression', method)['pipeline']
        member_predictions = np.column_stack([m.predict(rows) for m in fitted.estimators_])
        expected = np.average(member_predictions, axis=1, weights=weights)
        assert_allclose(fitted.predict(rows), expected, **TOL, err_msg=method)
        assert len(fitted.estimators_) == 4


def test_typed_example_equals_direct_predict(fit_once):
    row = models.make_prediction_row('3', 'Bakery', '2025-10-15')
    for choice, parameter in [('KNN regression', 15), ('Ensemble regression', 'Equal weights')]:
        pipeline = fit_once(choice, parameter)['pipeline']
        assert models.predict_one(pipeline, row) == float(pipeline.predict(row)[0])
