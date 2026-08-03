# -*- coding: utf-8 -*-
"""Build every Appendix D companion file from one source.

The published appendix, the Word form, the spreadsheet, and the Markdown
record all draw their field names from `content.py`, so a field cannot be
renamed in one format and not the others.  The worked example's figures are
recomputed here from Chapter 9's published inputs rather than typed.
"""

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docxkit import new_document, para, add_table  # noqa: E402
import content as C                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COMP = os.path.abspath(os.path.join(HERE, "..", "companion"))
WEX = os.path.join(COMP, "worked_example")
os.makedirs(WEX, exist_ok=True)

EX_NAMES = [f for _, f, _, _ in C.EXCHANGE_FIELDS]
VE_NAMES = [f for f, _ in C.VERIFICATION_FIELDS]
TOOL_NAMES = [f for f, _ in C.TOOL_FIELDS]
GRP_NAMES = [f for f, _ in C.GROUP_FIELDS]
REJ_NAMES = [f for f, _ in C.REJECTED_FIELDS]


def write_csv(path, header, rows=()):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


# ===========================================================================
# 1. The Chapter 9 arithmetic, recomputed
# ===========================================================================

CUSTOMERS = [f"C{n:03d}" for n in range(1, 11)]
CHURN_PROB = [0.05, 0.35, 0.15, 0.70, 0.10, 0.90, 0.60, 0.20, 0.65, 0.45]
CHURNED = [0, 1, 0, 0, 0, 1, 1, 0, 0, 0]
LAPSED_90D = [0, 0, 0, 1, 0, 1, 0, 0, 1, 1]

COST, BENEFIT = 12.0, 40.0
SAVE_RATE, SAVE_VALUE = 0.25, 160.0


def matrix(flags):
    tp = sum(1 for f, y in zip(flags, CHURNED) if f and y)
    fp = sum(1 for f, y in zip(flags, CHURNED) if f and not y)
    fn = sum(1 for f, y in zip(flags, CHURNED) if not f and y)
    tn = sum(1 for f, y in zip(flags, CHURNED) if not f and not y)
    return tp, fp, fn, tn


def rates(tp, fp, fn, tn):
    n = tp + fp + fn + tn
    acc = (tp + tn) / n
    prec = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * prec * rec / (prec + rec)) if prec and rec else None
    return acc, prec, rec, f1


def net(flags):
    treated = sum(flags)
    tp = matrix(flags)[0]
    return treated * COST, tp * BENEFIT, tp * BENEFIT - treated * COST


at50 = [1 if p >= 0.50 else 0 for p in CHURN_PROB]
at30 = [1 if p >= 0.30 else 0 for p in CHURN_PROB]
nobody = [0] * 10
everyone = [1] * 10

M50, M30 = matrix(at50), matrix(at30)
R50, R30 = rates(*M50), rates(*M30)
POLICIES = [
    ("Treat nobody", nobody),
    ("Model at 0.50", at50),
    ("Model at 0.30", at30),
    ("Ninety-day rule", LAPSED_90D),
    ("Treat everyone", everyone),
]
NETS = {name: net(flags) for name, flags in POLICIES}
THRESHOLD = COST / BENEFIT
BASE_RATE = sum(CHURNED) / len(CHURNED)
MAJORITY = 1 - BASE_RATE

failures = []


def assert_(label, actual, expected, tol=1e-9):
    ok = abs(actual - expected) <= tol if isinstance(expected, float) \
        else actual == expected
    if not ok:
        failures.append(f"{label}: got {actual!r}, expected {expected!r}")


# Every figure Chapter 9 publishes for the miniature.
assert_("threshold = COST / BENEFIT", THRESHOLD, 0.30)
assert_("expected value of a save", SAVE_RATE * SAVE_VALUE, BENEFIT)
assert_("sensitivity at $30 benefit", COST / 30.0, 0.40)
assert_("sensitivity at $60 benefit", COST / 60.0, 0.20)
assert_("base rate", BASE_RATE, 0.30)
assert_("majority-class floor", MAJORITY, 0.70)
assert_("matrix at 0.50", M50, (2, 2, 1, 5))
assert_("matrix at 0.30", M30, (3, 3, 0, 4))
assert_("matrix at 0.50 sums to n", sum(M50), 10)
assert_("matrix at 0.30 sums to n", sum(M30), 10)
assert_("accuracy at 0.50", R50[0], 0.70)
assert_("precision at 0.50", R50[1], 0.50)
assert_("recall at 0.50", round(R50[2], 2), 0.67)
assert_("F1 at 0.50", round(R50[3], 2), 0.57)
assert_("accuracy at 0.30", R30[0], 0.70)
assert_("precision at 0.30", R30[1], 0.50)
assert_("recall at 0.30", R30[2], 1.00)
assert_("F1 at 0.30", round(R30[3], 2), 0.67)
assert_("net, treat nobody", NETS["Treat nobody"][2], 0.0)
assert_("net, model at 0.50", NETS["Model at 0.50"][2], 32.0)
assert_("net, model at 0.30", NETS["Model at 0.30"][2], 48.0)
assert_("net, ninety-day rule", NETS["Ninety-day rule"][2], -8.0)
assert_("net, treat everyone", NETS["Treat everyone"][2], 0.0)
assert_("0.50 cut treats four", sum(at50), 4)
assert_("0.30 cut treats six", sum(at30), 6)
assert_("ninety-day rule treats four", sum(LAPSED_90D), 4)

with open(os.path.join(WEX, "arithmetic_check.json"), "w",
          encoding="utf-8") as fh:
    json.dump({
        "source": "Chapter 9, Code 9.1 and Code 9.2 (ten-customer "
                  "miniature), figures as published",
        "checks_run": 26,
        "all_passed": not failures,
        "failures": failures,
        "threshold": THRESHOLD,
        "matrix_at_0_50": {"TP": M50[0], "FP": M50[1], "FN": M50[2],
                           "TN": M50[3]},
        "matrix_at_0_30": {"TP": M30[0], "FP": M30[1], "FN": M30[2],
                           "TN": M30[3]},
        "policy_net": {k: v[2] for k, v in NETS.items()},
    }, fh, indent=2)

# ===========================================================================
# 2. Machine-readable field set
# ===========================================================================

write_csv(os.path.join(COMP, "Appendix_D_field_set.csv"),
          ["field_id", "field_name", "what_goes_in_it", "chapter_1_source"],
          [[i, f, w, s] for i, f, w, s in C.EXCHANGE_FIELDS] +
          [[f"V{n}", f, w, ""] for n, (f, w)
           in enumerate(C.VERIFICATION_FIELDS, 1)] +
          [[f"T{n}", f, w, ""] for n, (f, w)
           in enumerate(C.TOOL_FIELDS, 1)] +
          [[f"R{n}", f, w, ""] for n, (f, w)
           in enumerate(C.REJECTED_FIELDS, 1)] +
          [[f"G{n}", f, w, ""] for n, (f, w)
           in enumerate(C.GROUP_FIELDS, 1)])

# ===========================================================================
# 3. Blank spreadsheet sheets
# ===========================================================================

write_csv(os.path.join(COMP, "Appendix_D_exchange_log.csv"), EX_NAMES)
write_csv(os.path.join(COMP, "Appendix_D_verification_evidence.csv"), VE_NAMES)
write_csv(os.path.join(COMP, "Appendix_D_tools_used.csv"), TOOL_NAMES)
write_csv(os.path.join(COMP, "Appendix_D_group_contributions.csv"), GRP_NAMES)
write_csv(os.path.join(COMP, "Appendix_D_rejected_or_corrected.csv"), REJ_NAMES)

# ===========================================================================
# 4. The worked example, as data
# ===========================================================================

WEX_HEADER = {
    "Student name": "[STUDENT NAME]",
    "Group name and members, if applicable": "Not a group submission",
    "Course and section": "INTG1-GC 2300, Section [SECTION]",
    "Assignment or project": "Worked example — the Chapter 9 threshold "
                             "arithmetic on the ten-customer miniature "
                             "published in Code 9.1 and Code 9.2. Not a "
                             "graded exercise.",
    "Submission date": "[DATE]",
    "Notebook, workbook, dashboard, or report filename":
        "Ch09_threshold_walkthrough.ipynb",
    "Version of the submitted artifact": "v1.2",
}

WEX_TOOLS = [[
    "General-purpose assistant", "Not displayed", "Public web tool",
    "[DATE] to [DATE]",
    "Problem framing; code drafting; analytical interpretation; "
    "writing or editing",
]]

WEX_PRIVACY = [
    ["What information was supplied to the tool?",
     "The ten-row miniature printed in Code 9.1 — customer_id, "
     "churn_prob, churned, lapsed_90d — and the three cost figures "
     "Section 9.9 publishes. No file was uploaded."],
    ["What kind of information was it?",
     "Course-provided and synthetic. StyleCraft is a fictional retailer and "
     "the miniature is printed in the chapter."],
    ["Were any personal identifiers, credentials, proprietary records, or "
     "restricted data supplied?",
     "No."],
    ["What safeguards were used?",
     "Ten synthetic rows pasted as text; no connection to any live system; "
     "no real customer data at any point."],
]

WEX_EXCHANGES = [
    {
        "Exchange ID": "E1",
        "Stage": "Specify",
        "Tool and version": "General-purpose assistant, version not displayed, public web tool",
        "Prompt as sent":
            "\"Restate this churn label in the four-element form of Section "
            "3.5 — numerator concept, denominator, window, filters and "
            "eligibility. Use only what I give you. If an element is not "
            "determined by what I supplied, write UNSPECIFIED. Do not "
            "propose a definition of your own.\"",
        "Output received":
            "A four-element restatement, but it supplied a ninety-day "
            "inactivity window instead of marking the window UNSPECIFIED.",
        "Prediction recorded first":
            "Three of four elements determined by what I supplied; the "
            "window is the one I had not stated, so it should come back "
            "UNSPECIFIED.",
        "Decision": "Modified",
        "Error or limitation found":
            "Analytical: the label improvisation named in Section 9.11. It "
            "invented a ninety-day inactivity window rather than declaring "
            "the window unspecified.",
        "Verification performed":
            "Compared each element against Section 9.3's definition. The "
            "window is January 1 through June 30, 2026, and eligibility is "
            "the two-part Chapter 8 rule; neither was in my prompt.",
        "Change to the final work":
            "Used Section 9.3's window and eligibility rule verbatim in the "
            "notebook's label cell, and added the eligibility rule to the "
            "prompt for later exchanges.",
        "Analyst judgment, and what it taught you":
            "The window is a measurement decision and mine to make. An "
            "assistant asked for a definition will supply one; asking it to "
            "mark gaps only works if the prompt says so, and even then it "
            "must be checked.",
    },
    {
        "Exchange ID": "E2",
        "Stage": "Analyze",
        "Tool and version": "General-purpose assistant, version not displayed, public web tool",
        "Prompt as sent":
            "\"Here are ten customers with churn_prob and churned. Write a "
            "function that returns TP, FP, FN, and TN at a threshold I pass "
            "in, and assert that the four cells sum to the number of "
            "customers. State the four counts you expect at 0.50 before you "
            "write the code. Narrate nothing.\"",
        "Output received":
            "The function, the assertion, and a stated expectation of "
            "TP 2, FP 2, FN 1, TN 5 at 0.50.",
        "Prediction recorded first":
            "At 0.50: TP 2, FP 2, FN 1, TN 5, summing to 10.",
        "Decision": "Accepted",
        "Error or limitation found":
            "None material. It initially returned the cells in scikit-learn "
            "order, which is TN, FP, FN, TP; I relabeled rather than "
            "reordered.",
        "Verification performed":
            "Re-added the four cells by hand from the printed table: "
            f"{M50[0]} + {M50[1]} + {M50[2]} + {M50[3]} = {sum(M50)}, "
            "which is the evaluated population.",
        "Change to the final work":
            "Kept the function; renamed its return values so the reading "
            "order matches Table 9.3.",
        "Analyst judgment, and what it taught you":
            "Cell order is a real hazard when the matrix is quoted rather "
            "than plotted. From here on the prompt names the order I want.",
    },
    {
        "Exchange ID": "E3",
        "Stage": "Analyze",
        "Tool and version": "General-purpose assistant, version not displayed, public web tool",
        "Prompt as sent":
            "\"What threshold should I use for this churn model?\"",
        "Output received":
            "\"0.5 is the standard threshold for binary classification\", "
            "followed by a confusion matrix cut at 0.5 and an accuracy "
            "figure.",
        "Prediction recorded first":
            "None recorded — this was a deliberately loose prompt, and "
            "the point was to see what it would supply unprompted.",
        "Decision": "Rejected",
        "Error or limitation found":
            "Analytical: the silent threshold named in Section 9.11. It "
            "chose an operating point without asking for a cost, and did "
            "not say it was choosing.",
        "Verification performed":
            f"Re-derived the cut from the stated costs: ${COST:.0f} ÷ "
            f"${BENEFIT:.0f} = {THRESHOLD:.2f}. Checked the sensitivity: at "
            f"a ${30:.0f} benefit the cut moves to {COST/30:.2f}, at "
            f"${60:.0f} to {COST/60:.2f}.",
        "Change to the final work":
            f"Set the threshold to {THRESHOLD:.2f} in the notebook, with "
            f"the arithmetic in a comment above it and the ${COST:.0f} and "
            f"${BENEFIT:.0f} named as constants.",
        "Analyst judgment, and what it taught you":
            "A threshold is a cost assumption. Nobody agreed to 0.5, and "
            "0.5 is not more neutral than 0.30 — it is a different bet "
            "on which error is cheaper.",
    },
    {
        "Exchange ID": "E4",
        "Stage": "Analyze",
        "Tool and version": "General-purpose assistant, version not displayed, public web tool",
        "Prompt as sent":
            "\"Build a table comparing these policies on the ten customers: "
            "treat nobody, the model at 0.50, the model at 0.30, and treat "
            f"everyone. Cost is ${COST:.0f} per treated customer and a "
            f"reached churner is worth ${BENEFIT:.0f}. Report TP, FP, FN, "
            "TN, treated, and net. Narrate nothing.\"",
        "Output received":
            "The four-policy table, with nets of $0, +$32, +$48, and $0.",
        "Prediction recorded first":
            "Treat everyone nets exactly zero, because ten treatments at "
            f"${COST:.0f} is ${10*COST:.0f} and three saves at "
            f"${BENEFIT:.0f} is ${3*BENEFIT:.0f}.",
        "Decision": "Modified",
        "Error or limitation found":
            "Analytical: the missing opponent. My prompt named four "
            "policies and omitted the incumbent ninety-day rule, and the "
            "assistant did not ask for it.",
        "Verification performed":
            "Priced all five policies by hand. Ninety-day rule: four "
            f"treated for ${4*COST:.0f}, one churner reached for "
            f"${BENEFIT:.0f}, net −${abs(NETS['Ninety-day rule'][2]):.0f}.",
        "Change to the final work":
            "Added the ninety-day rule as a fifth row, so the table now "
            "shows the incumbent losing money where the model at 0.30 nets "
            f"+${NETS['Model at 0.30'][2]:.0f}.",
        "Analyst judgment, and what it taught you":
            "The omission was mine, not the tool's. A comparison without "
            "the incumbent is not a comparison, and the prompt has to carry "
            "the opponent.",
    },
    {
        "Exchange ID": "E5",
        "Stage": "Explain",
        "Tool and version": "General-purpose assistant, version not displayed, public web tool",
        "Prompt as sent":
            "\"Write two sentences summarizing this table for a marketing "
            "director. Use only the figures in it. Do not assert that any "
            "individual customer will churn.\"",
        "Output received":
            "Two fluent sentences, the first of which read \"the model "
            "identifies the six customers who will churn.\"",
        "Prediction recorded first":
            "It will reach for a verdict verb; Section 9.11 names this as "
            "the verdict language failure.",
        "Decision": "Modified",
        "Error or limitation found":
            "Communication: a verdict verb, and a wrong count. Six is the "
            f"treated list at {THRESHOLD:.2f}; the churners are "
            f"{sum(CHURNED)}.",
        "Verification performed":
            "Checked each number in the sentence against the table: six "
            f"treated, {M30[0]} of them churners, {M30[1]} of them not. "
            "Graded the verb against Section 7.2's registry.",
        "Change to the final work":
            "Rewrote as: the model ranks customers by estimated churn "
            f"probability, and treating the {sum(at30)} above "
            f"{THRESHOLD:.2f} reaches all {sum(CHURNED)} churners at a net "
            f"of +${NETS['Model at 0.30'][2]:.0f} on these ten customers.",
        "Analyst judgment, and what it taught you":
            "The instruction not to assert individual churn was in the "
            "prompt and was ignored. A prohibition in a prompt is a "
            "preference, not a control; the control is reading the output.",
    },
]

WEX_VERIFICATION = [
    ["The confusion matrix at the 0.50 threshold",
     "TP 2, FP 2, FN 1, TN 5",
     "Re-added by hand from the printed table",
     "The four cells sum to 10, the evaluated population",
     f"TP {M50[0]}, FP {M50[1]}, FN {M50[2]}, TN {M50[3]}; sum {sum(M50)}",
     "Pass", "None needed", "Cell 6 · E2"],
    ["The confusion matrix at the 0.30 threshold",
     "Recall rises to 1.00; accuracy does not move",
     "Re-added by hand from the printed table",
     "TP 3, FP 3, FN 0, TN 4; accuracy still 0.70",
     f"TP {M30[0]}, FP {M30[1]}, FN {M30[2]}, TN {M30[3]}; "
     f"accuracy {R30[0]:.2f}; recall {R30[2]:.2f}",
     "Pass",
     "Recorded that accuracy is unmoved between two policies worth $32 "
     "and $48",
     "Cell 8"],
    ["The threshold",
     f"{THRESHOLD:.2f}, from the published costs",
     "Re-derived from stated costs",
     f"${COST:.0f} ÷ ${BENEFIT:.0f}",
     f"{THRESHOLD:.2f}; sensitivity {COST/30:.2f} at a $30 benefit and "
     f"{COST/60:.2f} at $60",
     "Pass",
     "Replaced the assistant's 0.5; recorded the rejection",
     "Cell 9 · E3"],
    ["The expected value of a save",
     f"${BENEFIT:.0f}",
     "Hand calculation",
     f"{SAVE_RATE} × ${SAVE_VALUE:.0f}",
     f"${SAVE_RATE * SAVE_VALUE:.0f}",
     "Pass",
     "Confirmed the benefit constant used everywhere else",
     "Cell 9"],
    ["The five-policy ledger",
     "Treat everyone nets exactly zero",
     "Hand calculation on the printed table",
     f"10 × ${COST:.0f} spent against {sum(CHURNED)} × "
     f"${BENEFIT:.0f} reached",
     "$0, +$32, +$48, −$8, $0 across the five policies",
     "Pass",
     "Added the ninety-day rule after the check exposed its absence",
     "Cell 11 · E4"],
    ["The base rate and the majority-class floor",
     "Base rate near 0.30; the do-nothing rule is 0.70 accurate",
     "Counted from the label column",
     "3 churners in 10; floor 0.70",
     f"Base rate {BASE_RATE:.2f}; floor {MAJORITY:.2f}",
     "Pass",
     "Put the floor beside every accuracy figure",
     "Cell 5"],
    ["The summary sentence",
     "It will contain a verdict verb",
     "Clause-by-clause check against the table, and the verb graded "
     "against Section 7.2's registry",
     "Every number appears in the table; no verb stronger than the "
     "evidence licenses",
     "One verdict verb and one wrong count found and removed",
     "Pass",
     "Rewrote the sentence; recorded the rejection",
     "Memo ¶1 · E5"],
]

WEX_REJECTED = [
    ["\"0.5 is the standard threshold for binary classification.\"",
     "Rejected",
     "It chose an operating point without a cost and without saying it was "
     "choosing. At 0.5 this program leaves a churner untreated to avoid two "
     "vouchers, and the vouchers are cheaper.",
     f"The published costs: ${COST:.0f} per treatment, ${BENEFIT:.0f} per "
     f"reached churner. {COST:.0f} ÷ {BENEFIT:.0f} = {THRESHOLD:.2f}.",
     f"The threshold is {THRESHOLD:.2f}, with the arithmetic printed above "
     "it and its sensitivity at $30 and $60 shown."],
    ["\"The model identifies the six customers who will churn.\"",
     "Corrected",
     "A verdict verb on a probability, and a count that confuses the "
     "treated list with the churners.",
     f"The table: {sum(at30)} treated, {M30[0]} churners, {M30[1]} false "
     "positives.",
     "\"The model ranks customers by estimated churn probability, and "
     f"treating the {sum(at30)} above {THRESHOLD:.2f} reaches all "
     f"{sum(CHURNED)} churners.\""],
    ["The suggestion to resample the training data so the classes balance.",
     "Declined",
     "Resampling distorts the probability scale, and every dollar figure in "
     "this record descends from a probability. Section 9.11 names the "
     "rebalancing reflex.",
     "The economics depend on p, not on the ranking alone; a rescaled p "
     f"invalidates the ${BENEFIT:.0f} expected-benefit arithmetic.",
     "Nothing from this exchange entered the work. The class imbalance is "
     "reported as the base rate instead."],
    ["The model's ordering quality on ten customers.",
     "Limited",
     "Ten rows cannot support a fitted model, a calibration exhibit, or a "
     "sealed test set.",
     "The record's own verification table: every check here is arithmetic "
     "on published figures, not an out-of-sample grade.",
     f"The {THRESHOLD:.2f} threshold is derived and its arithmetic shown, "
     "and the record states that it has not been graded on a holdout."],
]

WEX_STATEMENT = (
    "I remain responsible for the submitted analysis. I reviewed the "
    "AI-assisted output identified above, made the decisions recorded in "
    "this record, and verified the final work using the evidence listed. I "
    "can explain the code, the calculations, the visualizations, and the "
    "recommendations in this submission. The remaining limitations are that "
    "ten customers cannot support a fitted model or a calibration exhibit, "
    f"so the {THRESHOLD:.2f} threshold is derived here but not yet graded "
    "on a sealed test set, and the ninety-day rule is compared as a single "
    "operating point rather than as a ranker."
)

# ===========================================================================
# 5. Markdown records
# ===========================================================================


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("\n", " ")
                                     .replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def md_record(completed):
    L = []
    A = L.append
    title = ("Appendix D — AI-Use Record (completed example)"
             if completed else "Appendix D — AI-Use Record")
    A(f"# {title}\n")
    if not completed:
        A("Replace every bracketed placeholder. A submitted record that "
          "still contains one has not been completed. Field names are the "
          "published ones and must not be renamed.\n")
    A("## D.5.1 Assignment and analyst information\n")
    info = (WEX_HEADER if completed else {
        k: "[" + k.upper().replace(" ", " ") + "]" for k in WEX_HEADER})
    A(md_table(["Field", "Response"], list(info.items())) + "\n")

    A("## D.5.2 AI tools used\n")
    A(md_table(TOOL_NAMES, WEX_TOOLS if completed
               else [["[" + n.upper() + "]" for n in TOOL_NAMES]]) + "\n")

    A("## D.5.3 Data and privacy declaration\n")
    A(md_table(["Question", "Response"],
               WEX_PRIVACY if completed
               else [[q, ""] for q, _ in C.PRIVACY_QUESTIONS]) + "\n")
    A("Sign exactly one of the three statements below. They are mutually "
      "exclusive.\n")
    A(md_table(["Statement", "Sign it when", "Signed"],
               [[a, b, "Yes" if (completed and a.startswith("1.")) else ""]
                for a, b in C.PRIVACY_STATUSES]) + "\n")

    A("## D.5.4 Exchange log\n")
    if completed:
        for ex in WEX_EXCHANGES:
            A(f"### {ex['Exchange ID']} — {ex['Stage']}\n")
            A(md_table(["Field", "Entry"],
                       [[k, v] for k, v in ex.items()
                        if k not in ("Exchange ID", "Stage")]) + "\n")
    else:
        A(md_table(["Field", "Entry"], [[n, ""] for n in EX_NAMES]))
        A("\nRepeat the block above once per meaningful exchange.\n")

    A("## D.5.5 Verification evidence\n")
    A(md_table(VE_NAMES, WEX_VERIFICATION if completed
               else [[""] * len(VE_NAMES)]) + "\n")

    A("## D.5.6 Rejected, corrected, or bounded output\n")
    A(md_table(REJ_NAMES, WEX_REJECTED if completed
               else [[""] * len(REJ_NAMES)]) + "\n")

    A("## D.5.7 Analyst-of-record statement\n")
    A("> " + (WEX_STATEMENT if completed else
              "I remain responsible for the submitted analysis. I reviewed "
              "the AI-assisted output identified above, made the decisions "
              "recorded in this record, and verified the final work using "
              "the evidence listed. I can explain the code, the "
              "calculations, the visualizations, and the recommendations in "
              "this submission. The remaining limitations are "
              "[LIMITATIONS].") + "\n")
    A("Name: " + ("[STUDENT NAME]" if completed else "[NAME]")
      + " · Date: [DATE]\n")

    A("## D.5.8 Group contribution record\n")
    A(md_table(GRP_NAMES,
               [["Not a group submission", "—", "—", "—", "—"]]
               if completed else [[""] * len(GRP_NAMES)]) + "\n")
    return "\n".join(L)


open(os.path.join(COMP, "Appendix_D_AI_Use_Record_FORM.md"), "w",
     encoding="utf-8").write(md_record(False))
open(os.path.join(WEX, "Appendix_D_Worked_Example_COMPLETED.md"), "w",
     encoding="utf-8").write(md_record(True))

# ===========================================================================
# 6. Word forms
# ===========================================================================


def word_record(path, completed):
    doc = new_document()
    para(doc, "ChapterTitle", "Appendix D")
    para(doc, "ChapterSubtitle",
         "AI-Use Record — completed example" if completed
         else "AI-Use Record")
    para(doc, "Byline", "Applied Business Analytics for Marketing "
                        "Decision-Making")
    para(doc, "Byline", "Version 1.0 · August 2026 · CC BY 4.0")

    if completed:
        para(doc, "BodyText",
             "This is one assignment documented from beginning to end, using "
             "the ten-customer miniature Chapter 9 publishes in Code 9.1 and "
             "Code 9.2. Every figure in it was recomputed from those inputs "
             "rather than typed. It answers no graded exercise.")
    else:
        para(doc, "BodyText",
             "Replace every bracketed placeholder. A submitted record that "
             "still contains one has not been completed. The field names "
             "below are the published ones and must not be renamed.")

    para(doc, "Heading1", "D.5.1 Assignment and Analyst Information")
    info = (list(WEX_HEADER.items()) if completed
            else [[k, ""] for k in WEX_HEADER])
    add_table(doc, "1", "Assignment and analyst information",
              ["Field", "Response"], info, widths=[4680, 4680])

    para(doc, "Heading1", "D.5.2 AI Tools Used")
    para(doc, "BodyText", "One block per tool. Table 2 records them.")
    add_table(doc, "2", "AI tools used",
              TOOL_NAMES,
              WEX_TOOLS if completed else [[""] * len(TOOL_NAMES)],
              widths=[1700, 1700, 2200, 1700, 2060])

    para(doc, "Heading1", "D.5.3 Data and Privacy Declaration")
    para(doc, "BodyText", "Table 3 is the declaration.")
    add_table(doc, "3", "Data and privacy declaration",
              ["Question", "Response"],
              WEX_PRIVACY if completed
              else [[q, ""] for q, _ in C.PRIVACY_QUESTIONS],
              widths=[3800, 5560])
    para(doc, "BodyText",
         "Sign exactly one of the three statements below. They are mutually "
         "exclusive.")
    add_table(doc, "3b", "The three declarations. Sign exactly one",
              ["Statement", "Sign it when", "Signed"],
              [[a, b, "Yes" if (completed and a.startswith("1.")) else ""]
               for a, b in C.PRIVACY_STATUSES],
              widths=[3200, 4560, 1600])

    para(doc, "Heading1", "D.5.4 Exchange Log")
    n = 4
    if completed:
        para(doc, "BodyText",
             f"One block per exchange. Tables 4 through {3 + len(WEX_EXCHANGES)}"
             " are the five meaningful exchanges in this assignment.")
        for ex in WEX_EXCHANGES:
            add_table(doc, str(n),
                      f"Exchange {ex['Exchange ID']} — {ex['Stage']}",
                      ["Field", "Entry"],
                      [[k, v] for k, v in ex.items()
                       if k not in ("Exchange ID", "Stage")],
                      widths=[2600, 6760])
            n += 1
    else:
        para(doc, "BodyText",
             "Table 4 is one exchange. Copy it once per meaningful "
             "exchange.")
        add_table(doc, "4", "One exchange", ["Field", "Entry"],
                  [[f, ""] for f in EX_NAMES], widths=[2600, 6760])
        n = 5

    para(doc, "Heading1", "D.5.5 Verification Evidence")
    para(doc, "BodyText", f"Table {n} carries the checks that mattered.")
    add_table(doc, str(n), "Verification evidence", VE_NAMES,
              WEX_VERIFICATION if completed else [[""] * len(VE_NAMES)],
              widths=[1450, 1300, 1180, 1240, 1420, 620, 1240, 910])
    n += 1

    para(doc, "Heading1", "D.5.6 Rejected, Corrected, or Bounded Output")
    para(doc, "BodyText", f"Table {n} records what did not survive intact.")
    add_table(doc, str(n), "Rejected, corrected, or bounded output",
              REJ_NAMES,
              WEX_REJECTED if completed else [[""] * len(REJ_NAMES)],
              widths=[2100, 1100, 2200, 1960, 2000])
    n += 1

    para(doc, "Heading1", "D.5.7 Analyst-of-Record Statement")
    para(doc, "BodyText",
         WEX_STATEMENT if completed else
         "I remain responsible for the submitted analysis. I reviewed the "
         "AI-assisted output identified above, made the decisions recorded "
         "in this record, and verified the final work using the evidence "
         "listed. I can explain the code, the calculations, the "
         "visualizations, and the recommendations in this submission. The "
         "remaining limitations are [LIMITATIONS].")
    para(doc, "BodyTextIndent",
         "Name: [STUDENT NAME]                    Date: [DATE]")

    para(doc, "Heading1", "D.5.8 Group Contribution Record")
    para(doc, "BodyText",
         f"Table {n} applies to group submissions only.")
    add_table(doc, str(n), "Group contribution record, one row per member",
              GRP_NAMES,
              [["Not a group submission", "—", "—", "—", "—"]]
              if completed else [[""] * len(GRP_NAMES)],
              widths=[1600, 2100, 2100, 2100, 1460])
    doc.save(path)


word_record(os.path.join(COMP, "Appendix_D_AI_Use_Record_FORM.docx"), False)
word_record(os.path.join(WEX, "Appendix_D_Worked_Example_COMPLETED.docx"),
            True)

# ===========================================================================
# 7. Spreadsheets
# ===========================================================================

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Font, Alignment  # noqa: E402


def xlsx(path, completed):
    wb = Workbook()
    sheets = [
        ("Assignment", ["Field", "Response"],
         (list(WEX_HEADER.items()) if completed
          else [[k, ""] for k in WEX_HEADER])),
        ("Tools used", TOOL_NAMES,
         WEX_TOOLS if completed else []),
        ("Data and privacy", ["Question", "Response"],
         WEX_PRIVACY if completed
         else [[q, ""] for q, _ in C.PRIVACY_QUESTIONS]),
        ("Exchange log", EX_NAMES,
         [[ex[f] for f in EX_NAMES] for ex in WEX_EXCHANGES]
         if completed else []),
        ("Verification evidence", VE_NAMES,
         WEX_VERIFICATION if completed else []),
        ("Rejected or bounded", REJ_NAMES,
         WEX_REJECTED if completed else []),
        ("Group contributions", GRP_NAMES,
         [["Not a group submission", "—", "—", "—", "—"]]
         if completed else []),
        ("Field definitions",
         ["field_id", "field_name", "what_goes_in_it", "chapter_1_source"],
         [[i, f, w, s] for i, f, w, s in C.EXCHANGE_FIELDS]),
    ]
    first = True
    for name, header, rows in sheets:
        ws = wb.active if first else wb.create_sheet()
        ws.title = name
        first = False
        ws.append(header)
        for c in ws[1]:
            c.font = Font(bold=True)
            c.alignment = Alignment(vertical="top", wrap_text=True)
        for r in rows:
            ws.append(list(r))
        for col in ws.columns:
            width = max(14, min(60, max(len(str(c.value or "")) for c in col)))
            ws.column_dimensions[col[0].column_letter].width = width
            for c in col:
                c.alignment = Alignment(vertical="top", wrap_text=True)
        ws.freeze_panes = "A2"
    wb.save(path)


xlsx(os.path.join(COMP, "Appendix_D_AI_Use_Record_FORM.xlsx"), False)
xlsx(os.path.join(WEX, "Appendix_D_Worked_Example_COMPLETED.xlsx"), True)

# ===========================================================================
# 8. README and CHANGELOG
# ===========================================================================

open(os.path.join(COMP, "README.md"), "w", encoding="utf-8").write(f"""\
# Appendix D — AI-Use Documentation Template, companion files

Every file here carries the same field names as the published appendix, and
all of them are generated from `Appendix_D_field_set.csv` by
`build_companion.py`. A field cannot be renamed in one format without being
renamed in all of them.

## The blank forms

The three forms share one stem and differ only in extension.

| File | Use it when |
|---|---|
| `Appendix_D_AI_Use_Record_FORM.docx` | The submission is a narrative assignment, a memo appendix, or a project deliverable. One vertical block per exchange. |
| `Appendix_D_AI_Use_Record_FORM.md` | The record lives in a Colab notebook or a repository |
| `Appendix_D_AI_Use_Record_FORM.xlsx` | The assignment has more than about a dozen exchanges. One exchange per row. |

The CSV files corresponding to the spreadsheet's worksheets are supplied
separately for loading in pandas or checking a submission:
`Appendix_D_exchange_log.csv`, `Appendix_D_verification_evidence.csv`,
`Appendix_D_tools_used.csv`, `Appendix_D_rejected_or_corrected.csv`, and
`Appendix_D_group_contributions.csv`. `Appendix_D_field_set.csv` carries all
{{n_fields}} published field definitions.

## The worked example

`worked_example/` documents one piece of work from beginning to end: the
Chapter 9 threshold arithmetic on the ten-customer miniature the chapter
publishes in Code 9.1 and Code 9.2, in all three formats.

Every figure in it — the {THRESHOLD:.2f} threshold, the two confusion
matrices, the five-policy ledger, the base rate — is recomputed from
Chapter 9's published inputs by `build_companion.py` rather than typed, and
`worked_example/arithmetic_check.json` records the result of those 26 checks.

The example answers no graded exercise. It uses figures the chapter already
prints, and it shows all four dispositions — rejected, corrected, limited,
and declined — because a record that carries only rejections misses the
ones that matter most in professional work.

## Retention

Keep the record and its evidence available for as long as the work can be
questioned: through the course's grading and appeal period here, and for the
period the organization requires in professional work. Then delete what you
no longer need, particularly exported conversations and any sample of data
that was a convenience rather than a requirement.

## Level 1

The compact notebook record is six lines and is reproduced in Section D.4 of
the published appendix. It is not a separate file here on purpose: it belongs
inside the notebook, beside the cell it describes, and it uses the same field
names as the exchange log so that it can be moved without rewriting.
""".replace("{n_fields}", str(len(C.EXCHANGE_FIELDS) + len(C.VERIFICATION_FIELDS) + len(C.TOOL_FIELDS) + len(C.REJECTED_FIELDS) + len(C.GROUP_FIELDS))))

open(os.path.join(COMP, "CHANGELOG.md"), "w", encoding="utf-8").write("""\
# Changelog

## v1.0 — August 2026

First release. Field set fixed at eleven exchange fields, eight verification
fields, five tool fields, four rejection fields, and five group fields, all
published in Appendix D Section D.3 and generated here from `field_set.csv`.

Worked example added: the Chapter 9 threshold arithmetic on the ten-customer
miniature, in Word, Markdown, and spreadsheet form, with the arithmetic
recomputed and asserted at build time.
""")

print("failures:", failures or "none")
print("companion files written to", COMP)
