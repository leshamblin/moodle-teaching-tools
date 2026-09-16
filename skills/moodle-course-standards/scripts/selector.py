"""Resolve a term and section pattern to a list of courses."""
from __future__ import annotations

import re
from typing import Dict, List


def parse_sections(fullname: str) -> List[str]:
    """Pull section numbers out of the parenthesised part of a course name.

    Handles 'MBA 520 (631)', 'MBA 507 (631 and 632)' and 'ACC 501 (631 | 632)'.
    """
    out = []  # type: List[str]
    for group in re.findall(r'\(([^)]*)\)', fullname):
        for num in re.findall(r'\d{3}', group):
            if num not in out:
                out.append(num)
    return out


def select_courses(courses: List[Dict], term: str, section_pattern: str) -> List[Dict]:
    """Return the courses whose fullname contains term and whose section matches.

    A course qualifies if ANY of its sections matches, because a crosslisted
    shell like 'MBA 507 (631 and 632)' is one Moodle course to review.
    """
    rx = re.compile(section_pattern)
    out = []  # type: List[Dict]
    for c in courses:
        fullname = c.get('fullname', '')
        if term.lower() not in fullname.lower():
            continue
        sections = parse_sections(fullname)
        if not any(rx.match(s) for s in sections):
            continue
        out.append({
            'id': c['id'],
            'shortname': c.get('shortname', ''),
            'fullname': fullname,
            'sections': sections,
        })
    return out
