"""Write the three sheet audit workbook."""
from __future__ import annotations

import os
from typing import Dict, List

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

import rules

LABELS = dict((row, label) for row, label, _kind in rules.RULES)

HEADER_FILL = PatternFill('solid', fgColor='DDDDDD')
BAD_FILL = PatternFill('solid', fgColor='F8CBAD')
UNKNOWN_FILL = PatternFill('solid', fgColor='FFE699')


def summarise(course: Dict, results: List) -> Dict:
    counts = {rules.YES: 0, rules.NO: 0, rules.SOMEWHAT: 0,
              rules.NA: 0, rules.UNKNOWN: 0}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    failures = [LABELS.get(r.row, 'row %s' % r.row) for r in results if r.verdict == rules.NO]
    return {
        'course': course,
        'yes': counts[rules.YES],
        'no': counts[rules.NO],
        'somewhat': counts[rules.SOMEWHAT],
        'na': counts[rules.NA],
        'unknown': counts[rules.UNKNOWN],
        'top_failures': '; '.join(failures[:3]),
        'results': results,
    }


def _header(ws, titles):
    ws.append(titles)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
    ws.freeze_panes = 'A2'


def write_workbook(rows: List[Dict], out_path: str) -> str:
    """rows: [{'course': {...}, 'results': [Result, ...]}, ...]"""
    summaries = [summarise(r['course'], r['results']) for r in rows]
    # Ranking sorts on confirmed failures only. Unknown is shown but never
    # counted, so a course is never ranked worst for our inability to check it.
    summaries.sort(key=lambda s: (-s['no'], -s['somewhat'], s['course'].get('shortname', '')))

    wb = openpyxl.Workbook()

    ws = wb.active
    ws.title = 'Ranking'
    _header(ws, ['Course', 'Sections', 'Instructor', 'Failed', 'Partial',
                 'Passed', 'Unknown', 'N/A', 'Worst three'])
    for s in summaries:
        c = s['course']
        ws.append([c.get('shortname', ''), ', '.join(c.get('sections', [])),
                   c.get('instructor', ''), s['no'], s['somewhat'], s['yes'],
                   s['unknown'], s['na'], s['top_failures']])
    for col, width in zip('ABCDEFGHI', [30, 12, 20, 8, 8, 8, 10, 8, 60]):
        ws.column_dimensions[col].width = width

    ws = wb.create_sheet('Detail')
    _header(ws, ['Course', 'Row', 'Item', 'Verdict'])
    for s in summaries:
        for r in s['results']:
            ws.append([s['course'].get('shortname', ''), r.row,
                       LABELS.get(r.row, ''), r.verdict])
            if r.verdict == rules.NO:
                ws.cell(ws.max_row, 4).fill = BAD_FILL
            elif r.verdict == rules.UNKNOWN:
                ws.cell(ws.max_row, 4).fill = UNKNOWN_FILL
    for col, width in zip('ABCD', [30, 6, 45, 12]):
        ws.column_dimensions[col].width = width

    ws = wb.create_sheet('Evidence')
    _header(ws, ['Course', 'Row', 'Item', 'Verdict', 'Evidence'])
    for s in summaries:
        for r in s['results']:
            if r.verdict in (rules.NO, rules.UNKNOWN, rules.SOMEWHAT):
                ws.append([s['course'].get('shortname', ''), r.row,
                           LABELS.get(r.row, ''), r.verdict, r.evidence])
    for col, width in zip('ABCDE', [30, 6, 45, 12, 90]):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2, min_col=5, max_col=5):
        row[0].alignment = Alignment(wrap_text=True, vertical='top')

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    wb.save(out_path)
    return out_path
