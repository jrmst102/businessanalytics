"""
Tests for stylecraft_metrics.py.

Every assertion checks a figure that is printed in Appendix B, or a bound the
appendix's Verification field requires. A failing test means the appendix and
the code have drifted apart; fix the appendix first, then the code.

Run:  python test_stylecraft_metrics.py
"""

import math
import numpy as np
import pandas as pd
import stylecraft_metrics as m

PASS, FAIL = [], []


def check(label, actual, expected, tol=5e-3):
    ok = (abs(actual - expected) <= tol
          if isinstance(expected, float) else actual == expected)
    (PASS if ok else FAIL).append((label, actual, expected))


def raises(label, fn, exc=Exception):
    try:
        fn()
    except exc:
        PASS.append((label, "raised", "raised")); return
    FAIL.append((label, "did not raise", "raise"))


# --------------------------------------------------------------------------
tx = pd.read_csv("appendix_b_practice_transactions.csv", parse_dates=["order_date"])
stores = pd.read_csv("appendix_b_stores.csv")
products = pd.read_csv("appendix_b_products.csv")

# --- the practice file's published invariants -----------------------------
check("practice file: order lines", len(tx), 20)
check("practice file: orders", m.order_count(tx), 12)
check("practice file: customers", m.customer_count(tx), 8)
check("practice file: net revenue", m.net_revenue(tx), 1312.00)
check("practice file: units", m.units_sold(tx), 28)
check("line_revenue recomputes", float((m.line_revenue(tx) - tx["line_revenue"]).abs().max()), 0.0)

# --- B.2 -------------------------------------------------------------------
check("gross sales", m.gross_sales(tx), 1350.00)
check("discount dollars", m.discount_dollars(tx), 38.00)
check("gross - discount = net", m.gross_sales(tx) - m.discount_dollars(tx), 1312.00)
check("contribution", m.contribution(tx), 637.00)
check("contribution margin", m.contribution_margin(tx), 0.4855)
check("contribution margin bounded above by 1", m.contribution_margin(tx) <= 1.0, True)
raises("net_revenue refuses an unresolved column",
       lambda: m.net_revenue(tx.assign(line_revenue=tx["line_revenue"].mask(tx.index == 0))),
       ValueError)

# --- B.3 -------------------------------------------------------------------
check("average order value", m.average_order_value(tx), 109.3333)
check("AOV is NOT the line-grain mean",
      abs(m.average_order_value(tx) - float(tx["line_revenue"].mean())) > 40, True)
dec = m.aov_decomposition(tx)
check("decomposition identity multiplies back",
      dec["units_per_order"] * dec["revenue_per_unit"], dec["aov"])
check("units per order", m.units_per_order(tx), 28 / 12)
check("revenue per customer", m.revenue_per_customer(tx), 164.00)
check("rev/customer = AOV x orders/customer",
      m.average_order_value(tx) * m.orders_per_customer(tx), m.revenue_per_customer(tx))

# store-type decomposition, the figures Appendix B Table B.7 prints
ov = (tx.groupby("order_id", as_index=False)
        .agg(store_id=("store_id", "first"), order_value=("line_revenue", "sum"),
             units=("quantity", "sum"))
        .merge(stores[["store_id", "store_type"]], on="store_id", how="left"))
ov["store_type"] = ov["store_type"].fillna("Digital")
bt = ov.groupby("store_type").agg(orders=("order_id", "size"),
                                  revenue=("order_value", "sum"),
                                  units=("units", "sum"))
check("suburban AOV", bt.loc["Suburban", "revenue"] / bt.loc["Suburban", "orders"], 220.00)
check("urban AOV", bt.loc["Urban", "revenue"] / bt.loc["Urban", "orders"], 78.00)

# --- B.4 -------------------------------------------------------------------
check("repeat-order share", m.repeat_order_share(tx), 4 / 12)

# Chapter 3's eighteen-order preview: three correct definitions, three answers
ch3 = pd.DataFrame({
    "order_id": [f"X{i:02d}" for i in range(18)],
    "customer_id": ["C01", "C01", "C01", "C02", "C02", "C03", "C04", "C04", "C04",
                    "C05", "C06", "C06", "C07", "C08", "C08", "C09", "C10", "C10"],
    "order_date": pd.to_datetime([
        "2024-08-10", "2025-09-14", "2026-02-02", "2024-11-05", "2025-01-20",
        "2025-10-03", "2025-08-19", "2025-12-24", "2026-05-30", "2024-09-01",
        "2026-01-15", "2026-01-28", "2025-11-11", "2024-07-22", "2026-04-10",
        "2026-06-06", "2025-02-14", "2025-05-02"]),
    "channel": ["Store", "Store", "Online", "Online", "Online", "Store", "Online",
                "Store", "App", "Store", "Store", "Store", "Online", "Store",
                "Store", "App", "Store", "Store"]})
kw = dict(window_start=pd.Timestamp("2025-07-01"),
          analysis_date=pd.Timestamp("2026-06-30"))
check("repeat rate, lifetime", m.repeat_purchase_rate(ch3, variant="lifetime", **kw), 0.60)
check("repeat rate, trailing 12m", m.repeat_purchase_rate(ch3, variant="t12m", **kw), 0.4286)
check("repeat rate, store only", m.repeat_purchase_rate(ch3, variant="store", **kw), 0.20)
raises("repeat rate refuses an unnamed variant",
       lambda: m.repeat_purchase_rate(ch3, variant="whatever", **kw), ValueError)
for v in ("lifetime", "t12m", "store"):
    r = m.repeat_purchase_rate(ch3, variant=v, **kw)
    check(f"repeat rate bounded [0,1] ({v})", 0.0 <= r <= 1.0, True)

# --- B.5: Chapter 1's four campaigns --------------------------------------
camp = pd.DataFrame({
    "campaign": ["New Arrivals", "Loyalty Offer", "Clearance", "Welcome Series"],
    "impressions": [52000, 41000, 68000, 75000], "clicks": [2860, 2540, 3400, 3000],
    "conversions": [310, 420, 390, 250], "revenue": [27900, 33600, 23400, 17500],
    "ad_spend": [1800, 1200, 9500, 5200], "margin_rate": [0.55, 0.32, 0.18, 0.50]})
check("pooled CTR", m.click_through_rate(camp["clicks"].sum(), camp["impressions"].sum()), 0.0500)
check("pooled post-click conversion",
      m.post_click_conversion_rate(camp["conversions"].sum(), camp["clicks"].sum()), 0.1161)
check("pooled ROAS", m.roas(camp["revenue"].sum(), camp["ad_spend"].sum()), 5.7853)
check("averaged ROAS differs from pooled by more than 6x",
      float((camp["revenue"] / camp["ad_spend"]).mean()) - 5.7853 > 6.0, True)
check("Clearance ROAS", m.roas(23400, 9500), 2.4632)
check("Clearance destroys contribution",
      m.net_contribution_after_ad_spend(23400, 0.18, 9500), -5288.0)
check("CPC undefined over zero clicks", math.isnan(m.cost_per_click(100, 0)), True)
check("CPM, Clearance", m.cpm(9500, 68000), 139.7059)
for _, c in camp.iterrows():
    r = m.click_through_rate(c["clicks"], c["impressions"])
    check(f"CTR bounded [0,1] ({c['campaign']})", 0.0 <= r <= 1.0, True)

# --- B.6 -------------------------------------------------------------------
send = dict(sent=10_000, bounced=400, delivered=9_600,
            unique_opens=2_688, unique_clicks=384, unsubscribes=48)
check("delivery rate", m.engagement_rate(send["delivered"], base=send["sent"], base_name="sent"), 0.96)
check("open rate on delivered",
      m.engagement_rate(send["unique_opens"], base=send["delivered"], base_name="delivered"), 0.28)
check("open rate on sent",
      m.engagement_rate(send["unique_opens"], base=send["sent"], base_name="sent"), 0.2688)
check("click-to-open rate",
      m.engagement_rate(send["unique_clicks"], base=send["unique_opens"], base_name="unique_opens"), 0.1429)
raises("engagement rate refuses an unnamed base",
       lambda: m.engagement_rate(1, base=2, base_name="guess"), ValueError)

# --- B.7 -------------------------------------------------------------------
f = m.funnel_rates([("Sessions", 40_000), ("Product views", 12_000),
                    ("Carts", 3_000), ("Orders", 1_200)])
check("funnel: step, carts to orders", float(f.loc[3, "step"]), 0.40)
check("funnel: cumulative", float(f.loc[3, "cumulative"]), 0.03)
check("funnel: steps multiply to cumulative",
      float(f.loc[1:, "step"].prod()), float(f.loc[3, "cumulative"]))
check("funnel: drop-off and step sum to 1",
      float(f.loc[3, "step"] + f.loc[3, "dropoff"]), 1.0)
raises("funnel refuses a stage larger than the one above it",
       lambda: m.funnel_rates([("A", 10), ("B", 20)]), ValueError)

# --- B.9 -------------------------------------------------------------------
actual = np.array([248.0, 96.0, 117.0, 84.0, 76.0, 68.0, 88.0, 93.0])
pred = np.array([210.0, 110.0, 130.0, 80.0, 95.0, 60.0, 92.0, 105.0])
check("MAE", m.mae(actual, pred), 14.00)
check("RMSE", m.rmse(actual, pred), 17.3565)
check("RMSE >= MAE", m.rmse(actual, pred) >= m.mae(actual, pred), True)
check("mean-baseline MAE", m.mae(actual, np.repeat(actual.mean(), len(actual))), 36.875)
check("margin over baseline, loss metric, is positive when the model wins",
      m.margin_over_baseline(m.mae(actual, pred),
                             m.mae(actual, np.repeat(actual.mean(), len(actual))),
                             direction="loss"), 22.875)
check("margin over baseline, gain metric, is positive when the model wins",
      m.margin_over_baseline(0.34, 0.28, direction="gain"), 0.06)
check("a losing candidate produces a negative margin under both conventions",
      m.margin_over_baseline(50.0, 36.875, direction="loss") < 0
      and m.margin_over_baseline(0.22, 0.28, direction="gain") < 0, True)
raises("margin over baseline refuses an unnamed direction",
       lambda: m.margin_over_baseline(1, 2, direction="whichever"), ValueError)

# --- B.10: Chapter 9's ten-customer miniature -----------------------------
p_ = [0.82, 0.61, 0.55, 0.52, 0.44, 0.33, 0.24, 0.18, 0.11, 0.06]
y_ = [1, 1, 0, 0, 1, 0, 0, 0, 0, 0]
check("threshold from costs", m.decision_threshold(12.0, 40.0), 0.30)
a = m.classification_metrics(y_, p_, 0.50)
b = m.classification_metrics(y_, p_, 0.30)
check("base rate", a["base_rate"], 0.30)
for k, v in dict(tp=2, fp=2, fn=1, tn=5).items():
    check(f"matrix at 0.50: {k}", a[k], v)
for k, v in dict(tp=3, fp=3, fn=0, tn=4).items():
    check(f"matrix at 0.30: {k}", b[k], v)
check("accuracy at 0.50", a["accuracy"], 0.70)
check("accuracy at 0.30", b["accuracy"], 0.70)
check("accuracy cannot tell the two policies apart", a["accuracy"], b["accuracy"])
check("precision at 0.50", a["precision"], 0.50)
check("recall at 0.50", a["recall"], 0.6667)
check("F1 at 0.50", a["f1"], 0.5714)
check("recall at 0.30", b["recall"], 1.00)
check("recall + FNR = 1", b["recall"] + b["fnr"], 1.0)
check("net value at 0.50", m.expected_net_value(y_, p_, 0.50, 12.0, 40.0), 32.0)
check("net value at 0.30", m.expected_net_value(y_, p_, 0.30, 12.0, 40.0), 48.0)
check("precision undefined when nothing is treated",
      math.isnan(m.classification_metrics(y_, p_, 0.99)["precision"]), True)
g = m.lift_and_gains(y_, p_)
check("top decile lift", float(g.loc[1, "lift"]), 3.3333)
check("top two deciles capture", float(g.loc[2, "cum_capture"]), 0.6667)
check("gains reach 1.0", float(g["cum_capture"].iloc[-1]), 1.0)

# --- B.11 ------------------------------------------------------------------
calm_a = [9800, 9400, 10100, 11200, 12600, 14100, 9500]
calm_f = [9600, 9200, 9900, 10800, 12200, 13500, 9300]
storm_a = [9800, 400, 10100, 11200, 12600, 14100, 9500]
storm_f = [9600, 7600, 9900, 10800, 12200, 13500, 9300]
check("calm week MAPE", m.mape(calm_a, calm_f), 2.7508)
check("storm week MAPE explodes", m.mape(storm_a, storm_f), 259.5897)
check("storm week MAE moves honestly", m.mae(storm_a, storm_f), 1314.2857)
check("mape_report prints its minimum denominator",
      m.mape_report(storm_a, storm_f)["min_denominator"], 400.0)
check("forecast bias, signed", m.forecast_bias(calm_a, calm_f), 314.2857)
raises("MAPE refuses a zero denominator",
       lambda: m.mape([0, 100], [50, 100]), ValueError)

# --- B.12: StyleCraft's Drop Alert test -----------------------------------
t_x, t_n, c_x, c_n = 390, 5000, 300, 5000
check("absolute lift, percentage points", absolute := m.absolute_lift(t_x, t_n, c_x, c_n) * 100, 1.80)
check("relative lift", m.relative_lift(t_x, t_n, c_x, c_n), 0.30)
check("relative and absolute are different units", abs(0.30 - absolute) > 1.0, True)
check("SE of the difference, unpooled",
      m.se_difference_unpooled(t_x, t_n, c_x, c_n) * 100, 0.5066)
check("break-even lift at dose 1", m.break_even_lift(0.12, 1, 28.00) * 100, 0.4286)
check("break-even lift doubles at dose 2", m.break_even_lift(0.12, 2, 28.00) * 100, 0.8571)
check("net per 1,000 at the point estimate",
      m.net_contribution_per_1000(0.018, 28.00, 0.12, 1), 384.00)
check("net per 1,000 at the interval's low edge",
      m.net_contribution_per_1000(0.0081, 28.00, 0.12, 1), 106.80)
check("net per 1,000 at the interval's high edge",
      m.net_contribution_per_1000(0.0279, 28.00, 0.12, 1), 661.20)
check("the interval clears break-even at dose 1", 0.0081 > m.break_even_lift(0.12, 1, 28.00), True)
check("the interval does NOT clear break-even at dose 2",
      0.0081 < m.break_even_lift(0.12, 2, 28.00), True)

# --------------------------------------------------------------------------
if __name__ == "__main__":
    for label, actual, expected in FAIL:
        print(f"FAIL  {label:52} got {actual!r}, expected {expected!r}")
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    raise SystemExit(1 if FAIL else 0)
