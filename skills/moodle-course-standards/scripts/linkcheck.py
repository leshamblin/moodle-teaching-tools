"""Link classification and HTTP checking.

classify, moodle_direct_url and check_external are copied verbatim from
skills/moodle-link-checkup/build_report.py. Skills in this repo ship
independently so they cannot import from each other. If you change one copy,
change the other.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from typing import List

_REFS = os.path.join(os.path.dirname(__file__), '..', 'references')


def load_auth_domains() -> List[str]:
    with open(os.path.join(_REFS, 'auth-domains.json')) as fh:
        return json.load(fh)['domains']


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
    except Exception:
        return 'ERR'


def link_verdict(url: str, code: str, auth_domains: List[str]) -> str:
    """Classify a checked link as ok, broken or auth.

    A 401/403/000/ERR from a domain known to require a login is 'auth', not
    'broken'. Ranking a course down because Panopto wanted a password would be
    scoring our own blind spot as their failure.
    """
    host = re.sub(r'^https?://', '', url).split('/')[0].lower()
    is_auth_domain = any(host == d or host.endswith('.' + d) for d in auth_domains)
    if code in ('401', '403', '000', 'ERR') and is_auth_domain:
        return 'auth'
    if code.startswith('2') or code.startswith('3'):
        return 'ok'
    if code in ('401', '403'):
        return 'auth'
    return 'broken'
