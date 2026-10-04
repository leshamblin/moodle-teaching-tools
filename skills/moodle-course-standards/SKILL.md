---
name: moodle-course-standards
description: Use when asked to audit online courses against the course review checklist, rank courses by how many standards they fail, or find which online MBA courses are worst. Triggers on "audit the online MBA courses", "which courses fail the checklist", "score these courses against the standards", "course quality review".
---

# Moodle Course Standards Audit

Scores online courses against the Poole course review checklist and ranks them by
confirmed failures, so hand review goes to the worst courses rather than to all
of them. Read only: it never writes to Moodle.

## When to Use

- "Which online MBA courses are the most egregious?"
- "Audit the Fall 2026 online sections against the checklist"
- Pre-semester or post-semester course quality review

## What It Produces

One workbook with three sheets: Ranking (one row per course, worst first),
Detail (one row per course per item), Evidence (the trigger for every failure).
With `--forms`, also a filled copy of the checklist per course in a `forms/`
folder next to the workbook.

## Prerequisites

- `MOODLE_PROD_URL` and `MOODLE_PROD_TOKEN` in `~/Documents/Programming/MoodleAPI/.env`
- python3 with openpyxl, pdfplumber, python-docx, python-pptx, requests
- `curl` on the path

## Steps

    cd skills/moodle-course-standards/scripts
    python3 audit.py --term "Fall 2026" --forms --out ~/Documents/Programming/MBA-Course-Review-Pilot/fall-2026-results/MBA-standards-Fall-2026.xlsx

About three minutes for 34 courses. `--skip-links` skips HTTP link checks,
`--refresh` ignores the cache, `--course-ids 11298,12521` runs named courses only.

## Critical Details

**How courses are selected.** The default lists Moodle category 8 (COM) and keeps
courses whose name contains the term, whose number is 500 level (`--numbers '^5'`)
and which have a 63x section (`--sections '^63\d$'`), the online MBA range. From
Fall 2026 the MBA courses carry departmental prefixes (MKT 510, ITAO 540, MIE 531),
so a name search for "MBA" finds almost nothing. The 601 sections are left out on
purpose: in Fall 2026 they are Master of Accounting courses plus MIE 501, MIE 519
and ECG 561. The Spring 2026 set of 43 is reproduced with
`--term "Spring 2026" --search MBA --sections '^6\d\d$' --numbers ''`.

**Unknown is not No.** A syllabus we cannot read, a file that 404s and a link that
wants a login all report Unknown. The ranking counts only confirmed failures.
Never change this: the output goes to the people who own the courses.

**Where the syllabus comes from.** In order: a file named like a syllabus, a
syllabus file inside a folder, a link named like one (Google Docs, Google Drive
and Dropbox links are fetched when shared publicly), then a file named like a
stand-in such as "Course Schedule", used only if its text reads like a syllabus.
PDF, DOCX, DOC (via macOS `textutil`), PPTX and plain text are read. A Google Doc
limited to NC State accounts, a OneDrive link, or no syllabus at all leaves the
syllabus rows Unknown. In Fall 2026, 28 of 34 syllabi were read.

**The reviewer's standard for Section 2 (rows 16 to 28).** On the course page is
Yes, only in the syllabus is Somewhat, in neither is No. If an item is not on the
page and the syllabus could not be read, the row is Unknown. Hidden sections are
ignored everywhere, since students never see them.

**Four items are out of reach.** Video length, audio quality and captions need
Panopto. "Expectations are clear" is a judgment call. All four report N/A.

**The rules are keyed on the checklist's row numbers.** If the source .xlsx
changes, `references/presence-patterns.json` and `references/syllabus-keywords.json`
must change with it.

**Run the golden test before trusting any output.**

    python3 -m pytest ../tests/test_golden.py -v

It compares the tool with an instructional designer's hand reviews of two Spring
2026 courses, on whether each row fails. The reviews, the course snapshots and
`disputed.json` (rows where the tool deliberately disagrees, with reasons) live in
`~/Documents/Programming/MBA-Course-Review-Pilot/golden`, never in this repo: this
repo is public, and they are named reviews of colleagues' courses with student
names in the forum data. Without that folder the test skips.
