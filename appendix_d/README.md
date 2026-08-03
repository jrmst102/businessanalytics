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
34 published field definitions.

## The worked example

`worked_example/` documents one piece of work from beginning to end: the
Chapter 9 threshold arithmetic on the ten-customer miniature the chapter
publishes in Code 9.1 and Code 9.2, in all three formats.

Every figure in it — the 0.30 threshold, the two confusion
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
