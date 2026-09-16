from __future__ import annotations
import os
import sys

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
