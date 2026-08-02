# Appendix B companion files

Companion assets for **Appendix B. Common Marketing Metrics**, Version 1.1,
August 2026.

| File | What it is |
|---|---|
| `metric_dictionary.csv` | Every entry, every field, one row per metric. This is the file to give an AI assistant as context instead of asking it to supply a definition. |
| `metric_dictionary.xlsx` | The same dictionary with the exclusion register and a family summary on separate sheets. |
| `metric_definition_form.docx` | The blank form from Table B.4, for a metric this appendix does not carry. |
| `stylecraft_metrics.py` | Tested Python functions for the most repeated metrics. Each implements one entry and names it. |
| `test_stylecraft_metrics.py` | The tests. Every one of them checks a figure printed in the appendix. |
| `appendix_b_practice_transactions.csv` | The twenty-line practice file the worked examples run on, plus its three dimension tables. |
| `CHANGELOG.md` | Definitional changes, with reasons. |

## The rule these files exist to enforce

A metric exists only as its definition. `stylecraft_metrics.py` implements the
entries rather than restating them: every function's docstring names the entry
it implements, and the tests assert the figures the appendix publishes. If a
definition changes, the test fails before the deliverable does.

## Reproducing the appendix's worked figures

```
python test_stylecraft_metrics.py
```

The practice file carries 20 order lines, 12 orders,
8 customers, and $1,312.00
of revenue — the same invariants Appendix A publishes, so a figure computed here
reconciles with one computed there.
