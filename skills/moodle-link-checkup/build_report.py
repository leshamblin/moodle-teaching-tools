#!/usr/bin/env python3
"""Build a Google-Docs-friendly HTML report of Moodle course resources with link checks.

Usage:
  python3 build_report.py --input <resources.json> --course-id <ID> [--moodle-base <URL>]

Input JSON shape (array of objects):
  {section, modname, cmid, name, filename, mimetype, filesize, fileurl, external}
"""

import argparse, json, html, re, subprocess, os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

COLORS = {
    'PDF': '#b30000', 'PowerPoint': '#d24726', 'Word': '#2b579a',
    'Google Slides': '#f4b400', 'Google Doc': '#4285f4',
    'Google Sheet': '#0f9d58', 'Google Form': '#673ab7',
    'Panopto Video': '#005587', 'YouTube': '#ff0000',
    'TED Talk': '#e62b1e', 'Podcast': '#1db954',
    'McGraw Hill': '#00558c', 'External Link': '#666',
}
KEEP = set(COLORS.keys())


def classify(it):
    mt = it.get('mimetype') or ''
    fn = it.get('filename') or ''
    if it['modname'] == 'url':
        ext = it.get('external') or ''
        if 'panopto' in ext: return 'Panopto Video'
        if 'youtube.com' in ext or 'youtu.be' in ext: return 'YouTube'
        if 'ted.com' in ext: return 'TED Talk'
        if 'spotify' in ext: return 'Podcast'
        if 'docs.google.com/presentation' in ext: return 'Google Slides'
        if 'docs.google.com/document' in ext: return 'Google Doc'
        if 'docs.google.com/spreadsheets' in ext: return 'Google Sheet'
        if 'docs.google.com/forms' in ext or 'forms.gle' in ext: return 'Google Form'
        if 'mheducation' in ext: return 'McGraw Hill'
        return 'External Link'
    if 'presentation' in mt or re.search(r'\.pptx?$', fn, re.I): return 'PowerPoint'
    if mt == 'application/pdf' or fn.lower().endswith('.pdf'): return 'PDF'
    if 'word' in mt or re.search(r'\.docx?$', fn, re.I): return 'Word'
    return 'Other'


def moodle_direct_url(raw):
    u = raw.replace('/webservice/pluginfile.php/', '/pluginfile.php/')
    u = re.sub(r'[?&]forcedownload=1', '', u)
    return u


def check_external(url, timeout=15):
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36'
    try:
        out = subprocess.run(
            ['curl', '-sIL', '-o', '/dev/null', '-w', '%{http_code}',
             '--max-time', str(timeout), '-A', ua, url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        code = (out.stdout or '').strip().split()[-1] if out.stdout else '000'
        if code in ('405', '403', '000'):
            out2 = subprocess.run(
                ['curl', '-sL', '-o', '/dev/null', '-w', '%{http_code}',
                 '--max-time', str(timeout), '-A', ua, url],
                capture_output=True, text=True, timeout=timeout + 5,
            )
            code = (out2.stdout or '').strip()
        return code
    except Exception as e:
        return f'ERR'


def week_key(name):
    m = re.search(r'Week\s+(\d+)', name)
    return (0, int(m.group(1)), name) if m else (1, 0, name)


def build(items, base_url, course_id, out_path):
    # Classify, build links, mark in_moodle
    for it in items:
        it['kind'] = classify(it)
        if it['modname'] == 'resource' and it.get('fileurl'):
            it['link'] = moodle_direct_url(it['fileurl'])
            it['in_moodle'] = True
        else:
            it['link'] = it.get('external') or f"{base_url}/mod/url/view.php?id={it['cmid']}"
            it['in_moodle'] = False

    items = [it for it in items if it['kind'] in KEEP]

    # Check external links in parallel
    external_urls = [it['link'] for it in items if not it['in_moodle']]
    with ThreadPoolExecutor(max_workers=8) as ex:
        status_map = dict(zip(external_urls, ex.map(check_external, external_urls)))

    for it in items:
        if it['in_moodle']:
            # Moodle returns a fileurl only for files it can serve. Filesize is a
            # secondary signal: if it's present and zero, the file is empty.
            has_url = bool(it.get('fileurl'))
            size = it.get('filesize')
            it['ok'] = has_url and (size is None or size > 0)
            it['status_note'] = (
                'verified via Moodle metadata' if it['ok']
                else ('empty file in Moodle' if size == 0 else 'no file URL returned by Moodle')
            )
        else:
            code = status_map.get(it['link'], '?')
            it['ok'] = code.startswith(('2', '3'))
            it['status_note'] = f'HTTP {code}'

    by_section = {}
    for it in items:
        by_section.setdefault(it['section'], []).append(it)
    sections = sorted(by_section.keys(), key=week_key)

    counts = Counter(it['kind'] for it in items)
    in_moodle_n = sum(1 for it in items if it['in_moodle'])
    external_n = len(items) - in_moodle_n
    broken = [it for it in items if not it['ok']]

    rows = []
    for sec in sections:
        rows.append(f'<h2>{html.escape(sec)}</h2>')
        rows.append('<table style="border-collapse:collapse;width:100%;margin-bottom:8px;">')
        for it in by_section[sec]:
            color = COLORS.get(it['kind'], '#666')
            label = html.escape(it.get('filename') or it['name'])
            mark = ('<span style="color:#0a7d2c;font-weight:bold;font-size:16px;">&#10003;</span>'
                    if it['ok'] else
                    '<span style="color:#c00;font-weight:bold;font-size:16px;">&#10007;</span>')
            type_cell = (f'<td style="padding:4px 10px;background:{color};color:#fff;'
                         f'font-size:11px;font-weight:600;text-align:center;'
                         f'white-space:nowrap;width:1%;">{it["kind"]}</td>')
            rows.append(
                f'<tr>'
                f'<td style="padding:4px 10px;width:1%;text-align:center;">{mark}</td>'
                f'{type_cell}'
                f'<td style="padding:4px 10px;">'
                f'<a href="{html.escape(it["link"])}" target="_blank">{label}</a>'
                f'</td>'
                f'</tr>'
            )
        rows.append('</table>')

    kind_summary = ', '.join(f'{n} {k}' for k, n in counts.most_common())
    broken_block = ''
    if broken:
        broken_block = (
            '<div style="background:#fff4f4;border:1px solid #c00;padding:10px 16px;'
            'border-radius:4px;margin:16px 0;"><strong style="color:#c00;">Broken links:</strong>'
            '<ul style="margin:8px 0 0 0;">'
            + ''.join(
                f'<li>[{html.escape(it["status_note"])}] {html.escape(it["section"])} &mdash; {html.escape(it["name"])}</li>'
                for it in broken
            )
            + '</ul></div>'
        )

    doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Course {course_id} — Resources</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 950px; margin: 40px auto; padding: 0 20px; color: #222; }}
  h1 {{ border-bottom: 3px solid #990000; padding-bottom: 8px; }}
  h2 {{ margin-top: 28px; color: #333; font-size: 17px; }}
  a {{ color: #0066cc; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .summary {{ background: #f5f5f5; padding: 12px 16px; border-radius: 4px; margin: 16px 0; line-height: 1.6; }}
  .note {{ color: #666; font-size: 13px; margin-top: 8px; }}
</style></head><body>
<h1>Course {course_id} — All Resource Links</h1>
<div class="summary">
  <strong>Course ID:</strong> {course_id} &nbsp;|&nbsp; <strong>Total:</strong> {len(items)} resources
  ({in_moodle_n} hosted in Moodle, {external_n} external)<br>
  {kind_summary}<br>
  <strong>Link check:</strong>
  <span style="color:#0a7d2c;font-weight:bold;">&#10003; {len(items) - len(broken)} working</span> &nbsp;|&nbsp;
  <span style="color:#c00;font-weight:bold;">&#10007; {len(broken)} need attention</span>
  <div class="note">Moodle files verified via server metadata. External links HEAD-checked for HTTP 2xx/3xx.</div>
</div>
{broken_block}
{''.join(rows)}
</body></html>"""

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        f.write(doc)

    return {
        'total': len(items),
        'in_moodle': in_moodle_n,
        'external': external_n,
        'working': len(items) - len(broken),
        'broken': len(broken),
        'broken_items': [
            {'section': it['section'], 'name': it['name'], 'status': it['status_note']}
            for it in broken
        ],
        'out_path': out_path,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Path to extracted resources JSON')
    ap.add_argument('--course-id', required=True)
    ap.add_argument('--moodle-base', default='https://moodle-courses2527.wolfware.ncsu.edu',
                    help='Moodle base URL (host portion only)')
    ap.add_argument('--out', default=None, help='Output HTML path')
    ap.add_argument('--open', action='store_true', help='Open in Chrome after building')
    args = ap.parse_args()

    with open(args.input) as f:
        items = json.load(f)

    out = args.out or os.path.expanduser(
        f'~/Documents/Programming/Demo/{args.course_id}-resources.html'
    )
    result = build(items, args.moodle_base.rstrip('/'), args.course_id, out)

    print(json.dumps(result, indent=2))

    if args.open:
        subprocess.run(['open', '-a', 'Google Chrome', out])


if __name__ == '__main__':
    main()
