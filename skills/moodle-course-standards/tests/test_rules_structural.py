from __future__ import annotations
import os
import sys

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


def test_row12_only_auth_links_is_unknown_not_no():
    """A course whose only links are Panopto (common here: course 8298 has 74)
    cannot be verified at all. That is Unknown, which the ranking ignores, not
    Yes, which would claim we checked something we did not."""
    assert rules.rule_course_links(bundle(), {'https://p': 'auth'}).verdict == rules.UNKNOWN


def test_row12_auth_links_do_not_count_against_checkable_ones():
    r = rules.rule_course_links(bundle(), {'https://p': 'auth', 'https://a': 'ok'})
    assert r.verdict == rules.YES


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
