"""Verdict types and the 34 scoring rules.

Every rule is a pure function of a cached bundle. No network, no file IO, no
clock. That is what makes them testable with a dict literal and what keeps the
golden fixture test meaningful.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, namedtuple
from typing import Dict, List, Optional

import linkcheck

YES = 'Yes'
NO = 'No'
SOMEWHAT = 'Somewhat'
NA = 'N/A'
UNKNOWN = 'Unknown'

Result = namedtuple('Result', 'row verdict evidence')

_REFS = os.path.join(os.path.dirname(__file__), '..', 'references')

INTRO_SECTION_RX = re.compile(r'start here|about|administration|welcome|general', re.I)
DEFAULT_SECTION_RX = re.compile(r'^(topic|week|section|unit)\s*\d*\s*$', re.I)
DATE_RX = re.compile(
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}'
    r'|\b\d{1,2}/\d{1,2}\b'
    r'|\bweek\s+\d+\s*[,:]'
    r'|\b\d+\s*(hours?|minutes?|weeks?)\b', re.I)
ASSESSMENT_MODS = ('assign', 'quiz', 'workshop', 'forum')


def load_presence_patterns() -> Dict:
    with open(os.path.join(_REFS, 'presence-patterns.json')) as fh:
        return json.load(fh)['patterns']


def _intro_sections(bundle: Dict) -> List[Dict]:
    """Sections a student would look in for course information."""
    out = []
    for sec in bundle.get('contents', []):
        if sec.get('section') == 0 or INTRO_SECTION_RX.search(sec.get('name') or ''):
            out.append(sec)
    return out


def _content_sections(bundle: Dict) -> List[Dict]:
    intro_ids = set(id(s) for s in _intro_sections(bundle))
    return [s for s in bundle.get('contents', []) if id(s) not in intro_ids]


def _searchable_text(sections: List[Dict]) -> str:
    parts = []
    for sec in sections:
        parts.append(sec.get('name') or '')
        parts.append(sec.get('summary') or '')
        for mod in sec.get('modules', []):
            parts.append(mod.get('name') or '')
            parts.append(mod.get('description') or '')
            for c in mod.get('contents') or []:
                parts.append(c.get('filename') or '')
    return '\n'.join(parts)


# ---------------------------------------------------------------- Section 1

def rule_course_banner(bundle: Dict) -> Result:
    course = bundle.get('course', {})
    img = course.get('courseimage') or ''
    overview = course.get('overviewfiles') or []
    if img or overview:
        return Result(8, YES, 'course image set')
    return Result(8, NO, 'no course image or overview file set')


def rule_course_format(bundle: Dict) -> Result:
    fmt = bundle.get('course', {}).get('format') or ''
    if fmt not in ('topics', 'weeks'):
        return Result(9, NO, 'course format is %r, not Topics or Weekly' % fmt)
    bad = [s.get('name') or '(unnamed)' for s in _content_sections(bundle)
           if DEFAULT_SECTION_RX.match((s.get('name') or '').strip())]
    if bad:
        return Result(9, NO, 'sections left at default names: %s' % ', '.join(bad[:5]))
    return Result(9, YES, 'format %s with named sections' % fmt)


def rule_course_structure(bundle: Dict) -> Result:
    """Compare each content section's module-type signature to the common one.

    Empty sections are deliberately NOT filtered out. A week with nothing in it
    is exactly the structural outlier this rule exists to catch.
    """
    sections = _content_sections(bundle)
    if len(sections) < 3:
        return Result(10, NA, 'fewer than 3 content sections to compare')
    sigs = {}
    for sec in sections:
        sig = frozenset(m.get('modname') for m in sec.get('modules', []))
        sigs[sec.get('name') or '(unnamed)'] = sig
    common = Counter(sigs.values()).most_common(1)[0][0]
    odd = [name for name, sig in sigs.items() if not common.issubset(sig)]
    if not odd:
        return Result(10, YES, '%d sections share a common structure' % len(sections))
    if len(odd) >= len(sections) / 2.0:
        return Result(10, NO, 'no dominant structure, %d of %d sections differ'
                      % (len(odd), len(sections)))
    return Result(10, SOMEWHAT, 'sections missing the common pattern: %s'
                  % ', '.join(sorted(odd)[:5]))


def rule_time_frame(bundle: Dict) -> Result:
    sections = _content_sections(bundle)
    if not sections:
        return Result(11, NA, 'no content sections')
    with_dates = [s for s in sections
                  if DATE_RX.search((s.get('name') or '') + ' ' + (s.get('summary') or ''))]
    if not with_dates:
        return Result(11, NO, 'no dates or durations in any section name or summary')
    if len(with_dates) < len(sections):
        missing = [s.get('name') or '(unnamed)' for s in sections if s not in with_dates]
        return Result(11, NO, 'sections with no timeframe: %s' % ', '.join(missing[:5]))
    return Result(11, YES, 'all %d content sections state a timeframe' % len(sections))


def rule_course_links(bundle: Dict, link_results: Dict[str, str]) -> Result:
    """link_results maps url -> 'ok' | 'broken' | 'auth'."""
    if not link_results:
        return Result(12, NA, 'no external links in this course')
    broken = sorted([u for u, v in link_results.items() if v == 'broken'])
    checkable = [u for u, v in link_results.items() if v in ('ok', 'broken')]
    if not checkable:
        return Result(12, UNKNOWN, 'every link needed a login, none could be verified')
    if not broken:
        return Result(12, YES, '%d links checked, all resolved' % len(checkable))
    if len(broken) == len(checkable):
        return Result(12, NO, 'all %d checkable links failed: %s'
                      % (len(broken), ', '.join(broken[:3])))
    return Result(12, SOMEWHAT, '%d of %d links failed: %s'
                  % (len(broken), len(checkable), ', '.join(broken[:3])))


# ---------------------------------------------------------------- Section 2

def rule_course_name_section(bundle: Dict) -> Result:
    course = bundle.get('course', {})
    text = (course.get('fullname') or '') + ' ' + (course.get('shortname') or '')
    if re.search(r'\(\s*\d{3}', text):
        return Result(16, YES, 'section number present in course name')
    return Result(16, NO, 'no section number in fullname or shortname')


def rule_presence(bundle: Dict, row: str, patterns: Optional[Dict] = None) -> Result:
    """The shared implementation behind rows 17 through 27.

    They differ only in the pattern they search for, which is why this is one
    function and a data file rather than eleven near-identical functions.
    """
    patterns = patterns or load_presence_patterns()
    spec = patterns[str(row)]
    rx = re.compile(spec['pattern'], re.I)
    haystack = _searchable_text(_intro_sections(bundle))
    m = rx.search(haystack)
    if m:
        return Result(int(row), YES, 'matched %r in the intro section' % m.group(0))
    return Result(int(row), NO, 'nothing matching %r in the intro section' % spec['pattern'])


def rule_welcome_forum(bundle: Dict) -> Result:
    forums = bundle.get('forums') or []
    if not forums:
        return Result(28, UNKNOWN, 'forum data unavailable for this course')
    posted = [f for f in forums if (f.get('numdiscussions') or 0) > 0]
    if posted:
        return Result(28, YES, '%s has %d discussions'
                      % (posted[0].get('name'), posted[0].get('numdiscussions')))
    names = ', '.join(f.get('name') or '(unnamed)' for f in forums[:3])
    return Result(28, NO, 'forums exist but none has a post: %s' % names)


# ---------------------------------------------------------------- Multimedia

def rule_slides_present(bundle: Dict) -> Result:
    found = []
    for sec in _content_sections(bundle):
        for mod in sec.get('modules', []):
            if mod.get('modname') != 'resource':
                continue
            for c in mod.get('contents') or []:
                kind = linkcheck.classify({'modname': 'resource',
                                           'mimetype': c.get('mimetype'),
                                           'filename': c.get('filename')})
                if kind in ('PDF', 'PowerPoint'):
                    found.append(c.get('filename') or kind)
    if found:
        return Result(53, YES, '%d slide or PDF resources, e.g. %s' % (len(found), found[0]))
    return Result(53, NO, 'no PDF or PowerPoint resources in the content sections')


def rule_assessment_instructions(bundle: Dict) -> Result:
    items = []
    for sec in bundle.get('contents', []):
        for mod in sec.get('modules', []):
            if mod.get('modname') in ASSESSMENT_MODS:
                items.append(mod)
    if not items:
        return Result(56, NA, 'no assignments, quizzes or graded forums')
    # core_course_get_contents omits 'description' unless the activity is set to
    # show it on the course page, and mod_assign_get_assignments is blocked for
    # this token because the admin account is not enrolled. If the key is absent
    # everywhere we cannot see instructions at all, which is UNKNOWN, not NO.
    if not any('description' in m for m in items):
        return Result(56, UNKNOWN,
                      'activity descriptions are not exposed by core_course_get_contents '
                      'for this token, so instructions could not be checked')
    bare = [m.get('name') or '(unnamed)' for m in items
            if not (m.get('description') or '').strip()]
    if not bare:
        return Result(56, YES, 'all %d assessments carry instructions' % len(items))
    if len(bare) == len(items):
        return Result(56, NO, 'none of the %d assessments has instructions' % len(items))
    return Result(56, SOMEWHAT, '%d of %d assessments have no instructions: %s'
                  % (len(bare), len(items), ', '.join(bare[:5])))


# ---------------------------------------------------------------- Out of reach

OUT_OF_REACH = {
    49: 'video length needs Panopto, not available from Moodle',
    50: 'audio and video quality is a judgment call',
    52: 'captions and transcripts need Panopto, not available from Moodle',
    55: 'clarity of expectations is a judgment call',
}


def rule_out_of_reach(row: int) -> Result:
    return Result(row, NA, OUT_OF_REACH[row])


# ---------------------------------------------------------------- Section 3


def load_syllabus_keywords() -> Dict:
    with open(os.path.join(_REFS, 'syllabus-keywords.json')) as fh:
        return json.load(fh)['keywords']


def rule_syllabus(text: str, status: str, row: str,
                  keywords: Optional[Dict] = None) -> Result:
    """Presence check for one required syllabus element.

    If the syllabus could not be read, this is UNKNOWN. Returning NO here would
    mean a course with a scanned PDF outranks a course that genuinely has no
    accessibility statement, which inverts the whole point of the audit.
    """
    keywords = keywords or load_syllabus_keywords()
    spec = keywords[str(row)]
    if status != 'ok':
        return Result(int(row), UNKNOWN, 'syllabus not readable: %s' % status)
    low = text.lower()
    for kw in spec['any']:
        if kw.lower() in low:
            return Result(int(row), YES, 'syllabus contains %r' % kw)
    return Result(int(row), NO,
                  'syllabus has none of: %s' % ', '.join(spec['any'][:4]))


# ---------------------------------------------------------------- Registry

PRESENCE_ROWS = ['17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27']
SYLLABUS_ROWS = ['31', '32', '33', '34', '35', '36', '37', '38',
                 '39', '40', '41', '42', '43', '44']

# (row, label, kind). kind selects how score_course calls it.
RULES = (
    [(8, 'Course Banner', 'bundle'),
     (9, 'Course Format', 'bundle'),
     (10, 'Course Structure', 'bundle'),
     (11, 'Time Frame for Modules', 'bundle'),
     (12, 'Course Links', 'links'),
     (16, 'Course name, number and section', 'bundle')]
    + [(int(r), load_presence_patterns()[r]['label'], 'presence') for r in PRESENCE_ROWS]
    + [(28, 'Welcome Forum/Announcement', 'bundle')]
    + [(int(r), load_syllabus_keywords()[r]['label'], 'syllabus') for r in SYLLABUS_ROWS]
    + [(49, 'Length of asynchronous video lectures', 'na'),
       (50, 'Audio/video quality', 'na'),
       (52, 'Captions and transcripts', 'na'),
       (53, 'Lecture slide PDFs/PowerPoints included', 'bundle'),
       (55, 'Expectations and instructions are clear', 'na'),
       (56, 'Instructions and/or rubrics for assessments', 'bundle')]
)

_BUNDLE_RULES = {
    8: rule_course_banner,
    9: rule_course_format,
    10: rule_course_structure,
    11: rule_time_frame,
    16: rule_course_name_section,
    28: rule_welcome_forum,
    53: rule_slides_present,
    56: rule_assessment_instructions,
}


def score_course(bundle: Dict, syllabus_text: str, syllabus_status: str,
                 link_results: Dict[str, str]) -> List[Result]:
    """Run all 38 rows against one course and return results in row order."""
    patterns = load_presence_patterns()
    keywords = load_syllabus_keywords()
    out = []  # type: List[Result]
    for row, _label, kind in RULES:
        if kind == 'bundle':
            out.append(_BUNDLE_RULES[row](bundle))
        elif kind == 'links':
            out.append(rule_course_links(bundle, link_results))
        elif kind == 'presence':
            out.append(rule_presence(bundle, str(row), patterns))
        elif kind == 'syllabus':
            out.append(rule_syllabus(syllabus_text, syllabus_status, str(row), keywords))
        elif kind == 'na':
            out.append(rule_out_of_reach(row))
    return sorted(out, key=lambda r: r.row)
