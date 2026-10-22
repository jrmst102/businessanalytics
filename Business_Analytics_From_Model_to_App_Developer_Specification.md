# Business Analytics in Action: From Model to App

## Developer specification

Version: 1.0  
Prepared: October 21, 2026  
Course owner: Dr. Jose Mendoza, NYU  
Target repository: <https://github.com/jrmst102/businessanalytics>  
Proposed application folder: `apps/from-model-to-app/`

## 1. Purpose and governing requirement

Build a local, browser-based teaching dashboard that turns the Mancino regression exercises into a working application. Students must be able to inspect the dataset, choose the models covered in this session, compare their results, type an observation, and obtain a prediction with clearly identified evaluation metrics.

The classroom model code is the engine. The dashboard and launcher are wrappers. A student opening the engine must recognize the same preprocessing, model constructors, parameter settings, `.fit()`, `.predict()`, and metric calculations used in the attached Colab notebooks.

Do not substitute an alternative implementation merely because it is more elegant, faster, or conventional. Preserve the taught analytical behavior. Explain and document the small adaptations required to move code from notebook cells into functions.

This specification authorizes an implementation plan. It does not claim that the app has already been developed or published. The developer should deliver a reviewable branch or pull request and follow the repository's contribution instructions.

## 2. Learning objectives

Students should be able to:

1. Connect notebook code with a functioning decision-support application.
2. Distinguish data preparation, model fitting, evaluation, and prediction.
3. Compare familiar regression models against a simple baseline.
4. Explain why validation performance guides model selection.
5. Interpret a typed-input prediction without confusing historical error metrics with certainty about that observation.
6. Translate forecast performance into a cautious managerial recommendation.

Learning a dashboard framework is not a prerequisite for understanding the engine. Keep the model code readable without requiring students to understand interface callbacks, caching, deployment, or application architecture.

## 3. Source notebooks and authority

The instructor will attach the classroom notebooks to the developer handoff. Expected sources are:

| Notebook | Role |
|---|---|
| `Mancino_Regression_KNN_Complete.ipynb` | KNN construction, comparison, and explanation |
| `Mancino_Regression_Trees_Complete.ipynb` | Regression-tree construction and interpretation |
| `Mancino_Random_Forests_Complete.ipynb` | Random-forest construction and interpretation |
| `Mancino_Neural_Networks_Complete.ipynb` | Network construction, scaling, and early stopping |
| `Mancino_Ensemble_Complete.ipynb` | Equal and weighted averaging exercises |
| `Mancino_Regression_Final.ipynb` | Integrated preprocessing, candidate grid, ensemble-member selection, final selection, and managerial interpretation |

Treat the attached, instructor-approved versions as authoritative. The parameter inventory below is grounded in the final notebook reviewed for this specification; verify it against the versions actually supplied.

Use the final integrated notebook for the app's default comparison workflow. Use the individual notebooks for explanatory text and the corresponding model sections. The standalone ensemble notebook uses fixed member configurations; the integrated notebook selects the best validation configuration in each family. The app's complete comparison mode must use the integrated notebook's rule and clearly identify its ensemble members.

Create `NOTEBOOK_MAP.md` documenting, for every extracted function:

- Source notebook filename and section or cell ID.
- Destination function in `models.py`.
- Changes made to extract the code.
- Confirmation that analytical behavior is unchanged.
- Any unresolved source discrepancy.

If supplied notebooks conflict in a way that changes predictions or evaluation, record the conflict and resolve it with the instructor before changing the engine. Do not silently blend two versions.

The reviewed final notebook provides this extraction starting point. Confirm cell IDs against the supplied attachment before implementation.

| Final-notebook cell ID | Engine responsibility |
|---|---|
| `final-004` | Dataset loading and validation |
| `final-006` | Feature derivation and chronological partitions |
| `final-009` | Pipelines, metrics, evaluation, and within-family selection |
| `final-011` | Mean-sales baseline |
| `final-013` | KNN presets |
| `final-015` | Regression-tree presets |
| `final-017` | Random-forest presets |
| `final-019` | Neural-network presets and target transformation |
| `final-021` | Family winners and ensemble assembly |
| `final-023` | Full leaderboard and automatic model selection |
| `final-025` | Final refit, test evaluation, and segment diagnostics |
| `final-027` | Result-driven managerial interpretation |

## 4. Scope

### Required in version 1

- One fixed Mancino dataset and the predictors used in class.
- KNN regression, regression trees, random forests, and neural networks.
- Equal-weight and weighted-average regression ensembles using those four families.
- The mean-sales baseline, visibly identified as a benchmark.
- Classroom parameter choices and a full comparison of the predefined candidates.
- Dataset exploration, validation comparison, final evaluation, and typed-input predictions.
- Short, result-driven managerial interpretation.
- A Python launch file that starts the local dashboard.
- A readable engine and notebook-to-code mapping.

### Outside version 1

- Classification, logistic regression, boosting, stacking, support-vector machines, or any additional algorithm not included in the attached regression exercises.
- AutoML, broad parameter searches, or automatic feature engineering.
- New predictors, a different target, or arbitrary uploaded datasets.
- A chatbot, generative-AI explanations, API keys, or paid services.
- Accounts, cloud hosting, databases, LMS integration, or automated inventory ordering.
- A native Windows `.exe` or separate packaged binaries for each operating system.

The random forest is itself an ensemble of trees. The two app choices labeled “Ensemble” refer specifically to averaging across the four classroom model families.

## 5. Application structure and delivery

Use this proposed folder layout, adapting only to established repository conventions:

| Path inside `apps/from-model-to-app/` | Responsibility |
|---|---|
| `models.py` | Classroom engine: features, splits, pipelines, models, metrics, selection, refitting, and prediction |
| `app.py` | Dashboard rendering, forms, input validation, application state, and presentation |
| `launch.py` | Local server startup and browser launch |
| `requirements.txt` | Exact, tested runtime dependencies |
| `README.md` | Student setup, launch instructions, model overview, and troubleshooting |
| `NOTEBOOK_MAP.md` | Traceability from attached notebooks to engine functions |
| `data/mancino_daily_sales.csv` | Approved teaching snapshot for reproducible, offline use after installation |
| `data/SOURCE.md` | Dataset origin, version, retrieval date, license attribution, and snapshot checksum |
| `tests/` | Focused parity, evaluation, input, and application smoke checks |

Store reference notebooks in the repository only if consistent with its conventions; otherwise link to their existing locations. Record the exact reference versions or checksums either way. Do not duplicate unrelated course files.

### Recommended wrapper technology

Use Streamlit for the local browser interface, with scikit-learn, pandas, NumPy, and the existing plotting tools for the engine and charts. Streamlit is an interface dependency, not a replacement for the taught modeling code. Keep its imports and decorators out of `models.py`.

This framework choice is a recommendation for a thin Python wrapper. Pin a tested compatible version during implementation. Do not introduce an additional frontend framework or separate API server for this scope.

### Launch behavior

After the documented first-time dependency installation, students run:

```bash
python launch.py
```

The launcher must:

1. Use the active Python interpreter and resolve `app.py` relative to its own file location.
2. Start the dashboard bound to the local computer, not exposed to the local network by default.
3. Open the dashboard in the default browser, or show a clickable local URL if browser opening fails.
4. Print a clear way to stop the app.
5. Handle a missing dependency or occupied port with a readable instruction.

It must work when launched from a different working directory. Do not require editing file paths, automatically modify the student's environment, install packages on every launch, or assume double-clicking a `.py` file works everywhere.

The README must give tested Windows and macOS setup commands, virtual-environment instructions, and a manual dashboard-launch fallback. A GitHub folder displays and distributes the code; visiting it does not execute a Python application in the browser.

## 6. Engine readability and separation

Keep `models.py` organized in the classroom sequence:

1. Imports and named constants.
2. Load and validate data.
3. Derive predictors and split dates.
4. Build preprocessing pipelines.
5. Compute metrics and fit the baseline.
6. KNN.
7. Regression tree.
8. Random forest.
9. Neural network.
10. Averaging ensembles.
11. Select a model, refit, and predict.

Use descriptive functions and ordinary Python dictionaries or DataFrames. Preserve familiar names such as `X_train`, `y_train`, `X_val`, `y_val`, `make_pipeline`, and `metrics` where practical. Avoid custom estimator hierarchies, metaprogramming, reflection, plugin registries, dependency-injection frameworks, and compressed one-line logic.

Use one clearly labeled constructor or function for each model family. The only necessary generalization should be the small shared preparation and evaluation helpers already present in the notebooks.

Illustrative boundaries, not a required new abstraction framework:

| Suggested engine function | Input | Output |
|---|---|---|
| `load_data` | Approved CSV path | Validated DataFrame |
| `prepare_data` | DataFrame | Derived features and named chronological partitions |
| `make_pipeline` | Classroom estimator and scaling flag | Unfitted pipeline |
| `fit_and_evaluate` | Candidate and training/validation partitions | Fitted candidate, predictions, and metrics |
| `select_model` | Ordered validation results | Selected name and unfitted copy of its specification |
| `finalize_model` | Frozen specification and development/test partitions | Refit model, matched baseline, and test results |
| `make_prediction_row` | Canonical store, category, and date | One-row DataFrame with the classroom feature order |
| `predict_one` | Fitted pipeline and feature row | Numeric predicted units |

Separate UI rendering from numerical returns. Replace notebook-only `display(...)` calls with returned values for `app.py` to display. Do not import Colab upload helpers into the model engine. These are wrapper adaptations, not analytical changes.

Extract the classroom code into readable functions during development. Do not execute whole notebooks at application runtime, invoke a hidden notebook kernel, or duplicate executable model definitions inside `app.py`.

Place a short explanation beside each model's code in the app, using the same constructor and parameter values as the engine. Do not maintain a second executable model implementation solely for display.

## 7. Dataset and feature contract

Source dataset:

<https://github.com/jrmst102/mancino/blob/main/data/v1_2025-11-01/mancino_daily_sales.csv>

The previously verified snapshot contains 22,875 observations, five stores, and 15 categories, covering January 1 through November 1, 2025. Verify those characteristics when packaging the approved snapshot. Do not silently replace the snapshot with a later remote file.

| Field | Engine treatment |
|---|---|
| `date` | Parse as a date; use for splitting and calendar features |
| `store_id` | Convert to string and treat as categorical |
| `category` | Treat as categorical |
| `weekday` | Derive from `date`, rather than trusting a user-entered weekday |
| `day_of_year` | Derive from `date`; the sole numeric predictor |
| `units_sold` | Numeric target; never an input feature |
| `revenue` | Visible in dataset exploration, excluded from predictors |
| `avg_price` | Visible in dataset exploration, excluded from predictors |
| Source `day_of_week` | May be visible; recompute the model's `weekday` from `date` |

Preserve these constants and feature order:

```python
CATEGORICAL = ['store_id', 'category', 'weekday']
NUMERIC = ['day_of_year']
FEATURES = CATEGORICAL + NUMERIC
TARGET = 'units_sold'
SEED = 42
```

Revenue contains outcome information. The observed average price is not established as known before the selling day. Neither may be added as a predictor in this version.

Validate required columns, nonmissing required values, parseable dates, numeric nonnegative targets, and unique `(date, store_id, category)` rows. Preserve the notebook's sort order: date, store, category. Invalid source data must produce an actionable error rather than silent imputation or row deletion.

Prefer the bundled approved CSV at runtime. A developer may download the approved source during packaging, recording attribution and checksum. The teaching app must not require GitHub credentials or a network request every time it launches.

## 8. Reproduce the classroom evaluation process

Split by ordered unique dates, using the notebook's exact boundary calculation:

```python
dates = np.sort(df['date'].unique())
train_end = dates[int(len(dates) * 0.60) - 1]
validation_end = dates[int(len(dates) * 0.80) - 1]
```

Training includes dates through `train_end`. Validation includes later dates through `validation_end`. Test includes all remaining dates. Never randomly split rows or place observations from the same date into different sets.

Expected partitions for the verified snapshot:

| Partition | Dates | Rows |
|---|---|---:|
| Training | January 1–July 2, 2025 | 13,725 |
| Validation | July 3–September 1, 2025 | 4,575 |
| Test | September 2–November 1, 2025 | 4,575 |

Fit encoders, feature scalers, and target scalers only through the candidate's training pipeline. Preserve `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`. The input wrapper must still reject unsupported stores and categories for the typed-prediction exercise.

Use `StandardScaler` for day of year in KNN and neural-network pipelines. Use numeric passthrough for tree and forest pipelines, following the integrated final notebook. Do not standardize indicator columns or change categorical encoding.

Preserve the neural network's `TransformedTargetRegressor` with `StandardScaler` for the target. Its predictions must be returned to unit-sales scale before evaluation or averaging.

## 9. Model inventory and allowed settings

Expose only the choices taught in class. The main student controls should select the listed presets; additional model parameters remain fixed and are explained in a “Classroom settings” panel.

| Choice | Classroom implementation | Student preset choices | Fixed settings from the integrated notebook |
|---|---|---|---|
| Mean-sales baseline | `DummyRegressor` | None | `strategy='mean'` |
| KNN regression | `KNeighborsRegressor` | `n_neighbors`: 5, 15, 50 | `weights='uniform'`, `n_jobs=-1`; numeric scaling enabled |
| Regression tree | `DecisionTreeRegressor` | `max_depth`: 3, 6, 12 | `min_samples_leaf=30`, `random_state=42`; numeric passthrough |
| Random forest | `RandomForestRegressor` | `n_estimators`: 50, 100, 200 | `max_depth=12`, `min_samples_leaf=30`, `max_features=0.8`, `bootstrap=True`, `random_state=42`, `n_jobs=-1` |
| Neural network | `MLPRegressor` inside `TransformedTargetRegressor` | Hidden layers: `(16,)`, `(32,)`, `(32, 16)` | ReLU, Adam, `alpha=0.01`, `batch_size=256`, `learning_rate_init=0.001`, `max_iter=300`, `early_stopping=True`, `validation_fraction=0.15`, `n_iter_no_change=20`, `random_state=42` |
| Equal-weight ensemble | `VotingRegressor` | Equal averaging | Four family winners; `n_jobs=1` |
| Weighted ensemble | `VotingRegressor` | Classroom weights `[1, 1, 2, 2]` | Same family winners, fixed member order; `n_jobs=1` |

Preserve omitted scikit-learn defaults through the pinned environment; do not replace them with “better” settings. For example, do not change KNN weighting, random-forest feature sampling, or neural-network early stopping.

The full comparison contains 15 candidates: one baseline, three KNNs, three trees, three forests, three networks, and two ensembles. Offer a “Run classroom comparison” action that evaluates that exact set.

An individual-model action may train only the selected preset and its baseline. Ensemble actions require the four family winners, so explain that the necessary individual comparisons will run first if not already available. Never assemble an ensemble from whichever models happen to be cached.

Keep the weighted preset fixed in version 1. A later editable-weights exercise would need explicit scope approval and the same validation-only selection discipline.

### Ensemble assembly

1. Choose the lowest validation MAE within each of the four individual families.
2. Preserve member order: KNN, regression tree, random forest, neural network.
3. Clone the selected specifications into `VotingRegressor`; it refits its members on the candidate training data.
4. Equal-weight prediction is the arithmetic average of four predictions.
5. Weighted prediction is their weighted average with weights `[1, 1, 2, 2]`, normalized by their sum.
6. Do not include the baseline as a member.

Display the member names, settings, and normalized weights. Explain that the weighted preset is illustrative, not optimized or guaranteed to improve accuracy.

## 10. Dashboard experience

Use the exact title “Business Analytics in Action: From Model to App.” Include a short subtitle identifying Mancino Market and daily unit-sales regression. Show a visible note that the dataset is synthetic.

Use five clearly labeled areas. They may be tabs or a simple navigation menu.

### A. Explore the dataset

- Display the source, row count, stores, categories, date range, and variable definitions.
- Show a searchable or filterable data table.
- Provide store, category, and date filters for viewing only.
- Show a compact sales distribution and sales-over-time chart.
- Identify the target and the excluded predictors.
- Display the fixed training, validation, and test boundaries.

Exploration filters must not change model training, validation metrics, or selection. Label them “View filters.” Do not turn this into an arbitrary data-subsetting exercise.

The full source dataset may be inspected, as requested. Explain that the holdout protects the computational evaluation workflow; the app does not claim that test labels are secret from a student viewing the raw CSV.

### B. Choose and run models

- Present the six learned approaches separately from the baseline benchmark.
- Show only the applicable classroom preset control for the selected family.
- Include a short explanation of how that model predicts.
- Use an explicit “Train and evaluate” submission action.
- Provide a separate “Run classroom comparison” action.
- Show progress while fitting and a readable status when complete.
- Make the selected model's engine code available in an expandable “Code from class” panel.

Training must not occur automatically on every keystroke, tab switch, or visualization filter change. Capture convergence warnings and show them beside the affected network result. Do not report a failed candidate as successfully evaluated.

### C. Compare and select

The validation leaderboard must include candidate name, model family, classroom settings, training MAE, validation MAE, validation RMSE, validation R², fitting time, and MAE improvement over the training-fitted baseline.

Use the notebook formula for improvement: `100 * (1 - candidate_mae / baseline_mae)`. If baseline MAE is zero, show “not defined” rather than divide by zero.

Sort by validation MAE, keeping full numeric precision for sorting. Round only display values. Use a readable training-versus-validation MAE chart. Explain metric units and that R² is not classification accuracy.

Students must be able to inspect any fitted candidate and compare it with the baseline. For the full classroom run, recommend the lowest validation MAE across all 15 candidates, with ties resolved by the notebook's insertion order: baseline first, then listed presets and ensembles. Do not select by rounded scores, test scores, or fitting time.

Before final evaluation, allow the student to choose a different completed candidate for a documented managerial reason. Label this a student selection, retain the validation-best recommendation, and record the reason. Freeze the chosen specification before accessing test outcomes. The default is the validation-best recommendation.

### D. Type inputs and predict

Provide actual text-entry fields for store ID, product category, and date. Do not replace the requested typed-input exercise with dropdowns alone. A nearby reference list may show valid stores and categories, and a “Load example inputs” button may populate the text fields.

On submission, validate the entries, construct the four classroom features, and call the selected fitted pipeline's `.predict()`. Display predicted units, the canonical accepted inputs, the model/configuration, the fitting period, and the matching evaluation metrics.

Prediction does not retrain the model, recompute the leaderboard, or alter the dataset. Detailed requirements appear in section 12.

### E. Final evaluation and managerial interpretation

Use an explicit “Finalize selected model and evaluate on test dates” action. Refit a cloned selected specification on training plus validation data, then score it on the fixed test period. Refit the mean-sales baseline on the same combined period for a fair comparison.

Display the chosen model's test MAE, RMSE, and R² beside the matched baseline; show mean signed error, underprediction frequency, and store/category diagnostics. Provide an actual-versus-predicted chart and short interpretation tied to the computed numbers.

Keep this final model available for typed-input predictions, clearly distinguished from training-period experiment models.

## 11. Fitted-model and evaluation states

The wrapper must prevent stale results and misleading metric labels. A small session-state dictionary is sufficient; do not build a separate workflow framework.

| State | Permitted behavior | Metric label |
|---|---|---|
| Not trained | Explore data and choose settings; prediction unavailable | No performance result yet |
| Candidate evaluated | Predict using the training-period model and compare validation results | “Validation performance: model fitted on training dates” |
| Selected for final evaluation | Frozen specification and recorded selection reason | Validation evidence remains visible |
| Finalized | Predict with the training-plus-validation refit | “Test performance: model refitted on development dates” |
| Inputs/settings changed | Preserve historical run if useful, but mark it as a different configuration; require retraining for new settings | Never relabel an old score as the new run |

Retain the exact fitted model used to produce each set of scores. Do not show a finalized model's test metrics beside a prediction produced by an earlier training-only model, or label the earlier validation score as an evaluation of the refit.

Changing a model preset must invalidate dependent ensemble results and any currently finalized selection derived from it. Do not silently recompute or overwrite final test results. An input-only prediction form change does not invalidate the fit.

Once final test outcomes are exposed, label subsequent tuning as additional exploration on an already inspected test period. Resetting UI controls must not claim that the same period has become unseen again. This is a teaching boundary, not an access-control system.

## 12. Typed-input prediction contract

### Input fields

| Field | Accepted input and behavior |
|---|---|
| Store ID | Text matching an approved dataset store after whitespace trimming; canonical stored value is a string |
| Product category | Typed category name; trim whitespace and allow case-insensitive matching only when it maps uniquely to one canonical category |
| Date | Valid ISO date, `YYYY-MM-DD`; derive weekday and day of year in Python |
| Actual units, optional | A separate, explicitly labeled field for evaluating this example after prediction; finite and nonnegative |

Explain that “type any data” means students can enter their own valid observation within this fixed feature schema. It does not mean arbitrary columns, a new target, or unsupported stores/categories.

Validation requirements:

- Reject missing required values and malformed dates before calling `.predict()`.
- Reject unknown stores/categories even though the preserved encoder supports ignored unknowns. Show valid examples.
- Do not silently fuzzy-match an ambiguous entry.
- Show the canonical category after normalization.
- Derive `weekday` and `day_of_year`; do not ask the user to supply contradictory calendar fields.
- Construct a one-row DataFrame in exactly `FEATURES` order.
- Treat submitted text as data. Never evaluate it as Python or interpolate it into a shell command.

Dates outside the observed range may produce an educational prediction, but must carry a visible extrapolation notice. If the year differs from the dataset year, explain that year is not a predictor: the model uses weekday and day of year and has not demonstrated generalization to that new year. Do not attach a claim of validated accuracy for an unseen forecast horizon.

For a date inside the model's fitting period, label the example as historical and potentially in-sample. A typed example is not automatically an independent test observation.

### Required prediction result

Display:

1. Expected daily units for the entered store/category/date, formatted to two decimals.
2. The model name, settings, and whether it is an experiment or finalized fit.
3. A summary of the accepted inputs and derived weekday/day of year.
4. The model's matching validation or test MAE, RMSE, and R², with evaluation dates and sample count.
5. The fitted baseline's prediction and the matching baseline evaluation, when available.
6. A short note: “These metrics summarize historical evaluation observations. They do not measure the accuracy of this new prediction.”

Example presentation, using placeholder numbers rather than hard-coded results:

> Predicted daily sales: 38.40 units. The selected model's validation MAE was 8.10 units per store/category/day. Actual sales for this example are not yet known.

Do not display classification accuracy, confidence percentages, a probability of correctness, or an invented prediction interval. MAE must not be rendered as `prediction ± MAE` and presented as a confidence range.

Preserve raw numerical predictions for calculations; round only for display. If a neural-network prediction is negative, flag it as an invalid physical sales estimate rather than silently clipping it and changing classroom behavior.

If optional actual units are supplied, report signed error as `actual - predicted` and absolute error for that observation. Do not calculate R² from a single observation, update historical evaluation metrics, or feed the example into training. Do not use the actual-value field as a predictor.

## 13. Managerial interpretation

Use deterministic templates populated from actual engine results, following the final notebook. Do not require a language-model service.

The interpretation must address:

- Whether the evaluated model beats its matched baseline and by how much in MAE units and percent.
- Whether an ensemble's validation gain over the best individual model is large enough to merit further consideration of its maintenance burden. Do not invent a significance claim or automatically substitute a model after seeing test scores.
- The meaning of MAE, RMSE, and signed error in unit-sales terms.
- Which stores/categories warrant review, alongside segment sample counts, mean sales, and WAPE where available.
- The distinction between observed sales, unconstrained demand, and an inventory order quantity.
- A proposed shadow pilot and the additional information needed: stockouts, inventory, lead times, planned prices/promotions, and operating costs.

Preserve the notebook's signed-error convention: positive means underprediction. Underprediction frequency is not a stockout rate. Higher absolute category error alone does not establish worse proportional performance. Handle zero sales in WAPE denominators as undefined.

Before finalization, label interpretation as based on validation evidence. After finalization, identify the test evidence explicitly. Do not promise profit improvement, cost savings, causal price effects, optimal orders, or operational readiness from forecast metrics alone.

Include one short student prompt asking for a model recommendation, numerical justification, an operational limitation, and one additional data requirement.

## 14. Reproducibility and model identity

Record the approved dataset checksum, notebook source versions, Python version, library versions, seed, candidate parameters, feature order, split boundaries, fitting period, and evaluation period for each run.

The earlier verification environment used Python 3.12.14, scikit-learn 1.8.0, NumPy 2.3.5, and pandas 2.2.3. These are reference values, not permission to assume every supplied notebook used that environment. Execute the supplied notebooks, record their actual environment, and pin the app to the verified compatible versions. Do not silently upgrade the engine while building the wrapper.

Prefer training the small classroom models locally, retaining fitted objects in the session. Loading arbitrary uploaded serialized models is outside scope. Avoid committing machine-specific cached models. If trusted model caching is later added, validate its data, parameter, and dependency versions before reuse.

A run identity must distinguish dataset version, full parameters, seed, preprocessing, partitions, and fit stage. The implementation can use a small dictionary plus a stable key; students need a readable summary, not a hashing framework.

## 15. Performance, usability, and failure behavior

- Keep training behind explicit form submissions. Typing inputs must not retrain.
- Preserve completed runs across normal dashboard rerenders within a session.
- Keep mutable fitted models isolated to the user's session. Do not mutate a globally shared cached estimator when changing settings.
- It is acceptable to reuse unchanged data and identical completed candidate runs. A cache must not conceal changed settings or stale metrics.
- Avoid nested parallel training of all forests/ensembles at once. Preserve the notebook's estimators and run the comparison in a controlled sequence.
- Target a warm single-row prediction within two seconds and the full predefined comparison within two minutes on the developer's documented reference laptop. Report measured timings; these are usability targets, not analytical acceptance thresholds.
- Use readable tables, axis labels, metric units, and keyboard-accessible forms. Do not encode model status only through color.
- Show missing data/dependency errors, invalid inputs, training failures, and convergence warnings in plain language. Keep technical detail available in the console or an expandable panel.
- If a candidate fails, mark its result failed and exclude it from selection. The complete classroom run remains incomplete until all predefined candidates succeed or the instructor explicitly accepts a documented exception.

## 16. Verification and acceptance criteria

### A. Notebook parity: required release gate

Execute the attached reference notebooks and the engine using the same approved dataset and pinned environment. Compare numerical outputs rather than merely checking constructor names.

| Check | Passing condition |
|---|---|
| Data preparation | Identical row order, target values, canonical categories, feature names/order, and date partitions |
| Preprocessing | Same encoded columns, scaling behavior, and training-only fitting |
| Individual models | All 12 classroom presets reproduce the corresponding reference predictions and MAE/RMSE/R² |
| Ensembles | Same validation-selected family members, order, weights, and predictions as the final integrated notebook |
| Selection | Same full-precision validation winner and tie behavior |
| Final refit | Same development-set refitting process and selected-model/baseline test predictions |
| Typed example | Dashboard prediction equals direct `.predict()` on the same fitted pipeline and constructed row |

Use `numpy.testing.assert_allclose` with an initial tolerance such as `rtol=1e-7, atol=1e-7` in the same environment. If a platform-dependent numerical difference exceeds this, investigate and document it; do not widen tolerance until a discrepancy disappears without explanation. Exclude wall-clock fitting time from numerical parity comparisons.

Verify ensemble arithmetic independently on several rows: the predicted value must equal the mean or normalized weighted mean of that fitted ensemble's member predictions.

### B. Evaluation and state checks

1. Every model uses identical chronological partitions; no date crosses partitions.
2. Test outcomes are not used for fitting, setting choices, member selection, or the validation recommendation.
3. Finalization freezes the chosen specification before scoring the test period.
4. Changing a preset cannot leave earlier predictions/metrics labeled as the new setting.
5. Changing a member invalidates dependent ensembles.
6. Prediction-form submissions and exploration filters do not change trained models or comparison scores.
7. Experiment-model predictions carry validation-fit provenance; finalized-model predictions carry final-fit provenance.
8. Resetting the interface does not claim a previously inspected test period is new.

### C. Input and presentation checks

- A valid typed store/category/date produces a finite prediction matching the engine.
- Empty, malformed, unknown, and ambiguous inputs receive useful messages.
- Supported category case/whitespace normalization is visible and deterministic.
- Dates outside the evaluation range and in a different year receive the specified notices.
- Historical in-sample examples are labeled correctly.
- The optional actual value produces only that observation's signed and absolute error.
- A negative prediction, zero baseline MAE, or zero WAPE denominator is handled without misleading arithmetic.
- Metric labels, units, and stage remain correct on every screen.

### D. Student-launch checks

Test fresh setup and launch on Windows and macOS. Record tested versions. Confirm browser opening or URL fallback, launch from another working directory, offline use after installation, and readable dependency/port failures.

### E. Pedagogical review

The instructor must be able to follow one input from the form through feature construction, the classroom model's `.predict()`, and the displayed result. `models.py` must be understandable independently of Streamlit. The notebook map must identify all adaptations, with no unexplained alternate model engine.

## 17. Developer handoff deliverables

Deliver:

1. A proposed repository folder or pull request containing the app, launcher, readable engine, dependencies, approved data snapshot, and attribution.
2. Student-facing README with tested setup/launch instructions and troubleshooting.
3. Completed notebook-to-engine mapping.
4. Verification evidence covering model parity, ensemble arithmetic, evaluation state, typed inputs, and launch checks.
5. A short walkthrough showing dataset exploration, one individual model, the full comparison, final selection, and a typed prediction.
6. A list of any source conflicts, changes needing instructor judgment, or acceptance items not yet verified.

Suggested implementation sequence: first reproduce notebook outputs in `models.py`; next add the dashboard; then add the launcher and student documentation; finally run parity and usability checks. Keep the engine reviewable before investing in interface polish.

The defining acceptance condition is: students can recognize the classroom code as the application's engine, and the dashboard produces the same analytical results with clear input and metric interpretation.

## 18. Implementation reference links

These references support wrapper and reproducibility decisions; the attached notebooks remain the authority for model behavior.

- Streamlit command-line launch: <https://docs.streamlit.io/develop/api-reference/cli/run>
- Streamlit session state and rerun behavior: <https://docs.streamlit.io/develop/concepts/architecture/session-state>
- scikit-learn model persistence and environment compatibility: <https://scikit-learn.org/stable/model_persistence.html>
- Course repository: <https://github.com/jrmst102/businessanalytics>
- Mancino source dataset: <https://github.com/jrmst102/mancino/blob/main/data/v1_2025-11-01/mancino_daily_sales.csv>

These links are background documentation, not an instruction to change classroom dependencies to the latest release.
