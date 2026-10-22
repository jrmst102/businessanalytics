"""Typed-input validation for the prediction form (wrapper code, not engine code).

Everything the student types is treated as data. These helpers trim, match and
parse text, then hand canonical values to ``models.make_prediction_row``.
They never evaluate text or build shell commands from it.
"""
import math
import re
from datetime import datetime

import pandas as pd

ISO_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class InputError(ValueError):
    """A typed value that cannot be used; the message is shown to the student."""


def _collapse(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


def resolve_store(text, stores):
    value = (text or '').strip()
    if not value:
        raise InputError('Store ID is required. Valid stores: ' + ', '.join(stores) + '.')
    if value in stores:
        return value
    raise InputError(f'Store "{value}" is not in the dataset. Valid stores: ' + ', '.join(stores) + '.')


def resolve_category(text, categories):
    """Exact match first; otherwise a unique case/whitespace-insensitive match."""
    value = (text or '').strip()
    if not value:
        raise InputError('Product category is required. Examples: ' + ', '.join(categories[:4]) + ' ...')
    if value in categories:
        return value
    matches = [c for c in categories if _collapse(c) == _collapse(value)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise InputError(f'"{value}" is ambiguous; it could be: ' + ', '.join(matches)
                         + '. Type one of them exactly.')
    partial = [c for c in categories if _collapse(value) in _collapse(c)]
    hint = (' Did you mean: ' + ', '.join(partial) + '?') if partial else ''
    raise InputError(f'Category "{value}" is not in the dataset.{hint} '
                     'Valid categories: ' + ', '.join(categories) + '.')


def parse_iso_date(text):
    value = (text or '').strip()
    if not value:
        raise InputError('Date is required, in YYYY-MM-DD form (for example 2025-10-15).')
    if not ISO_DATE_PATTERN.match(value):
        raise InputError(f'Date "{value}" is not in YYYY-MM-DD form (for example 2025-10-15).')
    try:
        parsed = datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise InputError(f'"{value}" is not a real calendar date.') from None
    return pd.Timestamp(parsed)


def parse_actual_units(text):
    """Optional field: empty means unknown; otherwise finite and nonnegative."""
    value = (text or '').strip()
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        raise InputError(f'Actual units "{value}" must be a number.') from None
    if not math.isfinite(number) or number < 0:
        raise InputError('Actual units must be a finite, nonnegative number.')
    return number


def validate_prediction_inputs(store_text, category_text, date_text, actual_text, stores, categories):
    """Return (canonical values, list of error messages). Nothing is predicted here."""
    values, errors = {}, []
    for key, func, args in [
        ('store_id', resolve_store, (store_text, stores)),
        ('category', resolve_category, (category_text, categories)),
        ('date', parse_iso_date, (date_text,)),
        ('actual_units', parse_actual_units, (actual_text,)),
    ]:
        try:
            values[key] = func(*args)
        except InputError as error:
            errors.append(str(error))
    return values, errors


def date_notices(when, fit_start, fit_end, eval_start, eval_end, data_start, data_end):
    """Educational notices about where a typed date sits relative to the fitted periods."""
    when = pd.Timestamp(when)
    notices = []
    if fit_start <= when <= fit_end:
        notices.append(('historical', 'This date lies inside the model\'s fitting period, so the example '
                                      'is historical and potentially in-sample. It is not an independent test observation.'))
    elif eval_start <= when <= eval_end:
        notices.append(('evaluation', 'This date lies inside the evaluation period whose metrics are shown below; '
                                      'the model did not fit on it, but those metrics already summarize this period.'))
    if when < data_start or when > data_end:
        notices.append(('extrapolation', f'Extrapolation notice: this date is outside the observed data range '
                                         f'({data_start.date()} to {data_end.date()}). The prediction is educational only; '
                                         'no validated accuracy is claimed for this horizon.'))
    if when.year != data_start.year:
        notices.append(('year', f'Year {when.year} differs from the dataset year {data_start.year}. Year is not a predictor: '
                                'the model uses weekday and day of year, and it has not demonstrated generalization to a new year.'))
    return notices
