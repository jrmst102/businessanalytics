# Appendix B — Metric dictionary changelog

The published appendix and this dictionary are generated from one source, so a
definition cannot change in one and not the other. Record every definitional
change here, with the date, the entry key, and the reason.

## Version 1.1 — August 2026

Revision pass answering the author's review of v1.0. Definitional and
verification changes, in the order the review raised them:

| Entry | Change |
|---|---|
| Front matter | The generative-AI disclosure claimed every formula was computed on the practice file. It was not: five families reuse their owning chapter's published figures. The disclosure now says what was actually done. |
| `margin_over_baseline` | **Corrected.** v1.0 defined the margin as candidate − baseline, which is the wrong sign for every loss metric in the dictionary and contradicted the appendix's own worked example. The entry is now direction-aware: baseline − candidate for loss metrics, candidate − baseline for gain metrics. `stylecraft_metrics.margin_over_baseline()` now requires the direction to be named, and four tests assert both conventions. |
| `pearson_r` | Required fields no longer say the two variables must share units. Correlation requires the same observational cases and grain, not the same units. |
| `post_click_conversion_rate` | Numerator and denominator now state the counting basis. The `[0, 1]` bound holds only when both count the same unit. |
| `open_rate`, `click_rate` | Unique opens and unique clicks are the headline numerators. Total opens and total clicks are named as a different quantity with no upper bound of 1. The claim that click rate cannot exceed open rate is withdrawn: a click can be recorded when the open pixel never fired. |
| `delivery_rate`, `bounce_rate` | The sum-to-one identity now states its condition — every message resolved, no suppressed or pending records in the denominator. |
| `roas` | A campaign with zero spend has an **undefined** return, not an infinite one, per the appendix's own notation standard. The same guard is now stated for cost per conversion, percentage variance, and percentage change. |
| `opt_in_rate` | Restricted to email and SMS consent, one channel per figure. `app_user` is not consent. |
| `app_user_share` | **New entry.** The point-in-time stock that `app_user` actually supports; the exclusion register now excludes only the adoption rate over a window. |
| `mse` | **New entry.** Moved out of the exclusion register: the syllabus asks for it, so the dictionary carries it rather than explaining its absence. |
| `ari` | Unit now records that the index can be negative, with a lower bound of −0.5. |
| `calibration` | Numerator is the count of observed positives in the bin, not the rate. |
| `fpr_fnr` | The fifty-case screen is labeled a course convention, not a statistical boundary. |
| `horizon_error` | A flat or falling error curve now prompts inspection rather than asserting one diagnosis. |
| `ci_difference` | General form `estimate ± z* × SE`, with z* = 1.96 for a 95 percent interval. |
| `selection_share` | The random-ordering capture floor holds in expectation. |
| `aov` | The grain field no longer says the metric cannot be computed at line grain; the warning is specifically against averaging line values. |
| `centroid` | Inverted clause repaired. |
| `decile_share` | Concentration claim now cites Schmittlein et al. (1993). |

Document-level changes: a CONTENTS block added to the front matter per blueprint
§2.4; the alphabetical index re-sorted letter-by-letter; the metric-definition
form referenced by its own table number; and in-text citations added for every
reference-list entry. Eight new production checks were added, including one that
would have caught the margin sign error and one that catches inline-markup loss.

## Version 1.0 — August 2026

First release. 123 entries across twelve families, audited against
Chapters 1–13, the front matter, the StyleCraft dataset specification, and the
syllabus session outcomes for both projects.

Definitional decisions taken at first release, each of which resolved a conflict
found during the audit rather than inventing a convention:

| Entry | Decision |
|---|---|
| `repeat_purchase_rate` | Trailing-twelve-month, all-channel definition adopted as the headline, per Chapter 3's managerial recommendation. Lifetime and store-only carried as named variants rather than dropped. |
| `repeat_order_share` | Kept as a separate entry from repeat purchase rate, because Chapters 12 and 13 compute an order-grain quantity under a name that invites a customer-grain reading. |
| `line_revenue` | Chapter 4's discounted form is canonical. Chapter 5's miniature omits the discount factor because its miniature carries no discount column; that is a property of the miniature, not a second definition. |
| `contribution` / `contribution_margin` | Defined on Chapter 13's cost basis, with the gross-profit relabel contingency carried in the entry, because the name is only correct if `line_cost` is fully loaded. |
| `revenue_per_month` | Entry records that Chapter 6 aggregates this to segment level as a mean of customer-level ratios while pooling the neighbouring discount-share row in the same table. Flagged to the author; see the build log. |
| `forecast_bias` | Chapter 10 operationalises this in code and defines it nowhere in prose. Appendix B is therefore its canonical definition, including the sign convention. |
| `cpm`, `dropoff_rate`, `ctor`, `delivery_rate`, `bounce_rate` | Cataloged here without a chapter owner: computable from certified fields, plausibly required by a project, and defined nowhere in the guide. |
| Segment index, lift versus base rate, reach, media frequency | Excluded. Absent from every chapter; see the exclusion register. |
