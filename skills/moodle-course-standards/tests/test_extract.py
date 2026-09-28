from __future__ import annotations
import os
import sys
import tempfile

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
        p = os.path.join(d, 'notes.rtf')
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


def _url_bundle(name, url):
    return {'course': {'id': 7}, 'contents': [{'section': 0, 'modules': [
        {'modname': 'url', 'name': 'Zoom syllabus review', 'contents': [{'fileurl': 'https://ncsu.zoom.us/j/1'}]},
        {'modname': 'url', 'name': name, 'contents': [{'fileurl': url}]}]}]}


def test_syllabus_link_is_found_when_no_file_is_uploaded():
    b = _url_bundle('READ: Course Syllabus', 'https://docs.google.com/document/d/abc/edit')
    assert extract.find_syllabus_module(b)['name'] == 'READ: Course Syllabus'


def test_share_links_become_direct_downloads():
    assert extract.direct_download_url('https://docs.google.com/document/d/abc_1/edit?usp=sharing') == \
        'https://docs.google.com/document/d/abc_1/export?format=txt'
    assert extract.direct_download_url('https://www.dropbox.com/scl/fi/x/S.pdf?rlkey=k&dl=0') == \
        'https://www.dropbox.com/scl/fi/x/S.pdf?rlkey=k&dl=1'


class _Resp(object):
    def __init__(self, code, ctype, body=b''):
        self.status_code, self.headers, self.content = code, {'content-type': ctype}, body


def test_link_needing_login_is_reported_not_extracted(monkeypatch, tmp_path):
    monkeypatch.setattr(extract.requests, 'get', lambda *a, **k: _Resp(401, 'text/html'))
    path, status = extract.download_link('https://docs.google.com/document/d/abc/edit', str(tmp_path / 's'))
    assert path == '' and 'needs a login' in status


def test_login_page_with_200_is_not_a_syllabus(monkeypatch, tmp_path):
    monkeypatch.setattr(extract.requests, 'get', lambda *a, **k: _Resp(200, 'text/html; charset=utf-8', b'<html>'))
    path, status = extract.download_link('https://1drv.ms/b/x', str(tmp_path / 's'))
    assert path == '' and 'web page or login' in status


def test_public_google_doc_is_saved_as_text(monkeypatch, tmp_path):
    monkeypatch.setattr(extract.requests, 'get', lambda *a, **k: _Resp(200, 'text/plain', b'Course description'))
    path, status = extract.download_link('https://docs.google.com/document/d/abc/edit', str(tmp_path / 's'))
    assert status == 'ok' and extract.extract_text(path) == ('Course description', 'ok')


def test_syllabus_inside_a_folder_is_found():
    """MIE 512 Fall 2026 keeps its syllabus in a 'Course Documents' folder."""
    b = {'contents': [{'section': 0, 'modules': [
        {'modname': 'folder', 'name': 'Course Documents', 'contents': [
            {'filename': 'Playposit Guide.pdf'}, {'filename': 'MIE 512_Course Syllabus.pdf'}]}]}]}
    mod = extract.find_syllabus_module(b)
    assert [c['filename'] for c in mod['contents']] == ['MIE 512_Course Syllabus.pdf']


def test_standin_is_marked_so_it_gets_checked():
    b = {'contents': [{'section': 0, 'modules': [
        {'modname': 'resource', 'name': 'Class Schedule',
         'contents': [{'filename': 'ITAO 550 Course Schedule Fall 2026.docx'}]}]}]}
    assert extract.find_syllabus_module(b).get('standin') is True


def test_a_bare_schedule_does_not_read_like_a_syllabus():
    assert not extract.looks_like_syllabus('Week 1 Aug 17. Week 2 Aug 24. Exam 1 Sep 14.')
    assert extract.looks_like_syllabus('Instructor: Hale. Office hours Tue. Grading: 40% exams.')


def test_dropbox_pdf_served_as_binary_is_recognised(monkeypatch, tmp_path):
    monkeypatch.setattr(extract.requests, 'get',
                        lambda *a, **k: _Resp(200, 'application/binary', b'%PDF-1.7 ...'))
    path, status = extract.download_link('https://www.dropbox.com/scl/fi/x/S.pdf?dl=0', str(tmp_path / 's'))
    assert status == 'ok' and path.endswith('.pdf')
