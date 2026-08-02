#!/usr/bin/env python3
"""Generate the companion template library from the built .docx.

Everything here is extracted from the published appendix rather than authored
separately, so a prompt cannot change on the page without changing in the
companion files.
"""
import csv, html, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(os.path.dirname(HERE),
                    'Appendix_C_AI_Prompting_Templates_for_Analytics_DRAFT.docx')

z = zipfile.ZipFile(DOCX)
doc = z.read('word/document.xml').decode('utf8')
paras = re.findall(r'<w:p>(?:(?!</w:p>).)*</w:p>', doc, re.S)


def style(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"/>', p)
    return m.group(1) if m else None


def text(p):
    return html.unescape(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.S)))


def block_lines(p):
    out = []
    for seg in re.split(r'<w:br/>', p):
        out.append(html.unescape(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', seg))))
    return out


# ------------------------------------------------------------- walk the body
templates, cur, pending_caption = [], None, None
for p in paras:
    s, t = style(p), text(p)
    if s == 'Heading2' and t.startswith('Template C.'):
        num, title = re.match(r'Template C\.(\d+) — (.*)', t).groups()
        cur = {'num': int(num), 'title': title, 'meta': [], 'prompts': [],
               'failures': [], 'audit': [], 'decide': [], 'record': ''}
        templates.append(cur)
        section = 'meta'
    elif cur is None:
        continue
    elif s == 'CodeCaption' and t.startswith('Prompt C.'):
        pending_caption = t
    elif s == 'CodeBlock' and pending_caption:
        label, ptitle = re.match(r'(Prompt C\.\d+)\. (.*)', pending_caption).groups()
        cur['prompts'].append({'label': label, 'title': ptitle,
                               'lines': block_lines(p)})
        pending_caption = None
    elif s in ('BodyText', 'BodyTextIndent'):
        if t.startswith('Owned by.'):
            cur['owner'] = t[len('Owned by.'):].strip()
        elif t.startswith('Use this template when.'):
            cur['when'] = t[len('Use this template when.'):].strip()
        elif t.startswith('What you must decide first.'):
            section = 'decide'
        elif t.startswith('Likely failure modes.'):
            section = 'failures'
        elif t.startswith('Audit after the response.'):
            section = 'audit'
        elif t.startswith('What to record in Appendix D.'):
            cur['record'] = t[len('What to record in Appendix D.'):].strip()
    elif s == 'ListBullet':
        cur[section].append(t.lstrip('• ')) if section in (
            'decide', 'failures', 'audit') else None

assert len(templates) == 19, len(templates)
n_prompts = sum(len(t['prompts']) for t in templates)

# ------------------------------------------------------------------ markdown
os.makedirs(os.path.join(HERE, 'templates'), exist_ok=True)
lib = ['# Appendix C — AI Prompting Templates for Analytics',
       '',
       'Companion template library, Version 1.0 (August 2026).',
       'Extracted from the published appendix; do not edit here and there.',
       '',
       'Every prompt below assumes the rules of the published appendix: supply only',
       'safe data (Section C.4), predict the result before you send, run the audit',
       'the entry names (Section C.3), and record the exchange under Appendix D.',
       '']
for t in templates:
    body = [f'## Template C.{t["num"]} — {t["title"]}', '',
            f'**Owned by.** {t["owner"]}', '',
            f'**Use this template when.** {t["when"]}', '',
            '**What you must decide first.**', '']
    body += [f'- {x}' for x in t['decide']] + ['']
    for pr in t['prompts']:
        body += [f'### {pr["label"]}. {pr["title"]}', '', '```text']
        body += pr['lines'] + ['```', '']
    body += ['**Likely failure modes.**', ''] + [f'- {x}' for x in t['failures']] + ['']
    body += ['**Audit after the response.**', ''] + [f'- {x}' for x in t['audit']] + ['']
    body += [f'**What to record in Appendix D.** {t["record"]}', '']
    open(os.path.join(HERE, 'templates', f'template_C{t["num"]:02d}.md'),
         'w', encoding='utf8').write('\n'.join(body))
    lib += body + ['---', '']
open(os.path.join(HERE, 'prompt_library.md'), 'w', encoding='utf8').write('\n'.join(lib))

# ---------------------------------------------------- plain text for copying
txt = ['APPENDIX C - AI PROMPTING TEMPLATES FOR ANALYTICS',
       'Plain-text prompts, optimized for copying. Version 1.0, August 2026.',
       'Replace every [BRACKETED] placeholder. Send everything else as written.',
       '']
for t in templates:
    for pr in t['prompts']:
        txt += ['=' * 76,
                f'{pr["label"]}  (Template C.{t["num"]}: {t["title"]})',
                f'{pr["title"]}',
                '=' * 76, ''] + pr['lines'] + ['']
open(os.path.join(HERE, 'prompts.txt'), 'w', encoding='utf8').write('\n'.join(txt))

# ------------------------------------------------------------ prompt finder
FINDER = [
    ('1', 'Sections 1.7 and 1.9', 'Review Before You Rely', []),
    ('2', 'Section 2.8', 'Ask for the Other Side', [1, 2]),
    ('3', 'Section 3.9', 'Draft the Dictionary, Audit the Draft', [3, 4]),
    ('4', 'Section 4.10', 'Delegate the Code, Never the Count', [5, 6]),
    ('5', 'Section 5.10', 'The Summary That Must Add Up', [7, 8]),
    ('6', 'Section 6.12', 'The Cluster Solution That Must Survive a Refit', [9]),
    ('7', 'Section 7.11', 'The Regression That Must Survive Its Audit', [10]),
    ('8', 'Section 8.11', 'The Pipeline That Must Survive Its Audit', [11]),
    ('9', 'Section 9.11', 'The Classifier That Must Survive Its Audit', [12]),
    ('10', 'Section 10.11', 'The Forecast You Priced Before You Ran It', [13]),
    ('11', 'Section 11.11',
     'Preregister With the Assistant, Then Audit the Analysis Against the Registration',
     [14, 15, 19]),
    ('12', 'Section 12.12', 'Predict the Faults Before You Look', [16, 17]),
    ('13', 'Section 13.11', 'Draft the Titles, Then Prove Them', [18, 19]),
]
by_num = {t['num']: t for t in templates}
with open(os.path.join(HERE, 'prompt_finder.csv'), 'w', newline='',
          encoding='utf8') as f:
    w = csv.writer(f)
    w.writerow(['chapter', 'ai_assistant_section', 'ai_in_practice_box',
                'template', 'template_title', 'prompt_labels', 'file'])
    for ch, sec, box, tmpls in FINDER:
        if not tmpls:
            w.writerow([ch, sec, box, '', '(no prompt printed; the four-question '
                        'audit of Section 1.9 governs every template)', '', ''])
        for n in tmpls:
            t = by_num[n]
            w.writerow([ch, sec, box, f'C.{n}', t['title'],
                        '; '.join(p['label'] for p in t['prompts']),
                        f'templates/template_C{n:02d}.md'])

print(f'templates: {len(templates)}   prompts: {n_prompts}')
print('wrote prompt_library.md, prompts.txt, prompt_finder.csv, templates/*.md')
