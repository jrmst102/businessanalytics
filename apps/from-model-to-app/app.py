"""Business Analytics in Action: From Model to App - Streamlit wrapper.

This file only renders the dashboard, validates typed inputs and keeps session
state. Every number shown comes from ``models.py`` (the classroom engine).
"""
import inspect
import traceback

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import inputs
import models

matplotlib.use('Agg')

TITLE = 'Business Analytics in Action: From Model to App'
FAMILY_CHOICES = ['KNN', 'Regression tree', 'Random forest', 'Neural network',
                  'Ensemble: equal weights', 'Ensemble: weighted average']
PRESETS = {
    'KNN': ('Number of neighbors (n_neighbors)', models.K_VALUES, models.knn_name),
    'Regression tree': ('Maximum depth (max_depth)', models.TREE_DEPTHS, models.tree_name),
    'Random forest': ('Number of trees (n_estimators)', models.FOREST_SIZES, models.forest_name),
    'Neural network': ('Hidden layers (hidden_layer_sizes)', models.NETWORK_LAYERS, models.network_name),
}
FAMILY_BUILDER = {'KNN': models.make_knn, 'Regression tree': models.make_tree,
                  'Random forest': models.make_forest, 'Neural network': models.make_network,
                  'Baseline': models.make_baseline, 'Ensemble': models.make_ensemble}
HOW_IT_PREDICTS = {
    'KNN': 'Averages units sold over the k most similar training observations (same store, category and '
           'weekday indicators plus a standardized day of year).',
    'Regression tree': 'Splits the training data into groups by repeated yes/no questions and predicts the '
                       'mean sales of the terminal leaf an observation falls into.',
    'Random forest': 'Averages many trees fitted to bootstrap samples with a random subset of columns at each '
                     'split; it is itself an ensemble of trees.',
    'Neural network': 'Passes the encoded features through hidden ReLU layers trained with Adam on a '
                      'standardized target; predictions are converted back to units.',
    'Ensemble: equal weights': 'Averages the predictions of the four family winners (KNN, tree, forest, network) '
                               'with 25% weight each.',
    'Ensemble: weighted average': 'Averages the four family winners with relative weights [1, 1, 2, 2], '
                                  'normalized to 1/6, 1/6, 1/3, 1/3. The weights are illustrative, not optimized.',
    'Baseline': 'Always predicts the mean of units sold on the fitting period.',
}
EXPERIMENT_LABEL = 'Validation performance: model fitted on training dates'
FINAL_LABEL = 'Test performance: model refitted on development dates'
HISTORICAL_NOTE = ('These metrics summarize historical evaluation observations. '
                   'They do not measure the accuracy of this new prediction.')


# ---------------------------------------------------------------------------
# Data and session state
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner='Loading the approved Mancino snapshot...')
def get_data():
    return models.prepare_data(models.load_data())


def init_state():
    defaults = {'candidates': {}, 'failed': {}, 'selection': None, 'final': None,
                'test_inspected': False, 'last_prediction': None, 'log': [],
                'store_text': '', 'category_text': '', 'date_text': '', 'actual_text': ''}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def log(message):
    st.session_state.log.append(message)


def stage_name():
    S = st.session_state
    if S.final is not None and not S.final.get('superseded'):
        return 'Finalized'
    if S.selection is not None:
        return 'Selected for final evaluation'
    if S.candidates:
        return 'Candidate evaluated'
    return 'Not trained'


def invalidate_dependents(changed_names):
    """A refitted or removed candidate invalidates ensembles, selection and final built on it."""
    S = st.session_state
    affected = set(changed_names)
    if affected & set(models.INDIVIDUAL_NAMES):
        for name in models.ENSEMBLE_NAMES:
            if S.candidates.pop(name, None) is not None:
                affected.add(name)
    if S.selection and S.selection['name'] in affected:
        log(f"Selection of {S.selection['name']} cleared: its configuration was refitted.")
        S.selection = None
    if S.final and S.final['selected_name'] in affected and not S.final.get('superseded'):
        S.final['superseded'] = True
        log(f"Final result for {S.final['selected_name']} marked as superseded (configuration refitted). "
            'Its test scores are kept for the record but are not reused.')


def fit_with_status(specs, data, title):
    """Fit a list of specifications one at a time, with a visible progress bar."""
    S = st.session_state
    with st.status(title, expanded=True) as status:
        bar = st.progress(0.0)
        for i, spec in enumerate(specs):
            st.write(f'Fitting {spec["name"]} ...')
            try:
                candidate = models.fit_candidate(spec, data)
                S.candidates[spec['name']] = candidate
                S.failed.pop(spec['name'], None)
                log(f"Evaluated {spec['name']}: validation MAE {candidate['result']['Validation MAE']:.3f}")
            except Exception as error:  # a failed candidate is recorded, never reported as evaluated
                S.failed[spec['name']] = f'{type(error).__name__}: {error}\n\n{traceback.format_exc()}'
                S.candidates.pop(spec['name'], None)
                log(f"FAILED {spec['name']}: {error}")
            bar.progress((i + 1) / len(specs))
        status.update(label=f'{title} - done', state='complete', expanded=False)


def ensure_individuals(data):
    missing = [spec for spec in models.individual_candidates() if spec['name'] not in st.session_state.candidates]
    if missing:
        st.info(f'Ensembles need the four family winners, so the {len(missing)} missing classroom preset(s) '
                'will be evaluated first.')
        fit_with_status(missing, data, 'Evaluating the individual classroom presets')
    return not any(name in st.session_state.failed for name in models.INDIVIDUAL_NAMES + [models.BASELINE_NAME])


def train_candidate(choice, preset, data, refit):
    S = st.session_state
    if choice.startswith('Ensemble'):
        if not ensure_individuals(data):
            st.error('At least one individual preset failed; fix it before building an ensemble.')
            return
        spec = next(s for s in models.ensemble_candidates(S.candidates) if s['name'] == choice)
        names = [choice]
    else:
        spec = models.candidate_by_name(PRESETS[choice][2](preset))
        names = [spec['name']]
    specs = [spec]
    if models.BASELINE_NAME not in S.candidates:
        specs.insert(0, models.candidate_by_name(models.BASELINE_NAME))
    already = [s for s in specs if s['name'] in S.candidates]
    if already and not refit:
        st.success(f'{already[0]["name"]} is already evaluated in this session with identical settings; '
                   'reusing that completed run. Tick "Refit" to fit it again.')
        specs = [s for s in specs if s['name'] not in S.candidates]
    if not specs:
        return
    invalidate_dependents([s['name'] for s in specs if s['name'] in S.candidates])
    fit_with_status(specs, data, f'Training and evaluating {", ".join(names)}')


def run_comparison(data):
    S = st.session_state
    specs = [s for s in models.individual_candidates() if s['name'] not in S.candidates]
    if specs:
        fit_with_status(specs, data, 'Classroom comparison: baseline and 12 presets')
    if any(name in S.failed for name in models.INDIVIDUAL_NAMES + [models.BASELINE_NAME]):
        st.error('The classroom comparison is incomplete: a candidate failed. See the failure panel below.')
        return
    ensembles = [s for s in models.ensemble_candidates(S.candidates) if s['name'] not in S.candidates]
    if ensembles:
        fit_with_status(ensembles, data, 'Classroom comparison: averaging ensembles')


# ---------------------------------------------------------------------------
# Small presentation helpers
# ---------------------------------------------------------------------------
def metric_table(scores, label):
    return pd.DataFrame([{label: 'MAE (units)', 'Value': scores['MAE']},
                         {label: 'RMSE (units)', 'Value': scores['RMSE']},
                         {label: 'R² (not accuracy)', 'Value': scores['R2']}]).set_index(label)


def candidate_metrics(candidate):
    r = candidate['result']
    return {'MAE': r['Validation MAE'], 'RMSE': r['Validation RMSE'], 'R2': r['Validation R2']}


def period_text(data, stage):
    if stage == 'final':
        return (f"fitted on {data['train'].date.min().date()} to {data['validation_end'].date()} "
                f"(training + validation); evaluated on {data['test'].date.min().date()} to "
                f"{data['test'].date.max().date()} (test, {len(data['X_test']):,} observations)")
    return (f"fitted on {data['train'].date.min().date()} to {data['train_end'].date()} (training); "
            f"evaluated on {data['validation'].date.min().date()} to {data['validation_end'].date()} "
            f"(validation, {len(data['X_val']):,} observations)")


def show_ensemble_members(candidate):
    if candidate['family'] != 'Ensemble':
        return
    S = st.session_state
    rows = []
    for (family, name), weight in zip(candidate['winners'].items(), models.normalized_weights(candidate['weights'])):
        settings = S.candidates[name]['settings'] if name in S.candidates else '(member refitted inside the ensemble)'
        rows.append({'Order': len(rows) + 1, 'Family': family, 'Member': name, 'Settings': settings,
                     'Normalized weight': weight})
    st.dataframe(pd.DataFrame(rows).set_index('Order'), use_container_width=True)
    st.caption('Members are the lowest-validation-MAE preset in each family, refitted inside VotingRegressor. '
               'The weighted preset is illustrative; it is not optimized and does not guarantee better accuracy.')


def source_of(*functions):
    return '\n\n'.join(inspect.getsource(f) for f in functions)


# ---------------------------------------------------------------------------
# A. Explore the dataset
# ---------------------------------------------------------------------------
def tab_explore(data):
    df = data['df']
    description = models.describe_data(df)
    st.subheader('Explore the dataset')
    st.markdown(f'**Source:** [mancino_daily_sales.csv]({models.DATA_SOURCE_URL}) (v1_2025-11-01 snapshot, '
                f'bundled offline; SHA-256 `{models.DATA_SHA256[:16]}...`). '
                'Mancino Market is a **synthetic** grocery retailer; the data are fictional teaching data (CC BY 4.0).')
    cols = st.columns(5)
    for col, (label, value) in zip(cols, description.items()):
        col.metric(label, f'{value:,}' if isinstance(value, int) else str(value))

    st.markdown('**Variable definitions**')
    st.table(pd.DataFrame([
        ['date', 'Selling date', 'Split the data; derive weekday and day_of_year'],
        ['store_id', 'Store identifier (1-5), treated as text', 'Categorical predictor'],
        ['category', 'Product category', 'Categorical predictor'],
        ['weekday', 'Derived from date in Python', 'Categorical predictor'],
        ['day_of_year', 'Derived from date; the only numeric predictor', 'Numeric predictor'],
        ['units_sold', 'Daily units for one store and category', 'TARGET (never an input)'],
        ['revenue', 'Realized revenue', 'Excluded: contains the outcome'],
        ['avg_price', 'Observed daily average price', 'Excluded: not known before the selling day'],
        ['day_of_week', 'Weekday in the source file', 'Visible only; weekday is recomputed from date'],
    ], columns=['Field', 'Meaning', 'Engine treatment']))

    st.markdown('**Fixed chronological partitions** (identical for every model; dates never cross sets)')
    st.table(data['partitions'])
    st.caption('The holdout protects the computational evaluation workflow. You can inspect the whole CSV here; '
               'the app does not claim test labels are secret from a student reading the file.')

    st.markdown('**View filters** (change what is displayed only; they never touch training or metrics)')
    f1, f2, f3 = st.columns(3)
    stores = f1.multiselect('Store', data['stores'], default=data['stores'], key='view_stores')
    categories = f2.multiselect('Category', data['categories'], default=data['categories'], key='view_categories')
    date_range = f3.date_input('Date range', (df.date.min().date(), df.date.max().date()),
                               min_value=df.date.min().date(), max_value=df.date.max().date(), key='view_dates')
    view = df[df.store_id.isin(stores) & df.category.isin(categories)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        view = view[(view.date >= pd.Timestamp(date_range[0])) & (view.date <= pd.Timestamp(date_range[1]))]
    search = st.text_input('Search table text (store, category or weekday)', key='view_search')
    if search.strip():
        needle = search.strip().lower()
        view = view[view[['store_id', 'category', 'weekday']].apply(
            lambda col: col.str.lower().str.contains(needle, regex=False)).any(axis=1)]
    st.dataframe(view, use_container_width=True, height=300)
    st.caption(f'{len(view):,} of {len(df):,} rows shown.')

    if len(view):
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
        axes[0].hist(view[models.TARGET], bins=30, color='#356DA8', edgecolor='white')
        axes[0].set(xlabel='Daily units per store/category', ylabel='Number of observations', title='Sales distribution')
        view.groupby('date')[models.TARGET].sum().plot(ax=axes[1], color='#356DA8')
        for boundary, label in [(data['train_end'], 'train end'), (data['validation_end'], 'validation end')]:
            axes[1].axvline(boundary, color='#B64B44', linestyle='--', linewidth=1)
            axes[1].text(boundary, axes[1].get_ylim()[1], label, fontsize=8, ha='right', va='top', color='#B64B44')
        axes[1].set(xlabel='Date', ylabel='Total units in view', title='Sales over time')
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# ---------------------------------------------------------------------------
# B. Choose and run models
# ---------------------------------------------------------------------------
def tab_models(data):
    S = st.session_state
    st.subheader('Choose and run models')
    st.markdown('Six learned approaches are available. The **mean-sales baseline** is a benchmark, not a '
                'learned model; it is fitted automatically alongside your first candidate.')
    choice = st.radio('Model family', FAMILY_CHOICES, horizontal=True, key='family_choice')
    st.markdown(f'**How it predicts:** {HOW_IT_PREDICTS[choice]}')

    with st.form('train_form'):
        preset = None
        if choice in PRESETS:
            label, options, _ = PRESETS[choice]
            preset = st.selectbox(label, options, format_func=str)
        elif choice == 'Ensemble: weighted average':
            st.markdown(f'Classroom weights `{models.ENSEMBLE_WEIGHTS}` for KNN, tree, forest, network '
                        f'(normalized: {", ".join(f"{w:.3f}" for w in models.normalized_weights(models.ENSEMBLE_WEIGHTS))}). '
                        'Fixed in this version.')
        else:
            st.markdown('Equal averaging of the four family winners (25% each).')
        refit = st.checkbox('Refit even if this configuration was already evaluated in this session', value=False)
        submitted = st.form_submit_button('Train and evaluate', type='primary')
    if submitted:
        train_candidate(choice, preset, data, refit)

    st.divider()
    st.markdown('**Run classroom comparison** evaluates the exact 15-candidate set from the final notebook: '
                'the baseline, three KNNs, three trees, three forests, three networks and two ensembles, in order. '
                'Completed identical runs from this session are reused.')
    if st.button('Run classroom comparison'):
        run_comparison(data)
        if models.is_complete_comparison(S.candidates):
            st.success('Classroom comparison complete: all 15 candidates evaluated. See "Compare and select".')

    if S.failed:
        with st.expander(f'{len(S.failed)} failed candidate(s) - excluded from selection', expanded=True):
            for name, detail in S.failed.items():
                st.error(f'{name} failed to fit.')
                st.code(detail)

    with st.expander('Classroom settings (fixed in this version)'):
        st.table(pd.DataFrame([
            ['Mean baseline', 'DummyRegressor', "strategy='mean'"],
            ['KNN', 'KNeighborsRegressor', "weights='uniform', n_jobs=-1; day_of_year standardized"],
            ['Regression tree', 'DecisionTreeRegressor', f'min_samples_leaf={models.MIN_LEAF}, random_state={models.SEED}; passthrough'],
            ['Random forest', 'RandomForestRegressor', f'max_depth=12, min_samples_leaf=30, max_features=0.8, bootstrap=True, random_state={models.SEED}, n_jobs=-1'],
            ['Neural network', 'MLPRegressor in TransformedTargetRegressor',
             f'relu, adam, alpha=0.01, batch_size=256, learning_rate_init=0.001, max_iter=300, early_stopping=True, '
             f'validation_fraction=0.15, n_iter_no_change=20, random_state={models.SEED}; target standardized'],
            ['Ensembles', 'VotingRegressor', f'four family winners in order KNN, tree, forest, network; n_jobs=1; weights {models.ENSEMBLE_WEIGHTS} for the weighted preset'],
        ], columns=['Choice', 'Constructor', 'Fixed settings']))
        st.caption(f'Preprocessing: OneHotEncoder(handle_unknown="ignore", sparse_output=False) on {models.CATEGORICAL}; '
                   f'StandardScaler or passthrough on {models.NUMERIC}. Seed {models.SEED}. Omitted scikit-learn defaults are kept.')

    with st.expander('Code from class (the engine functions used for this choice)'):
        family_key = 'Ensemble' if choice.startswith('Ensemble') else choice
        functions = [models.make_pipeline, FAMILY_BUILDER[family_key], models.fit_and_evaluate, models.metrics]
        if family_key == 'Ensemble':
            functions.insert(1, models.family_winners)
        st.code(source_of(*functions), language='python')
        st.caption('Read straight from models.py with inspect.getsource; there is no second copy of the model code.')

    if S.candidates:
        st.markdown('**Evaluated this session**')
        for name in models.results_table(S.candidates):
            c = S.candidates[name]
            r = c['result']
            line = (f"{name} - validation MAE {r['Validation MAE']:.3f} units, "
                    f"RMSE {r['Validation RMSE']:.3f}, R² {r['Validation R2']:.3f}, fit {r['Fit seconds']:.2f} s")
            if 'training_epochs' in c:
                line += f", training epochs {c['training_epochs']}"
            st.write(line)
            for message in c['warnings']:
                st.warning(f'{name}: {message}')


# ---------------------------------------------------------------------------
# C. Compare and select
# ---------------------------------------------------------------------------
def tab_compare(data):
    S = st.session_state
    st.subheader('Compare and select')
    if not S.candidates:
        st.info('No candidates evaluated yet. Train a model in "Choose and run models".')
        return
    complete = models.is_complete_comparison(S.candidates)
    st.caption(EXPERIMENT_LABEL + '. MAE and RMSE are in units sold per store/category/day. R² is the improvement '
               'over predicting the validation period\'s mean; it is not classification accuracy and can be negative.')
    board = models.leaderboard(S.candidates)
    display_cols = ['Model', 'Family', 'Settings', 'Train MAE', 'Validation MAE', 'Validation RMSE',
                    'Validation R2', 'Fit seconds', 'MAE improvement vs baseline (%)']
    shown = board[display_cols].copy()
    shown['MAE improvement vs baseline (%)'] = shown['MAE improvement vs baseline (%)'].map(
        lambda v: 'not defined' if pd.isna(v) else f'{v:.3f}')
    st.dataframe(shown.round(3), use_container_width=True, hide_index=True)
    if models.BASELINE_NAME not in S.candidates:
        st.warning('The mean baseline has not been fitted, so improvement over baseline is not defined yet.')

    fig, ax = plt.subplots(figsize=(10, 0.45 * len(board) + 1.5))
    board.set_index('Model')[['Train MAE', 'Validation MAE']].plot.barh(ax=ax, color=['#A7C4DE', '#356DA8'])
    ax.set_xlabel('MAE: units per store/category/day')
    ax.set_title('Training versus validation MAE (sorted by validation MAE)')
    ax.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    recommended = models.select_model(S.candidates)
    if complete:
        gain = models.ensemble_gain(S.candidates)
        st.success(f'**Validation-best recommendation (all 15 candidates):** {recommended}. '
                   f"Best individual: {gain['best_individual']}; best ensemble: {gain['best_ensemble']}; ensemble gain "
                   f"{gain['ensemble_gain_units']:.3f} MAE units ({gain['ensemble_gain_percent']:.2f}%). "
                   'A negative gain means the ensemble performed worse.')
        with st.expander('Family winners and residual correlations'):
            winners = models.family_winners(S.candidates)
            st.table(pd.DataFrame([{'Family': f, 'Selected configuration': n,
                                    'Validation MAE': S.candidates[n]['result']['Validation MAE']}
                                   for f, n in winners.items()]).round(3))
            st.dataframe(models.residual_correlations(S.candidates, winners, data).round(3))
            st.caption('High residual correlations limit the benefit of averaging.')
    else:
        st.info(f'**Validation-best among the {len(S.candidates)} candidates evaluated so far:** {recommended}. '
                'Run the classroom comparison for the full 15-candidate recommendation.')
    st.caption('Selection uses full-precision validation MAE; ties keep the earlier notebook entry '
               '(baseline first, then presets in listed order, then ensembles). Test scores and fitting time are never used.')

    with st.expander('Inspect a fitted candidate against the baseline'):
        name = st.selectbox('Candidate', list(models.results_table(S.candidates)), key='inspect_name')
        c = S.candidates[name]
        cols = st.columns(2)
        cols[0].table(metric_table(candidate_metrics(c), f'{name} (validation)'))
        if models.BASELINE_NAME in S.candidates:
            cols[1].table(metric_table(candidate_metrics(S.candidates[models.BASELINE_NAME]), 'Mean baseline (validation)'))
        st.write(f"Settings: {c['settings']}")
        show_ensemble_members(c)
        st.json(models.run_identity(name, c['settings'], data, 'experiment'))

    st.divider()
    st.markdown('**Select the specification to finalize**')
    if S.test_inspected:
        st.warning('Test outcomes have already been inspected in this session. Any further selection or tuning is '
                   'additional exploration on an already inspected test period, not a new unseen evaluation.')
    if S.selection:
        sel = S.selection
        st.info(f"Frozen selection: **{sel['name']}** ({sel['kind']}). Recommendation at freeze time: {sel['recommended']}."
                + (f" Reason: {sel['reason']}" if sel['reason'] else ''))
    names = list(models.results_table(S.candidates))
    with st.form('selection_form'):
        chosen = st.selectbox('Candidate to finalize (default: validation-best recommendation)', names,
                              index=names.index(recommended))
        reason = st.text_area('Managerial reason (required if you depart from the recommendation)', height=80)
        frozen = st.form_submit_button('Freeze this specification for final evaluation')
    if frozen:
        if chosen != recommended and not reason.strip():
            st.error('Please record a managerial reason for choosing a candidate other than the recommendation.')
        else:
            kind = 'validation-best recommendation' if chosen == recommended else 'student selection'
            S.selection = {'name': chosen, 'kind': kind, 'recommended': recommended, 'reason': reason.strip(),
                           'specification': models.clone(S.candidates[chosen]['specification']),
                           'family': S.candidates[chosen]['family'], 'settings': S.candidates[chosen]['settings'],
                           'complete_comparison': complete}
            log(f'Froze {chosen} ({kind}).')
            st.success(f'{chosen} frozen as a {kind}. Finalize it in "Final evaluation".')
            st.rerun()


# ---------------------------------------------------------------------------
# D. Type inputs and predict
# ---------------------------------------------------------------------------
def prediction_models():
    S = st.session_state
    options = {}
    if S.final is not None and not S.final.get('superseded'):
        options[f"Finalized: {S.final['selected_name']} (refit on training + validation)"] = ('final', S.final['selected_name'])
    for name in models.results_table(S.candidates):
        options[f'Experiment: {name} (fitted on training dates)'] = ('experiment', name)
    return options


def tab_predict(data):
    S = st.session_state
    st.subheader('Type inputs and predict')
    options = prediction_models()
    if not options:
        st.info('Prediction is unavailable until a model has been trained. No performance result yet.')
        return
    st.markdown('"Type any data" means your own valid observation within the fixed schema: an existing store, '
                'an existing category and a date. Weekday and day of year are derived from the date in Python. '
                'Prediction never retrains the model or changes the leaderboard.')
    with st.expander('Valid stores and categories'):
        st.write('Stores: ' + ', '.join(data['stores']))
        st.write('Categories: ' + ', '.join(data['categories']))
    if st.button('Load example inputs'):
        S.store_text, S.category_text, S.date_text, S.actual_text = '3', 'bakery', '2025-10-15', ''
        st.rerun()

    with st.form('predict_form'):
        model_label = st.selectbox('Fitted model to use', list(options))
        c1, c2, c3, c4 = st.columns(4)
        c1.text_input('Store ID', key='store_text', placeholder='e.g. 3')
        c2.text_input('Product category', key='category_text', placeholder='e.g. Bakery')
        c3.text_input('Date (YYYY-MM-DD)', key='date_text', placeholder='2025-10-15')
        c4.text_input('Actual units (optional, for evaluating this example)', key='actual_text', placeholder='leave blank if unknown')
        submitted = st.form_submit_button('Predict', type='primary')
    if submitted:
        values, errors = inputs.validate_prediction_inputs(
            S.store_text, S.category_text, S.date_text, S.actual_text, data['stores'], data['categories'])
        if errors:
            for message in errors:
                st.error(message)
            return
        stage, name = options[model_label]
        if stage == 'final':
            pipeline, baseline = S.final['final_model'], S.final['final_baseline']
            scores, baseline_scores = S.final['selected_test_metrics'], S.final['baseline_test_metrics']
            settings = S.final['settings']
        else:
            pipeline = S.candidates[name]['model']
            baseline = S.candidates[models.BASELINE_NAME]['model'] if models.BASELINE_NAME in S.candidates else None
            scores = candidate_metrics(S.candidates[name])
            baseline_scores = candidate_metrics(S.candidates[models.BASELINE_NAME]) if baseline is not None else None
            settings = S.candidates[name]['settings']
        row = models.make_prediction_row(values['store_id'], values['category'], values['date'])
        predicted = models.predict_one(pipeline, row)
        baseline_predicted = models.predict_one(baseline, row) if baseline is not None else None
        S.last_prediction = {'stage': stage, 'name': name, 'settings': settings, 'row': row, 'values': values,
                             'predicted': predicted, 'baseline_predicted': baseline_predicted,
                             'scores': scores, 'baseline_scores': baseline_scores}
    if S.last_prediction:
        show_prediction(S.last_prediction, data)


def show_prediction(p, data):
    stage, row, values = p['stage'], p['row'], p['values']
    st.markdown('---')
    st.markdown(f"### Predicted daily sales: **{p['predicted']:.2f} units**")
    if p['predicted'] < 0:
        st.error('The raw prediction is negative, which is not a valid physical sales estimate. It is shown '
                 'unclipped to preserve classroom behavior; treat it as a model limitation.')
    label = FINAL_LABEL if stage == 'final' else EXPERIMENT_LABEL
    fit_kind = 'finalized fit' if stage == 'final' else 'experiment (training-period fit)'
    st.write(f"**Model:** {p['name']} - {fit_kind}. Settings: {p['settings']}")
    st.write(f"**Fitting and evaluation:** {period_text(data, stage)}.")
    st.write(f"**Accepted inputs:** store {values['store_id']}, category \"{values['category']}\" "
             f"(canonical form of what you typed), date {values['date'].date()} -> weekday {row.iloc[0]['weekday']}, "
             f"day of year {row.iloc[0]['day_of_year']}.")
    st.dataframe(row, hide_index=True)

    fit_start = data['train'].date.min()
    fit_end = data['validation_end'] if stage == 'final' else data['train_end']
    eval_start = data['test'].date.min() if stage == 'final' else data['validation'].date.min()
    eval_end = data['test'].date.max() if stage == 'final' else data['validation_end']
    for _, text in inputs.date_notices(values['date'], fit_start, fit_end, eval_start, eval_end,
                                       data['df'].date.min(), data['df'].date.max()):
        st.warning(text)

    st.markdown(f'**{label}**')
    cols = st.columns(2)
    cols[0].table(metric_table(p['scores'], p['name']))
    if p['baseline_scores'] is not None:
        cols[1].table(metric_table(p['baseline_scores'], 'Mean baseline (same period)'))
        st.write(f"Fitted baseline prediction for this example: **{p['baseline_predicted']:.2f} units**.")
    else:
        cols[1].info('Baseline not fitted yet in this session.')
    st.info(HISTORICAL_NOTE + ' Actual sales for this example are not known unless you entered them below.')
    if values.get('actual_units') is not None:
        signed = values['actual_units'] - p['predicted']
        st.write(f"**This example only:** actual {values['actual_units']:.2f} units; signed error (actual - predicted) "
                 f"{signed:+.2f}; absolute error {abs(signed):.2f}. This single observation does not update the "
                 'historical metrics and is not used for training.')


# ---------------------------------------------------------------------------
# E. Final evaluation and managerial interpretation
# ---------------------------------------------------------------------------
def tab_final(data):
    S = st.session_state
    st.subheader('Final evaluation and managerial interpretation')
    if S.final is None and S.candidates:
        recommended = models.select_model(S.candidates)
        st.markdown('**Interpretation so far (validation evidence only)**')
        r = S.candidates[recommended]['result']
        if models.BASELINE_NAME in S.candidates:
            b = S.candidates[models.BASELINE_NAME]['result']['Validation MAE']
            gain_text = (f"{b - r['Validation MAE']:.2f} units ({100 * (1 - r['Validation MAE'] / b):.1f}%) below the "
                         'baseline\'s validation MAE' if b > 0 else 'not defined (baseline MAE is zero)')
        else:
            gain_text = 'not computable until the baseline is fitted'
        st.write(f"The validation-best candidate is **{recommended}** with validation MAE {r['Validation MAE']:.2f} "
                 f'units per store/category/day: {gain_text}. Freeze a selection in "Compare and select" before '
                 'opening the test period.')
    if S.selection is None and S.final is None:
        st.info('Freeze a specification in "Compare and select" first. The default is the validation-best recommendation.')
        return

    if S.selection and (S.final is None or S.final.get('superseded')):
        sel = S.selection
        st.write(f"Frozen specification: **{sel['name']}** ({sel['kind']}); settings: {sel['settings']}.")
        if sel['reason']:
            st.write(f"Recorded reason: {sel['reason']}")
        if S.test_inspected:
            st.warning('Test outcomes were already inspected in this session; this evaluation is additional '
                       'exploration on an inspected test period.')
        if st.button('Finalize selected model and evaluate on test dates', type='primary'):
            with st.spinner(f"Refitting {sel['name']} on training + validation and scoring the test dates..."):
                try:
                    final = models.finalize_model(sel['name'], models.clone(sel['specification']), data)
                except Exception as error:
                    st.error(f'Final refit failed: {type(error).__name__}: {error}')
                    st.code(traceback.format_exc())
                    return
            final.update({'family': sel['family'], 'settings': sel['settings'], 'kind': sel['kind'],
                          'reason': sel['reason'], 'recommended': sel['recommended'],
                          'gain': models.ensemble_gain(S.candidates) if models.is_complete_comparison(S.candidates) else None,
                          'superseded': False})
            S.final = final
            S.test_inspected = True
            log(f"Finalized {sel['name']}: test MAE {final['selected_test_metrics']['MAE']:.3f}")
            st.rerun()

    if S.final is None:
        return
    final = S.final
    if final.get('superseded'):
        st.warning(f"The final result below for {final['selected_name']} is from a configuration that was later "
                   'refitted. It is kept for the record and is not used for new predictions.')
    st.markdown(f"**{FINAL_LABEL}** - {final['selected_name']} ({final['kind']}); settings: {final['settings']}")
    st.caption(period_text(data, 'final'))
    for message in final['warnings']:
        st.warning(f'Final refit warning: {message}')
    st.dataframe(final['test_results'].round(3), hide_index=True, use_container_width=True)
    summary = final['summary'].copy()
    summary['MAE improvement over baseline (%)'] = summary['MAE improvement over baseline (%)'].map(
        lambda v: 'not defined' if pd.isna(v) else f'{v:.3f}')
    st.dataframe(summary.round(3), hide_index=True, use_container_width=True)
    st.caption('Signed error is actual minus predicted: positive means underprediction. '
               'Underprediction frequency is not a stockout rate.')

    c1, c2 = st.columns(2)
    c1.markdown('**Errors by store**')
    c1.dataframe(final['store_diagnostics'].round(2), use_container_width=True)
    c2.markdown('**Categories with the largest absolute errors**')
    c2.dataframe(final['category_diagnostics'].round(2), use_container_width=True)
    st.caption('WAPE = total absolute error / total observed sales; undefined when a segment has zero sales.')

    y_test, test_predictions, diagnostics = data['y_test'], final['test_predictions'], final['diagnostics']
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].scatter(y_test, test_predictions, alpha=0.15, s=12, color='#356DA8')
    low, high = min(y_test.min(), test_predictions.min()), max(y_test.max(), test_predictions.max())
    axes[0].plot([low, high], [low, high], color='#B64B44', linestyle='--')
    axes[0].set(xlabel='Actual units', ylabel='Predicted units', title='Final test: predictions')
    daily = diagnostics.groupby('date')[[models.TARGET, 'predicted_units']].sum()
    daily.plot(ax=axes[1], color=['#356DA8', '#B64B44'])
    axes[1].set(xlabel='Date', ylabel='Units across all stores/categories', title='Daily totals on the test period')
    axes[1].legend(['Actual units', 'Predicted units'])
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown('## Managerial interpretation (test evidence)')
    if final['kind'] == 'student selection':
        st.info(f"This is a student selection; the validation-best recommendation was {final['recommended']}. "
                f"Recorded reason: {final['reason'] or '(none)'}")
    st.markdown(models.managerial_briefing(final, final['family'], final['gain']))
    st.caption('The model forecasts observed sales, not unconstrained demand or an order quantity. MAE is an average '
               'error, not a prediction interval or a safety-stock allowance.')
    with st.expander('Run identity for the finalized model'):
        st.json(models.run_identity(final['selected_name'], final['settings'], data, 'final'))


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
def sidebar(data):
    S = st.session_state
    st.sidebar.markdown(f'**Status:** {stage_name()}')
    st.sidebar.write(f'{len(S.candidates)} of 15 classroom candidates evaluated'
                     + (' (comparison complete)' if models.is_complete_comparison(S.candidates) else ''))
    if S.selection:
        st.sidebar.write(f"Frozen: {S.selection['name']}")
    if S.final is not None:
        st.sidebar.write(f"Finalized: {S.final['selected_name']}" + (' (superseded)' if S.final.get('superseded') else ''))
    if S.test_inspected:
        st.sidebar.warning('Test period already inspected this session.')
    with st.sidebar.expander('Environment and data record'):
        st.json({**models.environment_record(), 'Dataset SHA-256': models.DATA_SHA256,
                 'Features': models.FEATURES, 'Target': models.TARGET,
                 'train_end': str(data['train_end'].date()), 'validation_end': str(data['validation_end'].date())})
    with st.sidebar.expander('Session log'):
        for line in S.log[-30:]:
            st.write(line)
    if st.sidebar.button('Reset fitted models and selections'):
        inspected = S.test_inspected
        for key in ['candidates', 'failed', 'selection', 'final', 'last_prediction', 'log']:
            del S[key]
        init_state()
        S.test_inspected = inspected
        if inspected:
            log('Interface reset. Note: the test period was already inspected in this session; it is not new again.')
        st.rerun()


def main():
    st.set_page_config(page_title=TITLE, layout='wide')
    init_state()
    st.title(TITLE)
    st.markdown('Mancino Market daily unit-sales regression: KNN, regression trees, random forests, neural networks '
                'and averaging ensembles against a mean-sales baseline. **The dataset is synthetic teaching data.**')
    try:
        data = get_data()
    except Exception as error:
        st.error(f'The dataset could not be loaded: {error}')
        st.stop()
    sidebar(data)
    tabs = st.tabs(['A. Explore the dataset', 'B. Choose and run models', 'C. Compare and select',
                    'D. Type inputs and predict', 'E. Final evaluation'])
    with tabs[0]:
        tab_explore(data)
    with tabs[1]:
        tab_models(data)
    with tabs[2]:
        tab_compare(data)
    with tabs[3]:
        tab_predict(data)
    with tabs[4]:
        tab_final(data)


main()
