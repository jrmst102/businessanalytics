# Dataset source and snapshot record

| Item | Value |
|---|---|
| File | `mancino_daily_sales.csv` (this folder) |
| Origin | <https://github.com/jrmst102/mancino/blob/main/data/v1_2025-11-01/mancino_daily_sales.csv> |
| Raw URL used for packaging | `https://raw.githubusercontent.com/jrmst102/mancino/main/data/v1_2025-11-01/mancino_daily_sales.csv` |
| Dataset version | `v1_2025-11-01` |
| Retrieved | 2026-10-22 |
| SHA-256 | `8441fb2df62432120396f81f3816f12bbd40007f03bb99fc0c1a79cfc1e028c1` |
| Rows | 22,875 (plus header) |
| Stores | 5 (`1`-`5`) |
| Categories | 15 |
| Date range | 2025-01-01 to 2025-11-01 |
| Columns | `date, store_id, category, avg_price, units_sold, revenue, day_of_week` |
| License | Creative Commons CC BY 4.0, per the Mancino repository README |
| Attribution | Mancino Market synthetic grocery dataset, maintained by Dr. Jose Mendoza (<https://github.com/jrmst102/mancino>) |

The data are **fully synthetic** teaching data describing five fictional Manhattan stores.

The checksum above is also stored as `DATA_SHA256` in `models.py`; `tests/test_engine.py`
fails if the bundled file is changed. Do not replace this snapshot with a later remote file
without updating this record, the constant, and re-running the notebook-parity tests.
