"""The tool must reproduce a human's scoring before its ranking goes anywhere.

This is the repo's self-check rule for analysis scripts: a plausible looking
wrong number is the failure mode here, and re-reading the rules does not catch
it.

The hand reviews are named reviews of colleagues' courses, and the course
snapshots carry student names in forum subjects, so none of it lives in this
public repo. It sits in a private folder, by default
~/Documents/Programming/MBA-Course-Review-Pilot/golden, or $COURSE_STANDARDS_GOLDEN:

    <id>-*.xlsx         the filled review checklist, verdicts in column B
    <id>-bundle.json    the course snapshot the review was made against
    <id>-syllabus.txt   that course's syllabus text
    disputed.json       rows where the tool deliberately disagrees, with reasons

The comparison is on whether a row fails (No versus anything else), because the
ranking counts failures. Yes versus Somewhat is a difference of degree.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import rules


GOLDEN_DIR = os.environ.get('COURSE_STANDARDS_GOLDEN',
                            os.path.expanduser('~/Documents/Programming/MBA-Course-Review-Pilot/golden'))
REVIEWS = sorted(glob.glob(os.path.join(GOLDEN_DIR, '[0-9]*-*.xlsx')))
REVIEW_IDS = [os.path.basename(p).split('-')[0] for p in REVIEWS]


def _load(cid: str):
    import openpyxl
    review = glob.glob(os.path.join(GOLDEN_DIR, '%s-*.xlsx' % cid))[0]
    ws = openpyxl.load_workbook(review, data_only=True)['Sheet1']
    with open(os.path.join(GOLDEN_DIR, '%s-bundle.json' % cid)) as fh:
        bundle = json.load(fh)
    with open(os.path.join(GOLDEN_DIR, '%s-syllabus.txt' % cid)) as fh:
        text = fh.read()
    return ws, bundle, text


@pytest.mark.filterwarnings('ignore:Data Validation extension')
@pytest.mark.skipif(not REVIEWS, reason='no hand reviews in %s' % GOLDEN_DIR)
@pytest.mark.parametrize('review', REVIEWS, ids=REVIEW_IDS)
def test_tool_agrees_with_hand_review_on_failures(review):
    cid = os.path.basename(review).split('-')[0]
    ws, bundle, text = _load(cid)
    with open(os.path.join(GOLDEN_DIR, 'disputed.json')) as fh:
        disputed = json.load(fh).get(cid, {})

    mismatches = []
    for r in rules.score_course(bundle, text, 'ok', {}):
        human = ws.cell(r.row, 2).value
        if human is None or r.verdict in (rules.NA, rules.UNKNOWN) or str(r.row) in disputed:
            continue
        if (human == rules.NO) != (r.verdict == rules.NO):
            mismatches.append('row %s: review said %s, tool said %s (%s)'
                              % (r.row, human, r.verdict, r.evidence))

    assert not mismatches, (
        'Tool disagrees with the hand review of course %s:\n  %s\n'
        'Fix the rule, or if the tool is right, record the row and why in '
        'disputed.json. Do not send a ranking until this passes.'
        % (cid, '\n  '.join(mismatches)))
