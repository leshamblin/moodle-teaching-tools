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


FALL_2026 = [
    {'id': 11298, 'shortname': 'MKT 510 (631) FALL 2026',
     'fullname': 'MKT 510 (631) Fall 2026 Marketing Management and Strategy'},
    {'id': 12521, 'shortname': 'ITAO 540 (631, 632) FALL 2026',
     'fullname': 'ITAO 540 (631, 632) Fall 2026 Principles of Operations'},
    {'id': 9068, 'shortname': 'ACC 530 (601) FALL 2026',
     'fullname': 'ACC 530 (601) Fall 2026 Advanced Income Tax'},
    {'id': 9077, 'shortname': 'BUS 360 (631) FALL 2026',
     'fullname': 'BUS 360 (631) Fall 2026 Marketing Methods'},
    {'id': 9881, 'shortname': 'MIE 531 (301 & 302) FALL 2026',
     'fullname': 'MIE 531 (301 &amp; 302) Fall 2026 Leading People 1'},
]


def test_number_pattern_keeps_only_graduate_online_sections():
    got = selector.select_courses(FALL_2026, 'Fall 2026', r'^63\d$', r'^5')
    assert [c['id'] for c in got] == [11298, 12521]


def test_fullname_entities_are_decoded():
    got = selector.select_courses(FALL_2026, 'Fall 2026', r'^30\d$', r'^5')
    assert got[0]['fullname'] == 'MIE 531 (301 & 302) Fall 2026 Leading People 1'
    assert got[0]['sections'] == ['301', '302']
