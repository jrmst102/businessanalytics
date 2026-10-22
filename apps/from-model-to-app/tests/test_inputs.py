"""Typed-input validation checks for the prediction form."""
import pandas as pd
import pytest

import inputs
import models

STORES = ['1', '2', '3', '4', '5']
CATEGORIES = ['Bakery', 'Dairy & Eggs', 'Meat and Seafood', 'Snacks/Cookies/Chips']


def test_store_matching():
    assert inputs.resolve_store('  3 ', STORES) == '3'
    with pytest.raises(inputs.InputError, match='required'):
        inputs.resolve_store('', STORES)
    with pytest.raises(inputs.InputError, match='Valid stores'):
        inputs.resolve_store('9', STORES)


def test_category_normalization_is_visible_and_deterministic():
    assert inputs.resolve_category('bakery', CATEGORIES) == 'Bakery'
    assert inputs.resolve_category('  DAIRY &   eggs ', CATEGORIES) == 'Dairy & Eggs'
    with pytest.raises(inputs.InputError, match='Did you mean'):
        inputs.resolve_category('dairy', CATEGORIES)
    with pytest.raises(inputs.InputError, match='not in the dataset'):
        inputs.resolve_category('Toys', CATEGORIES)


def test_ambiguous_category_is_rejected():
    with pytest.raises(inputs.InputError, match='ambiguous'):
        inputs.resolve_category('bakery', ['Bakery', 'BAKERY'])


def test_date_parsing():
    assert inputs.parse_iso_date(' 2025-10-15 ') == pd.Timestamp('2025-10-15')
    for bad in ['', '15/10/2025', '2025-13-01', '2025-02-30', 'tomorrow', '2025-1-5']:
        with pytest.raises(inputs.InputError):
            inputs.parse_iso_date(bad)


def test_actual_units_optional_and_validated():
    assert inputs.parse_actual_units('') is None
    assert inputs.parse_actual_units('12.5') == 12.5
    for bad in ['-1', 'abc', 'inf', 'nan']:
        with pytest.raises(inputs.InputError):
            inputs.parse_actual_units(bad)


def test_validate_collects_all_errors():
    values, errors = inputs.validate_prediction_inputs('', 'Toys', 'bad', '-2', STORES, CATEGORIES)
    assert len(errors) == 4 and values == {}
    values, errors = inputs.validate_prediction_inputs('2', 'bakery', '2025-05-01', '', STORES, CATEGORIES)
    assert not errors
    assert values['store_id'] == '2' and values['category'] == 'Bakery' and values['actual_units'] is None
    row = models.make_prediction_row(values['store_id'], values['category'], values['date'])
    assert list(row.columns) == models.FEATURES and row.iloc[0]['weekday'] == 'Thursday'


def test_date_notices():
    kwargs = dict(fit_start=pd.Timestamp('2025-01-01'), fit_end=pd.Timestamp('2025-07-02'),
                  eval_start=pd.Timestamp('2025-07-03'), eval_end=pd.Timestamp('2025-09-01'),
                  data_start=pd.Timestamp('2025-01-01'), data_end=pd.Timestamp('2025-11-01'))
    kinds = lambda when: [k for k, _ in inputs.date_notices(when, **kwargs)]
    assert kinds('2025-03-01') == ['historical']
    assert kinds('2025-08-01') == ['evaluation']
    assert kinds('2025-10-01') == []
    assert kinds('2025-12-25') == ['extrapolation']
    assert kinds('2026-01-10') == ['extrapolation', 'year']
