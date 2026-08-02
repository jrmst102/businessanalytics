#!/usr/bin/env python3
"""Generate the Appendix C worked examples and assert every figure they print.

Each example fills one template's placeholders with real values from
practice_transactions.csv and carries the hand computation an analyst runs when
the response arrives. No AI response is reproduced: the examples supply the
completed prompt and the arithmetic that grades whatever comes back, which is
the part a student cannot look up.
"""
import csv, os
from collections import defaultdict
from build_practice_file import STORE_TYPE, build, assert_invariants

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'worked_examples')
os.makedirs(OUT, exist_ok=True)

rows = build()
for name, got, want, ok in assert_invariants(rows):
    assert ok, (name, got, want)

# ------------------------------------------------------------------ figures
rev = round(sum(float(r['line_revenue']) for r in rows), 2)
units = sum(int(r['quantity']) for r in rows)
orders = sorted({r['order_id'] for r in rows})
custs = sorted({r['customer_id'] for r in rows})
aov = rev / len(orders)
aov_line_grain = rev / len(rows)                     # the trap
upo = units / len(orders)
rpu = rev / units

grp = defaultdict(lambda: {'rev': 0.0, 'orders': set(), 'units': 0, 'lines': 0})
for r in rows:
    g = grp[STORE_TYPE[r['store_id']]]
    g['rev'] += float(r['line_revenue'])
    g['orders'].add(r['order_id'])
    g['units'] += int(r['quantity'])
    g['lines'] += 1
GT = {k: {'rev': round(v['rev'], 2), 'n': len(v['orders']),
          'aov': v['rev'] / len(v['orders']), 'units': v['units'],
          'lines': v['lines'], 'share': v['rev'] / rev} for k, v in grp.items()}

weighted = sum(GT[k]['aov'] * GT[k]['n'] for k in GT) / len(orders)
averaged = sum(GT[k]['aov'] for k in GT) / len(GT)     # the trap

A = []


def ck(name, got, want, tol=0.005):
    ok = abs(got - want) <= tol if isinstance(got, float) else got == want
    A.append((name, got, want, ok))


ck('total revenue', rev, 1312.00)
ck('order-grain AOV', round(aov, 2), 109.33)
ck('line-grain AOV (the trap)', round(aov_line_grain, 2), 65.60)
ck('suburban AOV', round(GT['Suburban']['aov'], 2), 220.00)
ck('urban AOV', round(GT['Urban']['aov'], 2), 78.00)
ck('digital AOV', round(GT['Digital']['aov'], 2), 93.33)
ck('weighted recombination equals pooled AOV', round(weighted, 2), round(aov, 2))
ck('averaged average (the trap)', round(averaged, 2), 130.44)
ck('units per order', round(upo, 4), 2.3333)
ck('revenue per unit', round(rpu, 4), 46.8571)
ck('decomposition identity', round(upo * rpu, 2), round(aov, 2))
ck('store-type shares sum to 1', round(sum(GT[k]['share'] for k in GT), 6), 1.0)
ck('digital share of revenue', round(GT['Digital']['share'], 4), 0.4268)
ck('group order counts sum to 12', sum(GT[k]['n'] for k in GT), 12)
ck('group line counts sum to 20', sum(GT[k]['lines'] for k in GT), 20)

# -------------------------------------------- the raw file for the C.5 example
RAW_UNPARSEABLE = {'L00007', 'L00016'}
raw = []
for r in rows:
    q = dict(r)
    q['unit_price'] = ('n/a' if r['order_line_id'] in RAW_UNPARSEABLE
                       else f'${float(r["unit_price"]):,.2f}')
    raw.append(q)
with open(os.path.join(HERE, 'practice_transactions_raw.csv'), 'w', newline='',
          encoding='utf8') as f:
    w = csv.DictWriter(f, fieldnames=list(raw[0]))
    w.writeheader()
    w.writerows(raw)
ck('raw rows', len(raw), 20)
ck('raw values that will fail coercion', sum(1 for r in raw
                                             if r['unit_price'] == 'n/a'), 2)
ck('raw line_revenue total is untouched by the coercion',
   round(sum(float(r['line_revenue']) for r in raw), 2), 1312.00)

BANNER = (
    '> **How to read this.** The prompt below is Appendix C’s template with its\n'
    '> placeholders filled from `practice_transactions.csv`. No AI response is\n'
    '> reproduced — what an assistant returns varies. What does not vary is the\n'
    '> arithmetic that grades it, which is given under *Predict before you send*\n'
    '> and *Audit*. Write the predictions down before you send the prompt.\n')

SCHEMA = ('order_line_id, order_id, customer_id, product_id, store_id, channel, '
          'order_date, quantity, unit_price, discount_pct, line_revenue')

CERT = (f'rows {len(rows)}, distinct orders {len(orders)}, distinct customers '
        f'{len(custs)}, total revenue ${rev:,.2f}, total units {units}')


def write(n, title, template, body):
    slug = template.lower().replace('.', '').replace(' ', '_')
    path = os.path.join(OUT, f'{n:02d}_{slug}.md')
    open(path, 'w', encoding='utf8').write(
        f'# Worked example {n} — {title}\n\n'
        f'**Template.** {template}\n\n'
        f'**Data.** `practice_transactions.csv` — {CERT}. Synthetic, '
        f'course-provided, safe to paste.\n\n{BANNER}\n{body}\n')
    return path


APPD = (
    '## The Appendix D record\n\n'
    '| Field | Entry |\n|---|---|\n'
    '| Exchange ID | |\n| Tool and version | |\n'
    '| Which step | |\n| Prompt as sent | |\n'
    '| Output received | |\n| Decision: accepted, modified, rejected | |\n'
    '| Error or limitation found | |\n'
    '| Prediction written before the check | |\n'
    '| Verification performed, and its result | |\n'
    '| Change to the final work | |\n'
    '| Analyst judgment the tool could not make | |\n')

# -------------------------------------------------------------- example 1
write(1, 'Specify, then attack the specification', 'Templates C.1 and C.2', f"""
## The request

> *“The suburban store is doing better than the city store. Can you pull
> something together showing that before Friday?”* — regional manager

## Prompt C.1, filled in

```text
CONTEXT
Business request, verbatim: The suburban store is doing better than the city
store. Can you pull something together showing that before Friday?
Who made it: regional manager  Deadline stated or implied: Friday
Established facts: The extract covers 12 orders placed between 2026-02-11 and
2026-06-01 across one suburban store, one urban store, and the digital
channel. Nothing in it records store size, staffing, or catchment.
Tables available, with grain: practice_transactions.csv = one row equals one
order line
Fields available: {SCHEMA}
[...the ten components, the constraints, and the open-questions list, exactly
as printed in Prompt C.1...]
```

## Predict before you send

Write down which of the ten components the request cannot determine. The
honest count here is at least four: the decision, the decision-maker’s
alternatives, the comparison population, and what “doing better” is measured
on. A draft that returns fewer than four `UNSPECIFIED` rows has invented
something.

## Audit

- The request says *showing that*, which is the framing trap of Section 2.8.
  A specification that adopts it has committed to advocacy before any evidence
  exists. Check the analytical questions for a comparison rather than a
  demonstration.
- Confirm the unit of analysis is stated as *one row equals one what*. The
  file is order-line grain and the claim is about orders; the specification
  must say which.
- Confirm the limitations name what the file cannot establish: with
  {GT['Suburban']['n']} suburban orders and {GT['Urban']['n']} urban orders,
  no difference is separable from noise, and nothing here is causal.

## Then run Prompt C.2 on your own revision

Paste the completed specification and take the numbered critique. Revise on at
most two points; reject at least one with a one-sentence justification.

{APPD}""")

# -------------------------------------------------------------- example 2
write(2, 'Define average order value completely', 'Template C.4', f"""
## Prompt C.4, filled in

```text
Metric to define: average order value (AOV)
Decision it supports: whether the suburban format's basket justifies a second
suburban lease
Tables and fields available, with grain: practice_transactions.csv = one row
equals one order line; fields {SCHEMA}
Window boundary convention: inclusive on both ends, 2026-02-11 to 2026-06-01
[...the thirteen fields and the rules, exactly as printed in Prompt C.4...]
```

## Predict before you send

The whole entry turns on one field. Write down, before you read the response,
what the **denominator** must be and what the **grain** must be.

## Audit — the arithmetic that decides it

| Reading | Computation | Value |
|---|---|---|
| Order grain (correct) | ${rev:,.2f} ÷ {len(orders)} orders | **${aov:,.2f}** |
| Line grain (the trap) | ${rev:,.2f} ÷ {len(rows)} order lines | ${aov_line_grain:,.2f} |

The two differ by ${aov - aov_line_grain:,.2f}, which is a factor of
{aov / aov_line_grain:.2f}. A definition that names the numerator and the
denominator but not the grain permits both, and the file is at line grain, so
the wrong one is what naive code will return.

Two further checks. The unit must be stated as currency, not as a ratio. And
the verification the entry supplies must be hand-runnable: here, order
`O10003` sums to
${sum(float(r['line_revenue']) for r in rows if r['order_id'] == 'O10003'):,.2f}
(88.00 + 84.00 + 76.00), so any AOV computed over a set containing it must
move when that order is removed.

## Cross-check against Appendix B

Appendix B carries the canonical entry. If the returned definition diverges
from it, that is a definitional finding to record, not a difference to
reconcile privately.

{APPD}""")

# -------------------------------------------------------------- example 3
write(3, 'Draft one cleaning step', 'Template C.5', f"""
## The step

`practice_transactions_raw.csv` stores `unit_price` as currency strings
(`$88.00`), and {len(RAW_UNPARSEABLE)} of the {len(raw)} lines carry the
sentinel `n/a`. The step is: strip the currency formatting and coerce
`unit_price` to numeric, flagging what fails.

## Prompt C.5, filled in

```text
DATA DICTIONARY ENTRIES for the affected columns:
unit_price - catalog price per unit at the time of sale, stored as a currency
string in the raw file; ratio; permitted band $24.00 to $90.00; the literal
"n/a" is a sentinel for a price that was not captured.

CERTIFIED BASELINE from my verification log:
  rows {len(raw)}   distinct orders {len(orders)}   distinct customers {len(custs)}
  revenue ${rev:,.2f}   missing values in the affected columns 0

SAMPLE ROWS (course-provided synthetic data):
{chr(10).join('  ' + ', '.join(str(v) for v in raw[i].values()) for i in range(3))}

Write pandas code to strip currency formatting from unit_price and coerce it
to numeric, flagging values that fail. [...the rest of Prompt C.5 exactly as
printed, with the remedy declared as FLAG...]
```

## Predict before you send

| Quantity | Predicted after the step |
|---|---|
| Row count | {len(raw)} — unchanged |
| Distinct orders | {len(orders)} — unchanged |
| Revenue total (`line_revenue` is not touched) | ${rev:,.2f} — unchanged |
| New missing values in `unit_price` | {len(RAW_UNPARSEABLE)} |
| Rows dropped | 0 |

## Audit

- Compare every predicted quantity to the actual. The count that matters is
  the third row: `line_revenue` is a separate column and a step that
  recomputes it from a now-missing `unit_price` will move the revenue total,
  which is a silent change of the certified figure.
- If the returned code contains a `dropna`, the remedy changed from flag to
  drop without being asked. That is the unstated-default failure of Section
  4.10, and it costs {len(RAW_UNPARSEABLE)} rows here.
- Confirm the raw frame was not modified in place.
- Check the band: every parsed price must fall inside $24.00 to $90.00. A
  value outside it is a parsing error, not a bargain.

{APPD}""")

# -------------------------------------------------------------- example 4
write(4, 'Produce a descriptive table that must reconcile',
      'Template C.7', f"""
## The table

Average order value by store type, with the order count and the revenue share
beside it.

## Prompt C.7, filled in

```text
DATA DICTIONARY ENTRIES:
[the entries for order_id, store_id, line_revenue, and the store-type mapping
Suburban = S07, Urban = S02, Digital = ONLINE]

CERTIFIED TOTALS from my verification log:
  rows {len(rows)}   distinct orders {len(orders)}   distinct customers {len(custs)}
  total revenue ${rev:,.2f}

Write pandas code to produce average order value by store type, with the order
count and the revenue share beside it. [...the rest of Prompt C.7 exactly as
printed...]
```

## Predict before you send, then check against this

| Store type | Orders | Lines | Revenue | AOV | Revenue share |
|---|---|---|---|---|---|
""" + '\n'.join(
    f"| {k} | {GT[k]['n']} | {GT[k]['lines']} | ${GT[k]['rev']:,.2f} | "
    f"${GT[k]['aov']:,.2f} | {GT[k]['share']:.1%} |"
    for k in ('Suburban', 'Urban', 'Digital')) + f"""
| **All** | **{len(orders)}** | **{len(rows)}** | **${rev:,.2f}** | \
**${aov:,.2f}** | **100.0%** |

## Audit — the three reconciliations

1. **Orders and revenue reconcile.** {' + '.join(str(GT[k]['n']) for k in ('Suburban','Urban','Digital'))} = {len(orders)};
   {' + '.join(f'{GT[k]["rev"]:,.2f}' for k in ('Suburban','Urban','Digital'))} = {rev:,.2f}.
   Shares sum to 100 percent.
2. **The overall figure is weighted, not averaged.** Weighting the three group
   AOVs by their order counts returns ${weighted:,.2f}, which equals the pooled
   figure. Averaging the three group AOVs returns **${averaged:,.2f}**, which
   reconciles to nothing — it is Section 5.3’s averaged average, and it is
   what an unprompted assistant most often produces.
3. **One cell recomputed by hand.** Suburban:
   (${sum(float(r['line_revenue']) for r in rows if STORE_TYPE[r['store_id']]=='Suburban'):,.2f})
   ÷ {GT['Suburban']['n']} orders = ${GT['Suburban']['aov']:,.2f}.

## The verb check

Strike every causal verb before the table travels. *Suburban orders are larger
than urban orders in this extract* is supported. *The suburban format drives
larger baskets* is not, and nothing in {len(orders)} orders across
{len(custs)} customers ever will be.

{APPD}""")

# -------------------------------------------------------------- example 5
write(5, 'Specify a view, then audit it', 'Templates C.16 and C.17', f"""
## Prompt C.22, filled in

```text
I have practice_transactions.csv at order-line grain, with these columns
{SCHEMA}. I want to answer this question: is the average order value at the
suburban store higher than at the urban store? Propose three candidate views.
For each, state the mark type, every field-to-channel encoding, the
aggregation and the grain one mark represents, the axis ranges, the sort
order, and the palette. Do not use any column not in the schema I pasted; if
the question requires a field I have not given you, say so instead of assuming
it. Do not render or describe conclusions.
```

## Predict before you build

Write down, for each candidate: the comparison, the channel carrying it, that
channel’s rank in the perceptual hierarchy, and the two faults you expect.
On this schema, two faults are near certain.

- **The invented field.** There is no `store_type` column. The schema carries
  `store_id` only, with `S07`, `S02`, and the reserved `ONLINE`. A candidate
  that encodes `store_type` has invented it, and the correct response was to
  say so.
- **The grain slip.** A bar of `AVG(line_revenue)` by store returns
  ${GT['Suburban']['rev'] / GT['Suburban']['lines']:,.2f} suburban against
  ${GT['Urban']['rev'] / GT['Urban']['lines']:,.2f} urban — a gap of
  {(GT['Suburban']['rev']/GT['Suburban']['lines']) / (GT['Urban']['rev']/GT['Urban']['lines']) - 1:.0%},
  where the order-grain gap is
  ${GT['Suburban']['aov']:,.2f} against ${GT['Urban']['aov']:,.2f}, a gap of
  {GT['Suburban']['aov'] / GT['Urban']['aov'] - 1:.0%}. Both numbers are
  correct averages. Only one answers the question.

## Then audit with Prompt C.24

Describe the built view completely — including the filter state, which here
must disclose whether the {GT['Digital']['lines']} `ONLINE` lines are in or
out — and take the defect list. Two items to check for specifically:

- the axis floor, since a two-bar chart of ${GT['Urban']['aov']:,.2f} against
  ${GT['Suburban']['aov']:,.2f} truncated at 70 draws a ratio of roughly
  {(GT['Suburban']['aov'] - 70) / (GT['Urban']['aov'] - 70):.0f} to 1 where the
  true ratio is {GT['Suburban']['aov'] / GT['Urban']['aov']:.2f} to 1;
- the undisclosed filter, which leaves no trace in the image.

Repair against Appendix E, one mechanic at a time, and write one sentence per
repair on what changed in the reading.

{APPD}""")

# -------------------------------------------------------------- example 6
write(6, 'Title the view, then review the deliverable',
      'Templates C.18 and C.19', f"""
## Prompt C.25, filled in

```text
Here is a description of one view from a dashboard: two bars, one per physical
store, showing average order value computed at order grain over 2026-02-11 to
2026-06-01 inclusive. The suburban store (S07) shows ${GT['Suburban']['aov']:,.2f}
across {GT['Suburban']['n']} orders; the urban store (S02) shows
${GT['Urban']['aov']:,.2f} across {GT['Urban']['n']} orders. The vertical axis
runs from 0 to 240. The {GT['Digital']['n']} digital orders are excluded and
the exclusion is stated in the footer.

Write twelve candidate titles as complete sentences.

Do not use any number that I have not given you. Do not assert a cause, a
forecast, a payback period, or a claim about stores other than these 2. For
each candidate, state in a second line exactly which marks in the view a
reader would have to look at to verify it.
```

## Predict before you read

Write down how many of the twelve will overclaim and in which of the three
shapes — causal or predictive verb, generalized population, imported number.

## Audit — three sentences, graded

| Candidate title | Verdict |
|---|---|
| *Average order value at the suburban store is ${GT['Suburban']['aov']:,.2f} against ${GT['Urban']['aov']:,.2f} at the urban store over this window.* | **Earned.** Both numbers are marks; the window is in the footer. |
| *The suburban format drives larger baskets.* | **Rejected — causal verb, and a generalized population.** Two stores are not a format, and nothing here is causal. |
| *Suburban expansion would add ${GT['Suburban']['aov'] - GT['Urban']['aov']:,.2f} per order.* | **Rejected — imported number and a forecast.** The difference is arithmetic on two marks, but *would add* is a claim about stores that do not exist yet. |

Reject on the first failure rather than repairing. Then show the surviving
title on its view to someone who has seen neither, and confirm her paraphrase
is the claim you intended.

## Close with Prompt C.27

Paste the finished memo and the evidence behind each figure. On a deliverable
this small the review should surface at least three defects that are really
there: the sample is {len(orders)} orders across {len(custs)} customers with no
interval anywhere; the {GT['Digital']['n']} digital orders
({GT['Digital']['share']:.1%} of revenue) are excluded by a filter; and every
comparison is observational.

{APPD}""")

for name, got, want, ok in A:
    print(f'  {"PASS" if ok else "FAIL"}  {name}: {got}')
bad = sum(1 for *_, ok in A if not ok)
print(f'\n{len(A) - bad} passed, {bad} failed — '
      f'{len(os.listdir(OUT))} worked examples in {OUT}')
raise SystemExit(1 if bad else 0)
