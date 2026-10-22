"""Dashboard smoke test with Streamlit's headless AppTest.

Drives the real app: train a preset, run the comparison, freeze, finalize and
make a typed prediction, then checks the displayed prediction equals the
engine's direct ``.predict`` on the same fitted pipeline.
"""
import re

import pytest
from streamlit.testing.v1 import AppTest

import models
from conftest import APP_DIR

pytest.importorskip('streamlit')


def _app():
    at = AppTest.from_file(str(APP_DIR / 'app.py'), default_timeout=300)
    return at.run()


def _button(at, label):
    matches = [b for b in at.button if b.label == label]
    assert matches, f'Button {label!r} not found'
    return matches[0]


def test_dashboard_renders_without_training():
    at = _app()
    assert not at.exception
    assert at.title[0].value == 'Business Analytics in Action: From Model to App'
    assert any('synthetic' in m.value.lower() for m in at.markdown)
    assert any('No performance result yet' in i.value for i in at.info)


def test_full_student_flow():
    at = _app()
    # B: train one preset (KNN k=5) via the form; baseline is fitted alongside.
    at.radio(key='family_choice').set_value('KNN').run()
    at.selectbox[0].set_value(5)
    _button(at, 'Train and evaluate').click().run()
    assert not at.exception
    candidates = at.session_state['candidates']
    assert set(candidates) == {models.BASELINE_NAME, 'KNN (k=5)'}
    assert at.session_state['final'] is None

    # B: full comparison -> 15 candidates.
    _button(at, 'Run classroom comparison').click().run()
    assert not at.exception
    candidates = at.session_state['candidates']
    assert models.is_complete_comparison(candidates)
    expected = models.select_model(candidates)

    # C: freeze the recommendation (default selection) and finalize.
    _button(at, 'Freeze this specification for final evaluation').click().run()
    assert not at.exception
    assert at.session_state['selection']['name'] == expected
    assert at.session_state['selection']['kind'] == 'validation-best recommendation'
    _button(at, 'Finalize selected model and evaluate on test dates').click().run()
    assert not at.exception
    final = at.session_state['final']
    assert final['selected_name'] == expected and at.session_state['test_inspected'] is True
    assert any('Test performance: model refitted on development dates' in m.value for m in at.markdown)

    # D: typed prediction with the finalized model equals direct .predict().
    at.session_state['store_text'] = '3'
    at.session_state['category_text'] = ' bakery '
    at.session_state['date_text'] = '2025-10-15'
    at.session_state['actual_text'] = '20'
    _button(at, 'Predict').click().run()
    assert not at.exception
    p = at.session_state['last_prediction']
    row = models.make_prediction_row('3', 'Bakery', '2025-10-15')
    assert p['values']['category'] == 'Bakery'
    assert p['predicted'] == float(final['final_model'].predict(row)[0])
    shown = [m.value for m in at.markdown if 'Predicted daily sales' in m.value]
    assert shown and re.search(rf"{p['predicted']:.2f}", shown[0])

    # Invalid input never reaches .predict and shows a useful message.
    at.session_state['store_text'] = '9'
    at.session_state['date_text'] = '15/10/2025'
    _button(at, 'Predict').click().run()
    assert any('Valid stores' in e.value for e in at.error)
    assert any('YYYY-MM-DD' in e.value for e in at.error)

    # Refitting a member invalidates ensembles and supersedes the final result.
    at.radio(key='family_choice').set_value('KNN').run()
    at.selectbox[0].set_value(50)
    at.checkbox[0].check()
    _button(at, 'Train and evaluate').click().run()
    assert not at.exception
    assert models.EQUAL_ENSEMBLE_NAME not in at.session_state['candidates']
    if expected in models.ENSEMBLE_NAMES or expected == 'KNN (k=50)':
        assert at.session_state['final']['superseded'] is True
    assert at.session_state['test_inspected'] is True
