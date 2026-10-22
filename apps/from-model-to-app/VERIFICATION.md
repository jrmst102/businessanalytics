# Verification evidence

Reference machine: dev container (Ubuntu 24.04, x86-64, shared cloud CPU), Python 3.12.3,
scikit-learn 1.8.0, NumPy 2.3.5, pandas 2.2.3, Streamlit 1.66.1.
Dataset snapshot SHA-256 `8441fb2d...` (see `data/SOURCE.md`). Date: 2026-10-22.

Run everything with `python -m pytest tests -q` (48 tests, about 50 s on the reference machine).

## A. Notebook parity (release gate) — PASS

`tests/test_notebook_parity.py`:

- Data preparation: cells `final-002` to `final-006` of
  `notebooks/Mancino_Regression_Final.ipynb` are executed verbatim (only
  `display`/`Markdown` stubbed); `df`, `X_*`, `y_*`, feature order, `train_end`
  and `validation_end` are identical (`assert_frame_equal`).
- Predictions: **each of the 14 allowed configurations** (3 KNN, 3 trees,
  3 forests, 3 networks, 2 ensembles) is refitted by the engine on the
  development set (training + validation, 18,300 rows) and compared against the
  same specification written out verbatim with the classroom scikit-learn
  constructors, fitted on the same data and scored on the same 4,575 test rows:
  all predictions and all four metrics match at
  `numpy.testing.assert_allclose(rtol=1e-7, atol=1e-7)`. No tolerance widening
  was needed.
- Preprocessing: identical encoded columns (5 stores + 15 categories +
  7 weekdays + `day_of_year`); `day_of_year` standardized for KNN/network,
  passthrough for tree/forest.
- Ensembles: fixed members `model_0..3` (KNN k=50, tree depth 12, forest 100
  trees, network (16,)), `n_jobs=1`; `VotingRegressor` output equals the
  (weighted) mean of its fitted members' predictions on sample rows; weighted
  shares are exactly `[1/6, 1/6, 1/3, 1/3]`.
- Typed example: `predict_one` equals direct `.predict()` on the same fitted
  pipeline and row; the dashboard smoke test checks the same equality through
  the UI.

Reference results on the approved snapshot (test metrics from the development-set
refit; fit time and warm one-row prediction time on the reference machine):

| Configuration | R² | MSE | RMSE | MAPE | Fit | Predict |
|---|---:|---:|---:|---:|---:|---:|
| KNN, 5 neighbors | 0.545 | 121.25 | 11.01 | 28.33% | <0.1 s | 4 ms |
| KNN, 15 neighbors | 0.573 | 113.65 | 10.66 | 27.70% | <0.1 s | 4 ms |
| KNN, 50 neighbors | 0.571 | 114.38 | 10.69 | 28.28% | <0.1 s | 4 ms |
| Tree, depth 3 | 0.425 | 153.22 | 12.38 | 34.10% | <0.1 s | 2 ms |
| Tree, depth 6 | 0.584 | 110.77 | 10.52 | 27.72% | <0.1 s | 2 ms |
| Tree, depth 12 | 0.579 | 112.10 | 10.59 | 27.00% | <0.1 s | 2 ms |
| Forest, 50 trees | 0.585 | 110.67 | 10.52 | 26.93% | 0.6 s | 26 ms |
| Forest, 100 trees | 0.586 | 110.36 | 10.51 | 26.87% | 1.0 s | 24 ms |
| Forest, 200 trees | 0.586 | 110.44 | 10.51 | 26.89% | 2.4 s | 45 ms |
| Network (16,) | 0.593 | 108.39 | 10.41 | 27.20% | 2.1 s (99 epochs) | 3 ms |
| Network (32,) | 0.595 | 107.80 | 10.38 | 28.00% | 1.0 s (38 epochs) | 3 ms |
| Network (32, 16) | 0.599 | 106.78 | 10.33 | 25.39% | 2.2 s (58 epochs) | 3 ms |
| Ensemble, equal weights | 0.602 | 106.04 | 10.30 | 26.80% | 3.2 s | 37 ms |
| Ensemble, weighted average | 0.603 | 105.73 | 10.28 | 26.73% | 6.5 s | 67 ms |

All fits are far inside the two-minute target and warm predictions far inside the
two-second target. No convergence warnings were raised by any network
configuration. Zero test rows have zero actual sales, so no observations were
excluded from MAPE on this snapshot (the exclusion policy is exercised by the
metric tests below). The weighted-ensemble figures (R² 0.603, RMSE 10.28) equal
the final notebook's test refit of the same specification recorded during the
version 1.0 verification, as expected since the final notebook's validation
winners coincide with the fixed classroom members on this snapshot.

## B. Metric checks (hand-calculable examples) — PASS

`tests/test_engine.py`:

| Check | Evidence |
|---|---|
| Perfect predictions → MSE/RMSE/MAPE 0, R² 1 | `test_perfect_predictions_give_zero_errors` |
| Squared errors → MSE; its square root → RMSE | `test_mse_and_rmse_hand_example` (errors 1, −2 → MSE 2.5) |
| Positive-actual APEs averaged and in percent | `test_mape_hand_example_in_percent` (0.1, 0.2 → 15.00%) |
| Mixed zero/positive actuals: zero rows excluded from MAPE only, count reported | `test_mixed_zero_actuals_excluded_from_mape_only` |
| All-zero actuals → MAPE N/A with explanation | `test_all_zero_actuals_give_mape_na` |
| Constant actuals → R² undefined (no substituted 0/1) | `test_constant_actuals_give_r2_undefined` |
| Metrics on raw, unrounded predictions in original units | `test_metrics_use_raw_unrounded_values`; parity tests run on raw engine predictions |
| No percentage described as accuracy | app copy states R² "is not percentage accuracy" and MAPE is never relabeled; the smoke test drives the real copy |

## C. UI and behavior checks — PASS

`tests/test_app_smoke.py` (Streamlit headless AppTest against the real `app.py`):

| Requirement | Evidence |
|---|---|
| Exactly three tabs — Data, Model, Test — in order | `test_initial_launch_three_tabs_footer_no_results` |
| Footer exactly "Business Analytics and Data Visualization Fall 2026 - Prof. Jose Mendoza" on every tab | same test: the caption appears exactly 3 times |
| Exactly the five allowed model choices; KNN default; no result until "Train model" | same test |
| No baseline, leaderboard, "run all", winner or comparison actions | same test: the only buttons are Train model / Use example / Predict |
| Only the applicable parameter control is shown | `test_parameter_control_follows_the_selected_model` |
| Exactly four model-performance cards: R², MSE, RMSE, MAPE | `test_train_predict_and_invalidation_flow` |
| Dashboard typed-input forecast equals direct engine `.predict()` on the same fitted pipeline | same test |
| Invalid typed inputs get helpful errors and never reach `.predict` | same test (unknown store, malformed date) |
| Model/parameter changes clear stale results and disable prediction | same test (k 15 → 5 clears fit, metrics, prediction) |
| Viewing data, switching tabs or typing never retrains | training happens only inside the Train model handler; view filters subset a display copy only |
| Ensemble members fixed, no individual member scores displayed | `test_ensemble_uses_fixed_classroom_members` (engine) + the Model tab shows members as an explanatory caption only |
| Optional actual units are never a model feature | `make_prediction_row` takes only store/category/date; `tests/test_inputs.py` |

`tests/test_inputs.py` covers: canonical store/category matching (case and
whitespace-insensitive only when unique), ambiguity rejection, strict
`YYYY-MM-DD` dates, optional finite nonnegative actual units, and the
historical/extrapolation/different-year date notices.

## D. Student-launch checks

| Check | Linux (reference) | Windows | macOS |
|---|---|---|---|
| Fresh venv + `pip install -r requirements.txt` | pass | pending | pending |
| `python launch.py` from another working directory | pass | pending | pending |
| Bound to 127.0.0.1 only | pass | pending | pending |
| Browser opening or printed URL fallback | pass (`--no-browser` prints URL; headless container cannot open a browser) | pending | pending |
| Occupied-port and missing-dependency messages | pass | pending | pending |
| Offline use after installation | pass (no network access at runtime; CSV bundled) | pending | pending |
| Visual once-over of the three tabs in a real browser | pending | pending | pending |

Windows and macOS runs, and the in-browser visual check, must be performed on
real machines before release; the commands are in `README.md`. The headless
AppTest suite verifies the rendered structure (tabs, footer, cards, options,
state transitions) on the reference machine.

