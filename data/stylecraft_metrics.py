"""
StyleCraft metric functions — Appendix B, Version 1.0, August 2026.

Each function implements one Appendix B entry and names it. The functions do not
restate a definition; they implement the cataloged one, which is what makes the
tests in test_stylecraft_metrics.py meaningful. Where an entry admits variants,
the variant is a named argument with no default, so that the caller has to choose
and the choice appears at the call site.

A rate over an empty base returns NaN, never zero and never infinity.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NA = float("nan")


def _safe_div(num, den):
    """A rate over an empty base is undefined (Appendix B, Section B.1.4)."""
    den = float(den)
    return NA if den == 0 else float(num) / den


# ---------------------------------------------------------------------------
# B.2  Revenue, margin, and volume
# ---------------------------------------------------------------------------
def line_revenue(tx: pd.DataFrame) -> pd.Series:
    """Entry B.2.1. quantity x unit_price x (1 - discount_pct), recomputed."""
    return (tx["quantity"] * tx["unit_price"] * (1 - tx["discount_pct"])).round(2)


def gross_sales(tx: pd.DataFrame) -> float:
    """Entry B.2.2. Catalog value before discount."""
    return float((tx["quantity"] * tx["unit_price"]).sum())


def discount_dollars(tx: pd.DataFrame) -> float:
    """Entry B.2.3. Gross sales less net revenue."""
    return gross_sales(tx) - net_revenue(tx)


def net_revenue(tx: pd.DataFrame) -> float:
    """Entry B.2.4. Sum of line_revenue. Unresolved lines must be resolved first."""
    if tx["line_revenue"].isna().any():
        raise ValueError(
            "unresolved line_revenue: a total over a column containing missing "
            "values is the revenue of the resolved part wearing the whole label")
    return float(tx["line_revenue"].sum())


def contribution(tx: pd.DataFrame) -> float:
    """Entry B.2.6. Net revenue less variable cost, before the fixed footprint."""
    return float((tx["line_revenue"] - tx["line_cost"]).sum())


def contribution_margin(tx: pd.DataFrame) -> float:
    """Entry B.2.7. A pooled ratio, never the mean of line-level margins."""
    return _safe_div(contribution(tx), net_revenue(tx))


def units_sold(tx: pd.DataFrame) -> int:
    """Entry B.2.9. Sum of quantity, not a count of lines."""
    return int(tx["quantity"].sum())


def order_count(tx: pd.DataFrame) -> int:
    """Entry B.2.10. Distinct order_id — a distinct count is not a row count."""
    return int(tx["order_id"].nunique())


def customer_count(tx: pd.DataFrame) -> int:
    """Entry B.2.11. Distinct customer_id, excluding unresolved keys explicitly."""
    if tx["customer_id"].isna().any():
        raise ValueError("lines without a customer_id cannot be counted; resolve them")
    return int(tx["customer_id"].nunique())


# ---------------------------------------------------------------------------
# B.3  Basket and customer value
# ---------------------------------------------------------------------------
def average_order_value(tx: pd.DataFrame) -> float:
    """Entry B.3.1. Revenue over DISTINCT ORDERS. Never AVG at line grain."""
    return _safe_div(net_revenue(tx), order_count(tx))


def units_per_order(tx: pd.DataFrame) -> float:
    """Entry B.3.3. The volume factor of the decomposition identity."""
    return _safe_div(units_sold(tx), order_count(tx))


def revenue_per_unit(tx: pd.DataFrame) -> float:
    """Entry B.3.4. The price factor. Denominator is units, not lines or orders."""
    return _safe_div(net_revenue(tx), units_sold(tx))


def aov_decomposition(tx: pd.DataFrame) -> dict:
    """Entry B.3.5. Returns the two factors and asserts they multiply back."""
    upo, rpu, aov = units_per_order(tx), revenue_per_unit(tx), average_order_value(tx)
    if not np.isclose(upo * rpu, aov):
        raise AssertionError("the decomposition identity does not multiply back")
    return {"aov": aov, "units_per_order": upo, "revenue_per_unit": rpu}


def revenue_per_customer(tx: pd.DataFrame) -> float:
    """Entry B.3.6. A customer-grain quantity; not interchangeable with AOV."""
    return _safe_div(net_revenue(tx), customer_count(tx))


def orders_per_customer(tx: pd.DataFrame) -> float:
    """Entry B.3.7. The frequency factor between AOV and revenue per customer."""
    return _safe_div(order_count(tx), customer_count(tx))


# ---------------------------------------------------------------------------
# B.4  Retention
# ---------------------------------------------------------------------------
def repeat_purchase_rate(tx: pd.DataFrame, *, window_start, analysis_date,
                         variant: str) -> float:
    """
    Entry B.4.1. Three cataloged definitions; the variant must be named.

    variant='t12m'      trailing window, all channels  (the headline definition)
    variant='lifetime'  all history to the analysis date, all channels
    variant='store'     trailing window, store channel only
    """
    if variant not in {"t12m", "lifetime", "store"}:
        raise ValueError("name the variant: 't12m', 'lifetime', or 'store'")
    orders = tx.drop_duplicates("order_id")
    if variant == "lifetime":
        pop = orders[orders["order_date"] <= analysis_date]
    else:
        pop = orders[orders["order_date"].between(window_start, analysis_date)]
        if variant == "store":
            pop = pop[pop["channel"] == "Store"]
    counts = pop.groupby("customer_id").size()
    return _safe_div((counts >= 2).sum(), len(counts))


def repeat_order_share(tx: pd.DataFrame) -> float:
    """Entry B.4.2. An ORDER-grain measure. Not the share of customers who returned."""
    orders = (tx.groupby("order_id", as_index=False)
                .agg(customer_id=("customer_id", "first"),
                     order_date=("order_date", "min")))
    first = orders.groupby("customer_id")["order_date"].transform("min")
    return _safe_div(int((orders["order_date"] > first).sum()), len(orders))


# ---------------------------------------------------------------------------
# B.5  Acquisition, media, and campaign
# ---------------------------------------------------------------------------
def click_through_rate(clicks, impressions) -> float:
    """Entry B.5.3. Pool the totals; never average campaign-level rates."""
    return _safe_div(clicks, impressions)


def post_click_conversion_rate(conversions, clicks) -> float:
    """Entry B.5.4. Named for its denominator, so the definition travels."""
    return _safe_div(conversions, clicks)


def cost_per_click(spend, clicks) -> float:
    """Entry B.5.5."""
    return _safe_div(spend, clicks)


def cpm(spend, impressions) -> float:
    """Entry B.5.6. Cost per thousand impressions."""
    return _safe_div(spend, impressions) * 1000 if impressions else NA


def roas(revenue, ad_spend) -> float:
    """Entry B.5.9. Attributed, not incremental. Read beside margin."""
    return _safe_div(revenue, ad_spend)


def net_contribution_after_ad_spend(revenue, margin_rate, ad_spend) -> float:
    """Entry B.2.8. The correction to ROAS that margin supplies."""
    return float(revenue) * float(margin_rate) - float(ad_spend)


# ---------------------------------------------------------------------------
# B.6  CRM and engagement
# ---------------------------------------------------------------------------
def engagement_rate(numerator, *, base: int, base_name: str) -> float:
    """
    Entries B.6.1-B.6.6. The base must be named at the call site, because
    'open rate' denotes three different quantities depending on it.
    """
    if base_name not in {"sent", "delivered", "unique_opens"}:
        raise ValueError("name the base: 'sent', 'delivered', or 'unique_opens'")
    return _safe_div(numerator, base)


# ---------------------------------------------------------------------------
# B.7  Funnel
# ---------------------------------------------------------------------------
def funnel_rates(stages: list[tuple[str, int]]) -> pd.DataFrame:
    """
    Entries B.7.2-B.7.4. Step, drop-off, and cumulative rates for one funnel.
    Raises if the counts do not decrease, which means a stage is counting a
    different unit.
    """
    counts = [n for _, n in stages]
    if any(b > a for a, b in zip(counts, counts[1:])):
        raise ValueError("a later stage exceeds an earlier one: the stages are "
                         "not counting the same unit")
    top = counts[0]
    out = []
    for i, (name, n) in enumerate(stages):
        step = NA if i == 0 else _safe_div(n, counts[i - 1])
        out.append({"stage": name, "count": n, "step": step,
                    "dropoff": NA if i == 0 else 1 - step,
                    "cumulative": _safe_div(n, top)})
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# B.9 / B.10  Model evaluation
# ---------------------------------------------------------------------------
def mae(actual, predicted) -> float:
    """Entry B.9.6."""
    return float(np.abs(np.asarray(actual) - np.asarray(predicted)).mean())


def rmse(actual, predicted) -> float:
    """Entry B.9.7. Always at least the MAE on the same predictions."""
    return float(np.sqrt(((np.asarray(actual) - np.asarray(predicted)) ** 2).mean()))


def margin_over_baseline(candidate, baseline, *, direction: str) -> float:
    """
    Entry B.9.10. A signed difference from baseline, always oriented so that a
    positive value means the candidate is better. The direction must be named,
    because half the metrics in this dictionary improve downward.

    direction='loss'  MAE, RMSE, MSE, MAPE     -> baseline - candidate
    direction='gain'  capture, AUC, lift, net  -> candidate - baseline
    """
    if direction not in {"loss", "gain"}:
        raise ValueError("name the direction: 'loss' or 'gain'")
    return (float(baseline) - float(candidate) if direction == "loss"
            else float(candidate) - float(baseline))


def confusion_counts(y_true, scores, threshold: float) -> dict:
    """Entry B.10.2. The four counts, asserted to sum to the evaluated set."""
    y = np.asarray(y_true).astype(int)
    pred = (np.asarray(scores) >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    if tp + fp + fn + tn != len(y):
        raise AssertionError("the matrix must sum to the evaluated set")
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "treated": tp + fp}


def classification_metrics(y_true, scores, threshold: float) -> dict:
    """Entries B.10.3-B.10.7, all computed at one stated threshold."""
    c = confusion_counts(y_true, scores, threshold)
    prec = _safe_div(c["tp"], c["treated"])
    rec = _safe_div(c["tp"], c["tp"] + c["fn"])
    f1 = NA if (np.isnan(prec) or np.isnan(rec) or prec + rec == 0) \
        else 2 * prec * rec / (prec + rec)
    return {**c, "threshold": threshold,
            "base_rate": float(np.mean(np.asarray(y_true))),
            "accuracy": _safe_div(c["tp"] + c["tn"], len(y_true)),
            "precision": prec, "recall": rec, "f1": f1,
            "fpr": _safe_div(c["fp"], c["fp"] + c["tn"]),
            "fnr": _safe_div(c["fn"], c["fn"] + c["tp"])}


def decision_threshold(cost: float, benefit: float) -> float:
    """Entry B.10.10. Derived from costs, never taken from a software default."""
    return _safe_div(cost, benefit)


def expected_net_value(y_true, scores, threshold, cost, benefit,
                       per_thousand: bool = False) -> float:
    """Entry B.10.12."""
    c = confusion_counts(y_true, scores, threshold)
    net = c["tp"] * benefit - c["treated"] * cost
    return 1000.0 * net / len(y_true) if per_thousand else float(net)


def lift_and_gains(y_true, scores, bins: int = 10) -> pd.DataFrame:
    """
    Entries B.10.13-B.10.14. Ranks before cutting, so the groups are equal in
    size regardless of ties, which is what makes lift comparable across deciles.
    """
    df = pd.DataFrame({"y": np.asarray(y_true).astype(int),
                       "p": np.asarray(scores, dtype=float)})
    df = df.sort_values("p", ascending=False, kind="mergesort").reset_index(drop=True)
    df["bin"] = pd.qcut(df.index.to_series().rank(method="first"),
                        bins, labels=range(1, bins + 1)).astype(int)
    base = df["y"].mean()
    g = df.groupby("bin").agg(cases=("y", "size"), positives=("y", "sum"),
                              rate=("y", "mean"))
    g["lift"] = g["rate"] / base
    g["cum_capture"] = g["positives"].cumsum() / g["positives"].sum()
    g["cum_file"] = g["cases"].cumsum() / g["cases"].sum()
    if not np.isclose(g["cum_capture"].iloc[-1], 1.0):
        raise AssertionError("cumulative gains must reach 1.0 at the whole file")
    return g


# ---------------------------------------------------------------------------
# B.11  Forecast evaluation
# ---------------------------------------------------------------------------
def forecast_bias(actual, forecast) -> float:
    """Entry B.11.2. Mean signed error, actual minus forecast: positive = undershoot."""
    return float((np.asarray(actual) - np.asarray(forecast)).mean())


def mape(actual, forecast) -> float:
    """
    Entry B.11.3. Refuses to return a number over a non-positive denominator,
    because the denominator, not the forecast, produces the failure.
    """
    a = np.asarray(actual, dtype=float)
    if not (a > 0).all():
        raise ValueError("MAPE is undefined at zero and unstable near it: "
                         "report MAE and investigate the small denominators")
    return float((np.abs(a - np.asarray(forecast)) / a).mean() * 100)


def mape_report(actual, forecast) -> dict:
    """Entry B.11.3's verification: no MAPE is quoted without its denominator."""
    a = pd.Series(np.asarray(actual, dtype=float))
    return {"mae": mae(actual, forecast), "mape": mape(actual, forecast),
            "min_denominator": float(a.min()),
            "thin_periods": int((a < 0.25 * a.median()).sum())}


# ---------------------------------------------------------------------------
# B.12  Experiments
# ---------------------------------------------------------------------------
def absolute_lift(t_x, t_n, c_x, c_n) -> float:
    """Entry B.12.2. In percentage points when the metric is a rate."""
    return _safe_div(t_x, t_n) - _safe_div(c_x, c_n)


def relative_lift(t_x, t_n, c_x, c_n) -> float:
    """Entry B.12.3. A percentage change, not percentage points."""
    return _safe_div(absolute_lift(t_x, t_n, c_x, c_n), _safe_div(c_x, c_n))


def se_difference_unpooled(t_x, t_n, c_x, c_n) -> float:
    """Entry B.12.4. Uses each arm's own rate; this is the interval's SE."""
    p_t, p_c = _safe_div(t_x, t_n), _safe_div(c_x, c_n)
    return float(np.sqrt(p_c * (1 - p_c) / c_n + p_t * (1 - p_t) / t_n))


def break_even_lift(cost_per_exposure, doses, contribution_per_conversion) -> float:
    """Entry B.12.6. Undefined until the dose is stated."""
    return _safe_div(cost_per_exposure * doses, contribution_per_conversion)


def net_contribution_per_1000(lift, contribution_per_conversion,
                              cost_per_exposure, doses) -> float:
    """Entry B.12.7. Evaluate at both interval edges, not only the estimate."""
    return lift * 1000 * contribution_per_conversion - 1000 * cost_per_exposure * doses
