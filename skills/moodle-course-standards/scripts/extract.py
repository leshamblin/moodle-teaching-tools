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
# A URL module named like a syllabus but pointing at a meeting or a video.
NOT_A_SYLLABUS_LINK_RX = re.compile(r'zoom|video|recording|review session|quiz', re.I)
GDOC_RX = re.compile(r'docs\.google\.com/document/d/([\w-]+)')
GDRIVE_RX = re.compile(r'drive\.google\.com/(?:file/d/|open\?id=)([\w-]+)')
# Names that often hold the syllabus when nothing is called one. Only trusted
# if the text passes looks_like_syllabus.
SYLLABUS_STANDIN_RX = re.compile(
    r'course (schedule|guide|information|overview|outline)|class (schedule|document)|'
    r'schedule and polic|process and schedule', re.I)
SYLLABUS_MARKERS = ('grading', 'grade', 'instructor', 'office hours', 'course description',
                    'learning objective', 'learning outcome', 'academic integrity',
                    'accommodation', 'disabilit', 'late ')
CONTENT_EXT = (('application/pdf', '.pdf'),
               ('wordprocessingml', '.docx'),
               ('text/plain', '.txt'))


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
    """Pull plain text out of a PDF, DOCX, PPTX or TXT. Returns (text, status)."""
    lower = path.lower()
    try:
        if lower.endswith('.txt'):
            with open(path, encoding='utf-8', errors='replace') as fh:
                text = fh.read().strip()
            return (text, 'ok') if text else ('', 'text file was empty')
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
        if lower.endswith('.doc'):
            # Old binary Word. macOS ships textutil, which reads it natively.
            import subprocess
            try:
                out = subprocess.run(['textutil', '-convert', 'txt', '-stdout', path],
                                     capture_output=True, timeout=60)
            except FileNotFoundError:
                return '', 'unsupported file type: .doc (needs macOS textutil)'
            text = out.stdout.decode('utf-8', 'replace').strip()
            if not text:
                return '', 'doc contained no text'
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


def _modules(bundle: Dict):
    for section in bundle.get('contents', []):
        for mod in section.get('modules', []):
            yield mod


def find_syllabus_module(bundle: Dict) -> Optional[Dict]:
    """Return the module holding the syllabus, in order of confidence.

    1. a file resource named like a syllabus
    2. a syllabus file inside a folder, returned as a copy holding just that file
    3. a URL module named like one: in Fall 2026 many online MBA courses link
       their syllabus from Google Docs, Dropbox or OneDrive
    4. a file named like a stand-in ('Course Schedule', 'Course Overview'),
       marked 'standin' so the caller checks that it reads like a syllabus
    """
    for mod in _modules(bundle):
        if mod.get('modname') != 'resource':
            continue
        filename = (mod.get('contents') or [{}])[0].get('filename') or ''
        if SYLLABUS_RX.search(mod.get('name') or '') or SYLLABUS_RX.search(filename):
            return mod
    for mod in _modules(bundle):
        if mod.get('modname') != 'folder':
            continue
        for c in mod.get('contents') or []:
            if SYLLABUS_RX.search(c.get('filename') or ''):
                return dict(mod, contents=[c])
    for mod in _modules(bundle):
        name = mod.get('name') or ''
        if (mod.get('modname') == 'url' and SYLLABUS_RX.search(name)
                and not NOT_A_SYLLABUS_LINK_RX.search(name)):
            return mod
    for mod in _modules(bundle):
        if mod.get('modname') in ('resource', 'url') and SYLLABUS_STANDIN_RX.search(mod.get('name') or ''):
            return dict(mod, standin=True)
    return None


def looks_like_syllabus(text: str) -> bool:
    low = text.lower()
    return sum(1 for m in SYLLABUS_MARKERS if m in low) >= 3


def direct_download_url(url: str) -> str:
    """Turn a share link into one that returns the file itself.

    Works only for documents shared publicly. A document limited to NC State
    accounts answers with a login page, which download_link reports as such.
    """
    m = GDOC_RX.search(url)
    if m:
        return 'https://docs.google.com/document/d/%s/export?format=txt' % m.group(1)
    m = GDRIVE_RX.search(url)
    if m:
        return 'https://drive.google.com/uc?export=download&id=%s' % m.group(1)
    if 'dropbox.com' in url:
        url = re.sub(r'([?&])dl=0', r'\1dl=1', url)
        if 'dl=1' not in url:
            url += ('&' if '?' in url else '?') + 'dl=1'
    return url


def download_link(url: str, dest_base: str) -> Tuple[str, str]:
    """Fetch an external syllabus link. Returns (path, status).

    Never sends the Moodle token: these are other people's servers. An HTML
    answer is a login or viewer page, not the document, so it is reported as
    unreadable rather than extracted.
    """
    host = re.sub(r'^https?://([^/]+).*$', r'\1', url)
    try:
        resp = requests.get(direct_download_url(url), timeout=60, allow_redirects=True)
    except Exception as e:
        return '', 'syllabus link failed: %s' % type(e).__name__
    if resp.status_code in (401, 403):
        return '', 'syllabus link on %s needs a login' % host
    if resp.status_code != 200:
        return '', 'syllabus link on %s gave HTTP %s' % (host, resp.status_code)
    ctype = resp.headers.get('content-type', '')
    ext = next((e for key, e in CONTENT_EXT if key in ctype), None)
    if ext is None and resp.content[:4] == b'%PDF':
        ext = '.pdf'  # Dropbox serves files as application/binary
    elif ext is None and resp.content[:2] == b'PK' and 'html' not in ctype:
        ext = '.docx'
    if ext is None:
        if 'html' in ctype:
            return '', 'syllabus link on %s opens a web page or login, not a file' % host
        return '', 'syllabus link on %s returned %s' % (host, ctype or 'no content type')
    if not resp.content:
        return '', 'syllabus link on %s returned an empty file' % host
    path = dest_base + ext
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(resp.content)
    return path, 'ok'


def syllabus_text(bundle: Dict, base: str, token: str, cache_dir: str,
                  refresh: bool = False) -> Tuple[str, str]:
    """Locate, download, extract and cache the syllabus text for one course."""
    course_id = bundle.get('course', {}).get('id', 'unknown')
    cache_file = os.path.join(cache_dir, '%s-syllabus.txt' % course_id)
    status_file = cache_file + '.status'
    if not refresh and os.path.exists(cache_file) and os.path.exists(status_file):
        with open(status_file) as fh:
            status = fh.read().strip()
        with open(cache_file) as fh:
            return fh.read(), status

    mod = find_syllabus_module(bundle)
    if mod is None:
        text, status = '', 'no syllabus resource found in course'
    elif mod.get('modname') == 'url':
        contents = mod.get('contents') or [{}]
        url = contents[0].get('fileurl') or mod.get('url') or ''
        text = ''
        if not url:
            status = 'syllabus link has no url'
        else:
            path, status = download_link(url, os.path.join(cache_dir, '%s-syllabus-link' % course_id))
            if status == 'ok':
                text, status = extract_text(path)
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
    if mod is not None and mod.get('standin') and status == 'ok' and not looks_like_syllabus(text):
        text, status = '', 'no syllabus found; %r does not read like one' % mod.get('name')

    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'w') as fh:
        fh.write(text)
    with open(status_file, 'w') as fh:
        fh.write(status)
    return text, status
