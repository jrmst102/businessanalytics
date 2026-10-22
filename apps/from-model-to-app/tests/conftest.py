"""Shared fixtures: the engine run once, and the reference notebook executed once."""
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

# Code cells executed for parity, in notebook order. Plot-only cells are skipped.
NOTEBOOK_CELLS = ['final-002', 'final-004', 'final-006', 'final-009', 'final-011',
                  'final-013', 'final-015', 'final-017', 'final-019', 'final-021',
                  'final-023', 'final-025']


@pytest.fixture(scope='session')
def data():
    return models.prepare_data(models.load_data())


@pytest.fixture(scope='session')
def candidates(data):
    return models.run_classroom_comparison(data)


@pytest.fixture(scope='session')
def final(data, candidates):
    name = models.select_model(candidates)
    return models.finalize_model(name, models.clone(candidates[name]['specification']), data)


@pytest.fixture(scope='session')
def notebook_ns():
    """Execute the reference notebook's code cells verbatim and return its namespace.

    Only non-analytical pieces are replaced: ``display``/``Markdown`` stubs for
    IPython, the Colab upload import is never reached because the local CSV
    exists, and plots render to the Agg backend.
    """
    if not NOTEBOOK_PATH.exists():
        pytest.skip(f'Reference notebook not found at {NOTEBOOK_PATH}')
    cells = {c['id']: ''.join(c['source'])
             for c in json.loads(NOTEBOOK_PATH.read_text())['cells'] if c['cell_type'] == 'code'}
    namespace = {'display': lambda *a, **k: None, 'Markdown': lambda text: text}
    previous_cwd = os.getcwd()
    os.chdir(models.DATA_PATH.parent)  # so the notebook's LOCAL_CSV path resolves
    try:
        for cell_id in NOTEBOOK_CELLS:
            source = cells[cell_id].replace('from IPython.display import display, Markdown', '')
            exec(compile(source, cell_id, 'exec'), namespace)
    finally:
        os.chdir(previous_cwd)
    return namespace
