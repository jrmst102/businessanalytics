# Verification evidence

Reference machine: dev container (Ubuntu 24.04, x86-64, shared cloud CPU), Python 3.12.3,
scikit-learn 1.8.0, NumPy 2.3.5, pandas 2.2.3, matplotlib 3.10.9, Streamlit 1.66.1.
Dataset snapshot SHA-256 `8441fb2d...` (see `data/SOURCE.md`). Date: 2026-10-22.

Run everything with `python -m pytest tests -q` (27 tests, about 85 s on the reference machine).

## A. Notebook parity (release gate) - PASS

`tests/test_notebook_parity.py` executes cells `final-002` to `final-025` of
`notebooks/Mancino_Regression_Final.ipynb` verbatim (only `display`/`Markdown` stubbed and plots
sent to the Agg backend) and compares against `models.py` with
`numpy.testing.assert_allclose(rtol=1e-7, atol=1e-7)`.

| Check | Result |
|---|---|
| Data preparation: `df`, `X_*`, `y_*`, feature order, `train_end`, `validation_end` | identical (`assert_frame_equal`) |
| Preprocessing: encoded column names and transformed validation rows (KNN scaled, tree passthrough) | identical |
| 12 presets + baseline: validation predictions, Train MAE, Validation MAE/RMSE/R² | all within tolerance |
| Ensembles: family winners, member order `model_0..3`, weights `[1,1,2,2]`, predictions | identical |
| Selection: `select_model` == notebook `selected_name`; best individual / best ensemble / gain | identical |
| Final refit: test predictions, baseline predictions, MAE/RMSE/R², mean bias, underprediction rate, store and category diagnostics | identical |
| Typed example: `predict_one` == direct `.predict()` on the same pipeline and row | identical |
| Ensemble arithmetic on 5 validation rows: `VotingRegressor` output == (weighted) mean of fitted member predictions | identical |

Wall-clock fitting time is excluded from comparisons. No tolerance widening was needed.

Reference results on the approved snapshot (validation MAE, units per store/category/day):
baseline 13.223; KNN k=5/15/50 8.691/8.741/8.426; tree depth 3/6/12 10.332/8.594/8.550;
forest 50/100/200 trees 8.358/8.343/8.353; network (16,)/(32,)/(32,16) 8.178/8.226/8.523;
equal ensemble 8.189; weighted ensemble 8.168. Family winners: KNN k=50, tree depth 12,
forest 100 trees, network (16,). Selected: **Ensemble: weighted average** (gain over best
individual 0.010 units, 0.13%). Final test: MAE 7.938 vs refitted baseline 13.045 (39.1%
improvement), RMSE 10.282, R² 0.603, mean signed error +0.405, 49.7% underpredicted, 0 negative
predictions. No convergence warnings were raised by the three networks (49/43/51 epochs).

## B. Evaluation and state checks

| # | Requirement | Evidence |
|---|---|---|
| 1 | Identical chronological partitions; no date crosses sets | `test_partitions_are_chronological_and_complete` |
| 2 | Test outcomes not used for fitting, settings, members or recommendation | `select_model`, `family_winners`, `ensemble_gain` read only validation results; `finalize_model` is the only function touching `X_test` and is reached only via the explicit Finalize action after a frozen selection (`test_full_student_flow`) |
| 3 | Finalization freezes the specification before test scoring | `selection['specification']` is a clone taken at freeze time; `finalize_model` clones it again (`test_finalize_uses_development_period_and_frozen_spec`) |
| 4 | Changing a preset cannot leave old metrics labeled as the new setting | each candidate keeps its own fitted model and result; refitting replaces the entry and clears dependents (`invalidate_dependents`, smoke test) |
| 5 | Changing a member invalidates dependent ensembles | `test_clear_family_drops_dependent_ensembles`; smoke test asserts ensembles removed after refitting KNN k=50 |
| 6 | Prediction form and view filters do not change models or scores | prediction code only calls `.predict`; view filters only subset a display copy (`tab_explore`) |
| 7 | Experiment vs finalized provenance on predictions | `EXPERIMENT_LABEL` / `FINAL_LABEL` chosen from the stage of the model used; smoke test checks the final label |
| 8 | Reset does not claim the test period is new | sidebar reset preserves `test_inspected` and logs the note |

## C. Input and presentation checks

`tests/test_inputs.py` and the smoke test cover: valid inputs -> finite prediction equal to the
engine; empty, malformed, unknown and ambiguous entries -> specific messages; visible
case/whitespace normalization (`' bakery '` -> `Bakery`); extrapolation and different-year
notices; historical in-sample label; optional actual value -> only that observation's signed
and absolute error; negative prediction flagged (not clipped); zero baseline MAE -> "not
defined"; zero WAPE denominator -> undefined. Labels, units and stage text are set per screen.

## D. Student-launch checks

| Check | Linux (reference) | Windows | macOS |
|---|---|---|---|
| Fresh venv + `pip install -r requirements.txt` | pass | pending | pending |
| `python launch.py` from another working directory | pass (`/tmp`) | pending | pending |
| Bound to 127.0.0.1 only (`ss -ltn`) | pass | pending | pending |
| Browser opening or printed URL fallback | pass (`--no-browser` prints URL; headless container cannot open a browser) | pending | pending |
| Occupied-port message | pass | pending | pending |
| Missing-dependency message (system Python without packages) | pass | pending | pending |
| Offline use after installation | pass (no network access at runtime; CSV bundled) | pending | pending |

Windows and macOS runs must be performed on real machines before release; the commands are in
`README.md`.

## Performance (usability targets, not acceptance thresholds)

- Full 15-candidate classroom comparison: 19.6 s (`run_engine.py`), well under the two-minute target.
- Warm single-row prediction: 38 ms for the weighted ensemble, under the two-second target.
- Dashboard smoke flow (train, compare, freeze, finalize, predict, refit): 39 s under AppTest.

## E. Pedagogical review

Trace of one typed input: `tab_predict` -> `inputs.validate_prediction_inputs` ->
`models.make_prediction_row` (weekday and day of year derived exactly as in `prepare_data`) ->
`models.predict_one(fitted_pipeline, row)` -> displayed with the stage label. `models.py` imports
no Streamlit. All adaptations are listed in `NOTEBOOK_MAP.md`.

## Open items for the instructor

1. Windows and macOS launch checks (table D) are pending.
2. The supplied tree and ensemble notebooks have slightly different filenames than the spec
   (`NOTEBOOK_MAP.md`); their code matches the final notebook.
3. The notebooks were saved without outputs, so parity was established by executing them in the
   pinned environment rather than against stored Colab outputs.
