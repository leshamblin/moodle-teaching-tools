from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import rules

GOOD = """
MBA 520 Corporate Finance. Instructor: Dr. Smith, Nelson Hall 3120.
Office hours by appointment. Upon completion students will be able to value a firm.
Required text: Brealey, ISBN 978-1. Reliable internet and Excel required.
Late work loses 10 percent per day. Academic integrity is expected.
Accessibility: contact the Disability Resource Office. Zoom sessions weekly.
Library resources at lib.ncsu.edu. Moodle support is available through WolfWare.
Tech support: the help desk. This course is fully online and asynchronous.
Course description: an introduction to corporate finance. Assignments are graded.
"""


def test_present_keyword_is_yes():
    assert rules.rule_syllabus(GOOD, 'ok', '41').verdict == rules.YES


def test_absent_keyword_is_no():
    assert rules.rule_syllabus('Nothing useful here.', 'ok', '43').verdict == rules.NO


def test_unreadable_syllabus_is_unknown_never_no():
    r = rules.rule_syllabus('', 'pdf has no text layer, likely a scan', '43')
    assert r.verdict == rules.UNKNOWN
    assert 'no text layer' in r.evidence


def test_missing_syllabus_is_unknown_for_content_rows():
    r = rules.rule_syllabus('', 'no syllabus resource found in course', '35')
    assert r.verdict == rules.UNKNOWN


def test_evidence_quotes_the_matched_keyword():
    r = rules.rule_syllabus(GOOD, 'ok', '43')
    assert 'accessibility' in r.evidence.lower()


def test_all_fourteen_rows_present_in_good_syllabus():
    for row in ['31', '32', '33', '34', '35', '36', '37', '38',
                '39', '40', '41', '42', '43', '44']:
        assert rules.rule_syllabus(GOOD, 'ok', row).verdict == rules.YES, row


def test_registry_has_thirty_four_scored_rules():
    scored = [r for r in rules.RULES if r[0] not in rules.OUT_OF_REACH]
    assert len(scored) == 34


def test_registry_has_thirty_eight_rows_total():
    assert len(rules.RULES) == 38
