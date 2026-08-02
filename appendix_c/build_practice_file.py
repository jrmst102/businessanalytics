#!/usr/bin/env python3
"""Rebuild the Appendix C worked-example practice file.

The file reproduces every invariant Appendix A publishes for
practice_transactions.csv, so a figure quoted in an Appendix C worked example
can be traced to the same miniature Appendices A and B use:

    20 order lines, 12 orders, 8 customers, $1,312.00 revenue, 28 units
    AOV $109.33; order O10003 = 88.00 + 84.00 + 76.00 = 248.00
    ten lines carry the reserved ONLINE store id
    AOV $220.00 suburban against $78.00 urban
    catalog prices inside the $24-$90 band

If the shipped practice_transactions.csv differs from this reconstruction,
replace this file with it and regenerate the worked examples.
"""
import csv, os

# order_id, store_id, channel, date, [(product, qty, unit_price), ...]
ORDERS = [
    # --- suburban store S07: 2 orders, 5 lines, $440.00, AOV $220.00
    ('O10003', 'C0002', 'S07', 'Store', '2026-03-04',
     [('P1041', 1, 88.00), ('P1052', 2, 42.00), ('P1063', 1, 76.00)]),
    ('O10008', 'C0005', 'S07', 'Store', '2026-04-18',
     [('P1044', 2, 48.00), ('P1047', 2, 48.00)]),
    # --- urban store S02: 4 orders, 5 lines, $312.00, AOV $78.00
    ('O10001', 'C0001', 'S02', 'Store', '2026-02-11',
     [('P1010', 1, 78.00)]),
    ('O10004', 'C0003', 'S02', 'Store', '2026-03-09',
     [('P1011', 1, 78.00)]),
    ('O10009', 'C0006', 'S02', 'Store', '2026-04-25',
     [('P1012', 1, 78.00)]),
    ('O10011', 'C0001', 'S02', 'Store', '2026-05-14',
     [('P1020', 1, 30.00), ('P1021', 2, 24.00)]),
    # --- digital: 6 orders, 10 lines, $560.00
    ('O10002', 'C0002', 'ONLINE', 'Online', '2026-02-20',
     [('P1030', 2, 45.00)]),
    ('O10005', 'C0004', 'ONLINE', 'Online', '2026-03-15',
     [('P1031', 1, 85.00)]),
    ('O10006', 'C0004', 'ONLINE', 'Online', '2026-03-27',
     [('P1032', 2, 30.00), ('P1033', 1, 55.00)]),
    ('O10007', 'C0007', 'ONLINE', 'Online', '2026-04-02',
     [('P1034', 2, 36.00), ('P1035', 1, 28.00)]),
    ('O10010', 'C0008', 'ONLINE', 'Online', '2026-05-06',
     [('P1036', 1, 45.00), ('P1037', 2, 32.00)]),
    ('O10012', 'C0003', 'ONLINE', 'Online', '2026-06-01',
     [('P1038', 1, 37.00), ('P1039', 1, 24.00)]),
]

STORE_TYPE = {'S07': 'Suburban', 'S02': 'Urban', 'ONLINE': 'Digital'}


def build():
    rows, n = [], 0
    for oid, cid, sid, chan, date, lines in ORDERS:
        for prod, qty, price in lines:
            n += 1
            rows.append({
                'order_line_id': f'L{n:05d}',
                'order_id': oid,
                'customer_id': cid,
                'product_id': prod,
                'store_id': sid,
                'channel': chan,
                'order_date': date,
                'quantity': qty,
                'unit_price': f'{price:.2f}',
                'discount_pct': '0.00',
                'line_revenue': f'{qty * price:.2f}',
            })
    return rows


def assert_invariants(rows):
    rev = round(sum(float(r['line_revenue']) for r in rows), 2)
    units = sum(int(r['quantity']) for r in rows)
    orders = {r['order_id'] for r in rows}
    custs = {r['customer_id'] for r in rows}
    checks = []

    def ck(name, got, want):
        checks.append((name, got, want, got == want))

    ck('order lines', len(rows), 20)
    ck('distinct orders', len(orders), 12)
    ck('distinct customers', len(custs), 8)
    ck('total revenue', rev, 1312.00)
    ck('total units', units, 28)
    ck('AOV (2dp)', round(rev / len(orders), 2), 109.33)
    ck('order O10003 revenue',
       round(sum(float(r['line_revenue']) for r in rows
                 if r['order_id'] == 'O10003'), 2), 248.00)
    ck('O10003 line revenues',
       sorted(float(r['line_revenue']) for r in rows if r['order_id'] == 'O10003'),
       [76.0, 84.0, 88.0])
    ck('lines with reserved ONLINE store id',
       sum(1 for r in rows if r['store_id'] == 'ONLINE'), 10)
    for st, want in (('Suburban', 220.00), ('Urban', 78.00)):
        sel = [r for r in rows if STORE_TYPE[r['store_id']] == st]
        o = {r['order_id'] for r in sel}
        ck(f'AOV {st.lower()}',
           round(sum(float(r['line_revenue']) for r in sel) / len(o), 2), want)
    prices = [float(r['unit_price']) for r in rows]
    ck('catalog band $24-$90', (min(prices) >= 24.0, max(prices) <= 90.0),
       (True, True))
    ck('line revenue equals quantity x unit price on every line',
       all(abs(int(r['quantity']) * float(r['unit_price'])
               - float(r['line_revenue'])) < 1e-9 for r in rows), True)
    return checks


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    rows = build()
    with open(os.path.join(here, 'practice_transactions.csv'), 'w',
              newline='', encoding='utf8') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)

    fails = 0
    for name, got, want, ok in assert_invariants(rows):
        print(f'  {"PASS" if ok else "FAIL"}  {name}: {got!r}'
              + ('' if ok else f'  (expected {want!r})'))
        fails += not ok
    print(f'\n{"practice_transactions.csv written" if not fails else "INVARIANTS FAILED"}'
          f' — {len(rows)} lines, {fails} failures')
    raise SystemExit(1 if fails else 0)
