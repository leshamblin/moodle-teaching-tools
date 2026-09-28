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

INTRO_SECTION_RX = re.compile(r'start here|getting started|orientation|about|administration|welcome|general', re.I)
DEFAULT_SECTION_RX = re.compile(r'^(topic|week|section|unit)\s*\d*\s*$', re.I)
EXAM_SECTION_RX = re.compile(r'\b(exam|midterm|final|review|resources?|archive)\b', re.I)
GENERATED_IMAGE_RX = re.compile(r'/course/generated/')
IMG_RX = re.compile(r'<img\b', re.I)
WELCOME_POST_RX = re.compile(r'welcome', re.I)
INTRO_FORUM_RX = re.compile(r'introduc|icebreak|meet (each other|your classmates)', re.I)
NEGATION_BEFORE_RX = re.compile(r'\b(no|not|without|optional)\b[\w\s-]{0,12}$', re.I)
NEGATION_AFTER_RX = re.compile(r'^[\s:]*\(?\s*(optional|not required)', re.I)
DATE_RX = re.compile(
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}'
    r'|\b\d{1,2}/\d{1,2}\b'
    r'|\bweek\s+\d+\s*[,:]'
    r'|\b\d+\s*(hours?|minutes?|weeks?)\b', re.I)
ASSESSMENT_MODS = ('assign', 'quiz', 'workshop', 'forum')


def load_presence_patterns() -> Dict:
    with open(os.path.join(_REFS, 'presence-patterns.json')) as fh:
        return json.load(fh)['patterns']


def _visible(sec: Dict) -> bool:
    """Hidden sections are old material students never see, so no rule scores them."""
    return sec.get('visible', 1) != 0


def _intro_sections(bundle: Dict) -> List[Dict]:
    """Sections a student would look in for course information."""
    out = []
    for sec in bundle.get('contents', []):
        if not _visible(sec):
            continue
        if sec.get('section') == 0 or INTRO_SECTION_RX.search(sec.get('name') or ''):
            out.append(sec)
    return out


def _content_sections(bundle: Dict) -> List[Dict]:
    intro_ids = set(id(s) for s in _intro_sections(bundle))
    return [s for s in bundle.get('contents', [])
            if _visible(s) and id(s) not in intro_ids]


def _chunks(sections: List[Dict], filenames: bool = True,
            names_only: bool = False) -> List[str]:
    """Every section name and summary, module name and description, and file
    name, one string each, so a match can be judged by what it was found in.
    names_only keeps just section and module names."""
    out = []
    for sec in sections:
        out.append(sec.get('name') or '')
        if not names_only:
            out.append(sec.get('summary') or '')
        for mod in sec.get('modules', []):
            out.append(mod.get('name') or '')
            if names_only:
                continue
            out.append(mod.get('description') or '')
            if filenames:
                for c in mod.get('contents') or []:
                    out.append(c.get('filename') or '')
    return [c for c in out if c]



# ---------------------------------------------------------------- Section 1

def rule_course_banner(bundle: Dict) -> Result:
    """A banner is an image at the top of the course page.

    The course card image only shows on the dashboard, and when none is uploaded
    Moodle fills courseimage with a generated placeholder under
    /course/generated/, so that field alone passed every course.
    """
    contents = bundle.get('contents') or []
    top = contents[0] if contents else {}
    if IMG_RX.search(top.get('summary') or ''):
        return Result(8, YES, 'image at the top of the course page')
    for mod in (top.get('modules') or [])[:3]:
        if mod.get('modname') == 'label' and IMG_RX.search(mod.get('description') or ''):
            return Result(8, YES, 'banner image in %r at the top of the page' % mod.get('name'))
    course = bundle.get('course', {})
    img = course.get('courseimage') or ''
    if (img and not GENERATED_IMAGE_RX.search(img)) or course.get('overviewfiles'):
        return Result(8, SOMEWHAT, 'dashboard card image set, but no banner at the top of the page')
    return Result(8, NO, 'no image at the top of the course page')


def rule_course_format(bundle: Dict) -> Result:
    fmt = bundle.get('course', {}).get('format') or ''
    if fmt not in ('topics', 'weeks'):
        return Result(9, NO, 'course format is %r, not Topics or Weekly' % fmt)
    bad = [s.get('name') or '(unnamed)' for s in _content_sections(bundle)
           if DEFAULT_SECTION_RX.match((s.get('name') or '').strip())]
    if bad and len(bad) == len(_content_sections(bundle)):
        return Result(9, NO, 'every section left at its default name: %s' % ', '.join(bad[:5]))
    if bad:
        return Result(9, SOMEWHAT, 'sections left at default names: %s' % ', '.join(bad[:5]))
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
    if len(odd) > len(sections) * 0.75:
        return Result(10, NO, 'no dominant structure, %d of %d sections differ'
                      % (len(odd), len(sections)))
    return Result(10, SOMEWHAT, 'sections missing the common pattern: %s'
                  % ', '.join(sorted(odd)[:5]))


def rule_time_frame(bundle: Dict) -> Result:
    """Every teaching module should say when it runs.

    Exam, review and resource sections are not modules with a timeframe of their
    own, so a course is not marked down for an undated 'Final Exam' section.
    """
    sections = [s for s in _content_sections(bundle)
                if not EXAM_SECTION_RX.search(s.get('name') or '')]
    if not sections:
        return Result(11, NA, 'no content sections')
    with_dates = [s for s in sections
                  if DATE_RX.search((s.get('name') or '') + ' ' + (s.get('summary') or ''))]
    if not with_dates:
        return Result(11, NO, 'no dates or durations in any section name or summary')
    if len(with_dates) < len(sections):
        missing = [s.get('name') or '(unnamed)' for s in sections if s not in with_dates]
        verdict = SOMEWHAT if len(with_dates) * 2 >= len(sections) else NO
        return Result(11, verdict, 'sections with no timeframe: %s' % ', '.join(missing[:5]))
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
    """The course number and section should appear in the page content.

    Moodle's own course name always carries them, so checking the fullname
    passed every course. The checklist asks for them in the content, where a
    student reads them. The number is matched with any prefix, because Fall 2026
    courses such as MKT 510 still call themselves MBA 510 on the page.
    """
    course = bundle.get('course', {})
    fullname = course.get('fullname') or ''
    m = re.match(r'\s*[A-Z]{2,4}\s+(\d{3})', fullname)
    if not m:
        return Result(16, UNKNOWN, 'could not read a course number from %r' % fullname)
    number = m.group(1)
    sections = [s for s in re.findall(r'\d{3}', ' '.join(re.findall(r'\(([^)]*)\)', fullname)))]
    text = '\n'.join(_chunks(_intro_sections(bundle), filenames=False))
    if not re.search(r'\b[A-Z]{2,4}\s?-?%s\b' % number, text):
        return Result(16, NO, 'course number %s does not appear on the course page' % number)
    if sections and any(re.search(r'\b%s\b' % sec, text) for sec in sections):
        return Result(16, YES, 'course number and section appear on the course page')
    return Result(16, SOMEWHAT, 'course number %s on the page, section number not' % number)


def _syllabus_has(text: str, keywords: List[str]) -> Optional[str]:
    """First keyword present in text and not negated, or None."""
    low = text.lower()
    for kw in keywords:
        start = 0
        while True:
            i = low.find(kw.lower(), start)
            if i < 0:
                break
            before, after = low[max(0, i - 20):i], low[i + len(kw):i + len(kw) + 20]
            if not (NEGATION_BEFORE_RX.search(before) or NEGATION_AFTER_RX.search(after)):
                return kw
            start = i + 1
    return None


def rule_presence(bundle: Dict, row: str, patterns: Optional[Dict] = None,
                  syllabus_text: str = '', syllabus_status: str = '') -> Result:
    """The shared implementation behind rows 17 through 27.

    They differ only in the pattern they search for, which is why this is one
    function and a data file rather than eleven near-identical functions.

    The reviewer's standard: Yes if the element is on the course page, Somewhat
    if it is only in the syllabus, No if it is in neither. A pattern's optional
    'not_with' skips text that also matches it, so a label reading 'Syllabus
    with Schedule' is not counted as a separate schedule. 'names_only' matches
    section and module names only, so 'helpful for getting started' in a video
    description is not course navigation.
    """
    patterns = patterns or load_presence_patterns()
    spec = patterns[str(row)]
    rx = re.compile(spec['pattern'], re.I)
    skip = re.compile(spec['not_with'], re.I) if spec.get('not_with') else None
    for chunk in _chunks(_intro_sections(bundle), names_only=bool(spec.get('names_only'))):
        if skip and skip.search(chunk):
            continue
        m = rx.search(chunk)
        if m:
            return Result(int(row), YES, 'matched %r on the course page' % m.group(0))
    fallback = spec.get('syllabus') or []
    if fallback:
        if syllabus_status != 'ok':
            return Result(int(row), UNKNOWN,
                          'not on the course page, and the syllabus could not be read '
                          'to see whether it is covered there')
        kw = _syllabus_has(syllabus_text, fallback)
        if kw:
            return Result(int(row), SOMEWHAT,
                          'not on the course page, but the syllabus covers it (%r)' % kw)
    return Result(int(row), NO, 'nothing matching %r on the course page' % spec['pattern'])


def rule_welcome_forum(bundle: Dict) -> Result:
    """Yes needs both a welcome post and an introductions forum.

    Counting posts alone passed any course with a weekly announcement. The
    discussion subjects come from the bundle's 'discussions' key, forum id to
    subjects; bundles cached before it existed fall back to the post count.
    """
    forums = bundle.get('forums') or []
    if not forums:
        return Result(28, UNKNOWN, 'forum data unavailable for this course')
    visible = [f for f in forums if f.get('visible', 1) != 0]
    discussions = bundle.get('discussions')
    intro = [f for f in visible if INTRO_FORUM_RX.search(f.get('name') or '')]
    if discussions is None:
        posted = [f for f in visible if (f.get('numdiscussions') or 0) > 0]
        if posted:
            return Result(28, SOMEWHAT, '%s has %d discussions, subjects not fetched'
                          % (posted[0].get('name'), posted[0].get('numdiscussions')))
        return Result(28, NO, 'no forum has a post')
    welcome = None
    for f in visible:
        for subject in discussions.get(str(f.get('id')), []):
            if WELCOME_POST_RX.search(subject):
                welcome = '%s: %r' % (f.get('name'), subject)
                break
        if welcome:
            break
    if welcome and intro:
        return Result(28, YES, 'welcome post (%s) and an introductions forum (%s)'
                      % (welcome, intro[0].get('name')))
    if welcome:
        return Result(28, SOMEWHAT, 'welcome post (%s), no introductions forum' % welcome)
    if intro:
        return Result(28, SOMEWHAT, 'introductions forum (%s), no welcome post'
                      % intro[0].get('name'))
    return Result(28, NO, 'no welcome post and no introductions forum')


# ---------------------------------------------------------------- Multimedia

def rule_slides_present(bundle: Dict) -> Result:
    """Folders count: many courses keep each week's slides in a folder."""
    found = []
    for sec in _content_sections(bundle):
        for mod in sec.get('modules', []):
            if mod.get('modname') not in ('resource', 'folder'):
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
    kw = _syllabus_has(text, spec['any'])
    if kw:
        return Result(int(row), YES, 'syllabus contains %r' % kw)
    kw = _syllabus_has(text, spec.get('partial') or [])
    if kw:
        return Result(int(row), SOMEWHAT, 'syllabus only partly covers it (%r)' % kw)
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
            out.append(rule_presence(bundle, str(row), patterns,
                                     syllabus_text, syllabus_status))
        elif kind == 'syllabus':
            out.append(rule_syllabus(syllabus_text, syllabus_status, str(row), keywords))
        elif kind == 'na':
            out.append(rule_out_of_reach(row))
    return sorted(out, key=lambda r: r.row)
