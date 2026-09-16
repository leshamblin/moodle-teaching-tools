from __future__ import annotations
import os
import sys

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
