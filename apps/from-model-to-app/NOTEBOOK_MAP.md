# Notebook-to-engine map

Traceability from the classroom notebooks to `models.py`. The authoritative source is
`notebooks/Mancino_Regression_Final.ipynb` (the integrated notebook). The individual
notebooks supply explanatory text and were checked for consistency (see "Source review").

Reference versions (SHA-256 prefix of the files in `notebooks/` on 2026-10-22):

| Notebook | SHA-256 (first 16) | Role |
|---|---|---|
| `Mancino_Regression_Final.ipynb` | `224a1852bfbfa93f` | Authoritative engine source |
| `Mancino_Regression_KNN_Complete.ipynb` | `91a1d32f11edf9cf` | KNN explanation |
| `Mancino_Regression_Trees.ipynb` | `6c103adf57cb9c96` | Tree explanation (spec lists `..._Trees_Complete`; this is the supplied file) |
| `Mancino_Random_Forests_Complete.ipynb` | `a636a365b1af1303` | Forest explanation |
| `Mancino_Neural_Networks_Complete.ipynb` | `9579590b655a9e14` | Network explanation |
| `Mancino_Ensemble.ipynb` | `cd519958f41edaf8` | Ensemble explanation (spec lists `..._Ensemble_Complete`; this is the supplied file) |

Environment in which the notebooks were executed for parity: Python 3.12.3, scikit-learn 1.8.0,
NumPy 2.3.5, pandas 2.2.3 (pinned in `requirements.txt`). The only stored environment record in
the supplied notebooks is in `Mancino_Regression_Notebook.ipynb`/`_Starter.ipynb`
(`pandas 2.2.3 | scikit-learn 1.6.1`); the final and companion notebooks were saved without outputs.
The three stored validation MAEs there (baseline 13.223, KNN k=15 8.741, tree depth 6 8.594) match
the engine to three decimals, so the 1.6.1 -> 1.8.0 difference did not change these results.

## Cell-by-cell map

"Behavior unchanged" below means the parity tests in `tests/test_notebook_parity.py` compare the
engine against the notebook cells executed verbatim and pass at `rtol=1e-7, atol=1e-7`.

| Cell | Engine function(s) | Changes made to extract | Analytical behavior |
|---|---|---|---|
| `final-002` imports, `SEED`, `np.random.seed` | module header, constants | Dropped `io`, `IPython.display`, `matplotlib` (plots live in `app.py`). Added `hashlib`, `platform`, `warnings` for the reproducibility record and warning capture. `RUN_FINAL_TEST` flag replaced by the dashboard's explicit "Finalize" action. | Unchanged |
| `final-004` load and validate | `load_data`, `describe_data`, `dataset_checksum` | GitHub download and Colab `files.upload()` removed; the approved CSV is bundled (`DATA_PATH`). Each `assert` became a `ValueError`/`FileNotFoundError` with the notebook's message so a bad file yields an actionable error. `display(df.head())` removed; the app shows the table. | Unchanged (same checks, same sort order) |
| `final-006` features and split | `prepare_data`, constants `CATEGORICAL`, `NUMERIC`, `FEATURES`, `TARGET` | Module globals `X_train`, `y_val` ... are returned in a dictionary with the same names. `display(...)` of the partition table replaced by the returned `partitions` DataFrame. Added `stores`/`categories` lists for input validation. | Unchanged |
| `final-007` training plots | `app.py` tab A | Plot-only cell; rendered by the dashboard over the view filter instead of training only. Not part of the engine. | n/a |
| `final-009` `make_pipeline`, `metrics`, `clear_family`, `fit_and_evaluate`, `best_in_family` | same names | `fit_and_evaluate` takes `data` instead of reading globals and returns one `candidate` dictionary (fitted model, specification clone, validation predictions, result row, warnings) instead of writing to the three global dictionaries; `display(...)` removed. Warnings are captured with `warnings.catch_warnings(record=True)` so the app can show convergence warnings beside the result. A `Settings` text column was added to the result row for the leaderboard. `clear_family`/`best_in_family` take the candidates dictionary as an argument. | Unchanged |
| `final-011` baseline | `make_baseline` | Constructor wrapped in a one-line function. | Unchanged |
| `final-013` KNN presets | `make_knn`, `K_VALUES` | Loop body became a constructor function; the loop lives in `individual_candidates`. The `k <= len(X_train)` assertion is implied by the fixed presets. | Unchanged |
| `final-015` tree presets | `make_tree`, `TREE_DEPTHS`, `MIN_LEAF` | Same as above. | Unchanged |
| `final-017` forest presets | `make_forest`, `FOREST_SIZES` | Same as above. | Unchanged |
| `final-019` network presets | `make_network`, `NETWORK_LAYERS` | Same as above; `print('Training epochs', ...)` became `candidate['training_epochs']`. | Unchanged |
| `final-021` family winners and ensembles | `family_winners`, `make_ensemble`, `ensemble_candidates`, `normalized_weights`, `residual_correlations`, `ENSEMBLE_WEIGHTS` | Members are `clone(candidate['specification'])` rather than `clone(models[name])`; both yield an unfitted estimator with identical parameters. `family_winners` additionally refuses to run unless all 12 presets are present (the notebook ran them all by construction). `display(...)` removed. | Unchanged |
| `final-023` leaderboard and selection | `results_table`, `leaderboard`, `select_model`, `ensemble_gain`, `is_complete_comparison` | `results_table` rebuilds the notebook's `results` dict in `CANDIDATE_ORDER` so `min(...)` keeps the notebook's tie behavior even if a student trained candidates in a different order. The bar chart is drawn by `app.py`. | Unchanged |
| `final-025` final refit, test, diagnostics | `finalize_model`, `segment_errors` | `RUN_FINAL_TEST` gate replaced by the explicit app action; the function receives the frozen specification. Results returned in a dictionary; `display(...)` and plots moved to `app.py`. | Unchanged |
| `final-027` managerial briefing | `managerial_briefing` | Returns the Markdown string instead of `display(Markdown(...))`. One guard added: WAPE is printed as "undefined" when the denominator is zero. | Unchanged templates |
| (new) typed prediction | `make_prediction_row`, `predict_one` | Wrapper for the typed-input exercise: builds a one-row DataFrame in `FEATURES` order (weekday and day of year derived from the date exactly as in `final-006`) and calls the fitted pipeline's `.predict`. | Uses the classroom `.predict` |
| (new) reproducibility | `environment_record`, `run_identity`, `DATA_SHA256` | Records dataset checksum, versions, seed, parameters, feature order, split boundaries and fit/evaluation periods. | n/a |

Input validation (`inputs.py`) is wrapper code with no notebook counterpart.

## Source review of the companion notebooks

The companion notebooks use the same loading, splitting, preprocessing and metric code as the
final notebook. The only constructor differences are explicitly written scikit-learn defaults,
which do not change behavior:

- KNN notebook adds `metric='euclidean'` (default).
- Trees and forests notebooks add `criterion='squared_error'` (default).
- Neural-network notebook adds `tol=0.0001` (default).
- `Mancino_Ensemble.ipynb` uses fixed members (KNN k=50, tree depth 12, forest 100 trees,
  network (16,)). The final notebook selects members by validation MAE; on the approved
  snapshot the selected members are exactly these four, so the two notebooks agree.

`Mancino_Regression_Notebook.ipynb` and `Mancino_Regression_Starter.ipynb` are earlier
teaching versions (forest `min_samples_leaf=10`, standardized day of year for trees) and are not
among the spec's authoritative sources; they were not used for the engine.

**Unresolved discrepancies:** none that change predictions or evaluation.

## Items needing instructor confirmation

1. The spec's filenames `Mancino_Regression_Trees_Complete.ipynb` and
   `Mancino_Ensemble_Complete.ipynb` were not present; `Mancino_Regression_Trees.ipynb` and
   `Mancino_Ensemble.ipynb` were used. Their code matches the final notebook as described above.
2. The notebooks' own environment is not recorded (no saved outputs). Parity was established by
   executing them in the pinned environment listed above.
