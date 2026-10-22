"""HTTP wrapper around the classroom engine for the Node.js dashboard.

This file plays the role the Streamlit wrapper used to play: it validates
typed inputs, keeps per-browser-session fitted models, and returns engine
results as JSON. Every number comes from ``models.py``; no model is defined
here. Run locally via ``python launch.py`` (which starts this API and the
Node server) or directly: ``python -m waitress --port=8000 engine_api:app``.
"""
import inspect
import threading
import time
import traceback

from flask import Flask, jsonify, request

import inputs
import models

app = Flask(__name__)

FOOTER = 'Business Analytics and Data Visualization Fall 2026 - Prof. Jose Mendoza'
TITLE = 'Business Analytics in Action: From Model to App'

# The engine data, prepared once and treated as read-only.
DATA = models.prepare_data(models.load_data())

# JSON-safe ids for the classroom presets (tuples cannot travel as JSON keys).
PARAMETER_IDS = {
    'KNN regression': {'5': 5, '15': 15, '50': 50},
    'Regression tree': {'3': 3, '6': 6, '12': 12},
    'Random forest': {'50': 50, '100': 100, '200': 200},
    'Neural network': {'16': (16,), '32': (32,), '32,16': (32, 16)},
    'Ensemble regression': {'Equal weights': 'Equal weights',
                            'Weighted average': 'Weighted average'},
}
PARAMETER_LABELS = {
    'Neural network': {'16': 'One layer: 16 neurons', '32': 'One layer: 32 neurons',
                       '32,16': 'Two layers: 32 and 16 neurons'},
}
DEFAULT_IDS = {'KNN regression': '15', 'Regression tree': '6', 'Random forest': '100',
               'Neural network': '32,16', 'Ensemble regression': 'Equal weights'}
HOW_IT_PREDICTS = {
    'KNN regression': 'Averages units sold over the k most similar training observations '
                      '(same store, category and weekday indicators plus a standardized day of year).',
    'Regression tree': 'Splits the training data into groups by repeated yes/no questions and predicts '
                       'the mean sales of the terminal leaf an observation falls into.',
    'Random forest': 'Averages many trees fitted to bootstrap samples with a random subset of columns '
                     'at each split, which smooths out any single tree\'s quirks.',
    'Neural network': 'Passes the encoded features through hidden ReLU layers trained with Adam on a '
                      'standardized target; predictions are converted back to units.',
    'Ensemble regression': 'Averages the predictions of four fixed classroom models (KNN, tree, forest, '
                           'network) using the averaging method you choose. It is one selected model, '
                           'even though training it fits its four members.',
}
CONSTRUCTORS = {'KNN regression': models.make_knn, 'Regression tree': models.make_tree,
                'Random forest': models.make_forest, 'Neural network': models.make_network,
                'Ensemble regression': models.make_ensemble}
HISTORICAL_NOTE = ('Historical test performance for this configuration. Repeated parameter changes '
                   'are classroom exploration on the same test period, not new independent tests.')

# One active fitted model per browser session, like Streamlit's session state.
SESSIONS = {}
SESSIONS_LOCK = threading.Lock()
MAX_SESSIONS = 50


def _session_id():
    session_id = (request.headers.get('X-Session-Id') or '').strip()
    return session_id[:64] or None


def _store_session(session_id, entry):
    with SESSIONS_LOCK:
        SESSIONS[session_id] = entry
        while len(SESSIONS) > MAX_SESSIONS:  # drop the least recently used fit
            oldest = min(SESSIONS, key=lambda key: SESSIONS[key]['last_used'])
            del SESSIONS[oldest]


def _get_session(session_id):
    with SESSIONS_LOCK:
        entry = SESSIONS.get(session_id)
        if entry is not None:
            entry['last_used'] = time.time()
        return entry


def _parse_config(payload):
    choice = payload.get('choice')
    parameter_id = str(payload.get('parameter_id', ''))
    if choice not in models.MODEL_CHOICES:
        raise ValueError(f'{choice!r} is not one of the five classroom model choices.')
    if parameter_id not in PARAMETER_IDS[choice]:
        raise ValueError(f'{parameter_id!r} is not a classroom preset for {choice}.')
    return choice, parameter_id, PARAMETER_IDS[choice][parameter_id]


def _ensemble_note(parameter_id):
    shares = (models.normalized_weights(models.ENSEMBLE_WEIGHTS)
              if parameter_id == 'Weighted average' else [0.25] * 4)
    members = '; '.join(f'{name} ({settings}), weight {share:.3f}'
                        for (name, settings), share in zip(models.ENSEMBLE_MEMBERS, shares))
    return ('Fixed classroom members (from the ensemble notebook), in order: ' + members
            + '. Members are fixed — the app never searches for configurations — and only '
              'the combined ensemble result is shown.')


# ---------------------------------------------------------------------------
# Read-only metadata and data
# ---------------------------------------------------------------------------
@app.get('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.get('/api/meta')
def meta():
    choices = []
    for choice in models.MODEL_CHOICES:
        labels = PARAMETER_LABELS.get(choice, {})
        choices.append({
            'name': choice,
            'parameter_label': models.PRESETS[choice]['label'],
            'options': [{'id': pid, 'label': labels.get(pid, pid)}
                        for pid in PARAMETER_IDS[choice]],
            'default_id': DEFAULT_IDS[choice],
            'how_it_predicts': HOW_IT_PREDICTS[choice],
            'ensemble_notes': ({pid: _ensemble_note(pid) for pid in PARAMETER_IDS[choice]}
                               if choice == 'Ensemble regression' else None),
        })
    facts = models.describe_data(DATA['df'])
    return jsonify({
        'title': TITLE,
        'footer': FOOTER,
        'choices': choices,
        'historical_note': HISTORICAL_NOTE,
        'facts': {key: str(value) if not isinstance(value, int) else value
                  for key, value in facts.items()},
        'source_url': models.DATA_SOURCE_URL,
        'stores': DATA['stores'],
        'categories': DATA['categories'],
    })


@app.get('/api/dataset')
def dataset():
    df = DATA['df']
    columns = ['date', 'store_id', 'category', 'weekday', 'day_of_year',
               'units_sold', 'revenue', 'avg_price']
    columns = [c for c in columns if c in df.columns]
    frame = df[columns].copy()
    frame['date'] = frame['date'].dt.strftime('%Y-%m-%d')
    return jsonify({'columns': columns, 'rows': frame.values.tolist()})


@app.get('/api/source')
def source():
    choice = request.args.get('choice')
    if choice not in CONSTRUCTORS:
        return jsonify({'error': 'Unknown model choice.'}), 400
    functions = [models.make_pipeline, CONSTRUCTORS[choice]]
    if choice == 'Ensemble regression':
        functions.insert(1, models.ensemble_member_estimators)
    return jsonify({'source': '\n\n'.join(inspect.getsource(f) for f in functions)})


# ---------------------------------------------------------------------------
# Train the one selected configuration
# ---------------------------------------------------------------------------
@app.post('/api/train')
def train():
    session_id = _session_id()
    if not session_id:
        return jsonify({'error': 'Missing X-Session-Id header.'}), 400
    try:
        choice, parameter_id, parameter = _parse_config(request.get_json(force=True))
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    estimator, settings = models.build_model(choice, parameter)
    try:
        result = models.fit_selected_model(estimator, DATA)
    except Exception as error:
        with SESSIONS_LOCK:  # a failed fit clears any previous result
            SESSIONS.pop(session_id, None)
        return jsonify({'error': f'Training failed: {type(error).__name__}: {error}',
                        'detail': traceback.format_exc()}), 500
    now = time.time()
    _store_session(session_id, {'choice': choice, 'parameter_id': parameter_id,
                                'settings': settings, 'result': result, 'last_used': now})
    return jsonify(_train_response(choice, parameter_id, settings, result))


def _train_response(choice, parameter_id, settings, result):
    scores = result['scores']
    return {
        'choice': choice,
        'parameter_id': parameter_id,
        'settings': settings,
        'scores': {
            'R2': scores['R2'], 'MSE': scores['MSE'], 'RMSE': scores['RMSE'],
            'MAPE': scores['MAPE'],
            'R2_note': scores.get('R2_note'), 'MAPE_note': scores.get('MAPE_note'),
            'observations': scores['observations'],
            'positive_observations': scores['positive_observations'],
            'zero_excluded_from_mape': scores['zero_excluded_from_mape'],
        },
        'fit_seconds': result['fit_seconds'],
        'development_rows': result['development_rows'],
        'test_rows': result['test_rows'],
        'development_start': str(result['development_start'].date()),
        'development_end': str(result['development_end'].date()),
        'test_start': str(result['test_start'].date()),
        'test_end': str(result['test_end'].date()),
        'warnings': result['warnings'],
        'training_epochs': result.get('training_epochs'),
        'historical_note': HISTORICAL_NOTE,
    }


# ---------------------------------------------------------------------------
# Predict one typed observation with the session's fitted model
# ---------------------------------------------------------------------------
@app.post('/api/predict')
def predict():
    session_id = _session_id()
    if not session_id:
        return jsonify({'error': 'Missing X-Session-Id header.'}), 400
    payload = request.get_json(force=True)
    entry = _get_session(session_id)
    if entry is None:
        return jsonify({'error': 'Train a model in the Model tab before making a prediction.'}), 409
    try:
        choice, parameter_id, _ = _parse_config(payload)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    if (entry['choice'], entry['parameter_id']) != (choice, parameter_id):
        return jsonify({'error': 'The model or parameter changed after training. '
                                 'Train the new configuration before predicting.'}), 409

    values, errors = inputs.validate_prediction_inputs(
        payload.get('store', ''), payload.get('category', ''), payload.get('date', ''),
        payload.get('actual', ''), DATA['stores'], DATA['categories'])
    if errors:
        return jsonify({'errors': errors}), 400

    result = entry['result']
    row = models.make_prediction_row(values['store_id'], values['category'], values['date'])
    predicted = models.predict_one(result['pipeline'], row)
    notices = [text for _, text in inputs.date_notices(
        values['date'], result['development_start'], result['development_end'],
        result['test_start'], result['test_end'],
        DATA['df'].date.min(), DATA['df'].date.max())]

    actual_eval = None
    if values.get('actual_units') is not None:
        actual = values['actual_units']
        signed = actual - predicted
        actual_eval = {
            'actual': actual, 'signed_error': signed, 'absolute_error': abs(signed),
            'ape_percent': (100 * abs(signed) / actual) if actual > 0 else None,
        }
    return jsonify({
        'predicted': predicted,
        'negative': predicted < 0,
        'choice': entry['choice'],
        'parameter_id': entry['parameter_id'],
        'settings': entry['settings'],
        'canonical': {
            'store_id': values['store_id'], 'category': values['category'],
            'date': str(values['date'].date()), 'weekday': row.iloc[0]['weekday'],
            'day_of_year': int(row.iloc[0]['day_of_year']),
        },
        'notices': notices,
        'actual_eval': actual_eval,
        'scores': _train_response(entry['choice'], entry['parameter_id'],
                                  entry['settings'], result)['scores'],
    })


if __name__ == '__main__':
    import argparse
    import waitress
    parser = argparse.ArgumentParser(description='Run the classroom engine API.')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print(f'Engine API listening on http://127.0.0.1:{args.port}')
    waitress.serve(app, host='127.0.0.1', port=args.port, threads=8)
