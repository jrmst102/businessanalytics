"""Classroom engine for "Business Analytics in Action: From Model to App".

Every analytical step here is lifted from the approved Mancino classroom
notebooks and kept recognizable: the same preprocessing, constructors,
parameter presets, ``.fit()`` and ``.predict()`` used in class.
``NOTEBOOK_MAP.md`` lists each function's source notebook and every
adaptation made while moving cells into functions (manual model choice,
fixed ensemble members, MSE/MAPE reporting). The dashboard (``app.py``)
only calls these functions and displays what they return; it never defines
a second model. No Streamlit import belongs in this file.
"""

# ---------------------------------------------------------------------------
# 1. Import the tools and name the classroom constants           (final-002)
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
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.metrics import mean_squared_error, r2_score

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

# The five student model choices and their classroom parameter presets.
MIN_LEAF = 30
ENSEMBLE_WEIGHTS = [1, 1, 2, 2]  # Order: KNN, regression tree, random forest, neural network.
MODEL_CHOICES = ['KNN regression', 'Regression tree', 'Random forest',
                 'Neural network', 'Ensemble regression']
PRESETS = {
    'KNN regression': {'label': 'Number of neighbors', 'values': [5, 15, 50], 'default': 15},
    'Regression tree': {'label': 'Maximum depth', 'values': [3, 6, 12], 'default': 6},
    'Random forest': {'label': 'Number of trees', 'values': [50, 100, 200], 'default': 100},
    'Neural network': {'label': 'Hidden-layer architecture',
                       'values': [(16,), (32,), (32, 16)], 'default': (32, 16)},
    'Ensemble regression': {'label': 'Averaging method',
                            'values': ['Equal weights', 'Weighted average'],
                            'default': 'Equal weights'},
}


# ---------------------------------------------------------------------------
# 2. Load and inspect the data                                   (final-004)
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
        'Observations': len(df),
        'Stores': df.store_id.nunique(),
        'Categories': df.category.nunique(),
        'First date': df.date.min().date(),
        'Last date': df.date.max().date(),
    }


# ---------------------------------------------------------------------------
# 3. Define predictors and split by date                         (final-006)
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
    return {
        'df': df, 'train': train, 'validation': validation, 'test': test,
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'train_end': pd.Timestamp(train_end), 'validation_end': pd.Timestamp(validation_end),
        'stores': sorted(df['store_id'].unique(), key=lambda s: (len(s), s)),
        'categories': sorted(df['category'].unique()),
    }


# ---------------------------------------------------------------------------
# 4. Shared preprocessing                                        (final-009)
# ---------------------------------------------------------------------------
def make_pipeline(estimator, scale_numeric=False):
    preparation = ColumnTransformer([
        ('categories', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
        ('numeric', StandardScaler() if scale_numeric else 'passthrough', NUMERIC)
    ])
    return Pipeline([('prepare', preparation), ('model', estimator)])


# ---------------------------------------------------------------------------
# 5. Classroom model constructors              (final-013 to final-019)
# ---------------------------------------------------------------------------
def make_knn(k):
    assert isinstance(k, int) and k >= 1
    return make_pipeline(
        KNeighborsRegressor(n_neighbors=k, weights='uniform', n_jobs=-1), True)


def make_tree(depth):
    return make_pipeline(
        DecisionTreeRegressor(max_depth=depth, min_samples_leaf=MIN_LEAF, random_state=SEED))


def make_forest(size):
    return make_pipeline(
        RandomForestRegressor(n_estimators=size, max_depth=12, min_samples_leaf=30,
                              max_features=0.8, bootstrap=True, random_state=SEED, n_jobs=-1))


def make_network(layers):
    estimator = TransformedTargetRegressor(
        regressor=MLPRegressor(hidden_layer_sizes=layers, activation='relu', solver='adam',
                               alpha=0.01, batch_size=256, learning_rate_init=0.001,
                               max_iter=300, early_stopping=True, validation_fraction=0.15,
                               n_iter_no_change=20, random_state=SEED),
        transformer=StandardScaler())
    return make_pipeline(estimator, True)


# ---------------------------------------------------------------------------
# 6. Ensemble with the fixed classroom members  (Mancino_Ensemble_Complete)
# ---------------------------------------------------------------------------
# The member settings are fixed by the standalone ensemble notebook; the app
# never searches for members or optimizes weights.
ENSEMBLE_MEMBERS = [
    ('KNN', '50 neighbors, uniform weights, day_of_year standardized'),
    ('Regression tree', 'maximum depth 12, minimum leaf size 30'),
    ('Random forest', '100 trees, maximum depth 12, minimum leaf size 30, max_features=0.8'),
    ('Neural network', 'one hidden layer with 16 neurons, classroom settings, target standardized'),
]


def ensemble_member_estimators():
    """The four fixed member pipelines, in the notebook's order and names."""
    members = [make_knn(50), make_tree(12), make_forest(100), make_network((16,))]
    return [(f'model_{i}', member) for i, member in enumerate(members)]


def make_ensemble(method='Equal weights'):
    assert method in PRESETS['Ensemble regression']['values']
    weights = ENSEMBLE_WEIGHTS if method == 'Weighted average' else None
    return VotingRegressor(estimators=ensemble_member_estimators(), weights=weights, n_jobs=1)


def normalized_weights(weights):
    weights = np.asarray(weights, dtype=float)
    return weights / weights.sum()


# ---------------------------------------------------------------------------
# 7. Build the one selected specification
# ---------------------------------------------------------------------------
def build_model(choice, parameter):
    """The selected classroom estimator with its preset, plus a settings sentence."""
    allowed = PRESETS[choice]['values'] if choice in PRESETS else []
    if parameter not in allowed:
        raise ValueError(f'{parameter!r} is not a classroom preset for {choice}. '
                         f'Allowed values: {allowed}.')
    if choice == 'KNN regression':
        return make_knn(parameter), (f"n_neighbors={parameter}, weights='uniform', "
                                     'day_of_year standardized')
    if choice == 'Regression tree':
        return make_tree(parameter), (f'max_depth={parameter}, min_samples_leaf={MIN_LEAF}, '
                                      f'random_state={SEED}')
    if choice == 'Random forest':
        return make_forest(parameter), (f'n_estimators={parameter}, max_depth=12, '
                                        f'min_samples_leaf=30, max_features=0.8, random_state={SEED}')
    if choice == 'Neural network':
        return make_network(parameter), (f'hidden_layer_sizes={parameter}, relu, adam, alpha=0.01, '
                                         'early stopping; day_of_year and target standardized')
    if choice == 'Ensemble regression':
        share = ('25% each' if parameter == 'Equal weights' else
                 f'weights {ENSEMBLE_WEIGHTS} normalized to '
                 + ', '.join(f'{w:.3f}' for w in normalized_weights(ENSEMBLE_WEIGHTS)))
        return make_ensemble(parameter), (f'VotingRegressor, {parameter.lower()} ({share}); '
                                          'fixed classroom members KNN, tree, forest, network')
    raise ValueError(f'{choice!r} is not one of the five classroom model choices.')


# ---------------------------------------------------------------------------
# 8. Metrics: R², MSE, RMSE, MAPE                 (app adaptation, documented)
# ---------------------------------------------------------------------------
def evaluate_model(actual, predicted):
    """The four required metrics on raw predictions in original sales units.

    MAPE follows the documented zero-sales policy: rows with zero actual sales
    are excluded from MAPE only, and their count is reported. R² is undefined
    (None) when the actual values are constant; nothing is substituted for it.
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mse = float(mean_squared_error(actual, predicted))
    scores = {'MSE': mse, 'RMSE': float(np.sqrt(mse)),
              'observations': int(actual.size)}

    if np.ptp(actual) == 0:
        scores['R2'] = None
        scores['R2_note'] = ('R² is undefined: the actual values are constant on this '
                             'evaluation set, so there is no variance to explain.')
    else:
        scores['R2'] = float(r2_score(actual, predicted))

    positive = actual > 0
    scores['positive_observations'] = int(np.count_nonzero(positive))
    scores['zero_excluded_from_mape'] = int(np.count_nonzero(~positive))
    if positive.any():
        ape = np.abs((actual[positive] - predicted[positive]) / actual[positive])
        scores['MAPE'] = float(ape.mean() * 100)
    else:
        scores['MAPE'] = None
        scores['MAPE_note'] = 'MAPE: N/A — no positive actual sales.'
    return scores


# ---------------------------------------------------------------------------
# 9. Train model: the final notebook's development-set refit     (final-025)
# ---------------------------------------------------------------------------
def fit_selected_model(estimator, data):
    """Refit the one chosen specification on training + validation and score the test dates.

    This is the final notebook's refit performed directly for the student's
    manual choice: combine training and validation as the development set, fit
    a clone of the chosen pipeline on it, predict the held-out test
    observations, and compute the four metrics. The fitted pipeline is
    returned so the Test tab predicts with this exact object.
    """
    X_development = pd.concat([data['X_train'], data['X_val']])
    y_development = pd.concat([data['y_train'], data['y_val']])
    pipeline = clone(estimator)
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        pipeline.fit(X_development, y_development)
    fit_seconds = time.perf_counter() - started
    test_predictions = pipeline.predict(data['X_test'])
    result = {
        'pipeline': pipeline,
        'test_predictions': test_predictions,
        'scores': evaluate_model(data['y_test'], test_predictions),
        'fit_seconds': fit_seconds,
        'development_rows': len(X_development),
        'test_rows': len(data['X_test']),
        'development_start': data['train'].date.min(), 'development_end': data['validation_end'],
        'test_start': data['test'].date.min(), 'test_end': data['test'].date.max(),
        'warnings': [str(w.message) for w in caught],
    }
    model_step = getattr(pipeline, 'named_steps', {}).get('model')
    if isinstance(model_step, TransformedTargetRegressor) and isinstance(
            model_step.regressor_, MLPRegressor):
        result['training_epochs'] = int(model_step.regressor_.n_iter_)
    return result


# ---------------------------------------------------------------------------
# 10. Predict one typed observation       (wrapper adaptation of ``.predict``)
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
# 11. Reproducibility record (dataset, environment, run identity)
# ---------------------------------------------------------------------------
def environment_record():
    return {
        'Python': platform.python_version(),
        'scikit-learn': sklearn.__version__,
        'NumPy': np.__version__,
        'pandas': pd.__version__,
        'Seed': SEED,
    }


def run_identity(choice, settings, data, checksum=DATA_SHA256):
    """Readable provenance for one fitted configuration (developer documentation)."""
    return {
        'Model': choice,
        'Parameters': settings,
        'Fitting period': ('Training + validation (development): '
                           f"{data['train'].date.min().date()} to {data['validation_end'].date()}"),
        'Evaluation period': (f"Test: {data['test'].date.min().date()} to "
                              f"{data['test'].date.max().date()}"),
        'Features (order)': ', '.join(FEATURES),
        'Target': TARGET,
        'Split boundaries': (f"train_end={data['train_end'].date()}, "
                             f"validation_end={data['validation_end'].date()}"),
        'Dataset SHA-256': checksum,
        **environment_record(),
    }
