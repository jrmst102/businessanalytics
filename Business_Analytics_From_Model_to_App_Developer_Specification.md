# Business Analytics in Action: From Model to App

## Developer specification

Version: 2.0  
Updated: October 22, 2026  
Course owner: Dr. Jose Mendoza, NYU  
Target repository: <https://github.com/jrmst102/businessanalytics>  
Proposed application folder: `apps/from-model-to-app/`

## 1. Product objective and revision

Build a simple local dashboard that lets students explore the Mancino dataset, choose one classroom regression model with its parameters, train it, and type inputs to obtain a prediction.

This version supersedes the broader version 1.0 specification. The dashboard must have exactly three tabs, in this order:

1. Data
2. Model
3. Test

Only the currently selected model's results are shown. Remove the earlier baseline comparisons, candidate leaderboards, automatic winner selection, comparison charts, full classroom comparison action, and separate managerial evaluation area. A short explanation of the selected model's results is sufficient.

Show four model-performance metrics: R², MSE, RMSE, and MAPE. Do not add MAE or other metric cards to the student interface in this version. Existing classroom MAE calculations may remain in reference notebooks; they do not drive an app ranking or benchmark comparison.

Display this exact footer on all three tabs:

> Business Analytics and Data Visualization Fall 2026 - Prof. Jose Mendoza

This document specifies the developer handoff. It does not claim the application is already implemented or published.

## 2. Preserve the classroom engine

The model code is the engine. The interface and launcher are wrappers. Students must recognize the same preprocessing, constructors, parameter settings, `.fit()`, and `.predict()` used in class.

Preserve:

- The Mancino dataset, target, predictor definitions, and feature order.
- The categorical encoding and model-specific scaling.
- The classroom model constructors and listed parameter presets.
- Neural-network target transformation and early stopping.
- Ensemble averaging, member order, and classroom weights.
- The chronological data boundaries and the final notebook's development-set refit.

The instructor has authorized adding MSE and MAPE to the reported metrics and simplifying the interaction. Document these metric additions and the manual selection workflow as app adaptations. They must not change model predictions.

Use plain functions, descriptive names, short comments, and ordinary dictionaries or DataFrames. Keep familiar names such as `X_train`, `y_train`, `X_val`, `y_val`, and `FEATURES` where practical. Avoid custom estimator hierarchies, hidden AutoML, reflection, and elaborate application frameworks in the engine.

Keep all Streamlit imports, state handling, forms, layout, and caching in the wrapper. Extract code into readable functions during development; do not run entire notebooks or a hidden notebook kernel at application runtime.

## 3. Notebook sources and mapping

The instructor will supply the approved Colab notebooks:

| Notebook | Implementation source |
|---|---|
| `Mancino_Regression_KNN_Complete.ipynb` | KNN model and explanation |
| `Mancino_Regression_Trees_Complete.ipynb` | Regression-tree model and explanation |
| `Mancino_Random_Forests_Complete.ipynb` | Random-forest model and explanation |
| `Mancino_Neural_Networks_Complete.ipynb` | Network construction, scaling, and early stopping |
| `Mancino_Ensemble_Complete.ipynb` | Fixed member configurations and equal/weighted averaging |
| `Mancino_Regression_Final.ipynb` | Shared feature preparation, date splits, and final development-set refit |

The supplied approved versions are authoritative. Verify the parameter inventory in this specification against those versions. If a discrepancy changes predictions, document it and obtain instructor direction before changing the analytical implementation.

Use the final notebook's preprocessing: numeric scaling for KNN and neural networks; numeric passthrough for trees and forests.

Use the standalone ensemble notebook's fixed member configurations for this simplified app. Do not use the final notebook's validation-winner search to assemble the app's ensemble. This choice removes cross-model searching while preserving a classroom ensemble implementation.

Create `NOTEBOOK_MAP.md` with each engine function's source notebook, section/cell, destination function, and extraction changes. Explicitly identify:

1. Manual student choice replacing automatic model selection.
2. Fixed classroom ensemble members replacing family-winner searching.
3. MSE and MAPE reporting.
4. Display and input handling moved to the wrapper.

## 4. Scope and layout

### Required

- Exactly three tabs: Data, Model, Test.
- A fixed, approved Mancino data snapshot.
- One active model and parameter configuration at a time.
- Classroom model choices and limited classroom parameter presets.
- One explicit training action.
- Four performance metrics for that selected model.
- Typed-input predictions using the same fitted model.
- The exact course footer.
- A readable Python engine and a local launch file.

### Excluded

- Baseline/benchmark training or display.
- Cross-model score tables, rankings, comparison charts, saved score histories, or recommended winners.
- Automatic hyperparameter or model searches, including hidden searches for ensemble members.
- Additional algorithms, new predictors, arbitrary uploaded datasets, or different targets.
- Additional tabs, advanced-mode panels, separate evaluation workflows, or a managerial briefing generator.
- Cloud accounts, databases, API keys, language-model services, paid services, or automated inventory ordering.
- Platform-specific native application binaries.

When another model is selected, its results replace the current display after training. Do not accumulate a comparison table in the background and expose it through another screen.

## 5. Project structure and launch

Use the proposed folder `apps/from-model-to-app/`, adapting to repository conventions where necessary.

| File/path | Purpose |
|---|---|
| `models.py` | Classroom model constructors, preprocessing, fitting, metrics, and prediction |
| `app.py` | Three-tab dashboard, forms, validation, state, and footer |
| `launch.py` | Start the local dashboard and open the browser |
| `requirements.txt` | Pinned, tested runtime dependencies |
| `README.md` | Student setup, launch instructions, model overview, and troubleshooting |
| `NOTEBOOK_MAP.md` | Source traceability and documented adaptations |
| `data/mancino_daily_sales.csv` | Approved data snapshot |
| `data/SOURCE.md` | Dataset source, version, attribution, retrieval date, and checksum |
| `tests/` | Focused model-parity, metric, input, and application checks |

Use a thin Streamlit interface with the existing pandas, NumPy, scikit-learn, and plotting dependencies. Do not require a separate frontend or API service.

After documented first-time setup, students run:

~~~bash
python launch.py
~~~

The launcher must resolve paths relative to itself, use the active Python interpreter, bind the server locally, and open the default browser. Show a local URL if automatic browser opening fails. Provide readable dependency/port errors and a clear stopping instruction.

Do not install dependencies on every launch or assume a Python file can be double-clicked on every computer. Document tested Windows and macOS setup commands and a manual launch fallback. The approved CSV must work offline after dependency installation.

A GitHub folder distributes the application; opening the folder on GitHub does not run the dashboard.

## 6. Data tab

### Content

Keep this tab concise:

- A short dataset introduction identifying Mancino as a synthetic grocery retailer.
- A searchable or filterable data table.
- Compact dataset facts: observations, stores, categories, and date range.
- A small variable dictionary identifying the prediction target and model inputs.

One simple sales-over-time chart is sufficient. Do not add a collection of charts or advanced exploration controls.

Any table filters are viewing controls only. Label them accordingly and never use them to change model fitting or evaluation data.

### Dataset contract

Source:

<https://github.com/jrmst102/mancino/blob/main/data/v1_2025-11-01/mancino_daily_sales.csv>

The verified snapshot contains 22,875 observations, five stores, and 15 categories, from January 1 through November 1, 2025. Confirm these characteristics when packaging the approved snapshot. Do not silently refresh the data from a changing remote file.

| Field | Treatment |
|---|---|
| `date` | Parse as a date; derive calendar features and establish splits |
| `store_id` | Convert to string; categorical predictor |
| `category` | Categorical predictor |
| `weekday` | Derive from `date`; categorical predictor |
| `day_of_year` | Derive from `date`; numeric predictor |
| `units_sold` | Numeric prediction target |
| `revenue` | May be visible in the dataset; excluded from model inputs |
| `avg_price` | May be visible in the dataset; excluded from model inputs |
| Source `day_of_week` | May be visible; recompute the model's weekday from the date |

Keep the classroom constants and feature order:

~~~python
CATEGORICAL = ['store_id', 'category', 'weekday']
NUMERIC = ['day_of_year']
FEATURES = CATEGORICAL + NUMERIC
TARGET = 'units_sold'
SEED = 42
~~~

Revenue contains outcome information. Observed average price has not been established as known before the selling day. Neither is a predictor in this app.

Validate required columns and values, date parsing, numeric nonnegative targets, and uniqueness of `(date, store_id, category)`. Sort by date, store, and category as in the notebook. Do not silently impute, drop rows, or add new features.

## 7. Model tab

### Student interaction

Display:

1. A single model selector.
2. Only the parameter control relevant to that model.
3. A short explanation of how the model predicts.
4. One primary button: “Train model.”
5. Four result cards after a successful fit: R², MSE, RMSE, MAPE.
6. A short interpretation of these results, with the evaluation period and observation count.

Use these five top-level model choices:

- KNN regression
- Regression tree
- Random forest
- Neural network
- Ensemble regression

Ensemble regression has one averaging-method parameter: Equal weights or Weighted average. It remains one selected model, even though fitting it necessarily fits its four constituent estimators.

Do not include a baseline option, multi-select model control, “run all” action, winner selection, or cross-model comparisons.

The model selector may default to KNN, but no result is shown until “Train model” is clicked. Changing a model or parameter clears the displayed fit, metrics, and previous prediction, and makes prediction unavailable until the new configuration is trained.

### Classroom parameter controls

| Model | Visible parameter | Allowed values | Default |
|---|---|---|---|
| KNN regression | Number of neighbors | 5, 15, 50 | 15 |
| Regression tree | Maximum depth | 3, 6, 12 | 6 |
| Random forest | Number of trees | 50, 100, 200 | 100 |
| Neural network | Hidden-layer architecture | One layer: 16; one layer: 32; two layers: 32 and 16 | Two layers: 32 and 16 |
| Ensemble regression | Averaging method | Equal weights; Weighted average | Equal weights |

Fixed settings:

| Model | Settings to preserve |
|---|---|
| KNN | `weights='uniform'`, `n_jobs=-1`; standardize day of year |
| Regression tree | `min_samples_leaf=30`, `random_state=42`; numeric passthrough |
| Random forest | `max_depth=12`, `min_samples_leaf=30`, `max_features=0.8`, `bootstrap=True`, `random_state=42`, `n_jobs=-1`; numeric passthrough |
| Neural network | ReLU, Adam, `alpha=0.01`, `batch_size=256`, `learning_rate_init=0.001`, `max_iter=300`, `early_stopping=True`, `validation_fraction=0.15`, `n_iter_no_change=20`, `random_state=42`; input and target scaling |
| Ensemble | Classroom `VotingRegressor`, fixed members below, `n_jobs=1` |

Preserve unspecified scikit-learn defaults through the verified pinned environment. Do not add controls for other parameters.

One collapsed “Code from class” area may show the current constructor and relevant preprocessing. It must come from the actual engine implementation or an accurately maintained source excerpt, not a second executable implementation. Keep dependency versions and implementation diagnostics out of the main student flow.

### Fixed ensemble members

Use the fixed configurations in `Mancino_Ensemble_Complete.ipynb`:

| Member order | Member | Fixed configuration |
|---|---|---|
| 1 | KNN | 50 neighbors, uniform weights, numeric scaling |
| 2 | Regression tree | Maximum depth 12, minimum leaf size 30 |
| 3 | Random forest | 100 trees, maximum depth 12, minimum leaf size 30, `max_features=0.8` |
| 4 | Neural network | One hidden layer with 16 neurons; the classroom network settings and target transformation |

Equal weights give each member one-quarter. Weighted averaging uses `[1, 1, 2, 2]` in the order above, normalized by the sum. Present the member settings in a compact explanatory note; do not show their individual scores or predictions alongside the ensemble result.

Do not search for the best member configurations, optimize weights, fit unrelated candidates, or use whichever models were previously cached. The selected ensemble's performance is the sole displayed model performance.

## 8. Fitting and evaluation behind the simple interface

Retain the notebook's ordered unique-date split:

~~~python
dates = np.sort(df['date'].unique())
train_end = dates[int(len(dates) * 0.60) - 1]
validation_end = dates[int(len(dates) * 0.80) - 1]
~~~

For the approved snapshot:

| Partition | Dates | Rows |
|---|---|---:|
| Training | January 1–July 2, 2025 | 13,725 |
| Validation | July 3–September 1, 2025 | 4,575 |
| Test | September 2–November 1, 2025 | 4,575 |

The student manually chooses one configuration. No app procedure searches configurations or chooses a winner. Therefore, “Train model” performs the final notebook's refit directly for that chosen specification:

1. Preserve the named chronological partitions.
2. Combine training and validation as the development set.
3. Clone/build only the chosen model specification.
4. Fit its pipeline on development data, with 18,300 rows in the approved snapshot.
5. Predict the 4,575 held-out test observations.
6. Calculate the four requested metrics from those test predictions.
7. Retain that exact fitted pipeline for the Test tab.

Do not perform a hidden 15-candidate run or train a benchmark. A selected ensemble fits only its fixed constituent pipelines.

This workflow uses the same final refit taught in class, with manual model choice replacing automatic validation-based selection. Document this adaptation in the notebook map. There is no separately displayed training/validation metric series or extra finalization button.

Preserve `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`. Fit preprocessing within the selected development-set pipeline; do not fit it on held-out test data.

Use `StandardScaler` for KNN/network numeric inputs and passthrough for tree/forest numeric inputs. Preserve the network's `TransformedTargetRegressor(..., transformer=StandardScaler())` so predictions are returned to original sales units before metrics or averaging.

For neural networks, the internal random early-stopping holdout comes only from development data. It does not use the chronological test period.

Below the metrics, show a concise note:

> Historical test performance for this configuration. Repeated parameter changes are classroom exploration on the same test period, not new independent tests.

Never use observed test performance to update weights or automatically select another model. The app allows deliberate student exploration and accurately labels the repeated use of the historical holdout.

## 9. Required metrics and definitions

Show exactly these four metric cards for the selected fitted model:

| Metric | Definition | Display and interpretation |
|---|---|---|
| R² | `r2_score(actual, predicted)` | Dimensionless, three decimals; can be negative; not percentage accuracy |
| MSE | `mean_squared_error(actual, predicted)` | Squared units, two decimals; smaller is better |
| RMSE | `np.sqrt(MSE)` | Units per store/category/day, two decimals; larger misses receive more weight |
| MAPE | Mean absolute percentage error on observations with positive actual sales | Percentage, two decimals; smaller is better |

All metrics use raw, unrounded predictions on the same selected model's held-out test observations. MAPE may use fewer observations only for the explicitly documented zero-sales policy below. Predictions and errors must be in original unit-sales scale, not standardized target scale.

### MAPE zero-sales policy

For this nonnegative sales target:

- For rows with `actual > 0`, calculate `abs((actual - predicted) / actual)`.
- MAPE is the mean of those values multiplied by 100.
- Exclude rows with zero actual sales from MAPE only, and disclose their count.
- If no positive-actual rows remain, display “MAPE: N/A — no positive actual sales.”
- Continue calculating MSE, RMSE, and R² over all valid held-out observations.
- Do not silently divide by an arbitrary epsilon or display an enormous finite percentage as if it were an ordinary MAPE.

This is a documented MAPE reporting policy, not a change to fitted predictions. The current snapshot previously contained positive sales throughout; the policy still needs a meaningful edge-case check.

If R² cannot be defined, show N/A with a short explanation. Do not silently present a substituted 0 or 1 as an ordinary score. This may be implemented through an explicit constant-target check or `r2_score(..., force_finite=False)` with nonfinite-result handling.

MAPE can exceed 100%, and low-volume observations can disproportionately affect it. Do not relabel it as “accuracy,” calculate `100 - MAPE` as accuracy, or use it to promise accuracy for a new observation.

### Minimal result interpretation

Use short deterministic text such as:

> This model's RMSE is [value] units per store/category/day on the held-out dates. Its MAPE is [value]% across [count] positive-sales observations.

Follow with: “These are historical evaluation results, not a prediction interval or a guarantee for one new forecast.”

The numerical values must be computed. No hard-coded classroom scores, benchmark differences, or generative-AI explanation service.

## 10. Test tab

“Test” is the student-facing name for trying a typed observation. Explain briefly that the four performance metrics were computed on historical held-out rows, while the new input produces one forecast.

### Before training

Display: “Train a model in the Model tab before making a prediction.” Do not offer another model selector or silently fit a default model from this tab.

### Inputs

Provide text-entry fields, with a compact valid-values reference:

| Input | Rule |
|---|---|
| Store ID | Required; trim whitespace; match an existing dataset store; use canonical string ID |
| Product category | Required; trim whitespace; permit case-insensitive matching only when uniquely matched to a canonical category |
| Date | Required; valid ISO format `YYYY-MM-DD` |
| Actual units, optional | Separate field for evaluating this example; finite, nonnegative, and never a model feature |

Derive weekday and day of year automatically. Construct the one-row DataFrame in the same `FEATURES` order used for fitting.

Do not replace typed fields with dropdown-only inputs. A “Use example” action may populate them. Reject missing, unknown, ambiguous, or invalid inputs before prediction, with clear examples of accepted values. Do not silently fuzzy-match a category or allow the encoder to accept an unsupported store.

Use a single primary action: “Predict.” This calls the already fitted selected pipeline's `.predict()` without retraining, appending data, or recalculating the historical metrics.

### Prediction response

Display:

1. Predicted daily units, to two decimals.
2. Selected model name and chosen parameters.
3. Canonical accepted store/category/date and derived weekday.
4. The same four historical test metrics for that exact fitted model, in a compact panel.
5. A short explanation that the new observation's actual outcome is not known unless entered.

Do not show another model's forecast, benchmark forecast, ranking, or comparison.

Example layout with placeholder numbers:

> Predicted daily sales: 38.40 units  
> Model: KNN regression, 15 neighbors  
> Historical test metrics: R² [value] · MSE [value] · RMSE [value] · MAPE [value]%  
> These metrics describe historical held-out observations, not the accuracy of this new prediction.

For a date within the development fitting period, label the example historical and potentially in-sample. For dates beyond the observed period, flag extrapolation. For a different year, explain that year is not a predictor and the new year has not been validated. Such notices should be concise and do not require extra tabs or confirmation flows.

Evaluate predictions without rounding or clipping. If the raw forecast is negative, label it as an invalid physical sales estimate; do not silently replace it with zero and alter classroom behavior.

If actual units are supplied, show this observation's signed error (`actual - predicted`) and absolute error. A positive signed error means underprediction. An optional percentage error is APE for this one row, not MAPE, and must be N/A when actual is zero. Never compute a one-row R² or update the historical metrics from the entered example.

## 11. State, simplicity, and footer

Maintain one active fitted model. A small session-state dictionary is sufficient.

| Event | Required behavior |
|---|---|
| Initial launch | Data view available; no model scores or prediction |
| Model/parameter changes | Invalidate the active fit, metrics, and prior prediction |
| Train model | Fit only the requested configuration; show progress; replace the current result |
| Data view filtering | Change only the displayed table/chart |
| Prediction-input changes | Do not retrain or modify historical metrics |
| Predict | Validate inputs and use the active fitted pipeline |
| Training failure | Clear old results; show a useful error; keep prediction disabled |
| Ordinary tab change/rerender | Preserve the active fitted model |

Keep form submissions explicit so typing does not trigger fitting. If using Streamlit reruns, preserve session state correctly and isolate mutable fitted objects by session. Do not expose cache controls to students.

The footer must read exactly:

> Business Analytics and Data Visualization Fall 2026 - Prof. Jose Mendoza

Render it consistently below the content of Data, Model, and Test. Use readable, subdued text; it must not overlap tables, forms, metrics, or mobile content. A shared footer function is appropriate. Additional navigation or a separate footer tab is not.

## 12. Suggested engine functions

Keep function boundaries close to the classroom code:

| Function | Responsibility |
|---|---|
| `load_data` | Load and validate the approved CSV |
| `prepare_data` | Derive features and preserve chronological partitions |
| `make_pipeline` | Classroom encoding and scaling |
| Model constructor functions | Create the selected classroom estimator with its preset |
| `fit_selected_model` | Refit the chosen specification on development data and retain the pipeline |
| `evaluate_model` | Return R², MSE, RMSE, MAPE, and metric provenance/counts |
| `make_prediction_row` | Build canonical features for one typed observation |
| `predict_one` | Call the retained fitted pipeline and return predicted units |

Do not import the dashboard framework into `models.py`, execute notebook display code, or construct duplicate model implementations in `app.py`. Application logic should call the engine and render its returned values.

No `select_best_model`, `compare_models`, benchmark-training function, or family-winner search is needed for the app workflow.

## 13. Reproducibility, performance, and errors

Record the data checksum, notebook versions, exact dependency versions, seed, selected parameters, feature order, fitting dates, and evaluation dates. Make technical provenance available in the developer documentation and a compact result caption, not a complex student control panel.

Pin the environment verified against the supplied notebooks. The previous verification environment used Python 3.12.14, scikit-learn 1.8.0, NumPy 2.3.5, and pandas 2.2.3; confirm compatibility with the approved attachments rather than silently upgrading.

Training occurs only through “Train model.” Do not load arbitrary uploaded serialized models or share mutable fitted estimators between sessions. A selected ensemble may take longer because it fits four members; use a short progress message without exposing a comparison workflow.

Target a warm prediction within two seconds and a selected-model fit, including ensemble, within two minutes on the developer's documented reference laptop. Record actual timings.

Use keyboard-accessible inputs, readable labels and units, and status indicators that do not depend only on color. Present convergence warnings beside the affected selected-model result. Keep detailed technical error information available to developers without overwhelming students.

## 14. Verification and acceptance criteria

### Notebook parity

Use identical approved data and pinned dependencies. Check the selected specification against its direct classroom implementation refitted on the same development data. The app's parameter choices are manual; notebook parity does not require reproducing the removed leaderboard.

Verify:

1. Identical row order, features, target, date boundaries, and development/test membership.
2. Matching encoded columns, numeric scaling, and target inverse transformation.
3. Matching predictions for each allowed model preset, evaluated one configuration at a time.
4. Matching ensemble predictions using the fixed standalone classroom members.
5. Dashboard typed-input forecasts matching direct engine `.predict()` on the same fitted object.

Use a justified tight numerical tolerance, such as `rtol=1e-7, atol=1e-7` in the same environment. Investigate unexplained discrepancies rather than widening tolerance to hide them. Fitting time is not a numerical parity criterion.

### Metric checks

Test the four metrics against independent hand-calculable examples:

- Perfect predictions produce MSE/RMSE/MAPE of zero where defined.
- Squared errors produce MSE, and its square root produces RMSE.
- Positive-actual percentage errors are averaged and converted to percent correctly.
- Mixed zero/positive actuals exclude zero rows from MAPE only and report the count.
- All-zero actuals produce MAPE N/A.
- Constant-actual R² is presented as undefined when appropriate.
- Metrics use raw predictions in original sales units.
- No percentage is described as classification accuracy or certainty for a typed example.

### UI and behavior checks

- Exactly three tabs: Data, Model, Test, in that order.
- Exactly the five allowed top-level model choices.
- Only the applicable parameter control is shown.
- Exactly four model-performance cards: R², MSE, RMSE, MAPE.
- No baseline result, leaderboard, automatic winner, comparison chart, or “run all” action.
- Ensemble members remain fixed and have no individual performance display.
- Model or parameter changes clear stale results and disable prediction.
- Viewing data, changing tabs, or typing does not retrain.
- Typed invalid inputs receive helpful errors; optional actual values are not predictors.
- Input forecasts and displayed historical scores come from the same fitted pipeline.
- The footer exactly matches the requested text on every tab.
- Fresh setup and local launch are tested on Windows and macOS.

## 15. Developer deliverables

Deliver a reviewable repository folder or pull request containing the engine, three-tab dashboard, launcher, pinned requirements, approved data snapshot, source attribution, and tests.

Include:

- A concise student README for setup and the Data → Model → Test workflow.
- The notebook-to-engine map, including the authorized workflow and metric adaptations.
- Evidence of model parity, MAPE edge-case handling, input validation, and three-tab behavior.
- A short walkthrough demonstrating one model, its four metrics, and one typed prediction.
- Any unresolved source discrepancy or unverified platform requirement.

The release criterion is a straightforward student experience: inspect the data, select one familiar model and parameter, train it, then type inputs and receive a forecast with clearly labeled metrics.

## 16. Reference links

- Streamlit launch: <https://docs.streamlit.io/develop/api-reference/cli/run>
- Streamlit session state: <https://docs.streamlit.io/develop/concepts/architecture/session-state>
- Course repository: <https://github.com/jrmst102/businessanalytics>
- Mancino data: <https://github.com/jrmst102/mancino/blob/main/data/v1_2025-11-01/mancino_daily_sales.csv>

The attached classroom notebooks govern model behavior. Framework documentation supports the wrapper implementation.
