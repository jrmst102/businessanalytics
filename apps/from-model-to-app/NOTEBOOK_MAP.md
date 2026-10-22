# Notebook-to-engine map

Traceability from the classroom notebooks to `models.py` for the version 2.0 app
(three tabs: Data, Model, Test; one selected model at a time). The authoritative
sources are the supplied notebooks in `notebooks/`; cell identifiers such as
`final-006` refer to `Mancino_Regression_Final.ipynb`.

Reference versions (SHA-256 prefix of the files in `notebooks/` on 2026-10-22):

| Notebook | SHA-256 (first 16) | Role |
|---|---|---|
| `Mancino_Regression_Final.ipynb` | `224a1852bfbfa93f` | Shared feature preparation, date splits, development-set refit |
| `Mancino_Regression_KNN_Complete.ipynb` | `91a1d32f11edf9cf` | KNN model and explanation |
| `Mancino_Regression_Trees.ipynb` | `6c103adf57cb9c96` | Regression-tree model (spec lists `..._Trees_Complete`; this is the supplied file) |
| `Mancino_Random_Forests_Complete.ipynb` | `a636a365b1af1303` | Random-forest model and explanation |
| `Mancino_Neural_Networks_Complete.ipynb` | `9579590b655a9e14` | Network construction, scaling, early stopping |
| `Mancino_Ensemble.ipynb` | `cd519958f41edaf8` | Fixed member configurations and equal/weighted averaging (spec lists `..._Ensemble_Complete`; this is the supplied file) |

Environment used for parity: Python 3.12, scikit-learn 1.8.0, NumPy 2.3.5,
pandas 2.2.3 (pinned in `requirements.txt`).

## Source-to-function map

"Predictions unchanged" means `tests/test_notebook_parity.py` compares the engine
against the same specification written out verbatim from the notebook, refitted on
the same development data, at `rtol=1e-7, atol=1e-7`.

| Source (notebook, section/cell) | Engine function | Changes made to extract | Analytical behavior |
|---|---|---|---|
| Final, `final-002` imports and `SEED` | module header, constants | Dropped plotting/IPython/Colab imports (display lives in `app.py`). Added `hashlib`, `platform`, `warnings` for the reproducibility record and warning capture. | Unchanged |
| Final, `final-004` load and validate | `load_data`, `describe_data`, `dataset_checksum` | GitHub download and Colab `files.upload()` removed; the approved CSV is bundled (`DATA_PATH`). Each `assert` became a `ValueError`/`FileNotFoundError` with the notebook's message. `display(df.head())` removed; the Data tab shows the table. | Unchanged (same checks, same sort order) |
| Final, `final-006` features and split | `prepare_data`, constants `CATEGORICAL`, `NUMERIC`, `FEATURES`, `TARGET` | Module globals `X_train`, `y_val`, ... are returned in a dictionary with the same names. Added `stores`/`categories` lists for input validation. | Unchanged |
| Final, `final-009` `make_pipeline` | `make_pipeline` | Copied as-is: `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` on the categoricals; `StandardScaler` or passthrough on `day_of_year`. | Unchanged |
| KNN notebook / `final-013` | `make_knn` | Loop body became a constructor function; the allowed k values are the classroom presets `[5, 15, 50]`. | Unchanged |
| Trees notebook / `final-015` | `make_tree` | Same; depths `[3, 6, 12]`, `min_samples_leaf=30`, `random_state=42`. | Unchanged |
| Forests notebook / `final-017` | `make_forest` | Same; sizes `[50, 100, 200]` with the fixed forest settings. | Unchanged |
| Networks notebook / `final-019` | `make_network` | Same; architectures `[(16,), (32,), (32, 16)]`, `TransformedTargetRegressor(..., transformer=StandardScaler())`, early stopping on a random 15% of the fitting data. `print('Training epochs', ...)` became `result['training_epochs']`. | Unchanged |
| Ensemble notebook, `base_estimators` + `WEIGHTS` cells | `ensemble_member_estimators`, `make_ensemble`, `ENSEMBLE_WEIGHTS`, `ENSEMBLE_MEMBERS` | The standalone notebook's **fixed** members (KNN k=50; tree depth 12; forest 100 trees; network (16,)) in its order and `model_0..3` names; `VotingRegressor(..., n_jobs=1)`; weights `[1, 1, 2, 2]` for the weighted preset. | Unchanged |
| Final, `final-025` development refit | `fit_selected_model` | The `RUN_FINAL_TEST` gate and the prior selection machinery are replaced by the app's explicit "Train model" action for the one chosen specification: concatenate training + validation, fit a clone, predict the test rows, compute metrics, retain the fitted pipeline. The baseline refit, diagnostics tables and plots of that cell are not part of this app. | Unchanged for the fitted specification |
| Final/companions, `metrics` cell | `evaluate_model` | Replaces the notebooks' MAE/RMSE/R² reporting with the app's four metrics (see adaptations 3 below). Metrics operate on the same raw predictions in original sales units. | Reporting changed as authorized; predictions unchanged |
| (new, wrapper adaptation) | `make_prediction_row`, `predict_one` | Builds a one-row DataFrame in `FEATURES` order (weekday and day of year derived from the date exactly as in `final-006`) and calls the fitted pipeline's `.predict`. | Uses the classroom `.predict` |
| (new) reproducibility | `environment_record`, `run_identity`, `DATA_SHA256` | Records dataset checksum, versions, seed, parameters, feature order, split boundaries and fit/evaluation periods. | n/a |

Input validation (`inputs.py`) and all display/state code (`app.py`) are wrapper
code with no notebook counterpart.

## Documented adaptations (authorized by the instructor)

1. **Manual student choice replaces automatic model selection.** The final
   notebook evaluates 15 candidates on validation data and selects the lowest
   validation MAE before its test refit. The app removes that search entirely:
   the student picks one of five model choices and one classroom preset, and
   "Train model" performs the final notebook's development-set refit directly
   for that specification. No leaderboard, baseline, family winners,
   `select_model`, or comparison exists in the app.
2. **Fixed classroom ensemble members replace family-winner searching.** The
   app's ensemble uses the standalone ensemble notebook's fixed members (KNN
   k=50; tree depth 12; forest 100 trees; network (16,)) rather than the final
   notebook's validation-winner search. On the approved snapshot the final
   notebook's winners happen to be exactly these four configurations, so the
   two sources agree numerically.
3. **MSE and MAPE reporting.** The notebooks report MAE, RMSE and R². The app
   shows R², MSE, RMSE and MAPE for the selected model. MSE is
   `mean_squared_error`; MAPE averages `abs((actual - predicted)/actual)` over
   rows with positive actual sales only (zero-sales rows are excluded from
   MAPE alone and their count disclosed; all-zero actuals give "N/A"). R² is
   reported as undefined when the actual values are constant. These are
   reporting changes only; fitted models and predictions are untouched. The
   classroom MAE remains in the reference notebooks and does not drive any app
   ranking or benchmark.
4. **Display and input handling moved to the wrapper.** All Streamlit imports,
   session state, forms, the three tabs, the footer, typed-input validation
   (`inputs.py`) and every plot/table render live in `app.py`; `models.py`
   contains no display code and no Streamlit import. The "Code from class"
   expander reads the engine functions with `inspect.getsource`, so there is
   no second executable implementation.

## Source review of the companion notebooks

The companion notebooks use the same loading, splitting, preprocessing and
constructor code as the final notebook. The only constructor differences are
explicitly written scikit-learn defaults, which do not change behavior:

- KNN notebook adds `metric='euclidean'` (default).
- Trees and forests notebooks add `criterion='squared_error'` (default).
- Neural-network notebook adds `tol=0.0001` (default).

`Mancino_Regression_Notebook.ipynb` and `Mancino_Regression_Starter.ipynb` are
earlier teaching versions (forest `min_samples_leaf=10`, standardized day of
year for trees) and are not among the spec's authoritative sources; they were
not used for the engine.

**Open discrepancy note for the instructor:** the supplied files are named
`Mancino_Regression_Trees.ipynb` and `Mancino_Ensemble.ipynb`, while the
specification lists `Mancino_Regression_Trees_Complete.ipynb` and
`Mancino_Ensemble_Complete.ipynb`. Their contents match the specification's
parameter inventory, so the engine was built from them; confirm they are the
approved versions.
