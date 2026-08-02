"""
Appendix B — worked-example data.

Builds the miniature StyleCraft practice table that Appendix B's worked examples
use, and verifies it against every invariant Appendix A publishes for
practice_transactions.csv:

    20 order lines, 12 orders, 8 customers, $1,312.00 revenue, 28 units,
    AOV $109.33, order O10003 = 88.00 + 84.00 + 76.00 = 248.00,
    10 lines carrying the reserved store_id ONLINE,
    AOV $220.00 suburban against $78.00 urban,
    every unit_price inside the $24-$90 catalog band,
    every discount_pct in [0, 1].

Every figure printed by this script is a figure that appears in Appendix B.
Nothing here is generated randomly; the file is authored and then checked.
"""

import pandas as pd
import numpy as np

# --------------------------------------------------------------------------
# 1. The practice file
# --------------------------------------------------------------------------
# columns match StyleCraft's transactions schema (Dataset Spec 3.4)
COLS = ["order_id", "order_line_id", "customer_id", "product_id", "store_id",
        "channel", "order_date", "quantity", "unit_price", "discount_pct",
        "campaign_id"]

rows = [
    # order,   line,   cust,   product, store,    channel, date,         qty, price, disc, campaign
    ("O10001", "L0001", "C001", "P0104", "S01",    "Store",  "2026-01-14", 1, 54.00, 0.00, None),
    ("O10001", "L0002", "C001", "P0117", "S01",    "Store",  "2026-01-14", 1, 42.00, 0.00, None),
    ("O10002", "L0003", "C003", "P0121", "ONLINE", "Online", "2026-01-22", 2, 45.00, 0.00, "CMP014"),
    ("O10002", "L0004", "C003", "P0133", "ONLINE", "Online", "2026-01-22", 1, 36.00, 0.25, "CMP014"),
    ("O10003", "L0005", "C002", "P0201", "S07",    "Store",  "2026-02-07", 1, 88.00, 0.00, None),
    ("O10003", "L0006", "C002", "P0203", "S07",    "Store",  "2026-02-07", 1, 84.00, 0.00, None),
    ("O10003", "L0007", "C002", "P0142", "S07",    "Store",  "2026-02-07", 1, 76.00, 0.00, None),
    ("O10004", "L0008", "C004", "P0129", "ONLINE", "Online", "2026-02-19", 2, 42.00, 0.00, "CMP014"),
    ("O10005", "L0009", "C001", "P0118", "S02",    "Store",  "2026-03-03", 2, 39.00, 0.00, None),
    ("O10006", "L0010", "C005", "P0205", "ONLINE", "Online", "2026-03-11", 1, 65.00, 0.20, "CMP021"),
    ("O10006", "L0011", "C005", "P0151", "ONLINE", "Online", "2026-03-11", 1, 24.00, 0.00, "CMP021"),
    ("O10007", "L0012", "C002", "P0207", "S07",    "Store",  "2026-03-28", 1, 90.00, 0.00, None),
    ("O10007", "L0013", "C002", "P0136", "S07",    "Store",  "2026-03-28", 1, 62.00, 0.00, None),
    ("O10007", "L0014", "C002", "P0148", "S07",    "Store",  "2026-03-28", 1, 40.00, 0.00, None),
    ("O10008", "L0015", "C006", "P0125", "ONLINE", "Online", "2026-04-09", 2, 34.00, 0.00, None),
    ("O10009", "L0016", "C001", "P0160", "S01",    "Store",  "2026-04-25", 2, 30.00, 0.00, None),
    ("O10010", "L0017", "C003", "P0209", "ONLINE", "Online", "2026-05-06", 1, 80.00, 0.20, "CMP021"),
    ("O10010", "L0018", "C003", "P0113", "ONLINE", "Online", "2026-05-06", 1, 48.00, 0.00, "CMP021"),
    ("O10011", "L0019", "C007", "P0127", "ONLINE", "Online", "2026-05-18", 2, 44.00, 0.00, None),
    ("O10012", "L0020", "C008", "P0131", "ONLINE", "Online", "2026-06-02", 3, 31.00, 0.00, "CMP014"),
]
tx = pd.DataFrame(rows, columns=COLS)
tx["order_date"] = pd.to_datetime(tx["order_date"])
tx["line_revenue"] = (tx["quantity"] * tx["unit_price"]
                      * (1 - tx["discount_pct"])).round(2)
# unit_cost is exactly half of catalog unit_price: a stated, hand-checkable rule
tx["unit_cost"] = (tx["unit_price"] * 0.50).round(2)
tx["line_cost"] = (tx["quantity"] * tx["unit_cost"]).round(2)

# dimension tables
stores = pd.DataFrame([
    ("S01", "SoHo",         "NYC Urban",    "Urban"),
    ("S02", "West Village", "NYC Urban",    "Urban"),
    ("S07", "Greenwich",    "NYC Suburban", "Suburban"),
], columns=["store_id", "store_name", "metro", "store_type"])

customers = pd.DataFrame([
    ("C001", "2024-09-02", "NYC Urban",    "Insider",  True,  True),
    ("C002", "2025-03-15", "NYC Suburban", "None",     False, False),
    ("C003", "2024-11-20", "NYC Urban",    "VIP",      True,  True),
    ("C004", "2025-08-01", "NYC Urban",    "None",     True,  False),
    ("C005", "2025-10-12", "NYC Urban",    "Insider",  True,  True),
    ("C006", "2025-12-04", "NYC Suburban", "None",     False, False),
    ("C007", "2026-01-30", "NYC Urban",    "None",     True,  True),
    ("C008", "2026-02-14", "NYC Suburban", "None",     True,  False),
], columns=["customer_id", "signup_date", "home_metro", "loyalty_tier",
            "email_opt_in", "app_user"])
customers["signup_date"] = pd.to_datetime(customers["signup_date"])

products = pd.DataFrame(
    [(p, p in {"P0201", "P0203", "P0205", "P0207", "P0209"})
     for p in sorted(tx["product_id"].unique())],
    columns=["product_id", "is_occasionwear"])

ANALYSIS_DATE = pd.Timestamp("2026-06-30")

# --------------------------------------------------------------------------
# 2. Invariants published in Appendix A — these must all hold
# --------------------------------------------------------------------------
checks = []


def check(label, actual, expected, tol=0.005):
    ok = (abs(actual - expected) <= tol if isinstance(expected, float)
          else actual == expected)
    checks.append((label, actual, expected, ok))
    return ok


check("rows (order lines)", len(tx), 20)
check("distinct orders", tx["order_id"].nunique(), 12)
check("distinct customers", tx["customer_id"].nunique(), 8)
check("total revenue", float(tx["line_revenue"].sum()), 1312.00)
check("total units", int(tx["quantity"].sum()), 28)
check("lines with store_id ONLINE", int((tx["store_id"] == "ONLINE").sum()), 10)
check("order O10003 revenue",
      float(tx.loc[tx["order_id"] == "O10003", "line_revenue"].sum()), 248.00)
check("unit_price floor", float(tx["unit_price"].min()) >= 24.0, True)
check("unit_price ceiling", float(tx["unit_price"].max()) <= 90.0, True)
check("discount_pct bounded",
      bool(tx["discount_pct"].between(0, 1).all()), True)
check("order_line_id unique", bool(tx["order_line_id"].is_unique), True)

orders = (tx.groupby("order_id", as_index=False)
            .agg(customer_id=("customer_id", "first"),
                 store_id=("store_id", "first"),
                 channel=("channel", "first"),
                 order_date=("order_date", "min"),
                 order_value=("line_revenue", "sum"),
                 order_cost=("line_cost", "sum"),
                 units=("quantity", "sum"),
                 lines=("line_revenue", "size")))
check("order-grain rows", len(orders), 12)
check("order-grain revenue preserved",
      float(orders["order_value"].sum()), 1312.00)

AOV = orders["order_value"].sum() / len(orders)
check("chain AOV", round(float(AOV), 2), 109.33)

ov = orders.merge(stores[["store_id", "store_type"]], on="store_id", how="left")
ov["store_type"] = ov["store_type"].fillna("Digital")
by_type = (ov.groupby("store_type", as_index=False)
             .agg(orders=("order_id", "size"),
                  revenue=("order_value", "sum"),
                  units=("units", "sum")))
by_type["aov"] = (by_type["revenue"] / by_type["orders"]).round(2)
check("suburban AOV",
      float(by_type.loc[by_type["store_type"] == "Suburban", "aov"].iloc[0]),
      220.00)
check("urban AOV",
      float(by_type.loc[by_type["store_type"] == "Urban", "aov"].iloc[0]),
      78.00)

# --------------------------------------------------------------------------
# 3. Every worked figure Appendix B prints
# --------------------------------------------------------------------------
out = {}

# --- B.2 revenue, margin, volume ---
out["gross_sales"] = float((tx["quantity"] * tx["unit_price"]).sum())
out["discount_dollars"] = out["gross_sales"] - float(tx["line_revenue"].sum())
out["net_revenue"] = float(tx["line_revenue"].sum())
out["total_cost"] = float(tx["line_cost"].sum())
out["contribution"] = round(out["net_revenue"] - out["total_cost"], 2)
out["contribution_margin"] = out["contribution"] / out["net_revenue"]
out["units_sold"] = int(tx["quantity"].sum())
out["order_count"] = int(tx["order_id"].nunique())
out["customer_count"] = int(tx["customer_id"].nunique())

# --- B.3 basket and customer value ---
out["aov"] = float(AOV)
out["aov_line_grain_WRONG"] = float(tx["line_revenue"].mean())
out["aov_simple_average_WRONG"] = float(by_type["aov"].mean())
out["units_per_order"] = out["units_sold"] / out["order_count"]
out["revenue_per_unit"] = out["net_revenue"] / out["units_sold"]
out["identity_check"] = out["units_per_order"] * out["revenue_per_unit"]
out["revenue_per_customer"] = out["net_revenue"] / out["customer_count"]
out["orders_per_customer"] = out["order_count"] / out["customer_count"]
out["rpc_identity"] = out["aov"] * out["orders_per_customer"]

# decomposition by metro group (urban store vs suburban store orders)
dec = by_type[by_type["store_type"].isin(["Urban", "Suburban"])].copy()
dec["units_per_order"] = dec["units"] / dec["orders"]
dec["revenue_per_unit"] = dec["revenue"] / dec["units"]
dec["identity"] = dec["units_per_order"] * dec["revenue_per_unit"]
out["decomp"] = dec.set_index("store_type")[
    ["orders", "revenue", "units", "aov", "units_per_order",
     "revenue_per_unit", "identity"]].to_dict("index")
out["aov_ratio"] = 220.00 / 78.00
out["basket_factor"] = (dec.set_index("store_type").loc["Suburban", "units_per_order"]
                        / dec.set_index("store_type").loc["Urban", "units_per_order"])
out["price_factor"] = (dec.set_index("store_type").loc["Suburban", "revenue_per_unit"]
                       / dec.set_index("store_type").loc["Urban", "revenue_per_unit"])

# occasionwear unit share, by store type, unit weighted
lines_p = tx.merge(products, on="product_id", how="left")
lines_p = lines_p.merge(stores[["store_id", "store_type"]], on="store_id", how="left")
lines_p["store_type"] = lines_p["store_type"].fillna("Digital")
occ = (lines_p.assign(occ_units=lambda d: d["quantity"].where(d["is_occasionwear"], 0))
       .groupby("store_type", as_index=False)
       .agg(occ_units=("occ_units", "sum"), units=("quantity", "sum")))
occ["occasionwear_unit_share"] = occ["occ_units"] / occ["units"]
out["occ_share"] = occ.set_index("store_type")["occasionwear_unit_share"].to_dict()

# --- B.4 retention ---
oc = orders.groupby("customer_id").size()
out["repeat_customers"] = int((oc >= 2).sum())
out["repeat_purchase_rate"] = float((oc >= 2).mean())
first_order = orders.groupby("customer_id")["order_date"].transform("min")
orders2 = orders.assign(is_repeat_order=(orders["order_date"] > first_order).astype(int))
out["repeat_orders"] = int(orders2["is_repeat_order"].sum())
out["repeat_order_share"] = out["repeat_orders"] / len(orders2)
out["recency_days"] = (ANALYSIS_DATE - orders.groupby("customer_id")["order_date"].max()).dt.days.to_dict()

# --- B.5 media / campaign: Chapter 1's four campaigns, verbatim ---
camp = pd.DataFrame({
    "campaign": ["New Arrivals", "Loyalty Offer", "Clearance", "Welcome Series"],
    "impressions": [52000, 41000, 68000, 75000],
    "clicks": [2860, 2540, 3400, 3000],
    "conversions": [310, 420, 390, 250],
    "revenue": [27900, 33600, 23400, 17500],
    "ad_spend": [1800, 1200, 9500, 5200],
    "margin_rate": [0.55, 0.32, 0.18, 0.50],
})
camp["ctr"] = camp["clicks"] / camp["impressions"]
camp["post_click_conversion_rate"] = camp["conversions"] / camp["clicks"]
camp["roas"] = camp["revenue"] / camp["ad_spend"]
camp["cpc"] = camp["ad_spend"] / camp["clicks"]
camp["cost_per_conversion"] = camp["ad_spend"] / camp["conversions"]
camp["cpm"] = camp["ad_spend"] / camp["impressions"] * 1000
camp["gross_margin_dollars"] = camp["revenue"] * camp["margin_rate"]
camp["net_contribution_after_ad_spend"] = (camp["gross_margin_dollars"]
                                           - camp["ad_spend"])
out["campaigns"] = camp.round(4).to_dict("records")
out["pooled_ctr"] = camp["clicks"].sum() / camp["impressions"].sum()
out["pooled_conv"] = camp["conversions"].sum() / camp["clicks"].sum()
out["simple_avg_conv_WRONG"] = camp["post_click_conversion_rate"].mean()
out["pooled_roas"] = camp["revenue"].sum() / camp["ad_spend"].sum()
out["simple_avg_roas_WRONG"] = camp["roas"].mean()

# --- B.9 / B.10 classification: Chapter 9's ten-customer miniature ---
mini = pd.DataFrame({
    "customer_id": [f"C{i:03d}" for i in range(1, 11)],
    "p":       [0.82, 0.61, 0.55, 0.52, 0.44, 0.33, 0.24, 0.18, 0.11, 0.06],
    "churned": [1,    1,    0,    0,    1,    0,    0,    0,    0,    0],
    "recency_days": [12, 30, 45, 60, 120, 22, 95, 40, 150, 200],
})
COST, BENEFIT = 12.0, 40.0
THRESHOLD = COST / BENEFIT
out["threshold"] = THRESHOLD


def matrix(p, y, t):
    pred = (p >= t).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    assert tp + fp + fn + tn == len(y), "the matrix must sum"
    return tp, fp, fn, tn


out["cm"] = {}
for t in (0.50, 0.30):
    tp, fp, fn, tn = matrix(mini["p"], mini["churned"], t)
    treated = tp + fp
    out["cm"][t] = dict(
        tp=tp, fp=fp, fn=fn, tn=tn, treated=treated,
        accuracy=(tp + tn) / len(mini),
        precision=(tp / treated) if treated else float("nan"),
        recall=(tp / (tp + fn)) if (tp + fn) else float("nan"),
        fpr=(fp / (fp + tn)) if (fp + tn) else float("nan"),
        fnr=(fn / (fn + tp)) if (fn + tp) else float("nan"),
        net=tp * BENEFIT - treated * COST,
    )
    pr, rc = out["cm"][t]["precision"], out["cm"][t]["recall"]
    out["cm"][t]["f1"] = (2 * pr * rc / (pr + rc)) if (pr + rc) else float("nan")
out["base_rate"] = float(mini["churned"].mean())
out["majority_baseline_accuracy"] = float(max(mini["churned"].mean(),
                                              1 - mini["churned"].mean()))

# --- B.11 forecast: Chapter 10's seven-day miniature ---
# a series whose naive MAE is 1,300.00 and whose seasonal-naive MAE is 514.29
# is reproduced here only as the published pair; the check is the arithmetic form
def mae(a, f):
    return float((np.asarray(a) - np.asarray(f)).__abs__().mean())


def mape(a, f):
    a = np.asarray(a, dtype=float)
    assert (a > 0).all(), "MAPE is undefined at zero and unstable near it"
    return float((np.abs(a - np.asarray(f)) / a).mean() * 100)


storm_actual = [9800, 400, 10100, 11200, 12600, 14100, 9500]
storm_fc = [9600, 7600, 9900, 10800, 12200, 13500, 9300]
out["storm_ape_tuesday"] = abs(400 - 7600) / 400 * 100
out["storm_mape"] = mape(storm_actual, storm_fc)
out["storm_mae"] = mae(storm_actual, storm_fc)
out["storm_within_10pct"] = int((np.abs(np.array(storm_actual)
                                        - np.array(storm_fc))
                                / np.array(storm_actual) * 100 <= 10).sum())

# --- B.12 experiment: Chapter 11's ab_test, verbatim ---
c_x, c_n, t_x, t_n = 300, 5000, 390, 5000
c_rate, t_rate = c_x / c_n, t_x / t_n
abs_lift = t_rate - c_rate
rel_lift = abs_lift / c_rate
se_un = np.sqrt(c_rate * (1 - c_rate) / c_n + t_rate * (1 - t_rate) / t_n)
pool = (c_x + t_x) / (c_n + t_n)
se_pool = np.sqrt(pool * (1 - pool) * (1 / c_n + 1 / t_n))
out["exp"] = dict(c_rate=c_rate, t_rate=t_rate, abs_lift=abs_lift,
                  rel_lift=rel_lift, risk_ratio=t_rate / c_rate,
                  se_un=se_un * 100, se_pool=se_pool * 100)
COST_PER_ALERT, ALERTS, CONTRIB = 0.12, 1, 28.00
out["break_even"] = COST_PER_ALERT * ALERTS / CONTRIB
out["break_even_dose2"] = COST_PER_ALERT * 2 / CONTRIB
for label, lift in (("low", 0.0081), ("point", abs_lift), ("high", 0.0279)):
    incr = lift * 1000
    out[f"net_per_1000_{label}"] = incr * CONTRIB - 1000 * COST_PER_ALERT
    out[f"incr_{label}"] = incr

# --- B.13 dashboard measures: Chapter 13's declared constants ---
out["annual_footprint"] = 92000.0
out["weekly_footprint"] = 92000.0 / 52
out["cm_dashboard"] = 0.46
out["weekly_revenue_at_coverage"] = (92000.0 / 52) / 0.46
out["mature_store_annual_contribution"] = 137000.0
out["fy_open_range_width"] = 860000 - 620000
out["store_equivalents"] = (860000 - 620000) / 137000


# --- Chapter 3's three repeat purchase rates, reproduced from its published table
# (Section 3.10.3). The point of the example is that three CORRECT formulas give
# three different numbers because the window and the eligible population differ.
ch3_orders = pd.DataFrame({
    "customer_id": ["C01", "C01", "C01", "C02", "C02", "C03",
                    "C04", "C04", "C04", "C05", "C06", "C06",
                    "C07", "C08", "C08", "C09", "C10", "C10"],
    "order_date": pd.to_datetime([
        "2024-08-10", "2025-09-14", "2026-02-02", "2024-11-05",
        "2025-01-20", "2025-10-03", "2025-08-19", "2025-12-24",
        "2026-05-30", "2024-09-01", "2026-01-15", "2026-01-28",
        "2025-11-11", "2024-07-22", "2026-04-10", "2026-06-06",
        "2025-02-14", "2025-05-02"]),
    "channel": ["Store", "Store", "Online", "Online", "Online",
                "Store", "Online", "Store", "App", "Store",
                "Store", "Store", "Online", "Store", "Store",
                "App", "Store", "Store"],
})
a_date = pd.Timestamp("2026-06-30")
w_start = pd.Timestamp("2025-07-01")
hist = ch3_orders[ch3_orders["order_date"] <= a_date]
rate_a = float((hist.groupby("customer_id").size() >= 2).mean())
inw = ch3_orders[ch3_orders["order_date"].between(w_start, a_date)]
rate_b = float((inw.groupby("customer_id").size() >= 2).mean())
sw = inw[inw["channel"] == "Store"]
rate_c = float((sw.groupby("customer_id").size() >= 2).mean())
out["ch3_rate_lifetime"] = rate_a
out["ch3_rate_t12m"] = rate_b
out["ch3_rate_store_t12m"] = rate_c
out["ch3_denominators"] = (hist["customer_id"].nunique(),
                           inw["customer_id"].nunique(),
                           sw["customer_id"].nunique())
out["ch3_numerators"] = (int((hist.groupby("customer_id").size() >= 2).sum()),
                         int((inw.groupby("customer_id").size() >= 2).sum()),
                         int((sw.groupby("customer_id").size() >= 2).sum()))
check("Ch3 lifetime repeat rate", round(rate_a, 2), 0.60)
check("Ch3 trailing-12m repeat rate", round(rate_b, 2), 0.43)
check("Ch3 store-only repeat rate", round(rate_c, 2), 0.20)

# --- B.6 CRM and engagement: one email send, every denominator named
send = dict(sent=10_000, bounced=400, delivered=9_600,
            unique_opens=2_688, unique_clicks=384, unsubscribes=48)
out["email"] = dict(
    delivery_rate=send["delivered"] / send["sent"],
    bounce_rate=send["bounced"] / send["sent"],
    open_rate_delivered=send["unique_opens"] / send["delivered"],
    open_rate_sent=send["unique_opens"] / send["sent"],
    click_rate_delivered=send["unique_clicks"] / send["delivered"],
    click_rate_sent=send["unique_clicks"] / send["sent"],
    click_to_open_rate=send["unique_clicks"] / send["unique_opens"],
    unsubscribe_rate_delivered=send["unsubscribes"] / send["delivered"],
)
out["email_raw"] = send

# --- B.7 funnel: one population, four stages, step and cumulative rates
funnel = [("Sessions", 40_000), ("Product views", 12_000),
          ("Carts", 3_000), ("Orders", 1_200)]
out["funnel"] = []
top = funnel[0][1]
for i, (stage, n) in enumerate(funnel):
    step = None if i == 0 else n / funnel[i - 1][1]
    out["funnel"].append(dict(stage=stage, n=n, step=step, cumulative=n / top,
                              dropoff=None if i == 0 else 1 - step))
out["funnel_product_of_steps"] = (12_000 / 40_000) * (3_000 / 12_000) * (1_200 / 3_000)

# --- B.8 segmentation measures on the practice file's eight customers
cf = (orders.groupby("customer_id", as_index=False)
      .agg(frequency=("order_id", "size"), monetary=("order_value", "sum"),
           last_order=("order_date", "max")))
cf["aov"] = cf["monetary"] / cf["frequency"]
cf["recency_days"] = (ANALYSIS_DATE - cf["last_order"]).dt.days
cf = cf.merge(customers[["customer_id", "home_metro"]], on="customer_id")
seg = (cf.groupby("home_metro", as_index=False)
       .agg(customers=("customer_id", "size"), revenue=("monetary", "sum")))
seg["customer_share"] = seg["customers"] / seg["customers"].sum()
seg["revenue_share"] = seg["revenue"] / seg["revenue"].sum()
seg["revenue_per_customer"] = seg["revenue"] / seg["customers"]
out["segments"] = seg.round(4).to_dict("records")
out["cf"] = cf.round(2).to_dict("records")

# --- B.9 numeric prediction error, on eight customers
actual = np.array([248.0, 96.0, 117.0, 84.0, 76.0, 68.0, 88.0, 93.0])
pred   = np.array([210.0, 110.0, 130.0, 80.0, 95.0, 60.0, 92.0, 105.0])
err = actual - pred
out["reg"] = dict(mae=float(np.abs(err).mean()),
                  rmse=float(np.sqrt((err ** 2).mean())),
                  mean_baseline=float(actual.mean()),
                  mae_baseline=float(np.abs(actual - actual.mean()).mean()))
out["reg"]["mae_margin"] = out["reg"]["mae_baseline"] - out["reg"]["mae"]

# --- B.10 lift and cumulative gains on the ten-customer scored file
sc = mini.sort_values("p", ascending=False).reset_index(drop=True)
sc["decile"] = range(1, 11)
sc["lift"] = sc["churned"] / out["base_rate"]
sc["cum_capture"] = sc["churned"].cumsum() / sc["churned"].sum()
sc["cum_file"] = (sc.index + 1) / len(sc)
out["gains"] = sc[["decile", "p", "churned", "lift", "cum_capture",
                   "cum_file"]].round(3).to_dict("records")
inc = sc["recency_days"] > 90
out["incumbent"] = dict(treated=int(inc.sum()),
                        caught=int(sc.loc[inc, "churned"].sum()),
                        net=float(sc.loc[inc, "churned"].sum() * BENEFIT
                                  - inc.sum() * COST),
                        capture=float(sc.loc[inc, "churned"].sum()
                                      / sc["churned"].sum()),
                        file_share=float(inc.mean()))

# --- B.11 forecast: one week, calm and storm-struck
calm_actual = [9800, 9400, 10100, 11200, 12600, 14100, 9500]
calm_fc     = [9600, 9200, 9900, 10800, 12200, 13500, 9300]
out["fc_calm"] = dict(mae=mae(calm_actual, calm_fc),
                      mape=mape(calm_actual, calm_fc),
                      min_denom=min(calm_actual))
out["fc_storm"] = dict(mae=out["storm_mae"], mape=out["storm_mape"],
                       min_denom=min(storm_actual),
                       within_10pct=out["storm_within_10pct"])
out["fc_bias_calm"] = float(np.mean(np.array(calm_actual) - np.array(calm_fc)))

# --- B.4 cohort retention, period-active, with the observability mask
coh = pd.DataFrame({
    "cohort": ["2026-01", "2026-01", "2026-02", "2026-02", "2026-03"],
    "period": [0, 1, 0, 1, 0],
    "active": [200, 68, 180, 54, 240],
})
sizes = {"2026-01": 200, "2026-02": 180, "2026-03": 240}
coh["size"] = coh["cohort"].map(sizes)
coh["retention"] = coh["active"] / coh["size"]
out["cohort"] = coh.round(3).to_dict("records")

# --------------------------------------------------------------------------
# 4. Report
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 74)
    print("APPENDIX A PRACTICE-FILE INVARIANTS")
    print("=" * 74)
    fails = 0
    for label, actual, expected, ok in checks:
        fails += (not ok)
        print(f"{'PASS' if ok else 'FAIL':<5} {label:<34} {actual!s:>14}"
              f"   expected {expected!s}")
    print(f"\n{len(checks) - fails} passed, {fails} failed\n")

    print("=" * 74)
    print("WORKED FIGURES")
    print("=" * 74)
    for k, v in out.items():
        if isinstance(v, (int, float, np.floating)):
            print(f"  {k:<34} {v:,.4f}" if isinstance(v, float)
                  else f"  {k:<34} {v}")
    print("\n  decomposition by store type:")
    print(dec.to_string(index=False))
    print("\n  occasionwear unit share:", out["occ_share"])
    print("\n  confusion matrices:")
    for t, d in out["cm"].items():
        print(f"    t={t}: {d}")
    print("\n  campaigns:")
    print(camp.round(4).to_string(index=False))
    print("\n  order-grain table:")
    print(ov.to_string(index=False))
    assert fails == 0, "practice-file invariants failed"
