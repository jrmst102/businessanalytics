#!/usr/bin/env python3
"""Editable Word template library, built from the published .docx.

Same stylesheet as the appendix, one Heading 1 per template, so a student can
delete what does not apply and fill the placeholders in Word.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build import Doc                                    # noqa: E402
import extract_library as X                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
d = Doc()
d.p('ChapterTitle', 'Appendix C — Editable Template Library')
d.p('ChapterSubtitle', 'AI Prompting Templates for Analytics')
d.p('Byline', 'Companion file to Appendix C · Version 1.0 · August 2026')
d.p('Byline', 'Except where otherwise noted, licensed under CC BY 4.0.')

d.h1('How to Use This File')
d.body_(
    'This file carries the same templates as the published appendix, in an editable '
    'form. Work in a copy. Delete the templates you are not using, replace every '
    'bracketed placeholder, and delete any constraint that genuinely does not apply '
    'to your task.')
d.ind(
    'Three controls recur throughout the library, and none of them should be deleted, '
    'although their wording changes by task: use only supplied information, expose '
    'rather than fill missing information, and stop at the boundary of the delegated '
    'work. Section C.2 of the appendix explains why each is load-bearing. If a '
    'template’s phrasing does not fit your task, replace it with phrasing that does '
    'rather than dropping the control.')
d.ind(
    'The published appendix carries the failure modes, the audit, and the Appendix D '
    'record for every template. They are reproduced here in short form; where the two '
    'differ, the published appendix governs.')

for t in X.templates:
    d.h1(f'Template C.{t["num"]} — {t["title"]}')
    d.body_(f'**Owned by.** {t["owner"]}')
    d.ind(f'**Use this template when.** {t["when"]}')
    d.ind('**Decide first.**')
    for x in t['decide']:
        d.bullet(x)
    for pr in t['prompts']:
        d.prompt(f'{pr["label"]}. {pr["title"]}', pr['lines'])
    d.p('BodyText', '**Watch for.**')
    for x in t['failures']:
        d.bullet(x)
    d.p('BodyText', '**Audit.**')
    for x in t['audit']:
        d.bullet(x)
    d.p('BodyText', f'**Record in Appendix D.** {t["record"]}')

out = d.save(os.path.join(HERE, 'Appendix_C_Template_Library_EDITABLE.docx'),
             'Appendix C — Editable Template Library',
             tpl=os.path.join(os.path.dirname(HERE), 'tpl'))
print('wrote', out)
