# Business Analytics in Action: From Model to App

A local, browser-based teaching dashboard for the Mancino regression unit.
Explore the dataset, choose **one** classroom model (KNN, regression tree, random
forest, neural network, or the averaging ensemble) with its classroom parameter,
train it, read its four test metrics (R², MSE, RMSE, MAPE), then type a store,
category and date to get one prediction from the same fitted model.

The dataset (Mancino Market) is **synthetic** teaching data. See `data/SOURCE.md`.

## What is in this folder

| File | Role |
|---|---|
| `models.py` | The classroom engine: preprocessing, model constructors, fitting, metrics and prediction, extracted from the Mancino notebooks. Readable without knowing Streamlit. |
| `app.py` | The three-tab dashboard (Streamlit): rendering, forms, session state, footer. Calls `models.py`; defines no models. |
| `inputs.py` | Validation of the typed store, category, date and optional actual units. |
| `launch.py` | Starts the local dashboard and opens your browser. |
| `run_engine.py` | Fits one configuration from the command line (developer convenience). |
| `requirements.txt` | Pinned, tested dependencies. |
| `NOTEBOOK_MAP.md` | Which notebook cell became which function, and every adaptation made. |
| `VERIFICATION.md` | Parity, metric, input and three-tab behavior evidence. |
| `data/mancino_daily_sales.csv`, `data/SOURCE.md` | Approved offline data snapshot and its provenance. |
| `tests/` | Model-parity, metric, input and application checks. |

## First-time setup

You need Python 3.12 (3.11–3.13 should also work; 3.12 is the verified version).
Run the commands from a terminal opened in this folder (`apps/from-model-to-app`).

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell refuses to run the activation script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt
with `.\.venv\Scripts\activate.bat`.

**macOS / Linux (Terminal)**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Installation needs the internet once. After that the app runs offline: the data
file is bundled. You do not reinstall dependencies on later launches — just
activate the environment and launch.

## Launch the dashboard

With the virtual environment activated:

```bash
python launch.py
```

The launcher starts the app on `http://localhost:8501` (this computer only),
opens your default browser, and prints the link in case the browser does not
open. Stop it with `Ctrl+C` in the terminal. It works from any working
directory, e.g. `python path/to/launch.py`.

Options: `python launch.py --port 8600` if 8501 is busy; `--no-browser` to only
print the link.

**Manual fallback** if the launcher cannot be used:

```bash
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Note: viewing this folder on GitHub displays the code; it does not run the app.
Clone or download the repository and follow the steps above.

## Using the app: Data → Model → Test

1. **Data** — a short introduction to the Mancino snapshot, dataset facts, the
   variable dictionary (target and model inputs), a filterable table and one
   sales-over-time chart. The filters change the view only; they never change
   model fitting or evaluation data.
2. **Model** — pick one of the five model choices and its single classroom
   parameter, then press **Train model**. The app refits that one specification
   on the development dates (training + validation, 18,300 rows) and shows four
   result cards — R², MSE, RMSE, MAPE — computed on the 4,575 held-out test
   observations, with a short interpretation. Changing the model or parameter
   clears the results until you train again. "Code from class" shows the actual
   engine code used.
3. **Test** — type a store ID, category and date (`YYYY-MM-DD`); optionally the
   actual units for this one example. The app validates the entries, derives
   weekday and day of year, and calls the fitted pipeline's `.predict()` —
   no retraining. You get the predicted daily units, the model and parameters
   used, and the same four historical test metrics for context.

Training only happens when you press **Train model**. Typing inputs, switching
tabs or changing view filters never retrains anything. Only the currently
selected model's results are shown; there is no leaderboard or comparison.

## The models (classroom settings)

| Choice | scikit-learn class | Student parameter (default in bold) | Fixed settings |
|---|---|---|---|
| KNN regression | `KNeighborsRegressor` | neighbors 5, **15**, 50 | `weights='uniform'`, day of year standardized |
| Regression tree | `DecisionTreeRegressor` | depth 3, **6**, 12 | `min_samples_leaf=30`, `random_state=42` |
| Random forest | `RandomForestRegressor` | 50, **100**, 200 trees | `max_depth=12`, `min_samples_leaf=30`, `max_features=0.8`, `bootstrap=True`, `random_state=42` |
| Neural network | `MLPRegressor` in `TransformedTargetRegressor` | (16,), (32,), **(32, 16)** | ReLU, Adam, `alpha=0.01`, `batch_size=256`, `max_iter=300`, early stopping (15%, patience 20), target standardized |
| Ensemble regression | `VotingRegressor` | **Equal weights** or Weighted average `[1, 1, 2, 2]` | fixed classroom members: KNN k=50, tree depth 12, forest 100 trees, network (16,) |

Features: `store_id`, `category`, `weekday`, `day_of_year` (the last two derived
from the date). Target: `units_sold`. `revenue` and `avg_price` are shown in the
data but never used as predictors. Split: first 60% of dates train, next 20%
validate, last 20% test (2025-01-01 to 07-02, 07-03 to 09-01, 09-02 to 11-01);
"Train model" fits on training + validation and evaluates on the test dates.

MAPE note: rows with zero actual sales are excluded from MAPE only (the count is
disclosed); MAPE can exceed 100% and is **not** "accuracy". R² is dimensionless,
can be negative, and is not percentage accuracy either.

## Running the tests

```bash
python -m pytest tests -q
```

The parity tests refit every allowed configuration and compare it against the
direct classroom implementation on the same development data; the full suite
takes several minutes on the reference machine (see `VERIFICATION.md` for
timings). For a quick check, run
`python -m pytest tests/test_engine.py tests/test_inputs.py tests/test_app_smoke.py -q`.

## Troubleshooting

- **`Missing Python packages: ...`** — the virtual environment is not active or
  the install step was skipped. Activate it and run
  `python -m pip install -r requirements.txt`.
- **`Port 8501 is already in use`** — another dashboard is still running. Close
  it or use `python launch.py --port 8600`.
- **Browser did not open** — copy the printed `http://localhost:...` link into
  your browser.
- **`Dataset not found`** — restore `data/mancino_daily_sales.csv` from the link
  in `data/SOURCE.md`; the checksum must match.
- **Neural-network convergence warning** — shown beside the affected result; try
  the same configuration again or note it in your write-up.
- **`python` not found on Windows** — use `py -3.12` instead of `python` for the
  setup commands.
- **Training feels slow** — the ensemble fits four models and takes the longest
  (roughly half a minute on the reference machine); a progress message is shown.

## Reference environment

Verified on Linux (dev container, Ubuntu 24.04) with Python 3.12.3,
scikit-learn 1.8.0, NumPy 2.3.5, pandas 2.2.3, Streamlit 1.66.1.
