# Appendix D — AI-Use Record (completed example)

## D.5.1 Assignment and analyst information

| Field | Response |
|---|---|
| Student name | [STUDENT NAME] |
| Group name and members, if applicable | Not a group submission |
| Course and section | INTG1-GC 2300, Section [SECTION] |
| Assignment or project | Worked example — the Chapter 9 threshold arithmetic on the ten-customer miniature published in Code 9.1 and Code 9.2. Not a graded exercise. |
| Submission date | [DATE] |
| Notebook, workbook, dashboard, or report filename | Ch09_threshold_walkthrough.ipynb |
| Version of the submitted artifact | v1.2 |

## D.5.2 AI tools used

| Product name | Model or version | Access mode | Dates used | Purpose categories |
|---|---|---|---|---|
| General-purpose assistant | Not displayed | Public web tool | [DATE] to [DATE] | Problem framing; code drafting; analytical interpretation; writing or editing |

## D.5.3 Data and privacy declaration

| Question | Response |
|---|---|
| What information was supplied to the tool? | The ten-row miniature printed in Code 9.1 — customer_id, churn_prob, churned, lapsed_90d — and the three cost figures Section 9.9 publishes. No file was uploaded. |
| What kind of information was it? | Course-provided and synthetic. StyleCraft is a fictional retailer and the miniature is printed in the chapter. |
| Were any personal identifiers, credentials, proprietary records, or restricted data supplied? | No. |
| What safeguards were used? | Ten synthetic rows pasted as text; no connection to any live system; no real customer data at any point. |

Sign exactly one of the three statements below. They are mutually exclusive.

| Statement | Sign it when | Signed |
|---|---|---|
| 1. No restricted information was supplied. | Nothing confidential, personally identifiable, proprietary, or otherwise restricted was placed into an AI tool at any point in this work. | Yes |
| 2. Restricted information was used only within the approved environment named above. | The environment, the permission under which it was used, and the information supplied are all recorded in the table above. |  |
| 3. A possible incident occurred and has been reported. | Describe it above, report it to your instructor, and do not sign statement 1 or 2. Reporting an incident is not a penalty; concealing one is a different matter. |  |

## D.5.4 Exchange log

### E1 — Specify

| Field | Entry |
|---|---|
| Tool and version | General-purpose assistant, version not displayed, public web tool |
| Prompt as sent | "Restate this churn label in the four-element form of Section 3.5 — numerator concept, denominator, window, filters and eligibility. Use only what I give you. If an element is not determined by what I supplied, write UNSPECIFIED. Do not propose a definition of your own." |
| Output received | A four-element restatement, but it supplied a ninety-day inactivity window instead of marking the window UNSPECIFIED. |
| Prediction recorded first | Three of four elements determined by what I supplied; the window is the one I had not stated, so it should come back UNSPECIFIED. |
| Decision | Modified |
| Error or limitation found | Analytical: the label improvisation named in Section 9.11. It invented a ninety-day inactivity window rather than declaring the window unspecified. |
| Verification performed | Compared each element against Section 9.3's definition. The window is January 1 through June 30, 2026, and eligibility is the two-part Chapter 8 rule; neither was in my prompt. |
| Change to the final work | Used Section 9.3's window and eligibility rule verbatim in the notebook's label cell, and added the eligibility rule to the prompt for later exchanges. |
| Analyst judgment, and what it taught you | The window is a measurement decision and mine to make. An assistant asked for a definition will supply one; asking it to mark gaps only works if the prompt says so, and even then it must be checked. |

### E2 — Analyze

| Field | Entry |
|---|---|
| Tool and version | General-purpose assistant, version not displayed, public web tool |
| Prompt as sent | "Here are ten customers with churn_prob and churned. Write a function that returns TP, FP, FN, and TN at a threshold I pass in, and assert that the four cells sum to the number of customers. State the four counts you expect at 0.50 before you write the code. Narrate nothing." |
| Output received | The function, the assertion, and a stated expectation of TP 2, FP 2, FN 1, TN 5 at 0.50. |
| Prediction recorded first | At 0.50: TP 2, FP 2, FN 1, TN 5, summing to 10. |
| Decision | Accepted |
| Error or limitation found | None material. It initially returned the cells in scikit-learn order, which is TN, FP, FN, TP; I relabeled rather than reordered. |
| Verification performed | Re-added the four cells by hand from the printed table: 2 + 2 + 1 + 5 = 10, which is the evaluated population. |
| Change to the final work | Kept the function; renamed its return values so the reading order matches Table 9.3. |
| Analyst judgment, and what it taught you | Cell order is a real hazard when the matrix is quoted rather than plotted. From here on the prompt names the order I want. |

### E3 — Analyze

| Field | Entry |
|---|---|
| Tool and version | General-purpose assistant, version not displayed, public web tool |
| Prompt as sent | "What threshold should I use for this churn model?" |
| Output received | "0.5 is the standard threshold for binary classification", followed by a confusion matrix cut at 0.5 and an accuracy figure. |
| Prediction recorded first | None recorded — this was a deliberately loose prompt, and the point was to see what it would supply unprompted. |
| Decision | Rejected |
| Error or limitation found | Analytical: the silent threshold named in Section 9.11. It chose an operating point without asking for a cost, and did not say it was choosing. |
| Verification performed | Re-derived the cut from the stated costs: $12 ÷ $40 = 0.30. Checked the sensitivity: at a $30 benefit the cut moves to 0.40, at $60 to 0.20. |
| Change to the final work | Set the threshold to 0.30 in the notebook, with the arithmetic in a comment above it and the $12 and $40 named as constants. |
| Analyst judgment, and what it taught you | A threshold is a cost assumption. Nobody agreed to 0.5, and 0.5 is not more neutral than 0.30 — it is a different bet on which error is cheaper. |

### E4 — Analyze

| Field | Entry |
|---|---|
| Tool and version | General-purpose assistant, version not displayed, public web tool |
| Prompt as sent | "Build a table comparing these policies on the ten customers: treat nobody, the model at 0.50, the model at 0.30, and treat everyone. Cost is $12 per treated customer and a reached churner is worth $40. Report TP, FP, FN, TN, treated, and net. Narrate nothing." |
| Output received | The four-policy table, with nets of $0, +$32, +$48, and $0. |
| Prediction recorded first | Treat everyone nets exactly zero, because ten treatments at $12 is $120 and three saves at $40 is $120. |
| Decision | Modified |
| Error or limitation found | Analytical: the missing opponent. My prompt named four policies and omitted the incumbent ninety-day rule, and the assistant did not ask for it. |
| Verification performed | Priced all five policies by hand. Ninety-day rule: four treated for $48, one churner reached for $40, net −$8. |
| Change to the final work | Added the ninety-day rule as a fifth row, so the table now shows the incumbent losing money where the model at 0.30 nets +$48. |
| Analyst judgment, and what it taught you | The omission was mine, not the tool's. A comparison without the incumbent is not a comparison, and the prompt has to carry the opponent. |

### E5 — Explain

| Field | Entry |
|---|---|
| Tool and version | General-purpose assistant, version not displayed, public web tool |
| Prompt as sent | "Write two sentences summarizing this table for a marketing director. Use only the figures in it. Do not assert that any individual customer will churn." |
| Output received | Two fluent sentences, the first of which read "the model identifies the six customers who will churn." |
| Prediction recorded first | It will reach for a verdict verb; Section 9.11 names this as the verdict language failure. |
| Decision | Modified |
| Error or limitation found | Communication: a verdict verb, and a wrong count. Six is the treated list at 0.30; the churners are 3. |
| Verification performed | Checked each number in the sentence against the table: six treated, 3 of them churners, 3 of them not. Graded the verb against Section 7.2's registry. |
| Change to the final work | Rewrote as: the model ranks customers by estimated churn probability, and treating the 6 above 0.30 reaches all 3 churners at a net of +$48 on these ten customers. |
| Analyst judgment, and what it taught you | The instruction not to assert individual churn was in the prompt and was ignored. A prohibition in a prompt is a preference, not a control; the control is reading the output. |

## D.5.5 Verification evidence

| Claim or output checked | Prediction, recorded first | Verification method | Expected value or condition | Actual result | Verdict | Action taken | Evidence location |
|---|---|---|---|---|---|---|---|
| The confusion matrix at the 0.50 threshold | TP 2, FP 2, FN 1, TN 5 | Re-added by hand from the printed table | The four cells sum to 10, the evaluated population | TP 2, FP 2, FN 1, TN 5; sum 10 | Pass | None needed | Cell 6 · E2 |
| The confusion matrix at the 0.30 threshold | Recall rises to 1.00; accuracy does not move | Re-added by hand from the printed table | TP 3, FP 3, FN 0, TN 4; accuracy still 0.70 | TP 3, FP 3, FN 0, TN 4; accuracy 0.70; recall 1.00 | Pass | Recorded that accuracy is unmoved between two policies worth $32 and $48 | Cell 8 |
| The threshold | 0.30, from the published costs | Re-derived from stated costs | $12 ÷ $40 | 0.30; sensitivity 0.40 at a $30 benefit and 0.20 at $60 | Pass | Replaced the assistant's 0.5; recorded the rejection | Cell 9 · E3 |
| The expected value of a save | $40 | Hand calculation | 0.25 × $160 | $40 | Pass | Confirmed the benefit constant used everywhere else | Cell 9 |
| The five-policy ledger | Treat everyone nets exactly zero | Hand calculation on the printed table | 10 × $12 spent against 3 × $40 reached | $0, +$32, +$48, −$8, $0 across the five policies | Pass | Added the ninety-day rule after the check exposed its absence | Cell 11 · E4 |
| The base rate and the majority-class floor | Base rate near 0.30; the do-nothing rule is 0.70 accurate | Counted from the label column | 3 churners in 10; floor 0.70 | Base rate 0.30; floor 0.70 | Pass | Put the floor beside every accuracy figure | Cell 5 |
| The summary sentence | It will contain a verdict verb | Clause-by-clause check against the table, and the verb graded against Section 7.2's registry | Every number appears in the table; no verb stronger than the evidence licenses | One verdict verb and one wrong count found and removed | Pass | Rewrote the sentence; recorded the rejection | Memo ¶1 · E5 |

## D.5.6 Rejected, corrected, or bounded output

| Output, claim, limitation, or suggestion | Disposition | Reason for disposition | Evidence used | What appears in the final work |
|---|---|---|---|---|
| "0.5 is the standard threshold for binary classification." | Rejected | It chose an operating point without a cost and without saying it was choosing. At 0.5 this program leaves a churner untreated to avoid two vouchers, and the vouchers are cheaper. | The published costs: $12 per treatment, $40 per reached churner. 12 ÷ 40 = 0.30. | The threshold is 0.30, with the arithmetic printed above it and its sensitivity at $30 and $60 shown. |
| "The model identifies the six customers who will churn." | Corrected | A verdict verb on a probability, and a count that confuses the treated list with the churners. | The table: 6 treated, 3 churners, 3 false positives. | "The model ranks customers by estimated churn probability, and treating the 6 above 0.30 reaches all 3 churners." |
| The suggestion to resample the training data so the classes balance. | Declined | Resampling distorts the probability scale, and every dollar figure in this record descends from a probability. Section 9.11 names the rebalancing reflex. | The economics depend on p, not on the ranking alone; a rescaled p invalidates the $40 expected-benefit arithmetic. | Nothing from this exchange entered the work. The class imbalance is reported as the base rate instead. |
| The model's ordering quality on ten customers. | Limited | Ten rows cannot support a fitted model, a calibration exhibit, or a sealed test set. | The record's own verification table: every check here is arithmetic on published figures, not an out-of-sample grade. | The 0.30 threshold is derived and its arithmetic shown, and the record states that it has not been graded on a holdout. |

## D.5.7 Analyst-of-record statement

> I remain responsible for the submitted analysis. I reviewed the AI-assisted output identified above, made the decisions recorded in this record, and verified the final work using the evidence listed. I can explain the code, the calculations, the visualizations, and the recommendations in this submission. The remaining limitations are that ten customers cannot support a fitted model or a calibration exhibit, so the 0.30 threshold is derived here but not yet graded on a sealed test set, and the ninety-day rule is compared as a single operating point rather than as a ranker.

Name: [STUDENT NAME] · Date: [DATE]

## D.5.8 Group contribution record

| Member | AI-assisted task performed | Verification performed | Final artifact contribution | Peer confirmation |
|---|---|---|---|---|
| Not a group submission | — | — | — | — |
