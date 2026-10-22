# Business Analytics in Action: From Model to App

A local, browser-based teaching dashboard that turns the Mancino regression notebooks into a
working decision-support application. Explore the dataset, train the classroom models (KNN,
regression trees, random forests, neural networks, two averaging ensembles) against a mean-sales
baseline, compare validation results, finalize one model on the test dates, and type your own
store/category/date to get a prediction with clearly labeled metrics.

The dataset (Mancino Market) is **synthetic** teaching data. See `data/SOURCE.md`.

## What is in this folder

| File | Role |
|---|---|
| `models.py` | The classroom engine: the code from `Mancino_Regression_Final.ipynb`, organized as functions in the notebook's order. Readable without knowing Streamlit. |
| `app.py` | The dashboard (Streamlit). Rendering, forms, session state. Calls `models.py`; defines no models. |
| `inputs.py` | Validation of the typed store, category, date and optional actual units. |
| `launch.py` | Starts the local dashboard and opens your browser. |
| `run_engine.py` | Runs the whole classroom workflow from the command line, without the dashboard. |
| `requirements.txt` | Pinned, tested dependencies. |
| `NOTEBOOK_MAP.md` | Which notebook cell became which function, and every adaptation made. |
| `VERIFICATION.md` | Parity, state, input and launch evidence. |
| `data/mancino_daily_sales.csv`, `data/SOURCE.md` | Approved offline data snapshot and its provenance. |
| `tests/` | Notebook-parity gate, engine/evaluation checks, input checks, dashboard smoke test. |

## First-time setup

You need Python 3.12 (3.11-3.13 should also work; 3.12 is the verified version). Run the
commands from a terminal opened in this folder (`apps/from-model-to-app`).

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell refuses to run the activation script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt with
`.\.venv\Scripts\activate.bat`.

**macOS / Linux (Terminal)**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Installation needs the internet once. After that the app runs offline: the data file is bundled.

## Launch the dashboard

With the virtual environment activated:

```bash
python launch.py
```

The launcher starts the app on `http://localhost:8501` (this computer only), opens your default
browser, and prints the link in case the browser does not open. Stop it with `Ctrl+C` in the
terminal. It works from any working directory, e.g. `python path/to/launch.py`.

Options: `python launch.py --port 8600` if 8501 is busy; `--no-browser` to only print the link.

**Manual fallback** if the launcher cannot be used:

```bash
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Note: viewing this folder on GitHub displays the code; it does not run the app. Clone or
download the repository and follow the steps above.

## Using the app

1. **A. Explore the dataset** - source, variables, fixed training/validation/test dates, a
   filterable table and charts. The "view filters" only change what you see.
2. **B. Choose and run models** - pick a family and its classroom preset, press
   **Train and evaluate**. **Run classroom comparison** evaluates the exact 15 candidates of the
   final notebook. "Code from class" shows the engine code that was just used.
3. **C. Compare and select** - validation leaderboard, train-vs-validation chart, the
   validation-best recommendation, and a form to freeze the specification to finalize (you may
   choose another completed candidate with a recorded managerial reason).
4. **D. Type inputs and predict** - type a store ID, category and date (`YYYY-MM-DD`); optionally
   the actual units. The app validates the entries, builds the four classroom features and calls
   the fitted pipeline's `.predict()`. Metrics shown are the model's historical validation or test
   metrics; they do not measure the accuracy of your new prediction.
5. **E. Final evaluation** - refit the frozen specification on training + validation, score it
   once on the test dates beside a refitted baseline, read the diagnostics and the
   result-driven managerial interpretation.

Training only happens when you press a button. Typing inputs, switching tabs or changing view
filters never retrains anything. Refitting a preset invalidates dependent ensembles and marks a
finalized result built on it as superseded; the app never overwrites test results silently.

## The models (classroom settings)

| Choice | scikit-learn class | Student choice | Fixed settings |
|---|---|---|---|
| Mean baseline | `DummyRegressor` | none | `strategy='mean'` |
| KNN | `KNeighborsRegressor` | k = 5, 15, 50 | `weights='uniform'`, day of year standardized |
| Regression tree | `DecisionTreeRegressor` | depth 3, 6, 12 | `min_samples_leaf=30`, `random_state=42` |
| Random forest | `RandomForestRegressor` | 50, 100, 200 trees | `max_depth=12`, `min_samples_leaf=30`, `max_features=0.8`, `bootstrap=True`, `random_state=42` |
| Neural network | `MLPRegressor` in `TransformedTargetRegressor` | (16,), (32,), (32, 16) | ReLU, Adam, `alpha=0.01`, `batch_size=256`, `max_iter=300`, early stopping (15%, patience 20), target standardized |
| Ensembles | `VotingRegressor` | equal or weights [1, 1, 2, 2] | four family winners in order KNN, tree, forest, network |

Features: `store_id`, `category`, `weekday`, `day_of_year` (the last two derived from the date).
Target: `units_sold`. `revenue` and `avg_price` are shown but never used as predictors.
Split: first 60% of dates train, next 20% validate, last 20% test (2025-01-01 to 07-02,
07-03 to 09-01, 09-02 to 11-01).

## Running the tests

```bash
python -m pytest tests -q
```

`tests/test_notebook_parity.py` executes the reference notebook's code cells from
`../../notebooks/Mancino_Regression_Final.ipynb` and compares every number against the engine.
The full suite takes about one and a half minutes on the reference machine.

## Troubleshooting

- **`Missing Python packages: ...`** - the virtual environment is not active or the install step
  was skipped. Activate it and run `python -m pip install -r requirements.txt`.
- **`Port 8501 is already in use`** - another dashboard is still running. Close it or use
  `python launch.py --port 8600`.
- **Browser did not open** - copy the printed `http://localhost:...` link into your browser.
- **`Dataset not found`** - restore `data/mancino_daily_sales.csv` from the link in
  `data/SOURCE.md`; the checksum must match.
- **Neural-network convergence warning** - shown beside the network result; the notebook treats
  it as a diagnostic to address before opening the test set.
- **`python` not found on Windows** - use `py -3.12` instead of `python` for the setup commands.
- A blank page for a long time: the first load reads the CSV; fitting the full comparison takes
  under a minute on the reference laptop. Progress is shown in tab B.

## Reference environment

Verified on Linux (dev container, Ubuntu 24.04) with Python 3.12.3, scikit-learn 1.8.0,
NumPy 2.3.5, pandas 2.2.3, matplotlib 3.10.9, Streamlit 1.66.1. Windows and macOS launch checks
are listed as pending in `VERIFICATION.md`.
