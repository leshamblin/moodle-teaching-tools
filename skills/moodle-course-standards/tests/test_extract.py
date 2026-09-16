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
