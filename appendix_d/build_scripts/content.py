# -*- coding: utf-8 -*-
"""Appendix D. AI-Use Documentation Template — publication draft.

Content only.  Construction lives in docxkit.py; checks live in verify.py.
"""

REPO = "https://github.com/jrmst102/businessanalytics"

# ---------------------------------------------------------------------------
# The canonical field set.  This is the single source of truth: the published
# tables, the companion Word form, the spreadsheet log, and the Markdown
# version are all generated from it, so a field cannot be renamed in one
# format and not the others.
# ---------------------------------------------------------------------------

EXCHANGE_FIELDS = [
    ("D1", "Exchange ID",
     "A short stable label — E1, E2, E3 — written beside the cell, view, or "
     "paragraph the exchange produced, so the record and the work point at "
     "each other.",
     "—"),
    ("D2", "Stage",
     "Specify, prepare, analyze, visualize, explain, document, or review. One "
     "word; it is what makes a long log searchable.",
     "—"),
    ("D3", "Tool and version",
     "The product name and whatever version string the interface displays. "
     "Record the access mode too when it is not the obvious one.",
     "Which AI tool did you use, and for which step?"),
    ("D4", "Prompt as sent",
     "The prompt in the words you actually sent, not a tidied reconstruction. "
     "Long prompts may be attached and referenced by location.",
     "What prompt did you submit?"),
    ("D5", "Output received",
     "What came back, summarized in a sentence or two, with the location of "
     "the full response if you kept it.",
     "— (promised by the Table 1.6 note)"),
    ("D6", "Prediction recorded first",
     "What you wrote down before the output was run or read: the row count, "
     "the total, the shape, the direction, the band. Blank is a finding.",
     "—"),
    ("D7", "Decision",
     "Accepted, modified, rejected, or used only to generate questions. One "
     "of the four; not a paragraph.",
     "What did you accept, revise, or reject?"),
    ("D8", "Error or limitation found",
     "Technical, analytical, factual, interpretive, or communication. Name "
     "the class and the instance.",
     "— (promised by the Table 1.6 note)"),
    ("D9", "Verification performed",
     "The check you ran and the result: the reconciled total, the hand "
     "calculation, the rerun, the baseline, the source consulted, the reader "
     "tested.",
     "How did you verify the final result?"),
    ("D10", "Change to the final work",
     "What is different in the submitted artifact because of this exchange. "
     "If nothing changed, say so and say why you kept it.",
     "—"),
    ("D11", "Analyst judgment, and what it taught you",
     "The decision you made that the tool could not make, and the one thing "
     "the exchange changed about how you will prompt or check next time.",
     "— (promised by the Table 1.6 note)"),
]

VERIFICATION_FIELDS = [
    ("Claim or output checked", "The specific number, table, chart, or "
     "sentence under test — not the assignment."),
    ("Prediction, recorded first", "What you expected, written before the "
     "check ran. A prediction written afterward verifies nothing."),
    ("Verification method", "Reconciliation, hand calculation, rerun, "
     "baseline comparison, holdout, source check, reader test."),
    ("Expected value or condition", "The figure or the condition that would "
     "count as a pass, stated in advance."),
    ("Actual result", "What the check returned, in the same units."),
    ("Verdict", "Pass, fail, or unresolved. Unresolved is a permitted "
     "verdict; a silent one is not."),
    ("Action taken", "What you did about it. A failed check with no action "
     "is an unrepaired defect, not a completed record."),
    ("Evidence location", "Where the evidence lives: cell, sheet, page, "
     "commit, file name."),
]

TOOL_FIELDS = [
    ("Product name", "Whatever the interface calls itself."),
    ("Model or version", "The version string displayed, if any. Write "
     "\"not displayed\" rather than guessing."),
    ("Access mode", "Public web tool, institutional account, embedded in "
     "Colab, embedded in another application, or local."),
    ("Dates used", "First and last date, or the single date."),
    ("Purpose categories", "One or more of the nine categories in "
     "Table D.8."),
]

PURPOSE_CATEGORIES = [
    ("Problem framing", "Turning a request into a specification; "
     "red-teaming a specification you wrote", "1–2"),
    ("Data preparation", "Drafting a cleaning or joining step whose effect "
     "on counts and totals you predicted first", "4"),
    ("Code drafting", "Writing a cell you specified, in a language you can "
     "read", "1, 4–11"),
    ("Debugging", "Explaining an error message and proposing the smallest "
     "correction", "4–11"),
    ("Method explanation", "Explaining what a method does, in terms you can "
     "check against the chapter", "1, 3–11"),
    ("Analytical interpretation", "Proposing readings of an output you have "
     "already verified", "5–11"),
    ("Visualization design", "Proposing chart specifications, encodings, "
     "layouts, or titles", "12–13"),
    ("Writing or editing", "Drafting or compressing prose that carries a "
     "finding", "13"),
    ("Adversarial review", "Arguing against your own specification, model, "
     "chart, or recommendation", "2, 7–13"),
]

PRIVACY_STATUSES = [
    ("1. No restricted information was supplied.",
     "Nothing confidential, personally identifiable, proprietary, or "
     "otherwise restricted was placed into an AI tool at any point in this "
     "work."),
    ("2. Restricted information was used only within the approved "
     "environment named above.",
     "The environment, the permission under which it was used, and the "
     "information supplied are all recorded in the table above."),
    ("3. A possible incident occurred and has been reported.",
     "Describe it above, report it to your instructor, and do not sign "
     "statement 1 or 2. Reporting an incident is not a penalty; "
     "concealing one is a different matter."),
]

PRIVACY_QUESTIONS = [
    ("What information was supplied to the tool?",
     "Name the tables, columns, and row counts, or the schema alone. "
     "\"The data\" is not an answer."),
    ("What kind of information was it?",
     "Synthetic, public, course-provided, de-identified, or confidential. "
     "The StyleCraft files are synthetic and are safe to paste."),
    ("Were any personal identifiers, credentials, proprietary records, or "
     "restricted data supplied?",
     "Yes or no. If yes, name the approved environment that permitted it, "
     "or report the incident to your instructor."),
    ("What safeguards were used?",
     "Schema only, safe sample, synthetic substitute, de-identification, "
     "aggregation, or an approved enterprise tool."),
]

REJECTED_FIELDS = [
    ("Output, claim, limitation, or suggestion",
     "Quote it. A paraphrase usually removes the thing that made it wrong, "
     "or the ambiguity that made it worth recording."),
    ("Disposition",
     "Rejected, corrected, limited, or declined. One of the four."),
    ("Reason for disposition",
     "The specific defect, ambiguity, or boundary, named."),
    ("Evidence used", "What you checked it against."),
    ("What appears in the final work",
     "The replacement, the correction, the stated limit, or the fact that "
     "nothing from this exchange was used."),
]

GROUP_FIELDS = [
    ("Member", "Name."),
    ("AI-assisted task performed", "Which exchanges, by ID."),
    ("Verification performed", "Which checks in the verification table are "
     "this member's."),
    ("Final artifact contribution", "The cells, views, sections, or "
     "paragraphs that carry this member's work."),
    ("Peer confirmation", "The initials of a second member who has read the "
     "row and agrees with it."),
]

# Chapter map: (chapter, what the chapter asks to be filed, level)
CHAPTER_MAP = [
    ("1", "Section 1.7 and the Review Before You Rely box; Exercise 1.6 asks "
     "for the compact record in the notebook and the full record for "
     "submission", "1 and 2"),
    ("2", "Section 2.8's adversarial review of your own specification; "
     "Exercise 2.7 asks for the full record", "2"),
    ("3", "Section 3.9's drafted dictionary entries and the audit of them; "
     "Exercise 3.7 asks for the full record", "2"),
    ("4", "Every delegated cleaning step, with the assistant's predicted "
     "effect on counts beside yours; Exercise 4.5 requires at least one "
     "recorded disagreement", "1 in the notebook, 2 for submission"),
    ("5", "Every drafted summary, with the denominator, the center, and the "
     "reconciliation audited; Exercise 5.5 requires at least one corrected "
     "summary", "1 in the notebook, 2 for submission"),
    ("6", "The feature build and the cluster audit; Exercise 6.6 requires "
     "the full exchange and which audit step changed your assessment most",
     "2"),
    ("7", "Both prompts of the two-prompt pattern, with the verbs graded "
     "against Section 7.2's registry; Exercise 7.6 requires the full "
     "exchange", "2"),
    ("8", "Both exchanges, plus the five-point audit written out in order; "
     "Exercise 8.6 requires every performance claim marked earned or not "
     "earned", "2"),
    ("9", "Both exchanges, plus the classification supplement; Exercise 9.6 "
     "requires the loose-prompt response and the re-prompted one, compared",
     "2"),
    ("10", "Both exchanges, plus the leaderboard band you predicted before "
     "reading the response; Exercise 10.6 requires the comparison of the two "
     "prompts", "2"),
    ("11", "Four moves — registration, analysis, adversarial review, "
     "drafting — each filed; Exercise 11.6 requires the UNSPECIFIED count "
     "and the marked-up recommendation", "2"),
    ("12", "Both exchanges of the five-step routine, plus the predicted "
     "faults, the graded prediction including false alarms, and a note per "
     "repair", "2"),
    ("13", "The exchanges — title generation and prose compression are "
     "separate tasks — with the candidates' verification lines and the "
     "clause-by-clause diff; the record travels inside the memo's appendix",
     "2"),
]

FORMAT_PARITY = [
    ("Word form", "`Appendix_D_AI_Use_Record_FORM.docx`",
     "A narrative assignment, a memo appendix, or a project deliverable"),
    ("Spreadsheet", "`Appendix_D_AI_Use_Record_FORM.xlsx`",
     "An assignment with many exchanges, or a term-long log"),
    ("Markdown", "`Appendix_D_AI_Use_Record_FORM.md`",
     "A Colab notebook, a GitHub repository, or a submission that must "
     "diff cleanly"),
    ("Google Docs and Sheets", "The Word and spreadsheet files, opened in "
     "Google Drive", "Group work with simultaneous editors"),
]
