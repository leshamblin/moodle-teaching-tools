from __future__ import annotations
import json
import os
import sys
import tempfile

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
