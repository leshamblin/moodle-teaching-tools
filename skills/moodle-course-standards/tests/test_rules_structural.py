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


def test_row8_image_at_top_of_page_is_yes():
    b = bundle()
    b['contents'][0]['summary'] = '<p><img src="banner.png" alt="MBA 520"></p>'
    assert rules.rule_course_banner(b).verdict == rules.YES


def test_row8_card_image_only_is_somewhat():
    b = bundle()
    b['course']['courseimage'] = 'https://m.edu/pluginfile.php/1/course/overviewfiles/x.png'
    assert rules.rule_course_banner(b).verdict == rules.SOMEWHAT


def test_row8_generated_placeholder_is_not_an_image():
    """Moodle fills courseimage with a generated SVG when none is uploaded."""
    b = bundle()
    b['course']['courseimage'] = 'https://m.edu/pluginfile.php/1/course/generated/course.svg'
    assert rules.rule_course_banner(b).verdict == rules.NO


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


def test_row16_number_and_section_on_page_is_yes():
    b = bundle()
    b['contents'][0]['summary'] = 'Welcome to MBA 520, section 631'
    assert rules.rule_course_name_section(b).verdict == rules.YES


def test_row16_number_only_on_page_is_somewhat():
    b = bundle()
    b['contents'][0]['modules'] = [{'modname': 'url', 'name': 'MBA 520 -- All Sections -- Office Hours'}]
    assert rules.rule_course_name_section(b).verdict == rules.SOMEWHAT


def test_row16_old_prefix_on_page_still_counts():
    """MKT 510 in Fall 2026 still calls itself MBA 510 in its content."""
    b = bundle()
    b['course']['fullname'] = 'MKT 510 (631) Fall 2026 Marketing Management'
    b['contents'][0]['summary'] = 'MBA 510 (631) course information'
    assert rules.rule_course_name_section(b).verdict == rules.YES


def test_row16_moodle_course_name_alone_is_no():
    assert rules.rule_course_name_section(bundle()).verdict == rules.NO


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


def test_presence_rule_looks_in_getting_started_section():
    """MKT 510 Fall 2026 keeps its syllabus link in section 1, 'Getting Started'."""
    b = bundle()
    b['contents'].insert(1, {'section': 1, 'name': 'Getting Started', 'summary': '',
                             'modules': [{'modname': 'url',
                                          'name': 'READ: Course Syllabus MBA 510 FALL 2026'}]})
    assert rules.rule_presence(b, '17').verdict == rules.YES


def test_presence_rule_missing_is_no():
    assert rules.rule_presence(bundle(), '17').verdict == rules.NO


def test_row28_forum_with_no_discussions_is_no():
    b = bundle()
    b['forums'] = [{'id': 5, 'name': 'Announcements', 'numdiscussions': 0}]
    assert rules.rule_welcome_forum(b).verdict == rules.NO


def test_row28_welcome_post_and_intro_forum_is_yes():
    b = bundle()
    b['forums'] = [{'id': 5, 'name': 'Announcements', 'numdiscussions': 2},
                   {'id': 6, 'name': 'Introduce Yourself!', 'numdiscussions': 40}]
    b['discussions'] = {'5': ['Grades in Moodle', 'Welcome to MBA 507'], '6': ['Intro']}
    assert rules.rule_welcome_forum(b).verdict == rules.YES


def test_row28_weekly_announcements_without_welcome_is_somewhat_with_intro_forum():
    b = bundle()
    b['forums'] = [{'id': 5, 'name': 'Announcements', 'numdiscussions': 13},
                   {'id': 6, 'name': 'Introduce Yourself!', 'numdiscussions': 40}]
    b['discussions'] = {'5': ['MBA 520, Week 9', 'Farewell to MBA 520!'], '6': ['Intro']}
    assert rules.rule_welcome_forum(b).verdict == rules.SOMEWHAT


def test_row28_posts_but_no_welcome_and_no_intro_forum_is_no():
    b = bundle()
    b['forums'] = [{'id': 5, 'name': 'Announcements', 'numdiscussions': 3}]
    b['discussions'] = {'5': ['Exam grades posted']}
    assert rules.rule_welcome_forum(b).verdict == rules.NO


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


def test_row9_some_default_names_is_somewhat():
    b = bundle()
    b['contents'].append({'section': 2, 'name': 'Week 2', 'summary': '', 'modules': []})
    assert rules.rule_course_format(b).verdict == rules.SOMEWHAT


def test_row11_exam_sections_need_no_dates():
    b = bundle()
    b['contents'].append({'section': 2, 'name': 'Final Exam', 'summary': '', 'modules': []})
    assert rules.rule_time_frame(b).verdict == rules.YES


def test_hidden_sections_are_ignored():
    b = bundle()
    b['contents'].append({'section': 2, 'name': 'Old Videos', 'summary': '', 'visible': 0,
                          'modules': []})
    assert rules.rule_time_frame(b).verdict == rules.YES


def test_row53_slides_inside_a_folder_count():
    b = bundle()
    b['contents'][1]['modules'] = [{'modname': 'folder', 'name': 'Lecture Slides and Data',
                                    'contents': [{'filename': 'W1 Regression.pptx',
                                                  'mimetype': 'application/vnd.openxmlformats-'
                                                              'officedocument.presentationml.presentation'}]}]
    assert rules.rule_slides_present(b).verdict == rules.YES


def test_presence_only_in_syllabus_is_somewhat():
    r = rules.rule_presence(bundle(), '23', syllabus_text='Email me; I reply within a day.',
                            syllabus_status='ok')
    assert r.verdict == rules.SOMEWHAT


def test_presence_missing_and_syllabus_unreadable_is_unknown():
    r = rules.rule_presence(bundle(), '23', syllabus_text='', syllabus_status='pdf has no text layer')
    assert r.verdict == rules.UNKNOWN


def test_presence_schedule_inside_syllabus_label_is_not_a_separate_schedule():
    b = bundle()
    b['contents'][0]['modules'] = [{'modname': 'label', 'name': 'Syllabus with Schedule'}]
    r = rules.rule_presence(b, '18', syllabus_text='Week 1 schedule', syllabus_status='ok')
    assert r.verdict == rules.SOMEWHAT


def test_row26_tutorial_is_not_tutoring():
    b = bundle()
    b['contents'][0]['modules'] = [{'modname': 'url', 'name': 'JMP tutorial videos'}]
    assert rules.rule_presence(b, '26', syllabus_status='ok').verdict == rules.NO


def test_row22_navigation_phrase_in_a_description_does_not_count():
    b = bundle()
    b['contents'][0]['modules'] = [{'modname': 'url', 'name': 'JMP introductory videos',
                                    'description': 'the first column is helpful for getting started'}]
    assert rules.rule_presence(b, '22', syllabus_status='ok').verdict == rules.NO
