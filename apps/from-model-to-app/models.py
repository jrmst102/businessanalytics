"""Classroom engine for "Business Analytics in Action: From Model to App".

Every function here is lifted from ``notebooks/Mancino_Regression_Final.ipynb``
and kept in the notebook's order. The dashboard (``app.py``) only calls these
functions and displays what they return; it never defines a second model.
Cell identifiers in the section headers refer to that notebook, and
``NOTEBOOK_MAP.md`` lists every adaptation made while moving cells into
functions. No Streamlit import belongs in this file.
"""

# ---------------------------------------------------------------------------
# 1. Import the tools and name the classroom constants      (final-002)
# ---------------------------------------------------------------------------
import hashlib
import platform
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.dummy import DummyRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

SEED = 42
np.random.seed(SEED)

# Approved teaching snapshot bundled with the app (see data/SOURCE.md).
DATA_PATH = Path(__file__).resolve().parent / 'data' / 'mancino_daily_sales.csv'
DATA_SOURCE_URL = ('https://github.com/jrmst102/mancino/blob/main/data/'
                   'v1_2025-11-01/mancino_daily_sales.csv')
DATA_SHA256 = '8441fb2df62432120396f81f3816f12bbd40007f03bb99fc0c1a79cfc1e028c1'
EXPECTED_ROWS, EXPECTED_STORES, EXPECTED_CATEGORIES = 22_875, 5, 15

# Feature contract (final-006).
CATEGORICAL = ['store_id', 'category', 'weekday']
NUMERIC = ['day_of_year']
FEATURES = CATEGORICAL + NUMERIC
TARGET = 'units_sold'

# Classroom presets (final-013 to final-021).
K_VALUES = [5, 15, 50]
TREE_DEPTHS = [3, 6, 12]
MIN_LEAF = 30
FOREST_SIZES = [50, 100, 200]
NETWORK_LAYERS = [(16,), (32,), (32, 16)]
FAMILIES = ['KNN', 'Regression tree', 'Random forest', 'Neural network']
ENSEMBLE_WEIGHTS = [1, 1, 2, 2]

BASELINE_NAME = 'Mean baseline'
EQUAL_ENSEMBLE_NAME = 'Ensemble: equal weights'
WEIGHTED_ENSEMBLE_NAME = 'Ensemble: weighted average'
ENSEMBLE_NAMES = [EQUAL_ENSEMBLE_NAME, WEIGHTED_ENSEMBLE_NAME]


def knn_name(k):
    return f'KNN (k={k})'


def tree_name(depth):
    return f'Tree (depth={depth})'


def forest_name(size):
    return f'Forest (trees={size})'


def network_name(layers):
    return f'Network (hidden={layers})'


# Notebook insertion order: baseline, then presets by family, then ensembles.
# ``min`` over this order reproduces the notebook's tie behavior (final-023).
CANDIDATE_ORDER = (
    [BASELINE_NAME]
    + [knn_name(k) for k in K_VALUES]
    + [tree_name(d) for d in TREE_DEPTHS]
    + [forest_name(s) for s in FOREST_SIZES]
    + [network_name(l) for l in NETWORK_LAYERS]
    + ENSEMBLE_NAMES
)
INDIVIDUAL_NAMES = [n for n in CANDIDATE_ORDER if n != BASELINE_NAME and n not in ENSEMBLE_NAMES]


# ---------------------------------------------------------------------------
# 2. Load and inspect the data                               (final-004)
# ---------------------------------------------------------------------------
def dataset_checksum(path=DATA_PATH):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_data(path=DATA_PATH):
    """Read the approved CSV and apply the notebook's validation checks.

    The notebook used ``assert``; the app raises ``ValueError`` with the same
    messages so a bad file produces an actionable error instead of a crash.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f'Dataset not found at {path}. Restore data/mancino_daily_sales.csv '
            f'from {DATA_SOURCE_URL} (see data/SOURCE.md).')
    df = pd.read_csv(path)

    required = {'date', 'store_id', 'category', 'units_sold'}
    if not required.issubset(df.columns):
        raise ValueError('The CSV is missing required columns: '
                         f'{sorted(required - set(df.columns))}.')
    try:
        df['date'] = pd.to_datetime(df['date'], errors='raise')
    except (ValueError, TypeError) as error:
        raise ValueError(f'Check unparseable dates in the CSV: {error}') from error
    if df[list(required)].isna().any().any():
        raise ValueError('Check missing required values.')
    if df.duplicated(['date', 'store_id', 'category']).any():
        raise ValueError('Check duplicate rows: (date, store_id, category) must be unique.')
    if not pd.api.types.is_numeric_dtype(df['units_sold']):
        raise ValueError('units_sold must be numeric.')
    if not df['units_sold'].ge(0).all():
        raise ValueError('Check negative unit sales.')
    df = df.sort_values(['date', 'store_id', 'category']).reset_index(drop=True)
    return df


def describe_data(df):
    """Row count, stores, categories, and date range (the notebook's print lines)."""
    return {
        'Rows': len(df),
        'Stores': df.store_id.nunique(),
        'Categories': df.category.nunique(),
        'First date': df.date.min().date(),
        'Last date': df.date.max().date(),
    }


# ---------------------------------------------------------------------------
# 3. Define predictors and split by date                     (final-006)
# ---------------------------------------------------------------------------
def prepare_data(df):
    """Derive the four classroom features and the chronological partitions.

    Returns an ordinary dictionary so the notebook's names (``X_train``,
    ``y_val`` ...) stay recognizable: ``data['X_train']`` is the notebook's
    ``X_train``.
    """
    df = df.copy()
    df['store_id'] = df['store_id'].astype(str)
    df['weekday'] = df['date'].dt.day_name()
    df['day_of_year'] = df['date'].dt.dayofyear

    dates = np.sort(df['date'].unique())
    train_end = dates[int(len(dates) * 0.60) - 1]
    validation_end = dates[int(len(dates) * 0.80) - 1]
    train = df.loc[df.date <= train_end].copy()
    validation = df.loc[(df.date > train_end) & (df.date <= validation_end)].copy()
    test = df.loc[df.date > validation_end].copy()
    assert train.date.max() < validation.date.min() <= validation.date.max() < test.date.min()

    X_train, y_train = train[FEATURES], train[TARGET]
    X_val, y_val = validation[FEATURES], validation[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]
    partitions = pd.DataFrame([
        {'Set': name, 'Rows': len(part), 'First date': part.date.min().date(),
         'Last date': part.date.max().date()}
        for name, part in [('Training', train), ('Validation', validation), ('Test', test)]
    ])
    return {
        'df': df, 'train': train, 'validation': validation, 'test': test,
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'train_end': pd.Timestamp(train_end), 'validation_end': pd.Timestamp(validation_end),
        'partitions': partitions,
        'stores': sorted(df['store_id'].unique(), key=lambda s: (len(s), s)),
        'categories': sorted(df['category'].unique()),
    }


# ---------------------------------------------------------------------------
# 4. Prepare a consistent comparison                         (final-009)
# ---------------------------------------------------------------------------
def make_pipeline(estimator, scale_numeric=False):
    preparation = ColumnTransformer([
        ('categories', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
        ('numeric', StandardScaler() if scale_numeric else 'passthrough', NUMERIC)
    ])
    return Pipeline([('prepare', preparation), ('model', estimator)])


def metrics(actual, predicted):
    return {'MAE': mean_absolute_error(actual, predicted),
            'RMSE': np.sqrt(mean_squared_error(actual, predicted)),
            'R2': r2_score(actual, predicted)}


def clear_family(candidates, family):
    """Discard a family and every dependent ensemble (notebook ``clear_family``)."""
    for name in list(candidates):
        if candidates[name]['family'] in {family, 'Ensemble'}:
            candidates.pop(name, None)


def fit_and_evaluate(name, family, estimator, data, settings=''):
    """Fit a clone on the training dates and score it on training and validation.

    Returns one ``candidate`` dictionary holding what the notebook spread over
    ``models[name]``, ``results[name]`` and ``validation_predictions[name]``,
    plus the unfitted specification and any warnings raised while fitting.
    """
    X_train, y_train, X_val, y_val = data['X_train'], data['y_train'], data['X_val'], data['y_val']
    fitted = clone(estimator)
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        fitted.fit(X_train, y_train)
    seconds = time.perf_counter() - started
    train_scores = metrics(y_train, fitted.predict(X_train))
    validation_predictions = fitted.predict(X_val)
    val_scores = metrics(y_val, validation_predictions)
    result = {'Model': name, 'Family': family, 'Settings': settings,
              'Train MAE': train_scores['MAE'],
              'Validation MAE': val_scores['MAE'], 'Validation RMSE': val_scores['RMSE'],
              'Validation R2': val_scores['R2'], 'Fit seconds': seconds}
    candidate = {
        'name': name, 'family': family, 'settings': settings,
        'specification': clone(estimator), 'model': fitted,
        'validation_predictions': validation_predictions,
        'result': result,
        'warnings': [str(w.message) for w in caught],
    }
    if family == 'Neural network':
        candidate['training_epochs'] = fitted.named_steps['model'].regressor_.n_iter_
    return candidate


def results_table(candidates):
    """The notebook's ``results`` dictionary, in notebook insertion order."""
    ordered = [n for n in CANDIDATE_ORDER if n in candidates]
    return {name: candidates[name]['result'] for name in ordered}


def best_in_family(candidates, family):
    results = results_table(candidates)
    names = [name for name in results if results[name]['Family'] == family]
    if not names:
        raise ValueError(f'Run the {family} section first.')
    return min(names, key=lambda name: results[name]['Validation MAE'])


# ---------------------------------------------------------------------------
# 5. Establish a baseline                                    (final-011)
# ---------------------------------------------------------------------------
def make_baseline():
    return DummyRegressor(strategy='mean')


# ---------------------------------------------------------------------------
# 6. KNN regression                                          (final-013)
# ---------------------------------------------------------------------------
def make_knn(k):
    assert isinstance(k, int) and k >= 1
    return make_pipeline(
        KNeighborsRegressor(n_neighbors=k, weights='uniform', n_jobs=-1), True)


# ---------------------------------------------------------------------------
# 7. Regression trees                                        (final-015)
# ---------------------------------------------------------------------------
def make_tree(depth):
    return make_pipeline(
        DecisionTreeRegressor(max_depth=depth, min_samples_leaf=MIN_LEAF, random_state=SEED))


# ---------------------------------------------------------------------------
# 8. Random forests                                          (final-017)
# ---------------------------------------------------------------------------
def make_forest(size):
    return make_pipeline(
        RandomForestRegressor(n_estimators=size, max_depth=12, min_samples_leaf=30,
                              max_features=0.8, bootstrap=True, random_state=SEED, n_jobs=-1))


# ---------------------------------------------------------------------------
# 9. Neural networks                                         (final-019)
# ---------------------------------------------------------------------------
def make_network(layers):
    estimator = TransformedTargetRegressor(
        regressor=MLPRegressor(hidden_layer_sizes=layers, activation='relu', solver='adam',
                               alpha=0.01, batch_size=256, learning_rate_init=0.001,
                               max_iter=300, early_stopping=True, validation_fraction=0.15,
                               n_iter_no_change=20, random_state=SEED),
        transformer=StandardScaler())
    return make_pipeline(estimator, True)


# ---------------------------------------------------------------------------
# 10. Averaging ensembles                                    (final-021)
# ---------------------------------------------------------------------------
def family_winners(candidates):
    """Lowest validation MAE in each family, in fixed KNN/tree/forest/network order.

    The notebook ran every preset before this step. The app enforces the same
    condition so an ensemble is never assembled from a partial comparison.
    """
    missing = [name for name in INDIVIDUAL_NAMES if name not in candidates]
    if missing:
        raise ValueError('All 12 individual presets must be evaluated before building '
                         f'an ensemble. Missing: {missing}.')
    return {family: best_in_family(candidates, family) for family in FAMILIES}


def make_ensemble(candidates, winners, weights=None):
    members = [(f'model_{i}', clone(candidates[name]['specification']))
               for i, name in enumerate(winners.values())]
    if weights is not None:
        assert len(weights) == 4 and np.isfinite(weights).all()
        assert np.all(np.asarray(weights) >= 0) and sum(weights) > 0
    return VotingRegressor(estimators=members, weights=weights, n_jobs=1)


def normalized_weights(weights):
    weights = np.asarray(weights, dtype=float)
    return weights / weights.sum()


def residual_correlations(candidates, winners, data):
    residuals = pd.DataFrame({family: data['y_val'].to_numpy() - candidates[name]['validation_predictions']
                              for family, name in winners.items()})
    return residuals.corr()


# ---------------------------------------------------------------------------
# Candidate catalogue: the 15 predefined classroom candidates
# ---------------------------------------------------------------------------
def individual_candidates():
    """Baseline plus the 12 presets, in notebook order, as unfitted specifications."""
    catalogue = [{'name': BASELINE_NAME, 'family': 'Baseline',
                  'settings': "strategy='mean'", 'estimator': make_baseline()}]
    for k in K_VALUES:
        catalogue.append({'name': knn_name(k), 'family': 'KNN',
                          'settings': f"n_neighbors={k}, weights='uniform'; day_of_year standardized",
                          'estimator': make_knn(k)})
    for depth in TREE_DEPTHS:
        catalogue.append({'name': tree_name(depth), 'family': 'Regression tree',
                          'settings': f'max_depth={depth}, min_samples_leaf={MIN_LEAF}',
                          'estimator': make_tree(depth)})
    for size in FOREST_SIZES:
        catalogue.append({'name': forest_name(size), 'family': 'Random forest',
                          'settings': f'n_estimators={size}, max_depth=12, min_samples_leaf=30, max_features=0.8',
                          'estimator': make_forest(size)})
    for layers in NETWORK_LAYERS:
        catalogue.append({'name': network_name(layers), 'family': 'Neural network',
                          'settings': f'hidden_layer_sizes={layers}, relu, adam, alpha=0.01, early stopping; '
                                      'day_of_year and target standardized',
                          'estimator': make_network(layers)})
    return catalogue


def candidate_by_name(name):
    for spec in individual_candidates():
        if spec['name'] == name:
            return spec
    raise KeyError(f'{name} is not a classroom candidate.')


def ensemble_candidates(candidates):
    """The two ensembles built from the current family winners."""
    winners = family_winners(candidates)
    member_text = ', '.join(f'{family}: {name}' for family, name in winners.items())
    return [
        {'name': EQUAL_ENSEMBLE_NAME, 'family': 'Ensemble',
         'settings': f'VotingRegressor, equal weights; members = {member_text}',
         'estimator': make_ensemble(candidates, winners), 'winners': winners,
         'weights': [1, 1, 1, 1]},
        {'name': WEIGHTED_ENSEMBLE_NAME, 'family': 'Ensemble',
         'settings': f'VotingRegressor, weights={ENSEMBLE_WEIGHTS}; members = {member_text}',
         'estimator': make_ensemble(candidates, winners, ENSEMBLE_WEIGHTS), 'winners': winners,
         'weights': list(ENSEMBLE_WEIGHTS)},
    ]


def fit_candidate(spec, data):
    candidate = fit_and_evaluate(spec['name'], spec['family'], spec['estimator'], data, spec['settings'])
    for key in ('winners', 'weights'):
        if key in spec:
            candidate[key] = spec[key]
    return candidate


def run_classroom_comparison(data, candidates=None, progress=None):
    """Evaluate the exact 15-candidate set in notebook order, one at a time.

    Completed, identical candidates already in ``candidates`` are reused.
    ``progress(index, total, name)`` is an optional status callback.
    """
    candidates = {} if candidates is None else candidates
    specs = individual_candidates()
    total = len(specs) + len(ENSEMBLE_NAMES)
    for i, spec in enumerate(specs):
        if progress:
            progress(i, total, spec['name'])
        if spec['name'] not in candidates:
            candidates[spec['name']] = fit_candidate(spec, data)
    for j, spec in enumerate(ensemble_candidates(candidates)):
        if progress:
            progress(len(specs) + j, total, spec['name'])
        if spec['name'] not in candidates:
            candidates[spec['name']] = fit_candidate(spec, data)
    if progress:
        progress(total, total, 'done')
    return candidates


# ---------------------------------------------------------------------------
# 11. Select the model using validation evidence             (final-023)
# ---------------------------------------------------------------------------
def leaderboard(candidates):
    results = results_table(candidates)
    if not results:
        return pd.DataFrame()
    table = pd.DataFrame(results.values()).sort_values(
        'Validation MAE', kind='stable').reset_index(drop=True)
    if BASELINE_NAME in results:
        baseline_val_mae = results[BASELINE_NAME]['Validation MAE']
        table['MAE improvement vs baseline (%)'] = (
            100 * (1 - table['Validation MAE'] / baseline_val_mae)
            if baseline_val_mae > 0 else np.nan)
    else:
        table['MAE improvement vs baseline (%)'] = np.nan
    return table


def select_model(candidates):
    """Lowest full-precision validation MAE; ties keep the earlier notebook entry."""
    results = results_table(candidates)
    if not results:
        raise ValueError('No evaluated candidates yet.')
    return min(results, key=lambda name: results[name]['Validation MAE'])


def ensemble_gain(candidates):
    """Best individual vs best ensemble on validation MAE (final-023 printout)."""
    results = results_table(candidates)
    winners = family_winners(candidates)
    best_individual = min(winners.values(), key=lambda name: results[name]['Validation MAE'])
    best_ensemble = best_in_family(candidates, 'Ensemble')
    units = results[best_individual]['Validation MAE'] - results[best_ensemble]['Validation MAE']
    percent = 100 * units / results[best_individual]['Validation MAE']
    return {'best_individual': best_individual, 'best_ensemble': best_ensemble,
            'ensemble_gain_units': units, 'ensemble_gain_percent': percent}


def is_complete_comparison(candidates):
    return all(name in candidates for name in CANDIDATE_ORDER)


# ---------------------------------------------------------------------------
# 12. Final evaluation on later dates                        (final-025)
# ---------------------------------------------------------------------------
def segment_errors(diagnostics, column):
    table = diagnostics.groupby(column).agg(
        Observations=('error', 'size'), Mean_sales=(TARGET, 'mean'),
        MAE=('absolute_error', 'mean'), Mean_signed_error=('error', 'mean'),
        Total_absolute_error=('absolute_error', 'sum'), Total_sales=(TARGET, 'sum'))
    table['WAPE_percent'] = 100 * table.Total_absolute_error / table.Total_sales.replace(0, np.nan)
    return table.drop(columns=['Total_absolute_error', 'Total_sales']).sort_values('MAE', ascending=False)


def finalize_model(selected_name, selected_specification, data):
    """Refit the frozen specification on training + validation and score the test dates.

    ``selected_specification`` must be an unfitted clone frozen before this call.
    The mean baseline is refitted on the same development period.
    """
    X_train, y_train, X_val, y_val = data['X_train'], data['y_train'], data['X_val'], data['y_val']
    X_test, y_test, test = data['X_test'], data['y_test'], data['test']

    X_development = pd.concat([X_train, X_val])
    y_development = pd.concat([y_train, y_val])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        final_model = clone(selected_specification).fit(X_development, y_development)
    test_predictions = final_model.predict(X_test)
    final_baseline = DummyRegressor(strategy='mean').fit(X_development, y_development)
    baseline_predictions = final_baseline.predict(X_test)
    selected_test_metrics = metrics(y_test, test_predictions)
    baseline_test_metrics = metrics(y_test, baseline_predictions)
    test_results = pd.DataFrame([
        {'Model': selected_name, **selected_test_metrics},
        {'Model': 'Refitted mean baseline', **baseline_test_metrics}
    ])

    diagnostics = test[['date', 'store_id', 'category', TARGET]].copy()
    diagnostics['predicted_units'] = test_predictions
    diagnostics['error'] = y_test.to_numpy() - test_predictions
    diagnostics['absolute_error'] = diagnostics.error.abs()
    diagnostics['underpredicted'] = diagnostics.error > 0
    mean_bias = diagnostics.error.mean()
    underprediction_rate = diagnostics.underpredicted.mean()
    negative_count = int(np.sum(test_predictions < 0))
    test_improvement_pct = (100 * (1 - selected_test_metrics['MAE'] / baseline_test_metrics['MAE'])
                            if baseline_test_metrics['MAE'] > 0 else np.nan)
    summary = pd.DataFrame([{
        'Mean signed error (actual - predicted)': mean_bias,
        'Underpredicted observations (%)': 100 * underprediction_rate,
        'Negative predictions': negative_count,
        'MAE improvement over baseline (%)': test_improvement_pct
    }])
    return {
        'selected_name': selected_name,
        'final_model': final_model, 'final_baseline': final_baseline,
        'test_predictions': test_predictions, 'baseline_predictions': baseline_predictions,
        'selected_test_metrics': selected_test_metrics, 'baseline_test_metrics': baseline_test_metrics,
        'test_results': test_results, 'diagnostics': diagnostics, 'summary': summary,
        'mean_bias': mean_bias, 'underprediction_rate': underprediction_rate,
        'negative_count': negative_count, 'test_improvement_pct': test_improvement_pct,
        'store_diagnostics': segment_errors(diagnostics, 'store_id'),
        'category_diagnostics': segment_errors(diagnostics, 'category'),
        'development_start': data['train'].date.min(), 'development_end': data['validation_end'],
        'test_start': test.date.min(), 'test_end': test.date.max(),
        'warnings': [str(w.message) for w in caught],
    }


# ---------------------------------------------------------------------------
# 13. Managerial recommendations                             (final-027)
# ---------------------------------------------------------------------------
def managerial_briefing(final, selected_family, gain=None):
    """Populate the notebook's briefing template from the final test results.

    ``gain`` is the dictionary from ``ensemble_gain`` and is only needed when
    the selected family is 'Ensemble'.
    """
    selected_name = final['selected_name']
    selected_test_metrics = final['selected_test_metrics']
    baseline_test_metrics = final['baseline_test_metrics']
    store_diagnostics, category_diagnostics = final['store_diagnostics'], final['category_diagnostics']
    mean_bias, underprediction_rate = final['mean_bias'], final['underprediction_rate']
    negative_count, test_improvement_pct = final['negative_count'], final['test_improvement_pct']

    worst_store = store_diagnostics.index[0]
    worst_category = category_diagnostics.index[0]
    store_mae = store_diagnostics.iloc[0]['MAE']
    category_mae = category_diagnostics.iloc[0]['MAE']
    category_wape = category_diagnostics.iloc[0]['WAPE_percent']
    wape_text = f'**{category_wape:.1f}%**' if np.isfinite(category_wape) else 'undefined (zero total sales)'
    bias_word = 'underpredicts' if mean_bias > 0 else 'overpredicts' if mean_bias < 0 else 'has no average signed bias'
    if selected_test_metrics['MAE'] < baseline_test_metrics['MAE']:
        adoption = (f'Use **{selected_name}** as a candidate for a controlled forecasting pilot. '
                    f'It reduced test MAE by **{test_improvement_pct:.1f}%** relative to the refitted mean-sales baseline. '
                    'This is an improvement in forecast error, not a measured reduction in inventory cost.')
    else:
        adoption = (f'Keep the mean-sales baseline as the operational reference. **{selected_name}** was selected on validation data '
                    'but did not improve test MAE. Investigate the generalization gap before piloting a more complex system; '
                    'do not pick a replacement by searching this test period.')
    if selected_family == 'Ensemble' and gain is not None:
        complexity = (f'The best ensemble improved validation MAE over **{gain["best_individual"]}** by '
                      f'**{gain["ensemble_gain_units"]:.3f} units ({gain["ensemble_gain_percent"]:.2f}%)**. '
                      'Assess whether that gain justifies maintaining four pipelines. A new future-period evaluation '
                      'is needed before making a data-driven switch to a simpler alternative.')
    else:
        complexity = (f'The validation rule selected **{selected_name}**. Do not add an ensemble solely because it combines more models. '
                      'Record the selected settings and compare any proposed replacement on new future periods.')
    if negative_count:
        output_note = (f' The selected model produced {negative_count:,} negative test estimates; define a nonnegative '
                       'forecasting rule and validate it on new data before operational use.')
    else:
        output_note = ' No negative test estimates were observed.'

    return f"""### Recommended approach
{adoption}

### What the errors mean
Test MAE was **{selected_test_metrics['MAE']:.2f} units per store/category/day**, versus **{baseline_test_metrics['MAE']:.2f}** for the baseline. RMSE was **{selected_test_metrics['RMSE']:.2f} units**, and R² was **{selected_test_metrics['R2']:.3f}**. These are aggregate measures, not guarantees for an individual order.

The model {bias_word} by **{abs(mean_bias):.2f} units on average** across the test observations. Actual sales exceeded predictions in **{100 * underprediction_rate:.1f}%** of observations. This frequency does not equal a stockout rate.{output_note}

### Where managers should review forecasts
Store **{worst_store}** had the largest store-level MAE, **{store_mae:.2f} units**. **{worst_category}** had the largest category-level MAE, **{category_mae:.2f} units**, with WAPE of {wape_text}. Review those segments first while considering their volumes; higher absolute error alone does not establish worse proportional performance. Use manager review for unusual promotions, disruptions, and inventory constraints.

### Complexity and implementation
{complexity}

### Pilot and data requirements
Run a proposed four-week shadow pilot, producing forecasts without automatically changing orders. Log forecasts before each selling day, compare them with actual sales and a simple historical store/category/weekday baseline, and review MAE and signed bias each week. Measure service levels, stockouts, spoilage, and inventory costs before claiming business value.

Add information available at prediction time: planned promotions and prices, historical sales lags, inventory availability, and supplier lead times. Establish how stockouts censor sales. The current calendar-and-category model is a teaching baseline for existing stores and categories, not a validated demand or replenishment system.

### Student recommendation
In 100–150 words, state the recommended approach, cite its validation and test evidence, identify one priority segment for review, and name one additional data requirement. Distinguish forecast accuracy from financial or operational impact.
"""


# ---------------------------------------------------------------------------
# 14. Predict one typed observation (wrapper adaptation of ``.predict``)
# ---------------------------------------------------------------------------
def make_prediction_row(store_id, category, date):
    """One-row DataFrame in exactly ``FEATURES`` order, deriving the calendar features."""
    date = pd.Timestamp(date)
    row = pd.DataFrame([{
        'store_id': str(store_id),
        'category': category,
        'weekday': date.day_name(),
        'day_of_year': date.dayofyear,
    }])
    return row[FEATURES]


def predict_one(fitted_pipeline, row):
    """Call the fitted pipeline's ``.predict`` on one row; returns the raw float."""
    return float(fitted_pipeline.predict(row)[0])


# ---------------------------------------------------------------------------
# 15. Reproducibility record (dataset, environment, run identity)
# ---------------------------------------------------------------------------
def environment_record():
    return {
        'Python': platform.python_version(),
        'scikit-learn': sklearn.__version__,
        'NumPy': np.__version__,
        'pandas': pd.__version__,
        'Seed': SEED,
    }


def run_identity(candidate_name, settings, data, stage, checksum=DATA_SHA256):
    """Readable summary that distinguishes one fitted model from another."""
    if stage == 'final':
        fit_start, fit_end = data['train'].date.min(), data['validation_end']
        eval_start, eval_end = data['test'].date.min(), data['test'].date.max()
        fit_label, eval_label = 'Training + validation (development)', 'Test'
    else:
        fit_start, fit_end = data['train'].date.min(), data['train_end']
        eval_start, eval_end = data['validation'].date.min(), data['validation_end']
        fit_label, eval_label = 'Training', 'Validation'
    record = {
        'Candidate': candidate_name,
        'Parameters': settings,
        'Stage': stage,
        'Fitting period': f'{fit_label}: {fit_start.date()} to {fit_end.date()}',
        'Evaluation period': f'{eval_label}: {eval_start.date()} to {eval_end.date()}',
        'Features (order)': ', '.join(FEATURES),
        'Target': TARGET,
        'Split boundaries': f"train_end={data['train_end'].date()}, validation_end={data['validation_end'].date()}",
        'Dataset SHA-256': checksum,
        **environment_record(),
    }
    record['Run key'] = ' | '.join(f'{k}={v}' for k, v in record.items())
    return record
