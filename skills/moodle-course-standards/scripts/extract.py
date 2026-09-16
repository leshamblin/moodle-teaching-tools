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
