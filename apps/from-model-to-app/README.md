# Business Analytics in Action: From Model to App

A teaching dashboard for the Mancino regression unit. Explore the dataset,
choose **one** classroom model (KNN, regression tree, random forest, neural
network, or the averaging ensemble) with its classroom parameter, train it,
read its four test metrics (R², MSE, RMSE, MAPE), then type a store, category
and date to get one prediction from the same fitted model.

The interface is a Node.js web app; every number it shows comes from the
Python classroom engine (`models.py`), served through a small engine API.
The dataset (Mancino Market) is **synthetic** teaching data. See `data/SOURCE.md`.

## What is in this folder

| File | Role |
|---|---|
| `models.py` | The classroom engine: preprocessing, model constructors, fitting, metrics and prediction, extracted from the Mancino notebooks. Readable without knowing the web stack. |
| `inputs.py` | Validation of the typed store, category, date and optional actual units. |
| `engine_api.py` | Python API around the engine (Flask): dataset, train, predict, code-from-class. Keeps one fitted model per browser session. Defines no models. |
| `server/` | Node.js web server (Express) and the three-tab dashboard (plain HTML/CSS/JS). Proxies `/api/*` to the engine API; contains no analytics logic. |
| `launch.py` | Starts both processes locally and opens your browser. |
| `run_engine.py` | Fits one configuration from the command line (developer convenience). |
| `requirements.txt` | Pinned, tested Python dependencies. `server/package.json` pins the Node side. |
| `Dockerfile`, `start.sh` | Hosted deployment image (used by DigitalOcean; not needed locally). |
| `NOTEBOOK_MAP.md` | Which notebook cell became which function, and every adaptation made. |
| `data/mancino_daily_sales.csv`, `data/SOURCE.md` | Approved offline data snapshot and its provenance. |
| `tests/` | Model-parity, metric, input and interface checks. |

## First-time setup

You need **Python 3.12** (3.11–3.13 should also work; 3.12 is the verified
version) and **Node.js 18 or newer** (<https://nodejs.org>). Run the commands
from a terminal opened in this folder (`apps/from-model-to-app`).

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install --prefix server
```

If PowerShell refuses to run the activation script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt
with `.\.venv\Scripts\activate.bat`.

**macOS / Linux (Terminal)**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm install --prefix server
```

Installation needs the internet once. After that the app runs offline: the data
file and all web assets are bundled. You do not reinstall dependencies on later
launches — just activate the environment and launch.

## Launch the dashboard

With the virtual environment activated:

```bash
python launch.py
```

The launcher starts the engine API on port 8000 and the dashboard on
`http://localhost:8080` (this computer only), opens your default browser, and
prints the link in case the browser does not open. Stop it with `Ctrl+C` in the
terminal. It works from any working directory, e.g. `python path/to/launch.py`.

Options: `python launch.py --port 8090 --engine-port 8010` if the defaults are
busy; `--no-browser` to only print the link.

**Manual fallback** if the launcher cannot be used (two terminals):

```bash
python engine_api.py --port 8000
node server/server.js            # uses PORT=8080 and ENGINE_URL=http://127.0.0.1:8000
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
Each browser session has its own fitted model.

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
direct classroom implementation on the same development data (about a minute on
the reference machine). For a quick check, run
`python -m pytest tests/test_engine.py tests/test_inputs.py tests/test_api.py -q`.

## Hosted copy (instructor only)

Students who cannot install Python/Node can use the hosted copy instead. The
repository root contains `.do/app.yaml`, a DigitalOcean App Platform spec that
builds `Dockerfile` here (one container running both processes, health check on
`/healthz`, port 8080). Create the app in the DigitalOcean console from this
GitHub repo — or update an existing app via Settings → App Spec — and give
students the resulting `...ondigitalocean.app` URL. Each browser session trains
its own model; all students share the instance's CPU.

## Troubleshooting

- **`Missing Python packages: ...`** — the virtual environment is not active or
  the install step was skipped. Activate it and run
  `python -m pip install -r requirements.txt`.
- **`Node.js was not found`** — install Node.js 18+ from <https://nodejs.org>
  and reopen the terminal.
- **`The web server packages are not installed yet`** — run
  `npm install --prefix server` once.
- **`Port ... is already in use`** — another dashboard is still running. Close
  it or use `python launch.py --port 8090 --engine-port 8010`.
- **Browser did not open** — copy the printed `http://localhost:...` link into
  your browser.
- **"The engine API is not reachable" in the page** — start the app with
  `python launch.py` (it runs both required processes).
- **`Dataset not found`** — restore `data/mancino_daily_sales.csv` from the link
  in `data/SOURCE.md`; the checksum must match.
- **Neural-network convergence warning** — shown beside the affected result; try
  the same configuration again or note it in your write-up.
- **`python` not found on Windows** — use `py -3.12` instead of `python` for the
  setup commands.
- **Training feels slow** — the ensemble fits four models and takes the longest
  (several seconds on the reference machine); a status message is shown.

## Reference environment

Verified on Linux (dev container, Ubuntu 24.04) with Python 3.12.3,
scikit-learn 1.8.0, NumPy 2.3.5, pandas 2.2.3, Flask 3.1.2, waitress 3.0.2,
Node.js 24 (any ≥18 works), Express 4.
