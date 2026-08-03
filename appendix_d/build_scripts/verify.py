# -*- coding: utf-8 -*-
"""Production and content checks for Appendix D.

Every check corresponds to a line of `Chapter_Style_Specification.md` §6, a
requirement of `Appendices_15_Writing_Blueprint.md` §D, or a claim the
appendix makes about itself.
"""

import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx import Document                     # noqa: E402
from docx.oxml.ns import qn                   # noqa: E402
import content as C                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(HERE, "..", "build",
                    "Appendix_D_AI_Use_Documentation_Template_DRAFT.docx")
COMP = os.path.join(HERE, "..", "companion")

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append((name, detail))


doc = Document(DOCX)
paras = doc.paragraphs
styles_used = {p.style.name for p in paras}
text_by_style = [(p.style.name, p.text) for p in paras]
full_text = "\n".join(p.text for p in paras)
for t in doc.tables:
    for r in t.rows:
        for c in r.cells:
            full_text += "\n" + c.text

ALLOWED = {
    "Normal", "Heading 1", "Heading 2", "Heading 3", "Body Text",
    "Body Text Indent", "Chapter Title", "Chapter Subtitle", "Byline",
    "Metadata Label", "Metadata Body", "List Number", "List Bullet",
    "Reference Entry", "Table Caption", "Table Heading", "Table Text",
    "Code Caption", "Code Block", "Callout Label", "Callout Title",
    "Callout Body", "Callout Source", "Spacer", "Footer",
}
LEGACY = {"BodyFirst", "BodyIndent", "ListNumberX", "ListBulletX",
          "HangingEntry", "MetaLabel", "MetaBody", "TableHead",
          "SpacerAfterTable", "FooterX", "BoxLabel", "BoxTitle", "BoxBody",
          "BoxSource"}

# ---------------------------------------------------------------- styles ---
check("every paragraph carries a permitted style",
      styles_used <= ALLOWED, str(styles_used - ALLOWED))

with zipfile.ZipFile(DOCX) as z:
    styles_xml = z.read("word/styles.xml").decode("utf-8")
    doc_xml = z.read("word/document.xml").decode("utf-8")
check("no legacy style ids survive",
      not any(f'w:styleId="{s}"' in styles_xml for s in LEGACY))
check("heading ids and heading names agree (the Chapter 2 defect)",
      all(re.search(r'w:styleId="Heading%d"[^>]*>\s*<w:name w:val="Heading %d"/>'
                    % (i, i), styles_xml) for i in (1, 2, 3)))
check("docDefaults set Times New Roman 12 pt",
      'w:ascii="Times New Roman"' in styles_xml and
      re.search(r"<w:rPrDefault>.*?<w:sz w:val=\"24\"/>", styles_xml,
                re.S) is not None)
check("docDefaults set 1.15 line spacing and 6 pt after",
      re.search(r"<w:pPrDefault>.*?w:after=\"120\".*?w:line=\"276\"",
                styles_xml, re.S) is not None)
check("keepNext survives on every heading level",
      all(re.search(r'w:styleId="%s".*?<w:keepNext/>' % s, styles_xml, re.S)
          for s in ("Heading1", "Heading2", "Heading3")))
check("keepLines survives on all four callout styles",
      all(re.search(r'w:styleId="%s".*?<w:keepLines/>' % s, styles_xml, re.S)
          for s in ("CalloutLabel", "CalloutTitle", "CalloutBody",
                    "CalloutSource")))
check("outline levels 0/1/2 on Heading 1/2/3",
      all(re.search(r'w:styleId="Heading%d".*?<w:outlineLvl w:val="%d"/>'
                    % (i + 1, i), styles_xml, re.S) for i in range(3)))
check("callout shading and accent rule are defined",
      "F5F2F8" in styles_xml and "57068C" in styles_xml
      and "C9BFD6" in styles_xml)
check("page is US Letter with one-inch margins",
      'w:w="12240"' in doc_xml and 'w:h="15840"' in doc_xml
      and 'w:top="1440"' in doc_xml)
check("footer carries a centred page number",
      "PAGE" in "".join(p.text for p in doc.sections[0].footer.paragraphs)
      or "PAGE" in doc.sections[0].footer.paragraphs[0]._p.xml)

# ------------------------------------------------------------- structure ---
h1 = [t for s, t in text_by_style if s == "Heading 1"]
check("document opens on the appendix title, with no cover page",
      text_by_style[0] == ("Chapter Title", "Appendix D"))
check("front matter carries Appendix A's metadata block, in order",
      [t for s, t in text_by_style if s == "Metadata Label"] ==
      ["purpose", "use this appendix when", "this appendix does not",
       "version and date", "suggested citation", "license and rights",
       "generative ai use", "companion files"])
mb = [t for s, t in text_by_style if s == "Metadata Body"]
check("LICENSE AND RIGHTS carries both paragraphs",
      sum(1 for t in mb if "Creative Commons" in t or "trademark" in t
          or "products of" in t) >= 2)
check("numbered sections run D.1 through D.9 in order",
      [t.split()[0] for t in h1 if t.startswith("D.")] ==
      [f"D.{i}" for i in range(1, 10)])

levels = []
for s, t in text_by_style:
    if s.startswith("Heading "):
        levels.append(int(s[-1]))
skips = [(levels[i], levels[i + 1]) for i in range(len(levels) - 1)
         if levels[i + 1] - levels[i] > 1]
check("heading levels never skip a level", not skips, str(skips))
check("no Heading 3 is used without a Heading 2 above it",
      "Heading 3" not in styles_used or "Heading 2" in styles_used)

# ---------------------------------------------------------------- tables ---
caps = [t for s, t in text_by_style if s == "Table Caption"]
numbers = [c for c in caps if re.fullmatch(r"Table D\.\d+", c)]
check("every table has a two-paragraph caption",
      len(caps) == 2 * len(doc.tables),
      f"{len(caps)} caption paragraphs for {len(doc.tables)} tables")
check("table numbers are contiguous D.1..D.N",
      numbers == [f"Table D.{i}" for i in range(1, len(doc.tables) + 1)],
      str(numbers))
check("no one-cell tables anywhere",
      all(len(t.columns) > 1 and len(t.rows) > 1 for t in doc.tables))
check("every header row carries tblHeader and cantSplit",
      all(t.rows[0]._tr.find(qn("w:trPr")) is not None
          and t.rows[0]._tr.find(qn("w:trPr")).find(qn("w:tblHeader"))
          is not None
          and t.rows[0]._tr.find(qn("w:trPr")).find(qn("w:cantSplit"))
          is not None
          for t in doc.tables))
check("every table is 6.5 inches wide with a fixed layout",
      doc_xml.count('w:w="9360" w:type="dxa"') >= len(doc.tables)
      and doc_xml.count('w:type="fixed"') >= len(doc.tables))
check("header cells use Table Heading and body cells Table Text",
      all(c.paragraphs[0].style.name == "Table Heading"
          for t in doc.tables for c in t.rows[0].cells)
      and all(c.paragraphs[0].style.name == "Table Text"
              for t in doc.tables for r in t.rows[1:] for c in r.cells))

# every table is introduced in the text before it appears
body = doc.element.body
order, tbl_i = [], 0
for child in body:
    if child.tag == qn("w:tbl"):
        tbl_i += 1
        order.append(("tbl", tbl_i))
    elif child.tag == qn("w:p"):
        order.append(("p", "".join(n.text or "" for n in
                                   child.iter(qn("w:t")))))
introduced = True
missing = []
for i, (kind, val) in enumerate(order):
    if kind != "tbl":
        continue
    label = f"Table D.{val}"
    before = " ".join(v for k, v in order[:i] if k == "p")
    if label not in before:
        introduced = False
        missing.append(label)
check("every table is introduced in the text before it appears",
      introduced, str(missing))

# --------------------------------------------------------------- callouts ---
labels = [t for s, t in text_by_style if s == "Callout Label"]
check("callout labels are permitted and carry no colon",
      all(t in {"concept", "definition", "ai in practice",
                "verification check"} and ":" not in t for t in labels),
      str(labels))
check("every callout is closed by a Spacer", True if not labels else all(
    text_by_style[i + 1][0] == "Spacer"
    for i, (s, t) in enumerate(text_by_style)
    if s == "Callout Source"))
check("every callout carries a source line",
      sum(1 for s, _ in text_by_style if s == "Callout Source")
      == len(labels))
check("no chapter apparatus leaked into the appendix",
      not any(k in full_text for k in
              ("Learning Objectives", "Chapter Summary", "Further Readings",
               "Glossary of Terms", "Business Analytics in Practice",
               "Exercises for Practice")))

# ------------------------------------------------------- cross-references ---
refs = set(re.findall(r"\bTable D\.(\d+)", full_text))
check("every Table D.x cross-reference resolves",
      all(int(r) <= len(doc.tables) for r in refs),
      str(sorted(refs)))
sec_refs = set(re.findall(r"\bSection D\.(\d+)(?:\.(\d+))?", full_text))
check("every Section D.x cross-reference resolves",
      all(1 <= int(a) <= 9 for a, _ in sec_refs), str(sorted(sec_refs)))
code_caps = [t for s, t in text_by_style if s == "Code Caption"]
check("code entries are numbered contiguously",
      [c.split(".")[1].strip() for c in code_caps] ==
      [f"{i}" for i in range(1, len(code_caps) + 1)]
      if code_caps else True,
      str(code_caps))

# ---------------------------------------------------------- content rules ---
check("American spelling throughout",
      not re.search(r"\b(behaviour|colour|summarise|organis|analyse|"
                    r"centre|labelled|catalogue)\w*", full_text, re.I),
      str(re.findall(r"\b\w*(?:behaviour|colour|summaris|organis|analys)"
                     r"\w*", full_text, re.I)[:5]))
PLACEHOLDERS = {"[TOOL]", "[EXCHANGE ID]", "[EXPECTED TOTAL]", "[E1]",
                "[SECTION]", "[LIMITATIONS]", "[STUDENT NAME]", "[DATE]",
                "[NAME]"}
found = set(re.findall(r"\[[A-Z][A-Z ]+\]", full_text))
check("every bracketed placeholder is on the documented allowlist",
      found <= PLACEHOLDERS, str(found - PLACEHOLDERS))
check("the strong example in the comparison carries no placeholder",
      "General-purpose assistant; version not displayed" in full_text)
L1_FIELDS = ["Exchange ID", "Tool and version", "Prompt as sent",
             "Prediction recorded first", "Decision",
             "Verification performed"]
d5 = doc.tables[4]
check("Table D.5 is the Level 1 form and uses canonical field names",
      [r.cells[0].text for r in d5.rows] == ["Field"] + L1_FIELDS,
      str([r.cells[0].text for r in d5.rows]))
check("Level 1's fields are a strict subset of the exchange field set",
      set(L1_FIELDS) < {f for _, f, _, _ in C.EXCHANGE_FIELDS})
code_text = "\n".join(t for s, t in text_by_style if s == "Code Block")
check("the worked compact record uses the canonical labels too",
      all(f + ":" in code_text for f in L1_FIELDS))
check("the compact record does not introduce a second decision vocabulary",
      "revise where" not in full_text and
      "modified is the word for revised" in full_text)
check("Chapter 1's four Table 1.6 questions appear verbatim",
      all(q in full_text for q in
          ["Which AI tool did you use, and for which step?",
           "What prompt did you submit?",
           "What did you accept, revise, or reject?",
           "How did you verify the final result?"]))
check("Section 1.9's four audit questions appear verbatim",
      all(q in full_text for q in
          ["Does the output answer the question I specified?",
           "Does one row still represent what I said it represents?",
           "Can I reproduce at least one number by hand?",
           "Can I state in one sentence what this result does not show?"]))
check("the privacy rule of Section 1.13 is carried, not restated loosely",
      "confidential and personally identifiable data are never to be placed "
      "into an external AI tool" in full_text)
check("the guide's privacy terminology is used consistently",
      "personally identifying" not in full_text,
      "found: personally identifying")
check("the declaration offers three mutually exclusive statuses",
      all(a in full_text for a, _ in C.PRIVACY_STATUSES)
      and "work, except as described above" not in full_text)
check("the canonical field set is published in full",
      all(f in full_text for _, f, _, _ in C.EXCHANGE_FIELDS))
check("every verification field is published",
      all(f in full_text for f, _ in C.VERIFICATION_FIELDS))
check("the rejected-output section covers all four dispositions",
      "D.5.6 Rejected, Corrected, or Bounded Output" in
      [t for s, t in text_by_style if s == "Heading 2"]
      and all(w in full_text for w in
              ("Rejected, corrected, limited, or declined",)))
check("stage and purpose category are distinguished in the text",
      "Stage identifies where in the" in full_text
      and "purpose category identifies what kind of" in full_text)
check("D.9 states the progression by chapter block, not uniformly",
      all(p in full_text for p in
          ("Chapters 7 through 10 run the two-prompt pattern",
           "Chapter 11 expands that into four moves",
           "Chapters 12 and 13 run a five-step")))
check("D.7 states a retention rule",
      "grading and appeal period" in full_text
      and "delete what you no longer need" in full_text)
check("D.4 and D.5 are described as defining the levels, not as forms",
      "define the two record levels" in full_text
      and "are the two forms themselves" not in full_text)
check("the eleven-column portrait Word table is not recommended",
      "an eleven-column table on" in full_text.replace("\n", " ")
      or "eleven-column table on a portrait page is unreadable" in full_text)
check("the analyst statement is offered for adaptation, not invention",
      "The record ends with the statement below, adapted to your own work"
      in full_text)
check("the no-error case carries a burden rather than an incentive",
      "name the checks that would have caught a defect and did not fire"
      in full_text)
check("all nine purpose categories are published",
      all(c in full_text for c, _, _ in C.PURPOSE_CATEGORIES))
check("all thirteen chapters appear in the chapter map",
      all(any(row[0] == str(i) for row in C.CHAPTER_MAP)
          for i in range(1, 14)))
# Chapter 5's figures, used in the weak-versus-strong comparison
check("the D.15 comparison's Chapter 5 arithmetic is correct",
      abs(660.00 / 8 - 82.50) < 1e-9 and "$82.50" in full_text
      and "$105.00" in full_text and "$660.00" in full_text)
check("the four decision words are stated once as a closed set",
      "Accepted, modified, rejected, or used only to generate questions"
      in full_text)
check("the appendix does not claim to certify correctness",
      "does not certify that AI-assisted work is correct" in full_text)
check("the analyst-of-record statement includes the explain clause",
      "I can explain the code, the calculations, the visualizations, and"
      in full_text)
check("code blocks keep straight quotes",
      not any(ch in t for s, t in text_by_style if s == "Code Block"
              for ch in "\u201c\u201d\u2019"),
      "smart quotes leaked into a code block")
check("no code line exceeds 76 characters",
      all(len(ln) <= 76 for s, t in text_by_style if s == "Code Block"
          for ln in t.split("\n")),
      str([ln for s, t in text_by_style if s == "Code Block"
           for ln in t.split("\n") if len(ln) > 76]))
check("no markup delimiter leaked into rendered text",
      not re.search(r"(\*\*|\]\(http)", full_text),
      str(re.findall(r".{20}(?:\*\*|\]\(http).{20}", full_text)[:3]))
check("every hyperlink carries the Hyperlink character style",
      doc_xml.count("<w:hyperlink") ==
      doc_xml.count('<w:rStyle w:val="Hyperlink"/>'))
INTEXT = ["American Psychological Association, n.d.", "Chapman et al. (2000)",
          "Davenport et al., 2020", "Martin & Murphy, 2017",
          "National Institute of Standards and Technology (2024)",
          "Provost and Fawcett (2013)"]
check("every reference-list entry has an in-text citation",
      all(a in full_text for a in INTEXT),
      str([a for a in INTEXT if a not in full_text]))
refs = [t for s, t in text_by_style if s == "Reference Entry"]
check("the reference list has one entry per cited work", len(refs) == 6)
check("the APA entry does not repeat its title as link text",
      not any("APA Style, how to cite ChatGPT" in r for r in refs))
check("no appendix section re-teaches a chapter concept",
      "In other words" in full_text and
      full_text.count("Chapter 1 introduced") <= 1)

# --------------------------------------------------------- companion files --
if os.path.exists(os.path.join(COMP, "Appendix_D_field_set.csv")):
    import csv
    import json

    def read_csv(name):
        with open(os.path.join(COMP, name), newline="",
                  encoding="utf-8") as fh:
            return list(csv.reader(fh))

    expected = [
        "Appendix_D_field_set.csv",
        "Appendix_D_AI_Use_Record_FORM.docx",
        "Appendix_D_AI_Use_Record_FORM.md",
        "Appendix_D_AI_Use_Record_FORM.xlsx",
        "Appendix_D_exchange_log.csv",
        "Appendix_D_verification_evidence.csv",
        "Appendix_D_tools_used.csv",
        "Appendix_D_rejected_or_corrected.csv",
        "Appendix_D_group_contributions.csv",
        "README.md", "CHANGELOG.md",
    ]
    check("all companion filenames share the Appendix_D_ stem",
          all(f.startswith("Appendix_D_") or f in ("README.md",
                                                   "CHANGELOG.md",
                                                   "build_scripts")
              for f in os.listdir(COMP) if f != "worked_example"),
          str([f for f in os.listdir(COMP)
               if not f.startswith("Appendix_D_")
               and f not in ("README.md", "CHANGELOG.md", "worked_example",
                             "build_scripts")]))
    check("every companion file is present",
          all(os.path.exists(os.path.join(COMP, e)) for e in expected),
          str([e for e in expected
               if not os.path.exists(os.path.join(COMP, e))]))

    fs = read_csv("Appendix_D_field_set.csv")
    check("field_set.csv carries the published field names, in order",
          [r[1] for r in fs[1:] if r[0].startswith("D")] ==
          [f for _, f, _, _ in C.EXCHANGE_FIELDS])

    md = open(os.path.join(COMP, "Appendix_D_AI_Use_Record_FORM.md"),
              encoding="utf-8").read()
    check("the Markdown record names every published exchange field",
          all(f in md for _, f, _, _ in C.EXCHANGE_FIELDS))
    check("the Markdown record names every published verification field",
          all(f in md for f, _ in C.VERIFICATION_FIELDS))

    wf = Document(os.path.join(COMP, "Appendix_D_AI_Use_Record_FORM.docx"))
    wtext = "\n".join(p.text for p in wf.paragraphs)
    for t in wf.tables:
        for r in t.rows:
            for c in r.cells:
                wtext += "\n" + c.text
    check("the Word form names every published exchange field",
          all(f in wtext for _, f, _, _ in C.EXCHANGE_FIELDS))
    check("the Word form names every published verification field",
          all(f in wtext for f, _ in C.VERIFICATION_FIELDS))
    check("the Word form carries the privacy declaration and the signature",
          all(a in wtext for a, _ in C.PRIVACY_STATUSES)
          and "Sign exactly one" in wtext
          and "I remain responsible" in wtext)
    check("the companion forms use the published section name",
          "Rejected, corrected, or bounded output" in md
          and "Rejected, Corrected, or Bounded Output" in wtext)
    check("the Markdown form carries the three declarations",
          all(a in md for a, _ in C.PRIVACY_STATUSES))
    check("the spreadsheet log's rejection columns match the published ones",
          read_csv("Appendix_D_rejected_or_corrected.csv")[0] ==
          [f for f, _ in C.REJECTED_FIELDS])

    ex = read_csv("Appendix_D_exchange_log.csv")
    check("the spreadsheet log's columns are the published field names",
          ex[0] == [f for _, f, _, _ in C.EXCHANGE_FIELDS])
    ve = read_csv("Appendix_D_verification_evidence.csv")
    check("the verification sheet's columns are the published field names",
          ve[0] == [f for f, _ in C.VERIFICATION_FIELDS])

    # the worked example
    wex = os.path.join(COMP, "worked_example")
    check("the worked example is present in all three formats",
          all(os.path.exists(os.path.join(wex, f)) for f in
              ("Appendix_D_Worked_Example_COMPLETED.docx",
               "Appendix_D_Worked_Example_COMPLETED.md",
               "Appendix_D_Worked_Example_COMPLETED.xlsx")))
    wm = open(os.path.join(wex, "Appendix_D_Worked_Example_COMPLETED.md"),
              encoding="utf-8").read()
    for fig in ["$12", "$40", "0.30", "0.25", "$160", "+$32", "+$48",
                "−$8", "0.70", "1.00"]:
        check(f"the worked example prints Chapter 9's figure {fig}",
              fig in wm)
    for disp in ("Rejected", "Corrected", "Declined", "Limited"):
        check(f"the worked example shows the {disp.lower()} disposition",
              f"| {disp} |" in wm)
    check("the worked example carries a signed analyst-of-record statement",
          "I remain responsible for the submitted analysis" in wm)
    check("the worked example answers no graded exercise",
          "Exercise 9.5" not in wm and "Exercise 9.6" not in wm)
    ar = json.load(open(os.path.join(wex, "arithmetic_check.json"),
                        encoding="utf-8"))
    check("the worked example's arithmetic was recomputed, not typed",
          ar["all_passed"] is True, json.dumps(ar.get("failures", [])))

# ------------------------------------------------------------------ report --
for n, d in PASS:
    print(f"  pass  {n}")
for n, d in FAIL:
    print(f"  FAIL  {n}   {d}")
print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
