"""Shared fixtures: the engine data, a fitted-result cache, and the notebook's data cells."""
import json
import os
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = APP_DIR.parents[1]
NOTEBOOK_PATH = REPO_DIR / 'notebooks' / 'Mancino_Regression_Final.ipynb'
sys.path.insert(0, str(APP_DIR))
os.environ.setdefault('MPLBACKEND', 'Agg')

import models  # noqa: E402

# Data-preparation cells of the final notebook, executed verbatim for parity.
DATA_CELLS = ['final-002', 'final-004', 'final-006']


@pytest.fixture(scope='session')
def data():
    return models.prepare_data(models.load_data())


@pytest.fixture(scope='session')
def fitted_cache():
    """One engine fit per configuration, shared across parity and behavior tests."""
    return {}


@pytest.fixture(scope='session')
def fit_once(fitted_cache, data):
    def _fit(choice, parameter):
        key = (choice, str(parameter))
        if key not in fitted_cache:
            estimator, _ = models.build_model(choice, parameter)
            fitted_cache[key] = models.fit_selected_model(estimator, data)
        return fitted_cache[key]
    return _fit


@pytest.fixture(scope='session')
def notebook_ns():
    """Execute the final notebook's data cells verbatim and return its namespace.

    Only non-analytical pieces are replaced: ``display``/``Markdown`` stubs for
    IPython, and the Colab upload import is never reached because the local CSV
    exists. Plots render to the Agg backend.
    """
    if not NOTEBOOK_PATH.exists():
        pytest.skip(f'Reference notebook not found at {NOTEBOOK_PATH}')
    cells = {c['id']: ''.join(c['source'])
             for c in json.loads(NOTEBOOK_PATH.read_text())['cells'] if c['cell_type'] == 'code'}
    namespace = {'display': lambda *a, **k: None, 'Markdown': lambda text: text}
    previous_cwd = os.getcwd()
    os.chdir(models.DATA_PATH.parent)  # so the notebook's LOCAL_CSV path resolves
    try:
        for cell_id in DATA_CELLS:
            source = cells[cell_id].replace('from IPython.display import display, Markdown', '')
            exec(compile(source, cell_id, 'exec'), namespace)
    finally:
        os.chdir(previous_cwd)
    return namespace
