"""Business Analytics in Action: From Model to App — Streamlit wrapper.

Three tabs: Data, Model, Test. This file only renders the dashboard,
validates typed inputs and keeps session state. Every number shown comes
from ``models.py`` (the classroom engine); no model is defined here.
"""
import inspect
import traceback

import pandas as pd
import streamlit as st

import inputs
import models

TITLE = 'Business Analytics in Action: From Model to App'
FOOTER = 'Business Analytics and Data Visualization Fall 2026 - Prof. Jose Mendoza'
CHART_COLOR = '#356DA8'

NETWORK_LABELS = {(16,): 'One layer: 16 neurons', (32,): 'One layer: 32 neurons',
                  (32, 16): 'Two layers: 32 and 16 neurons'}
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


# ---------------------------------------------------------------------------
# Data, session state and shared pieces
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner='Loading the approved Mancino snapshot...')
def get_data():
    return models.prepare_data(models.load_data())


def init_state():
    defaults = {'active': None, 'last_prediction': None,
                'store_text': '', 'category_text': '', 'date_text': '', 'actual_text': ''}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def footer():
    st.divider()
    st.caption(FOOTER)


def fmt_r2(scores):
    return 'N/A' if scores['R2'] is None else f"{scores['R2']:.3f}"


def fmt_mape(scores):
    return 'N/A' if scores['MAPE'] is None else f"{scores['MAPE']:.2f}%"


def parameter_text(choice, parameter):
    if choice == 'Neural network':
        return NETWORK_LABELS[parameter]
    return str(parameter)


def source_of(*functions):
    return '\n\n'.join(inspect.getsource(f) for f in functions)


# ---------------------------------------------------------------------------
# Tab 1: Data
# ---------------------------------------------------------------------------
def tab_data(data):
    df = data['df']
    st.subheader('The Mancino dataset')
    st.markdown('Mancino Market is a **synthetic** grocery retailer: fictional daily unit sales for '
                'five stores and fifteen product categories, used throughout the course. '
                f'Source: [mancino_daily_sales.csv]({models.DATA_SOURCE_URL}) '
                '(v1_2025-11-01 snapshot, bundled offline; see `data/SOURCE.md`).')
    facts = models.describe_data(df)
    st.markdown(f"**{facts['Observations']:,}** observations · **{facts['Stores']}** stores · "
                f"**{facts['Categories']}** categories · **{facts['First date']}** to "
                f"**{facts['Last date']}**")

    st.markdown('**Variable dictionary** — what the model predicts and what it uses')
    st.table(pd.DataFrame([
        ['units_sold', 'Daily units for one store and category', 'Prediction target'],
        ['store_id', 'Store identifier (1-5), treated as text', 'Model input (categorical)'],
        ['category', 'Product category', 'Model input (categorical)'],
        ['weekday', 'Derived from date in Python', 'Model input (categorical)'],
        ['day_of_year', 'Derived from date', 'Model input (numeric)'],
        ['date', 'Selling date', 'Derives weekday and day_of_year; sets the date splits'],
        ['revenue', 'Realized revenue', 'Visible only — contains the outcome, never an input'],
        ['avg_price', 'Observed daily average price', 'Visible only — not known before the selling day'],
        ['day_of_week', 'Weekday in the source file', 'Visible only — weekday is recomputed from date'],
    ], columns=['Field', 'Meaning', 'Role']))

    st.markdown('**Browse the data** — these filters change the view only; they never change '
                'model fitting or evaluation data.')
    f1, f2, f3 = st.columns(3)
    stores = f1.multiselect('Store (view filter)', data['stores'], default=data['stores'])
    categories = f2.multiselect('Category (view filter)', data['categories'], default=data['categories'])
    search = f3.text_input('Search table text (store, category or weekday)')
    view = df[df.store_id.isin(stores) & df.category.isin(categories)]
    if search.strip():
        needle = search.strip().lower()
        view = view[view[['store_id', 'category', 'weekday']].apply(
            lambda col: col.str.lower().str.contains(needle, regex=False)).any(axis=1)]
    st.dataframe(view, width='stretch', height=300)
    st.caption(f'{len(view):,} of {len(df):,} rows shown.')

    if len(view):
        st.markdown('**Total units sold per day** (across the stores and categories in view)')
        daily = view.groupby('date')[models.TARGET].sum().rename('Total units sold')
        st.line_chart(daily, color=CHART_COLOR, x_label='Date', y_label='Total units sold')
    footer()


# ---------------------------------------------------------------------------
# Tab 2: Model
# ---------------------------------------------------------------------------
def invalidate_on_change(config):
    """A model or parameter change clears the fit, metrics and prior prediction."""
    S = st.session_state
    if S.active is not None and S.active['config'] != config:
        S.active = None
        S.last_prediction = None


def train(choice, parameter, config, data):
    S = st.session_state
    estimator, settings = models.build_model(choice, parameter)
    message = ('Training the ensemble — it fits its four classroom members...'
               if choice == 'Ensemble regression' else f'Training {choice}...')
    try:
        with st.spinner(message):
            result = models.fit_selected_model(estimator, data)
    except Exception as error:
        S.active = None
        S.last_prediction = None
        st.error(f'Training failed: {type(error).__name__}: {error}. Previous results were '
                 'cleared; prediction stays unavailable until a model trains successfully.')
        with st.expander('Technical details (for the instructor or developer)'):
            st.code(traceback.format_exc())
        return
    S.active = {'config': config, 'choice': choice, 'parameter': parameter,
                'settings': settings, **result}
    S.last_prediction = None


def show_results(data):
    active = st.session_state.active
    scores = active['scores']
    cols = st.columns(4)
    cols[0].metric('R²', fmt_r2(scores))
    cols[1].metric('MSE', f"{scores['MSE']:.2f}")
    cols[2].metric('RMSE', f"{scores['RMSE']:.2f}")
    cols[3].metric('MAPE', fmt_mape(scores))
    if scores['R2'] is None:
        st.warning(scores['R2_note'])
    if scores['MAPE'] is None:
        st.warning(scores['MAPE_note'])
    elif scores['zero_excluded_from_mape']:
        st.caption(f"MAPE excludes {scores['zero_excluded_from_mape']:,} observations with zero "
                   'actual sales (documented reporting policy); the other metrics use all '
                   f"{scores['observations']:,} test observations.")

    for message in active['warnings']:
        st.warning(f'Training warning: {message}')

    rmse_text = (f"This model's RMSE is {scores['RMSE']:.2f} units per store/category/day "
                 'on the held-out dates.')
    if scores['MAPE'] is None:
        mape_text = 'Its MAPE is not defined because no held-out observation has positive actual sales.'
    else:
        mape_text = (f"Its MAPE is {scores['MAPE']:.2f}% across "
                     f"{scores['positive_observations']:,} positive-sales observations.")
    st.markdown(f'{rmse_text} {mape_text} R² is dimensionless and can be negative; it is not '
                'percentage accuracy. These are historical evaluation results, not a prediction '
                'interval or a guarantee for one new forecast.')
    st.caption(f"Evaluation period: {active['test_start'].date()} to {active['test_end'].date()} "
               f"({active['test_rows']:,} held-out test observations). Fitted on "
               f"{active['development_start'].date()} to {active['development_end'].date()} "
               f"(training + validation, {active['development_rows']:,} rows) in "
               f"{active['fit_seconds']:.1f} s."
               + (f" Network training epochs: {active['training_epochs']}."
                  if 'training_epochs' in active else ''))
    st.info(HISTORICAL_NOTE)


def tab_model(data):
    S = st.session_state
    st.subheader('Choose one model, train it, read its results')
    choice = st.selectbox('Model', models.MODEL_CHOICES, key='model_choice')
    preset = models.PRESETS[choice]
    parameter = st.selectbox(
        preset['label'], preset['values'], index=preset['values'].index(preset['default']),
        key=f'param_{choice}', format_func=lambda value: parameter_text(choice, value))
    config = (choice, parameter)
    invalidate_on_change(config)

    st.markdown(f'**How it predicts:** {HOW_IT_PREDICTS[choice]}')
    if choice == 'Ensemble regression':
        shares = (models.normalized_weights(models.ENSEMBLE_WEIGHTS)
                  if parameter == 'Weighted average' else [0.25] * 4)
        st.caption('Fixed classroom members (from the ensemble notebook), in order: '
                   + '; '.join(f'{name} ({settings}), weight {share:.3f}'
                               for (name, settings), share in zip(models.ENSEMBLE_MEMBERS, shares))
                   + '. Members are fixed — the app never searches for configurations — and only '
                     'the combined ensemble result is shown.')

    if st.button('Train model', type='primary'):
        train(choice, parameter, config, data)

    if S.active is None:
        st.info('No results yet for this configuration. Click "Train model" to fit it on the '
                'development dates and see its four test metrics.')
    else:
        show_results(data)

    with st.expander('Code from class', expanded=False):
        functions = [models.make_pipeline, CONSTRUCTORS[choice]]
        if choice == 'Ensemble regression':
            functions.insert(1, models.ensemble_member_estimators)
        st.code(source_of(*functions), language='python')
        st.caption('Read directly from models.py with inspect.getsource — the dashboard has no '
                   'second copy of the model code.')
    footer()


# ---------------------------------------------------------------------------
# Tab 3: Test
# ---------------------------------------------------------------------------
def tab_test(data):
    S = st.session_state
    st.subheader('Test the model with a typed observation')
    if S.active is None:
        st.info('Train a model in the Model tab before making a prediction.')
        footer()
        return

    st.markdown('The four performance metrics were computed on historical held-out rows. Typing a '
                'store, category and date below produces **one new forecast** with the same fitted '
                'model; it never retrains the model or changes the historical metrics.')
    with st.expander('Valid stores and categories'):
        st.write('Stores: ' + ', '.join(data['stores']))
        st.write('Categories: ' + ', '.join(data['categories']))
    if st.button('Use example'):
        S.store_text, S.category_text, S.date_text, S.actual_text = '3', 'Bakery', '2025-10-15', ''
        st.rerun()

    with st.form('predict_form'):
        c1, c2, c3, c4 = st.columns(4)
        c1.text_input('Store ID', key='store_text', placeholder='e.g. 3')
        c2.text_input('Product category', key='category_text', placeholder='e.g. Bakery')
        c3.text_input('Date (YYYY-MM-DD)', key='date_text', placeholder='2025-10-15')
        c4.text_input('Actual units (optional)', key='actual_text',
                      help='Only for evaluating this one example; never a model input.')
        submitted = st.form_submit_button('Predict', type='primary')
    if submitted:
        values, errors = inputs.validate_prediction_inputs(
            S.store_text, S.category_text, S.date_text, S.actual_text,
            data['stores'], data['categories'])
        if errors:
            for message in errors:
                st.error(message)
        else:
            row = models.make_prediction_row(values['store_id'], values['category'], values['date'])
            predicted = models.predict_one(S.active['pipeline'], row)
            S.last_prediction = {'config': S.active['config'], 'values': values,
                                 'row': row, 'predicted': predicted}
    if S.last_prediction is not None and S.last_prediction['config'] == S.active['config']:
        show_prediction(S.last_prediction, data)
    footer()


def show_prediction(p, data):
    active = st.session_state.active
    values, row, scores = p['values'], p['row'], active['scores']
    st.markdown('---')
    st.markdown(f"### Predicted daily sales: **{p['predicted']:.2f} units**")
    if p['predicted'] < 0:
        st.error('The raw prediction is negative, which is not a valid physical sales estimate. '
                 'It is shown unclipped to preserve classroom behavior; treat it as a model limitation.')
    st.write(f"**Model:** {active['choice']}, "
             f"{models.PRESETS[active['choice']]['label'].lower()}: "
             f"{parameter_text(active['choice'], active['parameter'])}.")
    st.write(f"**Accepted inputs:** store {values['store_id']}, category \"{values['category']}\" "
             f"(canonical form of what you typed), date {values['date'].date()} → "
             f"weekday {row.iloc[0]['weekday']}, day of year {row.iloc[0]['day_of_year']}.")
    for _, text in inputs.date_notices(values['date'],
                                       active['development_start'], active['development_end'],
                                       active['test_start'], active['test_end'],
                                       data['df'].date.min(), data['df'].date.max()):
        st.warning(text)

    st.markdown(f"**Historical test metrics:** R² {fmt_r2(scores)} · MSE {scores['MSE']:.2f} · "
                f"RMSE {scores['RMSE']:.2f} · MAPE {fmt_mape(scores)}")
    st.caption('These metrics describe historical held-out observations, not the accuracy of this '
               'new prediction. The actual outcome for your typed observation is not known unless '
               'you entered it.')
    if values.get('actual_units') is not None:
        actual = values['actual_units']
        signed = actual - p['predicted']
        ape = f'{100 * abs(signed) / actual:.2f}%' if actual > 0 else 'N/A (actual is zero)'
        st.write(f'**This example only:** actual {actual:.2f} units; signed error '
                 f'(actual − predicted) {signed:+.2f} — positive means underprediction; absolute '
                 f'error {abs(signed):.2f}; percentage error (APE, this one row, not MAPE) {ape}. '
                 'This single observation does not update the historical metrics and is never '
                 'used for training.')


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title=TITLE, layout='wide')
    init_state()
    st.title(TITLE)
    st.markdown('Explore the Mancino data, train one classroom regression model, and type inputs '
                'to get a prediction. **The dataset is synthetic teaching data.**')
    try:
        data = get_data()
    except Exception as error:
        st.error(f'The dataset could not be loaded: {error}')
        st.stop()
    tab1, tab2, tab3 = st.tabs(['Data', 'Model', 'Test'])
    with tab1:
        tab_data(data)
    with tab2:
        tab_model(data)
    with tab3:
        tab_test(data)


main()
