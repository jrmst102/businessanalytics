# Appendix C — Changelog

## Version 1.0 — August 2026

First draft. Built against `Appendices_15_Writing_Blueprint.md` v1.0,
`Chapter_Style_Specification.md` v1.0, `Book_Specifications.md` v1.0, the chapter
template, and a full audit of the AI-assistant sections of Chapters 1–13.

### Decisions recorded

1. **Nineteen templates, matching the blueprint's proposed library.** Every one
   is grounded in a chapter that prints a prompt, an AI in Practice box, or a
   named delegation — with one exception, recorded below.

2. **Template C.6 (diagnose a Python error) is owned by the appendix.** No
   chapter prints a debugging prompt. Section 1.9 names debugging as a
   legitimate use and Appendix A §A.14 catalogs the recurring errors by symptom,
   so the task recurs; the prompt does not exist anywhere in the manuscript. The
   entry says so in its *Owned by* line, following the precedent Appendix B set
   for metrics with no chapter behind them.

3. **Templates are labeled `Template C.1`–`C.19`; prompts are labeled
   `Prompt C.1`–`C.27`, continuously.** Sections are numbered separately,
   `C.1`–`C.12`. This mirrors Appendix A, where code entries `Code A.1`–`A.62`
   run across sections `A.1`–`A.16`, and it preserves the blueprint's template
   numbers so a chapter cross-reference resolves.

4. **Prompts are set in the Code Block style with a Code Caption.** They are not
   code. The style is used because it preserves line breaks, is monospaced, and
   copies cleanly, which is what a prompt needs. `Chapter_Style_Specification.md`
   §4.4 documents that pairing for code only and should be amended to cover
   prompts.

5. **Bracketed placeholders are a chapter convention, not a new one.** They
   first appear in §4.10 (`[one cleaning step]`), §5.10 (`[one specific table]`),
   and §12.12 (`[paste the schema]`). Chapters 1–3 print no placeholders, so
   Templates C.1–C.4 introduce them where the chapters did not.

6. **The blueprint's four segmentation templates are published as one
   (Template C.9) with two prompts,** because Chapter 6 prints one prompt and
   states the second in prose. The blueprint's four communication templates are
   published as one (Template C.18) with two prompts, for the same reason.

7. **Error-analysis prompts are folded into the audits of Templates C.11 and
   C.12** rather than given their own entry. Sections 8.11 and 9.11 each print a
   one-line question, which is not a template.

8. **Alternative text, palette generation, and the footer discipline are folded
   into Template C.16** as its second prompt. Sections 12.12 and 13.11 name all
   three as good uses; together they are one prompt.

9. **Section C.3 (the audit stack) is an added section.** The blueprint does not
   list it. Every chapter from 7 onward builds its audit cumulatively on
   Table 8.5, and no single place in the manuscript states the resulting map. A
   template library that names an audit per entry needs one.

10. **No "good" rewrite of a weak prompt is supplied.** Exercises 4.6, 5.6, and
    6.6 ask students to author those rewrites. Table C.6 gives the minimum
    repair as a direction, not as an answer.

### Verification

- 43 production checks against `Chapter_Style_Specification.md` §6 — all pass.
- 13 practice-file invariants against the figures Appendix A publishes — all pass.
- 18 worked-example figures asserted in code — all pass.
- Every `Template C.x`, `Prompt C.x`, `Table C.x`, and `Section C.x`
  cross-reference resolves.

### Open

- Length: 46 designed pages against the blueprint's 25–35 target. See the build
  log for options.
- Appendix D does not exist. Every template names the record it must leave; the
  field names are drawn from Chapter 1's Table 1.6 and §1.7 and will need
  reconciling when Appendix D is drafted.
- Appendix E does not exist. Templates C.16 and C.17 repair against it.
- Chapters 1, 2, 3, 12, and 13 never reference Appendix C. Chapters 4–11 do.
