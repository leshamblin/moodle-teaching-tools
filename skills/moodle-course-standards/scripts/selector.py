"""Resolve a term and section pattern to a list of courses."""
from __future__ import annotations

import html
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


COURSE_NUMBER_RX = re.compile(r'^[A-Z]{2,4}\s+(\d{3})')


def select_courses(courses: List[Dict], term: str, section_pattern: str,
                   number_pattern: str = '') -> List[Dict]:
    """Return the courses whose fullname contains term and whose section matches.

    A course qualifies if ANY of its sections matches, because a crosslisted
    shell like 'MBA 507 (631 and 632)' is one Moodle course to review.

    number_pattern, when given, must match the course number, so '^5' keeps
    the graduate courses. From Fall 2026 the MBA courses carry departmental
    prefixes (MKT 510, ITAO 540) instead of MBA, so a name search for "MBA"
    no longer finds them and the number is what identifies them.
    """
    rx = re.compile(section_pattern)
    num_rx = re.compile(number_pattern) if number_pattern else None
    out = []  # type: List[Dict]
    for c in courses:
        fullname = html.unescape(c.get('fullname', ''))
        if term.lower() not in fullname.lower():
            continue
        if num_rx:
            m = COURSE_NUMBER_RX.match(fullname)
            if not m or not num_rx.search(m.group(1)):
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
