# Appendix C — Companion Files

*AI Prompting Templates for Analytics* · Version 1.0 · August 2026
Companion to `Appendix_C_AI_Prompting_Templates_for_Analytics_DRAFT.docx`

Everything in this folder is generated from the published appendix, so a prompt
cannot change on the page without changing here. Re-run `extract_library.py`
after any edit to the appendix.

## What is here

| File | What it is |
|---|---|
| `prompt_library.md` | All 19 templates and 27 prompts in one Markdown file |
| `templates/template_C01.md` … `template_C19.md` | One editable file per template |
| `prompts.txt` | Plain text, optimized for copying. Prompts only, no commentary |
| `prompt_finder.csv` | Chapter → AI-assistant section → AI in Practice box → template |
| `Appendix_C_Template_Library_EDITABLE.docx` | The same templates in Word, on the book's stylesheet |
| `worked_examples/` | Six completed examples on the practice file |
| `practice_transactions.csv` | The miniature. 20 order lines, 12 orders, 8 customers, $1,312.00 |
| `practice_transactions_raw.csv` | The same file with currency-string prices and two sentinels, for Template C.5 |
| `build_practice_file.py` | Regenerates the practice file and re-asserts every invariant |
| `build_worked_examples.py` | Regenerates the worked examples and asserts every figure they print |
| `extract_library.py` | Extracts the library from the built `.docx` |
| `build_word_library.py` | Builds the editable Word library |
| `CHANGELOG.md` | Definitional decisions and revisions |

## The practice file

`practice_transactions.csv` reproduces every invariant Appendix A publishes for
its practice file, so a figure quoted in a worked example traces to the same
miniature used in Appendices A and B:

```
20 order lines · 12 orders · 8 customers · $1,312.00 revenue · 28 units
AOV $109.33   (the line-grain trap returns $65.60)
order O10003 = 88.00 + 84.00 + 76.00 = 248.00
ten lines carry the reserved ONLINE store id
AOV $220.00 suburban against $78.00 urban
catalog prices inside the $24-$90 band
```

It is synthetic and safe to paste into an external assistant. Nothing in it is
an answer to a graded exercise.

**If the shipped `practice_transactions.csv` from Appendix A differs from this
reconstruction, replace this file with it and re-run
`build_worked_examples.py`.** Every figure in the worked examples is computed
from the file rather than typed, so the examples will regenerate correctly.

## Running the checks

```bash
python3 build_practice_file.py      # 13 invariants
python3 build_worked_examples.py    # 18 figures, and regenerates the examples
python3 ../verify.py                # 43 production checks on the .docx
```

## Using the templates

1. Find the template by task in `prompt_finder.csv` or Table C.7 of the appendix.
2. Copy the prompt from `prompts.txt`.
3. Replace every `[BRACKETED]` placeholder. Send everything else as written.
4. Write your prediction down **before** you send it.
5. Run the audit the entry names. Section C.3 of the appendix maps every audit
   instrument in the guide to the task it governs.
6. Record the exchange under Appendix D, including the output you rejected.

## The three controls

Every prompt carries these, although the wording changes by task. Do not delete
them; if a template's phrasing does not fit your task, replace it with phrasing
that does.

1. **Use only supplied information.** *Use only the fields and facts above*,
   *do not use any column not in the schema I pasted*, *use only the numbers
   above*.
2. **Expose rather than fill missing information.** `UNSPECIFIED` where the
   template asks the assistant to complete a form; *say which field is missing
   and stop*, *name any feature you cannot trace*, *say what else you need
   rather than guessing* elsewhere.
3. **Stop at the boundary of the delegated work.** *Narrate nothing yet*,
   *do not interpret*, *do not render or describe conclusions*, *choose no
   threshold yourself*, *recommend nothing yet*.

## Privacy

Never paste confidential, proprietary, or personally identifiable data into an
external AI tool. Section C.4 of the appendix states what may and may not be
supplied. The files in this folder are synthetic and safe.

CC BY 4.0.
