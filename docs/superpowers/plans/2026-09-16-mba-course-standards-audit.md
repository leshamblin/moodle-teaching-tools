# MBA Course Standards Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Score 42 Spring 2026 online MBA courses against 34 items of the Poole course review checklist and rank them by confirmed failures.

**Architecture:** Six independent components behind one CLI. A selector resolves a term and section pattern to course IDs, a fetcher caches raw Moodle JSON to disk, an extractor caches syllabus text, a rule table of 34 pure functions scores each cached bundle, and a reporter writes a three sheet workbook. Caching sits between fetching and scoring so rule development reruns entirely offline.

**Tech Stack:** Python 3.8, openpyxl, pdfplumber, python-docx, python-pptx, requests, curl, pytest. Moodle REST web services, read only.

**Spec:** `docs/superpowers/specs/2026-09-16-mba-course-standards-audit-design.md`

## Global Constraints

- **Python 3.8.0.** No PEP 604 unions (`str | None`), no dict merge operator (`a | b`), no `match`. Use `typing.Optional`, `typing.List`, `typing.Dict`. Put `from __future__ import annotations` at the top of every module.
- **Read only against Moodle.** Never call a `moodle_*` write function. The token in use has admin rights and production writes are enabled, so this is a real hazard, not a formality.
- **Moodle base URL:** `https://moodle-courses2527.wolfware.ncsu.edu`
- **Token source:** `MOODLE_PROD_TOKEN` in `~/Documents/Programming/MoodleAPI/.env`. Never hardcode it, never print it, never write it into a cache file or a report.
- **The admin token is not enrolled in these courses.** Capability checked calls work, enrollment checked ones do not. `core_course_get_contents`, `core_course_get_courses_by_field` and `core_course_search_courses` are confirmed working. Any other call must be verified against course 8298 before code depends on it.
- **Five verdicts:** `YES`, `NO`, `SOMEWHAT`, `NA`, `UNKNOWN`. Only `NO` counts toward the ranking.
- **Only three rules may return `SOMEWHAT`:** row 10 course structure, row 12 course links, row 56 assessment instructions. Every other rule returns `YES`, `NO`, `NA` or `UNKNOWN`.
- **No em dashes** in any file this project writes, including reports, docs and commit messages. Use a comma, a colon, a period or parentheses.
- **Skill self containment.** Skills in this repo ship independently. Do not import across skill directories.

---

## File Structure

    skills/moodle-course-standards/
      SKILL.md                          instructions, written last
      scripts/
        audit.py                        CLI entry point, wires everything
        selector.py                     term + section pattern -> course ids
        fetch.py                        Moodle calls + raw JSON cache
        extract.py                      file download + text extraction + cache
        linkcheck.py                    link classification and HTTP checking
        rules.py                        verdict types, registry, all 34 rules
        report.py                       three sheet workbook writer
        forms.py                        optional per course checklist fill
      references/
        presence-patterns.json          patterns for the 11 shared presence rules
        syllabus-keywords.json          keyword sets for the 14 syllabus rules
        auth-domains.json               domains that 403 an anonymous checker
      templates/
        Course-Review-Checklist.xlsx    copy of the supplied blank form
      tests/
        fixtures/                       cached JSON + hand scored golden files
        test_linkcheck.py
        test_selector.py
        test_fetch.py
        test_extract.py
        test_rules_structural.py
        test_rules_syllabus.py
        test_report.py
        test_golden.py

Each rule is a pure function of a cached bundle, so every rule test is a dict literal in and a verdict out. No network in any test.

---

### Task 1: Skill scaffold and link checking module

`moodle-link-checkup/build_report.py` already has the three functions this needs, mixed in with HTML report building. Skills ship independently, so this copies the three pure functions rather than importing across skill directories. Copy them verbatim and credit the source in a header comment. If they ever change there, they must be changed here too, which is the price of the plugin's packaging model.

**Files:**
- Create: `skills/moodle-course-standards/scripts/linkcheck.py`
- Create: `skills/moodle-course-standards/references/auth-domains.json`
- Test: `skills/moodle-course-standards/tests/test_linkcheck.py`

**Interfaces:**
- Consumes: nothing
- Produces: `classify(item: dict) -> str`, `moodle_direct_url(raw: str) -> str`, `check_external(url: str, timeout: int = 15) -> str` returning an HTTP code string or `'ERR'`, and `link_verdict(url: str, code: str, auth_domains: list) -> str` returning one of `'ok'`, `'broken'`, `'auth'`.

- [ ] **Step 1: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_linkcheck.py
from __future__ import annotations
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import linkcheck


def test_classify_panopto_url():
    item = {'modname': 'url', 'external': 'https://ncsu.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=abc'}
    assert linkcheck.classify(item) == 'Panopto Video'


def test_classify_pdf_resource():
    item = {'modname': 'resource', 'mimetype': 'application/pdf', 'filename': 'syllabus.pdf'}
    assert linkcheck.classify(item) == 'PDF'


def test_moodle_direct_url_strips_webservice_and_forcedownload():
    raw = 'https://m.example.edu/webservice/pluginfile.php/123/mod_resource/content/1/a.pdf?forcedownload=1'
    assert linkcheck.moodle_direct_url(raw) == 'https://m.example.edu/pluginfile.php/123/mod_resource/content/1/a.pdf'


def test_link_verdict_auth_domain_is_not_broken():
    auth = ['panopto.com', 'mheducation.com']
    url = 'https://ncsu.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=abc'
    assert linkcheck.link_verdict(url, '403', auth) == 'auth'


def test_link_verdict_404_is_broken():
    assert linkcheck.link_verdict('https://example.edu/gone.pdf', '404', []) == 'broken'


def test_link_verdict_200_is_ok():
    assert linkcheck.link_verdict('https://example.edu/a.pdf', '200', []) == 'ok'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_linkcheck.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'linkcheck'`

- [ ] **Step 3: Create the auth domain list**

```json
{
  "comment": "Domains that return 401/403 to an anonymous checker because they want a login. A code from these is not evidence of a broken link.",
  "domains": [
    "panopto.com",
    "mheducation.com",
    "docs.google.com",
    "drive.google.com",
    "forms.gle",
    "wolfware.ncsu.edu",
    "moodle-courses2527.wolfware.ncsu.edu",
    "linkedin.com",
    "hbsp.harvard.edu",
    "wsj.com",
    "nytimes.com"
  ]
}
```

- [ ] **Step 4: Write the implementation**

Copy `classify`, `moodle_direct_url` and `check_external` verbatim from `skills/moodle-link-checkup/build_report.py` lines 26 to 71, then add `link_verdict`. Full file:

```python
# skills/moodle-course-standards/scripts/linkcheck.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_linkcheck.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add skills/moodle-course-standards/scripts/linkcheck.py \
        skills/moodle-course-standards/references/auth-domains.json \
        skills/moodle-course-standards/tests/test_linkcheck.py
git commit -m "feat: add link checking module for the course standards audit"
```

---

### Task 2: Course selector

**Files:**
- Create: `skills/moodle-course-standards/scripts/selector.py`
- Test: `skills/moodle-course-standards/tests/test_selector.py`

**Interfaces:**
- Consumes: nothing
- Produces: `select_courses(courses: list, term: str, section_pattern: str) -> list` returning dicts with keys `id`, `shortname`, `fullname`, `sections`; and `parse_sections(fullname: str) -> list` returning the section numbers found in parentheses.

- [ ] **Step 1: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_selector.py
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import selector

COURSES = [
    {'id': 8298, 'shortname': 'MBA 520 (631) SPRG 2026',
     'fullname': 'MBA 520 (631) Spring 2026 Corporate Finance'},
    {'id': 9065, 'shortname': 'MBA 507 (631 and 632) SPRG 2026',
     'fullname': 'MBA 507 (631 and 632) Spring 2026 Operations'},
    {'id': 1111, 'shortname': 'MBA 505 (001) SPRG 2026',
     'fullname': 'MBA 505 (001) Spring 2026 On Campus Section'},
    {'id': 2222, 'shortname': 'MBA 520 (631) FALL 2025',
     'fullname': 'MBA 520 (631) Fall 2025 Corporate Finance'},
]


def test_parse_sections_single():
    assert selector.parse_sections('MBA 520 (631) Spring 2026 Corporate Finance') == ['631']


def test_parse_sections_multiple():
    assert selector.parse_sections('MBA 507 (631 and 632) Spring 2026 Operations') == ['631', '632']


def test_selects_only_matching_term_and_section():
    got = selector.select_courses(COURSES, 'Spring 2026', r'^6\d\d$')
    assert [c['id'] for c in got] == [8298, 9065]


def test_excludes_on_campus_section():
    got = selector.select_courses(COURSES, 'Spring 2026', r'^6\d\d$')
    assert 1111 not in [c['id'] for c in got]


def test_excludes_other_term():
    got = selector.select_courses(COURSES, 'Spring 2026', r'^6\d\d$')
    assert 2222 not in [c['id'] for c in got]


def test_result_carries_sections():
    got = selector.select_courses(COURSES, 'Spring 2026', r'^6\d\d$')
    assert got[1]['sections'] == ['631', '632']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_selector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'selector'`

- [ ] **Step 3: Write the implementation**

```python
# skills/moodle-course-standards/scripts/selector.py
"""Resolve a term and section pattern to a list of courses."""
from __future__ import annotations

import re
from typing import Dict, List


def parse_sections(fullname: str) -> List[str]:
    """Pull section numbers out of the parenthesised part of a course name.

    Handles 'MBA 520 (631)', 'MBA 507 (631 and 632)' and 'ACC 501 (631 | 632)'.
    """
    out = []  # type: List[str]
    for group in re.findall(r'\(([^)]*)\)', fullname):
        for num in re.findall(r'\d{3}', group):
            if num not in out:
                out.append(num)
    return out


def select_courses(courses: List[Dict], term: str, section_pattern: str) -> List[Dict]:
    """Return the courses whose fullname contains term and whose section matches.

    A course qualifies if ANY of its sections matches, because a crosslisted
    shell like 'MBA 507 (631 and 632)' is one Moodle course to review.
    """
    rx = re.compile(section_pattern)
    out = []  # type: List[Dict]
    for c in courses:
        fullname = c.get('fullname', '')
        if term.lower() not in fullname.lower():
            continue
        sections = parse_sections(fullname)
        if not any(rx.match(s) for s in sections):
            continue
        out.append({
            'id': c['id'],
            'shortname': c.get('shortname', ''),
            'fullname': fullname,
            'sections': sections,
        })
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_selector.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add skills/moodle-course-standards/scripts/selector.py \
        skills/moodle-course-standards/tests/test_selector.py
git commit -m "feat: add course selector for term and section filtering"
```

---

### Task 3: Fetcher with on disk cache

**Files:**
- Create: `skills/moodle-course-standards/scripts/fetch.py`
- Test: `skills/moodle-course-standards/tests/test_fetch.py`

**Interfaces:**
- Consumes: nothing
- Produces: `load_token() -> tuple` returning `(base_url, token)`; `moodle_call(base, token, wsfunction, **params) -> object`; `fetch_bundle(base, token, course_id, cache_dir, refresh=False) -> dict` with keys `course`, `contents`, `forums`; `cache_path(cache_dir, course_id) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_fetch.py
from __future__ import annotations
import json, os, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import fetch


def test_cache_path_uses_course_id():
    p = fetch.cache_path('/tmp/cache', 8298)
    assert p.endswith('8298.json')


def test_fetch_bundle_reads_cache_without_calling(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        bundle = {'course': {'id': 8298}, 'contents': [], 'forums': []}
        os.makedirs(d, exist_ok=True)
        with open(fetch.cache_path(d, 8298), 'w') as fh:
            json.dump(bundle, fh)

        def boom(*a, **k):
            raise AssertionError('network was called despite a warm cache')

        monkeypatch.setattr(fetch, 'moodle_call', boom)
        got = fetch.fetch_bundle('https://x', 'tok', 8298, d)
        assert got['course']['id'] == 8298


def test_fetch_bundle_refresh_ignores_cache(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        with open(fetch.cache_path(d, 8298), 'w') as fh:
            json.dump({'course': {'id': 'stale'}, 'contents': [], 'forums': []}, fh)

        calls = []

        def fake(base, token, wsfunction, **params):
            calls.append(wsfunction)
            if wsfunction == 'core_course_get_courses_by_field':
                return {'courses': [{'id': 8298, 'format': 'weeks'}]}
            if wsfunction == 'core_course_get_contents':
                return [{'id': 1, 'name': 'Course Administration', 'modules': []}]
            return {'forums': []}

        monkeypatch.setattr(fetch, 'moodle_call', fake)
        got = fetch.fetch_bundle('https://x', 'tok', 8298, d, refresh=True)
        assert got['course']['format'] == 'weeks'
        assert 'core_course_get_contents' in calls


def test_moodle_call_raises_on_moodle_exception(monkeypatch):
    def fake_post(url, data, timeout):
        class R:
            status_code = 200

            def json(self):
                return {'exception': 'webservice_access_exception',
                        'message': 'Access control exception'}
        return R()

    monkeypatch.setattr(fetch.requests, 'post', fake_post)
    try:
        fetch.moodle_call('https://x', 'tok', 'core_course_get_contents', courseid=1)
    except fetch.MoodleError as e:
        assert 'Access control exception' in str(e)
    else:
        raise AssertionError('expected MoodleError')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_fetch.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'fetch'`

- [ ] **Step 3: Write the implementation**

```python
# skills/moodle-course-standards/scripts/fetch.py
"""Moodle REST calls and the on disk raw JSON cache.

Read only. Never add a function here that writes to Moodle.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Optional, Tuple

import requests

ENV_PATH = os.path.expanduser('~/Documents/Programming/MoodleAPI/.env')


class MoodleError(RuntimeError):
    pass


def load_token(env_path: str = ENV_PATH) -> Tuple[str, str]:
    """Read MOODLE_PROD_URL and MOODLE_PROD_TOKEN out of the .env file.

    The last uncommented assignment wins, which matches shell sourcing and is
    what makes the commented out user token in that file harmless.
    """
    values = {}  # type: Dict[str, str]
    with open(env_path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'([A-Z_]+)=(.*)$', line)
            if m:
                values[m.group(1)] = m.group(2).strip()
    base = values.get('MOODLE_PROD_URL', '').rstrip('/')
    token = values.get('MOODLE_PROD_TOKEN', '')
    if not base or not token:
        raise MoodleError('MOODLE_PROD_URL or MOODLE_PROD_TOKEN missing from ' + env_path)
    return base, token


def moodle_call(base: str, token: str, wsfunction: str, **params):
    """POST one web service call and return the decoded result.

    Moodle returns HTTP 200 with an 'exception' key on failure, so the status
    code alone never tells you whether the call worked.
    """
    data = {'wstoken': token, 'wsfunction': wsfunction, 'moodlewsrestformat': 'json'}
    for k, v in params.items():
        data[k] = v
    resp = requests.post(base + '/webservice/rest/server.php', data=data, timeout=60)
    if resp.status_code != 200:
        raise MoodleError('HTTP %s from %s' % (resp.status_code, wsfunction))
    payload = resp.json()
    if isinstance(payload, dict) and 'exception' in payload:
        raise MoodleError('%s: %s' % (wsfunction, payload.get('message', 'unknown')))
    return payload


def cache_path(cache_dir: str, course_id: int) -> str:
    return os.path.join(cache_dir, '%s.json' % course_id)


def fetch_bundle(base: str, token: str, course_id: int, cache_dir: str,
                 refresh: bool = False) -> Dict:
    """Return everything the rules need for one course, cached to disk.

    Keys: course (metadata incl. format and courseimage), contents (sections
    and modules), forums (forum instances with discussion counts).
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = cache_path(cache_dir, course_id)
    if not refresh and os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)

    by_field = moodle_call(base, token, 'core_course_get_courses_by_field',
                           field='id', value=course_id)
    course = (by_field.get('courses') or [{}])[0]
    contents = moodle_call(base, token, 'core_course_get_contents', courseid=course_id)

    try:
        forums = moodle_call(base, token, 'mod_forum_get_forums_by_courses',
                             **{'courseids[0]': course_id})
    except MoodleError:
        # Not fatal. The welcome forum rule reports UNKNOWN when this is empty.
        forums = []

    bundle = {'course': course, 'contents': contents, 'forums': forums}
    with open(path, 'w') as fh:
        json.dump(bundle, fh)
    return bundle
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_fetch.py -v`
Expected: 4 passed

- [ ] **Step 5: Verify `mod_forum_get_forums_by_courses` actually works for this token**

The plan assumes it does but the admin token is not enrolled, so this must be checked against a real course before anything depends on it.

Run:

```bash
cd ~/Documents/Programming/MoodleAPI && set -a && . ./.env && set +a && \
curl -s "$MOODLE_PROD_URL/webservice/rest/server.php" \
  -d "wstoken=$MOODLE_PROD_TOKEN" -d "moodlewsrestformat=json" \
  -d "wsfunction=mod_forum_get_forums_by_courses" -d "courseids[0]=8298" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(type(d), (d if isinstance(d,dict) else d[:1]))"
```

Expected: a list of forum dicts. If it returns an `exception`, record that in the spec's Open Questions and make row 28's rule return `UNKNOWN` permanently rather than guessing.

- [ ] **Step 6: Commit**

```bash
git add skills/moodle-course-standards/scripts/fetch.py \
        skills/moodle-course-standards/tests/test_fetch.py
git commit -m "feat: add Moodle fetcher with on disk bundle cache"
```

---

### Task 4: Document text extractor

**Files:**
- Create: `skills/moodle-course-standards/scripts/extract.py`
- Test: `skills/moodle-course-standards/tests/test_extract.py`

**Interfaces:**
- Consumes: `linkcheck.moodle_direct_url`
- Produces: `extract_text(path: str) -> tuple` returning `(text, status)` where status is `'ok'` or a reason string; `download(url: str, token: str, dest: str) -> tuple` returning `(path, status)`; `syllabus_text(bundle: dict, base: str, token: str, cache_dir: str) -> tuple` returning `(text, status)`.

This is the task where the spec's most important property lives: a failure to read must never become a failure to comply.

- [ ] **Step 1: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_extract.py
from __future__ import annotations
import os, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import extract


def test_extract_docx_returns_text():
    from docx import Document
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'syllabus.docx')
        doc = Document()
        doc.add_paragraph('Late work is accepted for 48 hours.')
        doc.save(p)
        text, status = extract.extract_text(p)
        assert status == 'ok'
        assert 'Late work' in text


def test_extract_unsupported_type_is_not_a_failure_to_comply():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'notes.txt')
        with open(p, 'w') as fh:
            fh.write('hello')
        text, status = extract.extract_text(p)
        assert text == ''
        assert status.startswith('unsupported')


def test_extract_empty_pdf_reports_no_text_layer():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'scan.pdf')
        with open(p, 'wb') as fh:
            fh.write(b'%PDF-1.4\n%%EOF\n')
        text, status = extract.extract_text(p)
        assert text == ''
        assert status != 'ok'


def test_download_appends_token_to_pluginfile_url(monkeypatch):
    seen = {}

    def fake_get(url, timeout, stream=False):
        seen['url'] = url

        class R:
            status_code = 200
            content = b'PK\x03\x04data'

            def iter_content(self, n):
                yield self.content
        return R()

    monkeypatch.setattr(extract.requests, 'get', fake_get)
    with tempfile.TemporaryDirectory() as d:
        path, status = extract.download(
            'https://m.edu/webservice/pluginfile.php/1/a.docx', 'TOK',
            os.path.join(d, 'a.docx'))
        assert status == 'ok'
        assert 'token=TOK' in seen['url']


def test_download_empty_body_is_an_error_not_silence(monkeypatch):
    def fake_get(url, timeout, stream=False):
        class R:
            status_code = 200

            def iter_content(self, n):
                yield b''
        return R()

    monkeypatch.setattr(extract.requests, 'get', fake_get)
    with tempfile.TemporaryDirectory() as d:
        path, status = extract.download('https://m.edu/a.docx', 'TOK',
                                        os.path.join(d, 'a.docx'))
        assert status.startswith('empty')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_extract.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract'`

- [ ] **Step 3: Write the implementation**

```python
# skills/moodle-course-standards/scripts/extract.py
"""Download course files and pull text out of them.

Every function returns (value, status). A non-'ok' status must reach the report
as UNKNOWN. It must never be collapsed into NO: that would rank a course as non
compliant because our parser failed, and these findings go to the people who own
the courses.
"""
from __future__ import annotations

import os
import re
from typing import Dict, Optional, Tuple

import requests

SYLLABUS_RX = re.compile(r'syllab', re.I)
OUTLINE_RX = re.compile(r'outline|schedule|calendar', re.I)


def download(url: str, token: str, dest: str) -> Tuple[str, str]:
    """Fetch a Moodle file to dest. Returns (path, status).

    Moodle pluginfile URLs need the web service token appended or they return a
    login page with HTTP 200, which extracts as empty text and looks exactly
    like a missing syllabus. That is why empty bodies are an explicit error.
    """
    if 'pluginfile.php' in url and 'token=' not in url:
        url = url + ('&' if '?' in url else '?') + 'token=' + token
    try:
        resp = requests.get(url, timeout=60, stream=True)
    except Exception as e:
        return '', 'download failed: %s' % type(e).__name__
    if getattr(resp, 'status_code', 0) != 200:
        return '', 'download HTTP %s' % resp.status_code
    total = 0
    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
    with open(dest, 'wb') as fh:
        for chunk in resp.iter_content(65536):
            if chunk:
                total += len(chunk)
                fh.write(chunk)
    if total == 0:
        return '', 'empty response body, token may be missing'
    return dest, 'ok'


def extract_text(path: str) -> Tuple[str, str]:
    """Pull plain text out of a PDF, DOCX or PPTX. Returns (text, status)."""
    lower = path.lower()
    try:
        if lower.endswith('.pdf'):
            import pdfplumber
            parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    parts.append(page.extract_text() or '')
            text = '\n'.join(parts).strip()
            if not text:
                return '', 'pdf has no text layer, likely a scan'
            return text, 'ok'
        if lower.endswith('.docx'):
            from docx import Document
            doc = Document(path)
            text = '\n'.join(p.text for p in doc.paragraphs).strip()
            if not text:
                return '', 'docx contained no paragraph text'
            return text, 'ok'
        if lower.endswith('.pptx'):
            from pptx import Presentation
            parts = []
            for slide in Presentation(path).slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        parts.append(shape.text_frame.text)
            text = '\n'.join(parts).strip()
            if not text:
                return '', 'pptx contained no text'
            return text, 'ok'
    except Exception as e:
        return '', 'extract failed: %s' % type(e).__name__
    return '', 'unsupported file type: %s' % os.path.splitext(path)[1]


def find_syllabus_module(bundle: Dict) -> Optional[Dict]:
    """Return the first resource whose name or filename looks like a syllabus."""
    for section in bundle.get('contents', []):
        for mod in section.get('modules', []):
            if mod.get('modname') != 'resource':
                continue
            name = mod.get('name') or ''
            contents = mod.get('contents') or [{}]
            filename = contents[0].get('filename') or ''
            if SYLLABUS_RX.search(name) or SYLLABUS_RX.search(filename):
                return mod
    return None


def syllabus_text(bundle: Dict, base: str, token: str, cache_dir: str) -> Tuple[str, str]:
    """Locate, download, extract and cache the syllabus text for one course."""
    course_id = bundle.get('course', {}).get('id', 'unknown')
    cache_file = os.path.join(cache_dir, '%s-syllabus.txt' % course_id)
    status_file = cache_file + '.status'
    if os.path.exists(cache_file) and os.path.exists(status_file):
        with open(status_file) as fh:
            status = fh.read().strip()
        with open(cache_file) as fh:
            return fh.read(), status

    mod = find_syllabus_module(bundle)
    if mod is None:
        text, status = '', 'no syllabus resource found in course'
    else:
        contents = mod.get('contents') or [{}]
        url = contents[0].get('fileurl') or ''
        filename = contents[0].get('filename') or 'syllabus'
        if not url:
            text, status = '', 'syllabus module has no file url'
        else:
            dest = os.path.join(cache_dir, '%s-%s' % (course_id, filename))
            path, status = download(url, token, dest)
            text = ''
            if status == 'ok':
                text, status = extract_text(path)

    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'w') as fh:
        fh.write(text)
    with open(status_file, 'w') as fh:
        fh.write(status)
    return text, status
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_extract.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add skills/moodle-course-standards/scripts/extract.py \
        skills/moodle-course-standards/tests/test_extract.py
git commit -m "feat: add document downloader and text extractor"
```

---

### Task 5: Rule framework and the 20 structural rules

**Files:**
- Create: `skills/moodle-course-standards/scripts/rules.py`
- Create: `skills/moodle-course-standards/references/presence-patterns.json`
- Test: `skills/moodle-course-standards/tests/test_rules_structural.py`

**Interfaces:**
- Consumes: `linkcheck.classify`, `linkcheck.link_verdict`, `linkcheck.load_auth_domains`
- Produces: `YES`, `NO`, `SOMEWHAT`, `NA`, `UNKNOWN` string constants; `Result = namedtuple('Result', 'row verdict evidence')`; `RULES` an ordered list of `(row, label, callable)`; `score_course(bundle, syllabus_text, syllabus_status, link_results) -> List[Result]`.

The 11 Section 2 presence rules share one implementation driven by the pattern file. That is the design, not a shortcut: they differ only in what they look for.

- [ ] **Step 1: Write the pattern file**

```json
{
  "comment": "Row number to search pattern for the shared Section 2 presence rules. Patterns are case insensitive regexes matched against module names, label descriptions and section summaries in the intro section (section 0) and any section whose name matches 'start here', 'about', 'administration' or 'welcome'.",
  "patterns": {
    "17": {"label": "Course Syllabus Document", "pattern": "syllab"},
    "18": {"label": "Course Outline/Schedule Document", "pattern": "outline|schedule|calendar|course at a glance"},
    "19": {"label": "Course overview/introduction", "pattern": "overview|introduction to the course|course intro"},
    "20": {"label": "Instructor/TA welcome video, audio or message", "pattern": "welcome|meet your instructor|meet the professor"},
    "21": {"label": "Instructor/TA bio with contact information", "pattern": "instructor|professor|faculty|bio|contact|office hour"},
    "22": {"label": "Course Navigation", "pattern": "navigat|getting started|how to use|how this course"},
    "23": {"label": "Communication Guidelines", "pattern": "communicat|netiquette|discussion guideline|email polic"},
    "24": {"label": "Course Technology", "pattern": "technolog|system requirement|software|hardware|minimum requirement"},
    "25": {"label": "Student Office hours information", "pattern": "office hour|student hour|drop.?in"},
    "26": {"label": "Link to Academic Support", "pattern": "academic support|tutor|writing center|library|dasa|counsel"},
    "27": {"label": "Course and Tech support", "pattern": "tech support|help ?desk|moodle support|wolftech|it support|ncsu support"}
  }
}
```

- [ ] **Step 2: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_rules_structural.py
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import rules


def bundle(**over):
    b = {
        'course': {'id': 1, 'format': 'weeks', 'courseimage': '',
                   'fullname': 'MBA 520 (631) Spring 2026 Corporate Finance',
                   'shortname': 'MBA 520 (631) SPRG 2026'},
        'contents': [
            {'section': 0, 'name': 'Course Administration', 'summary': '', 'modules': []},
            {'section': 1, 'name': 'Week 1, February 12 - 18: Intro', 'summary': '',
             'modules': [{'modname': 'resource', 'name': 'Slides',
                          'contents': [{'filename': 'w1.pdf', 'mimetype': 'application/pdf'}]}]},
        ],
        'forums': [],
    }
    b.update(over)
    return b


def test_row8_banner_missing_is_no():
    r = rules.rule_course_banner(bundle())
    assert r.verdict == rules.NO


def test_row8_banner_present_is_yes():
    b = bundle()
    b['course']['courseimage'] = 'https://m.edu/pluginfile.php/1/course/overviewfiles/x.png'
    assert rules.rule_course_banner(b).verdict == rules.YES


def test_row9_default_section_names_is_no():
    b = bundle()
    b['contents'][1]['name'] = 'Week 1'
    assert rules.rule_course_format(b).verdict == rules.NO


def test_row9_real_section_names_is_yes():
    assert rules.rule_course_format(bundle()).verdict == rules.YES


def test_row9_social_format_is_no():
    b = bundle()
    b['course']['format'] = 'social'
    assert rules.rule_course_format(b).verdict == rules.NO


def test_row11_dates_in_section_names_is_yes():
    assert rules.rule_time_frame(bundle()).verdict == rules.YES


def test_row11_no_dates_anywhere_is_no():
    b = bundle()
    b['contents'][1]['name'] = 'Introduction'
    assert rules.rule_time_frame(b).verdict == rules.NO


def test_row12_links_all_ok_is_yes():
    assert rules.rule_course_links(bundle(), {'https://a': 'ok'}).verdict == rules.YES


def test_row12_links_some_broken_is_somewhat():
    r = rules.rule_course_links(bundle(), {'https://a': 'ok', 'https://b': 'broken'})
    assert r.verdict == rules.SOMEWHAT
    assert 'https://b' in r.evidence


def test_row12_links_all_broken_is_no():
    assert rules.rule_course_links(bundle(), {'https://b': 'broken'}).verdict == rules.NO


def test_row12_auth_links_do_not_count_against():
    assert rules.rule_course_links(bundle(), {'https://p': 'auth'}).verdict == rules.YES


def test_row16_section_in_name_is_yes():
    assert rules.rule_course_name_section(bundle()).verdict == rules.YES


def test_row16_no_section_is_no():
    b = bundle()
    b['course']['fullname'] = 'MBA 520 Spring 2026 Corporate Finance'
    b['course']['shortname'] = 'MBA 520 SPRG 2026'
    assert rules.rule_course_name_section(b).verdict == rules.NO


def test_presence_rule_finds_module_in_intro_section():
    b = bundle()
    b['contents'][0]['modules'] = [{'modname': 'resource', 'name': 'Course Syllabus',
                                    'contents': [{'filename': 's.pdf'}]}]
    assert rules.rule_presence(b, '17').verdict == rules.YES


def test_presence_rule_missing_is_no():
    assert rules.rule_presence(bundle(), '17').verdict == rules.NO


def test_row28_forum_with_no_discussions_is_no():
    b = bundle()
    b['forums'] = [{'id': 5, 'name': 'Announcements', 'numdiscussions': 0}]
    assert rules.rule_welcome_forum(b).verdict == rules.NO


def test_row28_forum_with_a_discussion_is_yes():
    b = bundle()
    b['forums'] = [{'id': 5, 'name': 'Announcements', 'numdiscussions': 3}]
    assert rules.rule_welcome_forum(b).verdict == rules.YES


def test_row28_no_forum_data_is_unknown_not_no():
    b = bundle()
    b['forums'] = []
    assert rules.rule_welcome_forum(b).verdict == rules.UNKNOWN


def test_row53_pdf_slides_present_is_yes():
    assert rules.rule_slides_present(bundle()).verdict == rules.YES


def test_row53_no_slides_is_no():
    b = bundle()
    b['contents'][1]['modules'] = []
    assert rules.rule_slides_present(b).verdict == rules.NO


def test_row10_uniform_sections_is_yes():
    b = bundle()
    mods = [{'modname': 'resource', 'name': 'r', 'contents': [{}]},
            {'modname': 'assign', 'name': 'a'}]
    b['contents'] = [
        {'section': 0, 'name': 'Course Administration', 'summary': '', 'modules': []},
        {'section': 1, 'name': 'Week 1: A', 'summary': '', 'modules': list(mods)},
        {'section': 2, 'name': 'Week 2: B', 'summary': '', 'modules': list(mods)},
        {'section': 3, 'name': 'Week 3: C', 'summary': '', 'modules': list(mods)},
    ]
    assert rules.rule_course_structure(b).verdict == rules.YES


def test_row10_one_odd_section_is_somewhat():
    b = bundle()
    mods = [{'modname': 'resource', 'name': 'r', 'contents': [{}]},
            {'modname': 'assign', 'name': 'a'}]
    b['contents'] = [
        {'section': 0, 'name': 'Course Administration', 'summary': '', 'modules': []},
        {'section': 1, 'name': 'Week 1: A', 'summary': '', 'modules': list(mods)},
        {'section': 2, 'name': 'Week 2: B', 'summary': '', 'modules': list(mods)},
        {'section': 3, 'name': 'Week 3: C', 'summary': '', 'modules': []},
    ]
    r = rules.rule_course_structure(b)
    assert r.verdict == rules.SOMEWHAT
    assert 'Week 3' in r.evidence


def test_row56_all_assessments_have_instructions_is_yes():
    b = bundle()
    b['contents'][1]['modules'] = [
        {'modname': 'assign', 'name': 'HW1', 'description': 'Do the thing.'},
    ]
    assert rules.rule_assessment_instructions(b).verdict == rules.YES


def test_row56_some_missing_is_somewhat():
    b = bundle()
    b['contents'][1]['modules'] = [
        {'modname': 'assign', 'name': 'HW1', 'description': 'Do the thing.'},
        {'modname': 'quiz', 'name': 'Q1', 'description': ''},
    ]
    r = rules.rule_assessment_instructions(b)
    assert r.verdict == rules.SOMEWHAT
    assert 'Q1' in r.evidence


def test_row56_no_assessments_is_na():
    assert rules.rule_assessment_instructions(bundle()).verdict == rules.NA


def test_row56_no_description_key_anywhere_is_unknown_not_no():
    """core_course_get_contents may omit 'description' entirely. That is a
    blind spot on our side, not a course that failed to write instructions."""
    b = bundle()
    b['contents'][1]['modules'] = [
        {'modname': 'assign', 'name': 'HW1'},
        {'modname': 'quiz', 'name': 'Q1'},
    ]
    assert rules.rule_assessment_instructions(b).verdict == rules.UNKNOWN
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_rules_structural.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'rules'`

- [ ] **Step 4: Write the implementation**

```python
# skills/moodle-course-standards/scripts/rules.py
"""Verdict types and the 34 scoring rules.

Every rule is a pure function of a cached bundle. No network, no file IO, no
clock. That is what makes them testable with a dict literal and what keeps the
golden fixture test meaningful.
"""
from __future__ import annotations

import json
import os
import re
from collections import namedtuple, Counter
from typing import Dict, List, Optional

import linkcheck

YES = 'Yes'
NO = 'No'
SOMEWHAT = 'Somewhat'
NA = 'N/A'
UNKNOWN = 'Unknown'

Result = namedtuple('Result', 'row verdict evidence')

_REFS = os.path.join(os.path.dirname(__file__), '..', 'references')

INTRO_SECTION_RX = re.compile(r'start here|about|administration|welcome|general', re.I)
DEFAULT_SECTION_RX = re.compile(r'^(topic|week|section|unit)\s*\d*\s*$', re.I)
DATE_RX = re.compile(
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}'
    r'|\b\d{1,2}/\d{1,2}\b'
    r'|\bweek\s+\d+\s*[,:]'
    r'|\b\d+\s*(hours?|minutes?|weeks?)\b', re.I)
ASSESSMENT_MODS = ('assign', 'quiz', 'workshop', 'forum')


def load_presence_patterns() -> Dict:
    with open(os.path.join(_REFS, 'presence-patterns.json')) as fh:
        return json.load(fh)['patterns']


def _intro_sections(bundle: Dict) -> List[Dict]:
    """Sections a student would look in for course information."""
    out = []
    for sec in bundle.get('contents', []):
        if sec.get('section') == 0 or INTRO_SECTION_RX.search(sec.get('name') or ''):
            out.append(sec)
    return out


def _content_sections(bundle: Dict) -> List[Dict]:
    intro_ids = set(id(s) for s in _intro_sections(bundle))
    return [s for s in bundle.get('contents', []) if id(s) not in intro_ids]


def _searchable_text(sections: List[Dict]) -> str:
    parts = []
    for sec in sections:
        parts.append(sec.get('name') or '')
        parts.append(sec.get('summary') or '')
        for mod in sec.get('modules', []):
            parts.append(mod.get('name') or '')
            parts.append(mod.get('description') or '')
            for c in mod.get('contents') or []:
                parts.append(c.get('filename') or '')
    return '\n'.join(parts)


# ---------------------------------------------------------------- Section 1

def rule_course_banner(bundle: Dict) -> Result:
    course = bundle.get('course', {})
    img = course.get('courseimage') or ''
    overview = course.get('overviewfiles') or []
    if img or overview:
        return Result(8, YES, 'course image set')
    return Result(8, NO, 'no course image or overview file set')


def rule_course_format(bundle: Dict) -> Result:
    fmt = bundle.get('course', {}).get('format') or ''
    if fmt not in ('topics', 'weeks'):
        return Result(9, NO, 'course format is %r, not Topics or Weekly' % fmt)
    bad = [s.get('name') or '(unnamed)' for s in _content_sections(bundle)
           if DEFAULT_SECTION_RX.match((s.get('name') or '').strip())]
    if bad:
        return Result(9, NO, 'sections left at default names: %s' % ', '.join(bad[:5]))
    return Result(9, YES, 'format %s with named sections' % fmt)


def rule_course_structure(bundle: Dict) -> Result:
    """Compare each content section's module-type signature to the common one.

    Empty sections are deliberately NOT filtered out. A week with nothing in it
    is exactly the structural outlier this rule exists to catch.
    """
    sections = _content_sections(bundle)
    if len(sections) < 3:
        return Result(10, NA, 'fewer than 3 content sections to compare')
    sigs = {}
    for sec in sections:
        sig = frozenset(m.get('modname') for m in sec.get('modules', []))
        sigs[sec.get('name') or '(unnamed)'] = sig
    common = Counter(sigs.values()).most_common(1)[0][0]
    odd = [name for name, sig in sigs.items() if not common.issubset(sig)]
    if not odd:
        return Result(10, YES, '%d sections share a common structure' % len(sections))
    if len(odd) >= len(sections) / 2.0:
        return Result(10, NO, 'no dominant structure, %d of %d sections differ'
                      % (len(odd), len(sections)))
    return Result(10, SOMEWHAT, 'sections missing the common pattern: %s'
                  % ', '.join(sorted(odd)[:5]))


def rule_time_frame(bundle: Dict) -> Result:
    sections = _content_sections(bundle)
    if not sections:
        return Result(11, NA, 'no content sections')
    with_dates = [s for s in sections
                  if DATE_RX.search((s.get('name') or '') + ' ' + (s.get('summary') or ''))]
    if not with_dates:
        return Result(11, NO, 'no dates or durations in any section name or summary')
    if len(with_dates) < len(sections):
        missing = [s.get('name') or '(unnamed)' for s in sections if s not in with_dates]
        return Result(11, NO, 'sections with no timeframe: %s' % ', '.join(missing[:5]))
    return Result(11, YES, 'all %d content sections state a timeframe' % len(sections))


def rule_course_links(bundle: Dict, link_results: Dict[str, str]) -> Result:
    """link_results maps url -> 'ok' | 'broken' | 'auth'."""
    if not link_results:
        return Result(12, NA, 'no external links in this course')
    broken = sorted([u for u, v in link_results.items() if v == 'broken'])
    checkable = [u for u, v in link_results.items() if v in ('ok', 'broken')]
    if not checkable:
        return Result(12, UNKNOWN, 'every link needed a login, none could be verified')
    if not broken:
        return Result(12, YES, '%d links checked, all resolved' % len(checkable))
    if len(broken) == len(checkable):
        return Result(12, NO, 'all %d checkable links failed: %s'
                      % (len(broken), ', '.join(broken[:3])))
    return Result(12, SOMEWHAT, '%d of %d links failed: %s'
                  % (len(broken), len(checkable), ', '.join(broken[:3])))


# ---------------------------------------------------------------- Section 2

def rule_course_name_section(bundle: Dict) -> Result:
    course = bundle.get('course', {})
    text = (course.get('fullname') or '') + ' ' + (course.get('shortname') or '')
    if re.search(r'\(\s*\d{3}', text):
        return Result(16, YES, 'section number present in course name')
    return Result(16, NO, 'no section number in fullname or shortname')


def rule_presence(bundle: Dict, row: str, patterns: Optional[Dict] = None) -> Result:
    """The shared implementation behind rows 17 through 27.

    They differ only in the pattern they search for, which is why this is one
    function and a data file rather than eleven near-identical functions.
    """
    patterns = patterns or load_presence_patterns()
    spec = patterns[str(row)]
    rx = re.compile(spec['pattern'], re.I)
    haystack = _searchable_text(_intro_sections(bundle))
    m = rx.search(haystack)
    if m:
        return Result(int(row), YES, 'matched %r in the intro section' % m.group(0))
    return Result(int(row), NO, 'nothing matching %r in the intro section' % spec['pattern'])


def rule_welcome_forum(bundle: Dict) -> Result:
    forums = bundle.get('forums') or []
    if not forums:
        return Result(28, UNKNOWN, 'forum data unavailable for this course')
    posted = [f for f in forums if (f.get('numdiscussions') or 0) > 0]
    if posted:
        return Result(28, YES, '%s has %d discussions'
                      % (posted[0].get('name'), posted[0].get('numdiscussions')))
    names = ', '.join(f.get('name') or '(unnamed)' for f in forums[:3])
    return Result(28, NO, 'forums exist but none has a post: %s' % names)


# ---------------------------------------------------------------- Multimedia

def rule_slides_present(bundle: Dict) -> Result:
    found = []
    for sec in _content_sections(bundle):
        for mod in sec.get('modules', []):
            if mod.get('modname') != 'resource':
                continue
            for c in mod.get('contents') or []:
                kind = linkcheck.classify({'modname': 'resource',
                                           'mimetype': c.get('mimetype'),
                                           'filename': c.get('filename')})
                if kind in ('PDF', 'PowerPoint'):
                    found.append(c.get('filename') or kind)
    if found:
        return Result(53, YES, '%d slide or PDF resources, e.g. %s' % (len(found), found[0]))
    return Result(53, NO, 'no PDF or PowerPoint resources in the content sections')


def rule_assessment_instructions(bundle: Dict) -> Result:
    items = []
    for sec in bundle.get('contents', []):
        for mod in sec.get('modules', []):
            if mod.get('modname') in ASSESSMENT_MODS:
                items.append(mod)
    if not items:
        return Result(56, NA, 'no assignments, quizzes or graded forums')
    # core_course_get_contents omits 'description' unless the activity is set to
    # show it on the course page, and mod_assign_get_assignments is blocked for
    # this token because the admin account is not enrolled. If the key is absent
    # everywhere we cannot see instructions at all, which is UNKNOWN, not NO.
    if not any('description' in m for m in items):
        return Result(56, UNKNOWN,
                      'activity descriptions are not exposed by core_course_get_contents '
                      'for this token, so instructions could not be checked')
    bare = [m.get('name') or '(unnamed)' for m in items
            if not (m.get('description') or '').strip()]
    if not bare:
        return Result(56, YES, 'all %d assessments carry instructions' % len(items))
    if len(bare) == len(items):
        return Result(56, NO, 'none of the %d assessments has instructions' % len(items))
    return Result(56, SOMEWHAT, '%d of %d assessments have no instructions: %s'
                  % (len(bare), len(items), ', '.join(bare[:5])))


# ---------------------------------------------------------------- Out of reach

OUT_OF_REACH = {
    49: 'video length needs Panopto, not available from Moodle',
    50: 'audio and video quality is a judgment call',
    52: 'captions and transcripts need Panopto, not available from Moodle',
    55: 'clarity of expectations is a judgment call',
}


def rule_out_of_reach(row: int) -> Result:
    return Result(row, NA, OUT_OF_REACH[row])
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_rules_structural.py -v`
Expected: 26 passed

- [ ] **Step 6: Commit**

```bash
git add skills/moodle-course-standards/scripts/rules.py \
        skills/moodle-course-standards/references/presence-patterns.json \
        skills/moodle-course-standards/tests/test_rules_structural.py
git commit -m "feat: add rule framework and the 20 structural rules"
```

---

### Task 6: The 14 syllabus keyword rules

**Files:**
- Create: `skills/moodle-course-standards/references/syllabus-keywords.json`
- Modify: `skills/moodle-course-standards/scripts/rules.py` (append the keyword engine and the RULES registry)
- Test: `skills/moodle-course-standards/tests/test_rules_syllabus.py`

**Interfaces:**
- Consumes: `rules.Result`, `rules.UNKNOWN`
- Produces: `rule_syllabus(text: str, status: str, row: str, keywords: Optional[dict] = None) -> Result`; `RULES` the ordered registry of all 34; `score_course(bundle, syllabus_text, syllabus_status, link_results) -> List[Result]`.

- [ ] **Step 1: Write the keyword file**

```json
{
  "comment": "Row number to the keyword set that shows an element is present in the syllabus text. A row scores Yes if ANY keyword matches. These detect presence, never quality.",
  "keywords": {
    "31": {"label": "Instructor information", "any": ["instructor", "professor", "taught by", "faculty"]},
    "32": {"label": "Office information", "any": ["office location", "office:", "nelson hall", "office hours", "by appointment"]},
    "33": {"label": "Tech Support information", "any": ["tech support", "help desk", "helpdesk", "wolftech", "it support", "919-515-help"]},
    "34": {"label": "Course catalog description", "any": ["catalog description", "course description"]},
    "35": {"label": "Learning objectives/Outcomes", "any": ["learning objective", "learning outcome", "course objective", "upon completion", "students will be able to"]},
    "36": {"label": "Course format", "any": ["asynchronous", "synchronous", "online", "distance education", "fully online", "hybrid"]},
    "37": {"label": "Required materials", "any": ["required text", "required material", "textbook", "isbn", "required reading"]},
    "38": {"label": "Required technology", "any": ["required technology", "technology requirement", "computer requirement", "webcam", "reliable internet", "software"]},
    "39": {"label": "Library information", "any": ["library", "lib.ncsu.edu", "hunt library", "dh hill"]},
    "40": {"label": "Learning Activities and Assessments", "any": ["assignment", "assessment", "graded", "exam", "quiz", "project"]},
    "41": {"label": "Course grading policies", "any": ["late work", "late assignment", "late polic", "make-up", "makeup", "academic integrity", "plagiaris", "extra credit"]},
    "42": {"label": "Virtual Class Meetings", "any": ["zoom", "virtual class", "live session", "webex", "class meeting", "synchronous session"]},
    "43": {"label": "University Policies", "any": ["accessibility", "disability resource", "dro@ncsu", "non-discrimination", "nondiscrimination", "harassment", "equal opportunity"]},
    "44": {"label": "Moodle Support for Students", "any": ["moodle support", "moodle help", "wolfware", "learning technology"]}
  }
}
```

- [ ] **Step 2: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_rules_syllabus.py
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import rules

GOOD = """
MBA 520 Corporate Finance. Instructor: Dr. Smith, Nelson Hall 3120.
Office hours by appointment. Upon completion students will be able to value a firm.
Required text: Brealey, ISBN 978-1. Reliable internet and Excel required.
Late work loses 10 percent per day. Academic integrity is expected.
Accessibility: contact the Disability Resource Office. Zoom sessions weekly.
Library resources at lib.ncsu.edu. Moodle support is available through WolfWare.
Tech support: the help desk. This course is fully online and asynchronous.
Course description: an introduction to corporate finance. Assignments are graded.
"""


def test_present_keyword_is_yes():
    assert rules.rule_syllabus(GOOD, 'ok', '41').verdict == rules.YES


def test_absent_keyword_is_no():
    assert rules.rule_syllabus('Nothing useful here.', 'ok', '43').verdict == rules.NO


def test_unreadable_syllabus_is_unknown_never_no():
    r = rules.rule_syllabus('', 'pdf has no text layer, likely a scan', '43')
    assert r.verdict == rules.UNKNOWN
    assert 'no text layer' in r.evidence


def test_missing_syllabus_is_unknown_for_content_rows():
    r = rules.rule_syllabus('', 'no syllabus resource found in course', '35')
    assert r.verdict == rules.UNKNOWN


def test_evidence_quotes_the_matched_keyword():
    r = rules.rule_syllabus(GOOD, 'ok', '43')
    assert 'accessibility' in r.evidence.lower()


def test_all_fourteen_rows_present_in_good_syllabus():
    for row in ['31', '32', '33', '34', '35', '36', '37', '38',
                '39', '40', '41', '42', '43', '44']:
        assert rules.rule_syllabus(GOOD, 'ok', row).verdict == rules.YES, row


def test_registry_has_thirty_four_scored_rules():
    scored = [r for r in rules.RULES if r[0] not in rules.OUT_OF_REACH]
    assert len(scored) == 34


def test_registry_has_thirty_eight_rows_total():
    assert len(rules.RULES) == 38
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_rules_syllabus.py -v`
Expected: FAIL with `AttributeError: module 'rules' has no attribute 'rule_syllabus'`

- [ ] **Step 4: Append to `scripts/rules.py`**

```python
# ---------------------------------------------------------------- Section 3


def load_syllabus_keywords() -> Dict:
    with open(os.path.join(_REFS, 'syllabus-keywords.json')) as fh:
        return json.load(fh)['keywords']


def rule_syllabus(text: str, status: str, row: str,
                  keywords: Optional[Dict] = None) -> Result:
    """Presence check for one required syllabus element.

    If the syllabus could not be read, this is UNKNOWN. Returning NO here would
    mean a course with a scanned PDF outranks a course that genuinely has no
    accessibility statement, which inverts the whole point of the audit.
    """
    keywords = keywords or load_syllabus_keywords()
    spec = keywords[str(row)]
    if status != 'ok':
        return Result(int(row), UNKNOWN, 'syllabus not readable: %s' % status)
    low = text.lower()
    for kw in spec['any']:
        if kw.lower() in low:
            return Result(int(row), YES, 'syllabus contains %r' % kw)
    return Result(int(row), NO,
                  'syllabus has none of: %s' % ', '.join(spec['any'][:4]))


# ---------------------------------------------------------------- Registry

PRESENCE_ROWS = ['17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27']
SYLLABUS_ROWS = ['31', '32', '33', '34', '35', '36', '37', '38',
                 '39', '40', '41', '42', '43', '44']

# (row, label, kind). kind selects how score_course calls it.
RULES = (
    [(8, 'Course Banner', 'bundle'),
     (9, 'Course Format', 'bundle'),
     (10, 'Course Structure', 'bundle'),
     (11, 'Time Frame for Modules', 'bundle'),
     (12, 'Course Links', 'links'),
     (16, 'Course name, number and section', 'bundle')]
    + [(int(r), load_presence_patterns()[r]['label'], 'presence') for r in PRESENCE_ROWS]
    + [(28, 'Welcome Forum/Announcement', 'bundle')]
    + [(int(r), load_syllabus_keywords()[r]['label'], 'syllabus') for r in SYLLABUS_ROWS]
    + [(49, 'Length of asynchronous video lectures', 'na'),
       (50, 'Audio/video quality', 'na'),
       (52, 'Captions and transcripts', 'na'),
       (53, 'Lecture slide PDFs/PowerPoints included', 'bundle'),
       (55, 'Expectations and instructions are clear', 'na'),
       (56, 'Instructions and/or rubrics for assessments', 'bundle')]
)

_BUNDLE_RULES = {
    8: rule_course_banner,
    9: rule_course_format,
    10: rule_course_structure,
    11: rule_time_frame,
    16: rule_course_name_section,
    28: rule_welcome_forum,
    53: rule_slides_present,
    56: rule_assessment_instructions,
}


def score_course(bundle: Dict, syllabus_text: str, syllabus_status: str,
                 link_results: Dict[str, str]) -> List[Result]:
    """Run all 38 rows against one course and return results in row order."""
    patterns = load_presence_patterns()
    keywords = load_syllabus_keywords()
    out = []  # type: List[Result]
    for row, _label, kind in RULES:
        if kind == 'bundle':
            out.append(_BUNDLE_RULES[row](bundle))
        elif kind == 'links':
            out.append(rule_course_links(bundle, link_results))
        elif kind == 'presence':
            out.append(rule_presence(bundle, str(row), patterns))
        elif kind == 'syllabus':
            out.append(rule_syllabus(syllabus_text, syllabus_status, str(row), keywords))
        elif kind == 'na':
            out.append(rule_out_of_reach(row))
    return sorted(out, key=lambda r: r.row)
```

- [ ] **Step 5: Run the whole suite**

Run: `python3 -m pytest skills/moodle-course-standards/tests/ -v`
Expected: all tests pass, including the two registry count tests

- [ ] **Step 6: Commit**

```bash
git add skills/moodle-course-standards/scripts/rules.py \
        skills/moodle-course-standards/references/syllabus-keywords.json \
        skills/moodle-course-standards/tests/test_rules_syllabus.py
git commit -m "feat: add the 14 syllabus keyword rules and the rule registry"
```

---

### Task 7: Three sheet workbook reporter

**Files:**
- Create: `skills/moodle-course-standards/scripts/report.py`
- Test: `skills/moodle-course-standards/tests/test_report.py`

**Interfaces:**
- Consumes: `rules.Result`, `rules.RULES`, verdict constants
- Produces: `summarise(course: dict, results: list) -> dict`; `write_workbook(rows: list, out_path: str) -> str` where each row is `{'course': dict, 'results': List[Result]}`.

- [ ] **Step 1: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_report.py
from __future__ import annotations
import os, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import openpyxl
import report
import rules

COURSE_A = {'id': 1, 'shortname': 'MBA 520 (631)', 'fullname': 'MBA 520 (631) Spring 2026',
            'sections': ['631'], 'instructor': 'Smith'}
COURSE_B = {'id': 2, 'shortname': 'MBA 507 (632)', 'fullname': 'MBA 507 (632) Spring 2026',
            'sections': ['632'], 'instructor': 'Jones'}

RES_A = [rules.Result(8, rules.NO, 'no course image'),
         rules.Result(9, rules.NO, 'default section names'),
         rules.Result(10, rules.YES, 'consistent'),
         rules.Result(43, rules.UNKNOWN, 'syllabus not readable: scan')]
RES_B = [rules.Result(8, rules.YES, 'image set'),
         rules.Result(9, rules.YES, 'named'),
         rules.Result(10, rules.YES, 'consistent'),
         rules.Result(43, rules.NO, 'no accessibility statement')]


def test_summarise_counts_only_confirmed_no():
    s = report.summarise(COURSE_A, RES_A)
    assert s['no'] == 2
    assert s['unknown'] == 1
    assert s['yes'] == 1


def test_summarise_names_worst_failures():
    s = report.summarise(COURSE_A, RES_A)
    assert 'Course Banner' in s['top_failures']


def test_ranking_sorts_worst_first():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'r.xlsx')
        report.write_workbook([{'course': COURSE_B, 'results': RES_B},
                               {'course': COURSE_A, 'results': RES_A}], out)
        wb = openpyxl.load_workbook(out)
        ws = wb['Ranking']
        assert ws.cell(2, 1).value == 'MBA 520 (631)'
        assert ws.cell(3, 1).value == 'MBA 507 (632)'


def test_unknown_does_not_push_a_course_down_the_ranking():
    """A course with 1 No and 3 Unknown must rank above one with 2 No."""
    res_unknown = [rules.Result(8, rules.NO, 'x')] + [
        rules.Result(r, rules.UNKNOWN, 'unreadable') for r in (41, 42, 43)]
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'r.xlsx')
        report.write_workbook([{'course': COURSE_B, 'results': res_unknown},
                               {'course': COURSE_A, 'results': RES_A}], out)
        ws = openpyxl.load_workbook(out)['Ranking']
        assert ws.cell(2, 1).value == 'MBA 520 (631)'


def test_three_sheets_exist():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'r.xlsx')
        report.write_workbook([{'course': COURSE_A, 'results': RES_A}], out)
        wb = openpyxl.load_workbook(out)
        assert wb.sheetnames == ['Ranking', 'Detail', 'Evidence']


def test_detail_has_one_row_per_course_per_result():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'r.xlsx')
        report.write_workbook([{'course': COURSE_A, 'results': RES_A},
                               {'course': COURSE_B, 'results': RES_B}], out)
        ws = openpyxl.load_workbook(out)['Detail']
        assert ws.max_row == 1 + len(RES_A) + len(RES_B)


def test_evidence_sheet_only_carries_no_and_unknown():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'r.xlsx')
        report.write_workbook([{'course': COURSE_A, 'results': RES_A}], out)
        ws = openpyxl.load_workbook(out)['Evidence']
        assert ws.max_row == 1 + 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_report.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'report'`

- [ ] **Step 3: Write the implementation**

```python
# skills/moodle-course-standards/scripts/report.py
"""Write the three sheet audit workbook."""
from __future__ import annotations

from typing import Dict, List

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

import rules

LABELS = dict((row, label) for row, label, _kind in rules.RULES)

HEADER_FILL = PatternFill('solid', fgColor='DDDDDD')
BAD_FILL = PatternFill('solid', fgColor='F8CBAD')
UNKNOWN_FILL = PatternFill('solid', fgColor='FFE699')


def summarise(course: Dict, results: List) -> Dict:
    counts = {rules.YES: 0, rules.NO: 0, rules.SOMEWHAT: 0,
              rules.NA: 0, rules.UNKNOWN: 0}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    failures = [LABELS.get(r.row, 'row %s' % r.row) for r in results if r.verdict == rules.NO]
    return {
        'course': course,
        'yes': counts[rules.YES],
        'no': counts[rules.NO],
        'somewhat': counts[rules.SOMEWHAT],
        'na': counts[rules.NA],
        'unknown': counts[rules.UNKNOWN],
        'top_failures': '; '.join(failures[:3]),
        'results': results,
    }


def _header(ws, titles):
    ws.append(titles)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
    ws.freeze_panes = 'A2'


def write_workbook(rows: List[Dict], out_path: str) -> str:
    """rows: [{'course': {...}, 'results': [Result, ...]}, ...]"""
    summaries = [summarise(r['course'], r['results']) for r in rows]
    # Ranking sorts on confirmed failures only. Unknown is shown but never
    # counted, so a course is never ranked worst for our inability to check it.
    summaries.sort(key=lambda s: (-s['no'], -s['somewhat'], s['course'].get('shortname', '')))

    wb = openpyxl.Workbook()

    ws = wb.active
    ws.title = 'Ranking'
    _header(ws, ['Course', 'Sections', 'Instructor', 'Failed', 'Partial',
                 'Passed', 'Unknown', 'N/A', 'Worst three'])
    for s in summaries:
        c = s['course']
        ws.append([c.get('shortname', ''), ', '.join(c.get('sections', [])),
                   c.get('instructor', ''), s['no'], s['somewhat'], s['yes'],
                   s['unknown'], s['na'], s['top_failures']])
    for col, width in zip('ABCDEFGHI', [30, 12, 20, 8, 8, 8, 10, 8, 60]):
        ws.column_dimensions[col].width = width

    ws = wb.create_sheet('Detail')
    _header(ws, ['Course', 'Row', 'Item', 'Verdict'])
    for s in summaries:
        for r in s['results']:
            ws.append([s['course'].get('shortname', ''), r.row,
                       LABELS.get(r.row, ''), r.verdict])
            if r.verdict == rules.NO:
                ws.cell(ws.max_row, 4).fill = BAD_FILL
            elif r.verdict == rules.UNKNOWN:
                ws.cell(ws.max_row, 4).fill = UNKNOWN_FILL
    for col, width in zip('ABCD', [30, 6, 45, 12]):
        ws.column_dimensions[col].width = width

    ws = wb.create_sheet('Evidence')
    _header(ws, ['Course', 'Row', 'Item', 'Verdict', 'Evidence'])
    for s in summaries:
        for r in s['results']:
            if r.verdict in (rules.NO, rules.UNKNOWN, rules.SOMEWHAT):
                ws.append([s['course'].get('shortname', ''), r.row,
                           LABELS.get(r.row, ''), r.verdict, r.evidence])
    for col, width in zip('ABCDE', [30, 6, 45, 12, 90]):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2, min_col=5, max_col=5):
        row[0].alignment = Alignment(wrap_text=True, vertical='top')

    wb.save(out_path)
    return out_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_report.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add skills/moodle-course-standards/scripts/report.py \
        skills/moodle-course-standards/tests/test_report.py
git commit -m "feat: add three sheet audit workbook reporter"
```

---

### Task 8: CLI entry point

**Files:**
- Create: `skills/moodle-course-standards/scripts/audit.py`
- Modify: `skills/moodle-course-standards/tests/test_report.py` (no change; this task adds no new test file, the golden test in Task 9 covers the wiring)

**Interfaces:**
- Consumes: everything above
- Produces: `main(argv=None) -> int`; `collect_links(bundle) -> List[str]`; `check_all_links(urls, auth_domains, workers=8) -> Dict[str, str]`

- [ ] **Step 1: Write the implementation**

```python
# skills/moodle-course-standards/scripts/audit.py
"""CLI for the MBA online course standards audit.

Read only. Run:
    python3 audit.py --term "Spring 2026" --sections '^6\\d\\d$' --out ~/Desktop/audit.xlsx
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import extract
import fetch
import linkcheck
import report
import rules
import selector

DEFAULT_CACHE = os.path.expanduser('~/Documents/Programming/Demo/course-standards-cache')


def collect_links(bundle: Dict) -> List[str]:
    """Every external URL in the course, deduplicated."""
    urls = []
    for sec in bundle.get('contents', []):
        for mod in sec.get('modules', []):
            if mod.get('modname') != 'url':
                continue
            for c in mod.get('contents') or []:
                u = c.get('fileurl')
                if u and u not in urls:
                    urls.append(u)
            if not (mod.get('contents') or []) and mod.get('url'):
                if mod['url'] not in urls:
                    urls.append(mod['url'])
    return urls


def check_all_links(urls: List[str], auth_domains: List[str], workers: int = 8) -> Dict[str, str]:
    if not urls:
        return {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        codes = list(ex.map(linkcheck.check_external, urls))
    return dict((u, linkcheck.link_verdict(u, code, auth_domains))
                for u, code in zip(urls, codes))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Audit online courses against the review checklist')
    ap.add_argument('--term', default='Spring 2026')
    ap.add_argument('--sections', default=r'^6\d\d$', help='regex matched against section numbers')
    ap.add_argument('--search', default='MBA', help='course search string')
    ap.add_argument('--course-ids', default='', help='comma separated ids, overrides term and sections')
    ap.add_argument('--cache', default=DEFAULT_CACHE)
    ap.add_argument('--refresh', action='store_true', help='ignore the cache and refetch')
    ap.add_argument('--skip-links', action='store_true', help='skip HTTP link checking')
    ap.add_argument('--forms', action='store_true', help='also write a filled checklist per course')
    ap.add_argument('--out', default=os.path.expanduser('~/Desktop/MBA-standards.xlsx'))
    args = ap.parse_args(argv)

    base, token = fetch.load_token()
    os.makedirs(args.cache, exist_ok=True)
    auth_domains = linkcheck.load_auth_domains()

    if args.course_ids:
        ids = [int(x) for x in args.course_ids.split(',') if x.strip()]
        courses = [{'id': i, 'shortname': str(i), 'fullname': str(i), 'sections': []} for i in ids]
    else:
        found = fetch.moodle_call(base, token, 'core_course_search_courses',
                                  criterianame='search', criteriavalue=args.search,
                                  page=0, perpage=500)
        courses = selector.select_courses(found.get('courses', []), args.term, args.sections)

    print('%d courses selected' % len(courses))
    rows = []
    for i, course in enumerate(courses, 1):
        print('  [%d/%d] %s' % (i, len(courses), course['shortname']))
        bundle = fetch.fetch_bundle(base, token, course['id'], args.cache, args.refresh)
        # Prefer the live metadata for fullname and format.
        course.setdefault('instructor', ', '.join(
            c.get('fullname', '') for c in (bundle.get('course', {}).get('contacts') or [])))
        text, status = extract.syllabus_text(bundle, base, token, args.cache)
        links = {} if args.skip_links else check_all_links(collect_links(bundle), auth_domains)
        results = rules.score_course(bundle, text, status, links)
        rows.append({'course': course, 'results': results})

    path = report.write_workbook(rows, args.out)
    print('wrote %s' % path)

    if args.forms:
        import forms
        out_dir = os.path.join(os.path.dirname(args.out), 'forms')
        n = forms.write_all(rows, out_dir)
        print('wrote %d filled checklists to %s' % (n, out_dir))
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Smoke test against two real courses**

Run:

```bash
cd ~/Documents/Programming/moodle-teaching-tools/skills/moodle-course-standards/scripts && \
python3 audit.py --course-ids 8298,9065 --skip-links --out /tmp/smoke.xlsx
```

Expected: `2 courses selected`, then `wrote /tmp/smoke.xlsx`. Open it and confirm three sheets with plausible content. `--skip-links` keeps this fast; the link path is exercised in Task 9.

- [ ] **Step 3: Commit**

```bash
git add skills/moodle-course-standards/scripts/audit.py
git commit -m "feat: add audit CLI entry point"
```

---

### Task 9: Golden fixture test

**This task is gated on a human hand-scoring two courses.** Everything else can be built without it. Do not fabricate the expected values: a golden file invented by the same process it is meant to check proves nothing.

**Files:**
- Create: `skills/moodle-course-standards/tests/fixtures/<id>-bundle.json` (two of them)
- Create: `skills/moodle-course-standards/tests/fixtures/<id>-golden.json` (two of them)
- Create: `skills/moodle-course-standards/tests/test_golden.py`

**Interfaces:**
- Consumes: `rules.score_course`
- Produces: nothing downstream

- [ ] **Step 1: Pick the two courses and capture their bundles**

Choose one course expected to score well and one expected to score badly, so the fixtures cover both ends.

```bash
cd ~/Documents/Programming/moodle-teaching-tools/skills/moodle-course-standards && \
python3 -c "
import sys; sys.path.insert(0,'scripts')
import fetch, json
base, token = fetch.load_token()
for cid in (8298, 9065):
    b = fetch.fetch_bundle(base, token, cid, 'tests/fixtures', refresh=True)
    print(cid, len(b['contents']), 'sections')
"
mv tests/fixtures/8298.json tests/fixtures/8298-bundle.json
mv tests/fixtures/9065.json tests/fixtures/9065-bundle.json
```

- [ ] **Step 2: Hand score both courses**

A person opens each course in Moodle and fills in the checklist for the 34 in scope rows. Record as JSON, row number to verdict:

```json
{
  "course_id": 8298,
  "scored_by": "Elizabeth Shamblin",
  "scored_on": "2026-09-16",
  "verdicts": {
    "8": "No",
    "9": "Yes",
    "10": "Yes"
  }
}
```

Every one of the 34 rows must be present. Save as `tests/fixtures/8298-golden.json` and `tests/fixtures/9065-golden.json`.

- [ ] **Step 3: Write the test**

```python
# skills/moodle-course-standards/tests/test_golden.py
"""The tool must reproduce a human's scoring before it reports on 42 courses.

This is the repo's self-check rule for analysis scripts: a plausible looking
wrong number is the failure mode here, and re-reading the rules does not catch
it.
"""
from __future__ import annotations
import json, os, sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import rules

FIXTURES = os.path.join(HERE, 'fixtures')
GOLDEN = [f for f in sorted(os.listdir(FIXTURES)) if f.endswith('-golden.json')] \
    if os.path.isdir(FIXTURES) else []


@pytest.mark.skipif(not GOLDEN, reason='no hand scored fixtures recorded yet')
@pytest.mark.parametrize('golden_file', GOLDEN)
def test_tool_reproduces_hand_scoring(golden_file):
    with open(os.path.join(FIXTURES, golden_file)) as fh:
        golden = json.load(fh)
    cid = golden['course_id']
    with open(os.path.join(FIXTURES, '%s-bundle.json' % cid)) as fh:
        bundle = json.load(fh)

    syllabus_path = os.path.join(FIXTURES, '%s-syllabus.txt' % cid)
    if os.path.exists(syllabus_path):
        with open(syllabus_path) as fh:
            text, status = fh.read(), 'ok'
    else:
        text, status = '', 'no syllabus resource found in course'

    link_path = os.path.join(FIXTURES, '%s-links.json' % cid)
    links = json.load(open(link_path)) if os.path.exists(link_path) else {}

    got = dict((str(r.row), r.verdict) for r in
               rules.score_course(bundle, text, status, links))

    mismatches = []
    for row, expected in golden['verdicts'].items():
        actual = got.get(row)
        if actual != expected:
            mismatches.append('row %s: human said %s, tool said %s' % (row, expected, actual))

    assert not mismatches, (
        'Tool does not reproduce the hand scoring for course %s:\n  %s\n'
        'Fix the rules or correct the golden file. Do not report numbers until '
        'this passes.' % (cid, '\n  '.join(mismatches)))
```

- [ ] **Step 4: Run it and iterate on the rules until it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_golden.py -v`
Expected: 2 passed. Every mismatch is either a rule bug or a genuine disagreement about what the checklist item means. Resolve each one explicitly, and where the human was applying a standard the rule does not encode, change the rule, not the golden file.

- [ ] **Step 5: Commit**

```bash
git add skills/moodle-course-standards/tests/fixtures skills/moodle-course-standards/tests/test_golden.py
git commit -m "test: add hand scored golden fixtures for two courses"
```

---

### Task 10: Optional per course checklist fill

**Files:**
- Create: `skills/moodle-course-standards/scripts/forms.py`
- Create: `skills/moodle-course-standards/templates/Course-Review-Checklist.xlsx`
- Test: `skills/moodle-course-standards/tests/test_forms.py`

**Interfaces:**
- Consumes: `rules.Result`
- Produces: `write_all(rows: list, out_dir: str) -> int`; `fill_one(course: dict, results: list, template: str, out_path: str) -> str`

- [ ] **Step 1: Copy the template**

```bash
cp ~/Downloads/"Course Review Checklist for Online Courses.xlsx" \
   ~/Documents/Programming/moodle-teaching-tools/skills/moodle-course-standards/templates/Course-Review-Checklist.xlsx
```

- [ ] **Step 2: Write the failing test**

```python
# skills/moodle-course-standards/tests/test_forms.py
from __future__ import annotations
import os, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import openpyxl
import forms
import rules

TEMPLATE = os.path.join(os.path.dirname(__file__), '..', 'templates',
                        'Course-Review-Checklist.xlsx')


def test_fill_writes_verdict_into_column_b():
    course = {'id': 1, 'shortname': 'MBA 520 (631)', 'fullname': 'MBA 520 (631) Spring 2026',
              'instructor': 'Smith'}
    results = [rules.Result(8, rules.NO, 'no course image'),
               rules.Result(9, rules.YES, 'named sections')]
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'x.xlsx')
        forms.fill_one(course, results, TEMPLATE, out)
        ws = openpyxl.load_workbook(out)['Sheet1']
        assert ws.cell(8, 2).value == 'No'
        assert ws.cell(9, 2).value == 'Yes'


def test_fill_writes_evidence_into_comments_column():
    course = {'id': 1, 'shortname': 'MBA 520 (631)', 'fullname': 'x', 'instructor': 'y'}
    results = [rules.Result(8, rules.NO, 'no course image set')]
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'x.xlsx')
        forms.fill_one(course, results, TEMPLATE, out)
        ws = openpyxl.load_workbook(out)['Sheet1']
        assert 'no course image set' in (ws.cell(8, 3).value or '')


def test_fill_writes_header_block():
    course = {'id': 1, 'shortname': 'MBA 520 (631)',
              'fullname': 'MBA 520 (631) Spring 2026', 'instructor': 'Smith'}
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'x.xlsx')
        forms.fill_one(course, [], TEMPLATE, out)
        ws = openpyxl.load_workbook(out)['Sheet1']
        assert 'MBA 520' in (ws.cell(1, 2).value or '')
        assert ws.cell(3, 2).value == 'Smith'


def test_unknown_is_written_as_a_comment_not_a_dropdown_value():
    """'Unknown' is not one of the form's four values, so it goes in comments
    and the dropdown is left blank for a human to fill."""
    course = {'id': 1, 'shortname': 'x', 'fullname': 'x', 'instructor': 'y'}
    results = [rules.Result(43, rules.UNKNOWN, 'syllabus not readable: scan')]
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'x.xlsx')
        forms.fill_one(course, results, TEMPLATE, out)
        ws = openpyxl.load_workbook(out)['Sheet1']
        assert ws.cell(43, 2).value in (None, '')
        assert 'could not check' in (ws.cell(43, 3).value or '').lower()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_forms.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'forms'`

- [ ] **Step 4: Write the implementation**

```python
# skills/moodle-course-standards/scripts/forms.py
"""Fill one copy of the supplied checklist per course.

Writes into the original workbook so its Yes/No/Somewhat/N/A dropdowns and its
pre-written RECOMMEND text survive. Off by default: the stated deliverable is
the tool, not the paperwork.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List

import openpyxl

import rules

FORM_VALUES = (rules.YES, rules.NO, rules.SOMEWHAT, rules.NA)


def _safe(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', '-', name).strip('-')


def fill_one(course: Dict, results: List, template: str, out_path: str) -> str:
    wb = openpyxl.load_workbook(template)
    ws = wb['Sheet1']

    ws.cell(1, 2).value = course.get('fullname', '')
    ws.cell(2, 2).value = 'Spring 2026'
    ws.cell(3, 2).value = course.get('instructor', '')
    ws.cell(4, 2).value = 'Automated audit, moodle-course-standards'

    for r in results:
        if r.verdict in FORM_VALUES:
            ws.cell(r.row, 2).value = r.verdict
            ws.cell(r.row, 3).value = r.evidence
        else:
            # Unknown is not one of the form's values. Leave the dropdown blank
            # so a human fills it, and say why in the comment.
            ws.cell(r.row, 2).value = None
            ws.cell(r.row, 3).value = 'Could not check automatically: %s' % r.evidence

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    wb.save(out_path)
    return out_path


def write_all(rows: List[Dict], out_dir: str) -> int:
    template = os.path.join(os.path.dirname(__file__), '..', 'templates',
                            'Course-Review-Checklist.xlsx')
    n = 0
    for row in rows:
        course = row['course']
        name = _safe(course.get('shortname') or str(course.get('id')))
        fill_one(course, row['results'], template,
                 os.path.join(out_dir, '%s.xlsx' % name))
        n += 1
    return n
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest skills/moodle-course-standards/tests/test_forms.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add skills/moodle-course-standards/scripts/forms.py \
        skills/moodle-course-standards/templates/Course-Review-Checklist.xlsx \
        skills/moodle-course-standards/tests/test_forms.py
git commit -m "feat: add optional per course checklist fill"
```

---

### Task 11: SKILL.md and the real 42 course run

**Files:**
- Create: `skills/moodle-course-standards/SKILL.md`
- Modify: `README.md` (add the skill to the list)

**Interfaces:**
- Consumes: everything
- Produces: nothing

- [ ] **Step 1: Write SKILL.md**

Follow the structure of `skills/moodle-link-checkup/SKILL.md`: frontmatter with `name` and `description`, then When to Use, What It Produces, Prerequisites, Steps, Critical Details, Quick Reference.

```markdown
---
name: moodle-course-standards
description: Use when asked to audit online courses against a course review checklist, rank courses by how many standards they fail, or find which courses are worst. Triggers on "audit the online MBA courses", "which courses fail the checklist", "score these courses against the standards", "course quality review".
---

# Moodle Course Standards Audit

Scores online courses against the Poole course review checklist and ranks them by
confirmed failures, so hand review goes to the worst offenders rather than to all
42 courses.

## When to Use

- "Which online MBA courses are the most egregious?"
- "Audit the Spring 2026 online sections against the checklist"
- Pre-semester or post-semester course quality review

## What It Produces

One workbook with three sheets: Ranking (one row per course, worst first),
Detail (one row per course per item), Evidence (the specific trigger for every
failure). Optionally a filled copy of the checklist per course.

## Prerequisites

- `MOODLE_PROD_TOKEN` in `~/Documents/Programming/MoodleAPI/.env`
- python3 with openpyxl, pdfplumber, python-docx, python-pptx, requests
- `curl` on the path

## Steps

    cd skills/moodle-course-standards/scripts
    python3 audit.py --term "Spring 2026" --sections '^6\d\d$' --out ~/Desktop/MBA-standards.xlsx

Add `--forms` for the per course checklists, `--skip-links` for a fast run,
`--refresh` to ignore the cache.

## Critical Details

**Unknown is not No.** A syllabus we cannot parse, a file that 404s and a link
that wants a login all report Unknown. The ranking counts only confirmed
failures. Never change this: the output goes to the people who own the courses.

**Four items are out of reach.** Video length, audio quality and captions need
Panopto. "Expectations are clear" is a judgment call. All four report N/A.

**The rules are keyed on the checklist's row numbers.** If the source .xlsx
changes, `references/presence-patterns.json` and `references/syllabus-keywords.json`
must change with it.

**Run the golden test before trusting any output.**

    python3 -m pytest ../tests/test_golden.py -v
```

- [ ] **Step 2: Run the full suite**

Run: `python3 -m pytest skills/moodle-course-standards/tests/ -v`
Expected: all pass, including the golden tests

- [ ] **Step 3: Run the real audit**

```bash
cd ~/Documents/Programming/moodle-teaching-tools/skills/moodle-course-standards/scripts && \
python3 audit.py --term "Spring 2026" --sections '^6\d\d$' \
  --out ~/Desktop/MBA-standards-Spring-2026.xlsx
```

Expected: `42 courses selected`, then a workbook on the Desktop. Sanity check before showing anyone: does the worst course actually look bad when you open it in Moodle, and does the best one look fine? If the ranking disagrees with your instinct, the rules are wrong, not your instinct.

- [ ] **Step 4: Commit**

```bash
git add skills/moodle-course-standards/SKILL.md README.md
git commit -m "docs: add SKILL.md for the course standards audit"
```

---

## Notes for the executor

- **Do not run the audit against a current term without resolving spec Open Question 1.** Fall 2026 exposes only one online MBA section to the search API while Fall 2025 exposed 39. Until that is explained, a current term run will silently audit the wrong set.
- **Task 9 blocks on a human.** Build Tasks 1 through 8 and 10 first, and treat the golden test as the gate before any output is shown to anyone.
- **If `mod_forum_get_forums_by_courses` turns out to be blocked** for this token (Task 3 Step 5), row 28 becomes a permanent UNKNOWN and that has to be said in SKILL.md, not quietly absorbed.
