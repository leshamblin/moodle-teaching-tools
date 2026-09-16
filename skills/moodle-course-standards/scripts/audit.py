"""CLI for the MBA online course standards audit.

Read only. Run:
    python3 audit.py --term "Spring 2026" --sections '^6\\d\\d$' --out ~/Desktop/audit.xlsx
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import extract
import fetch
import linkcheck
import report
import rules
import selector

DEFAULT_CACHE = os.path.expanduser('~/Documents/Programming/Demo/course-standards-cache')


def collect_links(bundle: Dict) -> List[str]:
    """Every external URL in the course, deduplicated."""
    urls = []
    for sec in bundle.get('contents', []):
        for mod in sec.get('modules', []):
            if mod.get('modname') != 'url':
                continue
            for c in mod.get('contents') or []:
                u = c.get('fileurl')
                if u and u not in urls:
                    urls.append(u)
            if not (mod.get('contents') or []) and mod.get('url'):
                if mod['url'] not in urls:
                    urls.append(mod['url'])
    return urls


def check_all_links(urls: List[str], auth_domains: List[str], workers: int = 8) -> Dict[str, str]:
    if not urls:
        return {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        codes = list(ex.map(linkcheck.check_external, urls))
    return dict((u, linkcheck.link_verdict(u, code, auth_domains))
                for u, code in zip(urls, codes))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Audit online courses against the review checklist')
    ap.add_argument('--term', default='Spring 2026')
    ap.add_argument('--sections', default=r'^6\d\d$', help='regex matched against section numbers')
    ap.add_argument('--search', default='MBA', help='course search string')
    ap.add_argument('--course-ids', default='', help='comma separated ids, overrides term and sections')
    ap.add_argument('--cache', default=DEFAULT_CACHE)
    ap.add_argument('--refresh', action='store_true', help='ignore the cache and refetch')
    ap.add_argument('--skip-links', action='store_true', help='skip HTTP link checking')
    ap.add_argument('--forms', action='store_true', help='also write a filled checklist per course')
    ap.add_argument('--out', default=os.path.expanduser('~/Desktop/MBA-standards.xlsx'))
    args = ap.parse_args(argv)

    base, token = fetch.load_token()
    os.makedirs(args.cache, exist_ok=True)
    auth_domains = linkcheck.load_auth_domains()

    if args.course_ids:
        ids = [int(x) for x in args.course_ids.split(',') if x.strip()]
        courses = [{'id': i, 'shortname': str(i), 'fullname': str(i), 'sections': []} for i in ids]
    else:
        found = fetch.moodle_call(base, token, 'core_course_search_courses',
                                  criterianame='search', criteriavalue=args.search,
                                  page=0, perpage=500)
        courses = selector.select_courses(found.get('courses', []), args.term, args.sections)

    print('%d courses selected' % len(courses))
    rows = []
    for i, course in enumerate(courses, 1):
        print('  [%d/%d] %s' % (i, len(courses), course['shortname']))
        bundle = fetch.fetch_bundle(base, token, course['id'], args.cache, args.refresh)
        meta = bundle.get('course', {})
        if course.get('shortname') == str(course['id']):
            course['shortname'] = meta.get('shortname') or course['shortname']
            course['fullname'] = meta.get('fullname') or course['fullname']
            course['sections'] = selector.parse_sections(course['fullname'])
        course.setdefault('instructor', ', '.join(
            c.get('fullname', '') for c in (meta.get('contacts') or [])))
        text, status = extract.syllabus_text(bundle, base, token, args.cache)
        links = {} if args.skip_links else check_all_links(collect_links(bundle), auth_domains)
        results = rules.score_course(bundle, text, status, links)
        rows.append({'course': course, 'results': results})

    path = report.write_workbook(rows, args.out)
    print('wrote %s' % path)

    if args.forms:
        import forms
        out_dir = os.path.join(os.path.dirname(args.out), 'forms')
        n = forms.write_all(rows, out_dir)
        print('wrote %d filled checklists to %s' % (n, out_dir))
    return 0


if __name__ == '__main__':
    sys.exit(main())
