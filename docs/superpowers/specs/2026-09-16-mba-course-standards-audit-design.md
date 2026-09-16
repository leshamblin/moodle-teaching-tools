# MBA Online Course Standards Audit

Design spec, 2026-09-16.

## Purpose

Elizabeth has been asked to identify which of Poole's online MBA courses are the
most egregious offenders against a course review checklist. Doing that by hand
means opening 42 Moodle courses and scoring 38 items in each. This builds a
reusable tool that scores the mechanically decidable items automatically and
ranks the courses, so the human effort goes into the ones that come out worst
rather than into the survey.

The deliverable is the tool, not a one-time report. It should be rerunnable next
term and usable by other instructional designers on the team.

## Scope

**Courses:** Spring 2026 online MBA sections, 42 of them. Identified by matching
"Spring 2026" in the Moodle course fullname and a section number in the 600
series, which is NC State's distance education range. The selector accepts an
explicit list of course IDs as an override.

Spring 2026 was chosen over the current term because it is the most recent fully
taught online term. Its courses are complete, so a low score reflects a real gap
rather than a course still being built. Fall 2026 currently exposes only one
online MBA section to the API, which is unresolved and noted under Open
Questions.

**Ships as:** a fourth skill in this repo, `skills/moodle-course-standards/`,
laid out like its siblings: `SKILL.md`, `scripts/`, `templates/`, `references/`.

## Source checklist

`Course Review Checklist for Online Courses.xlsx`, supplied as a blank form.
Sheet1 holds the items, Sheet2 holds the dropdown values Yes / No / Somewhat /
N/A. Data validation covers 44 cells across B8:B28, B31:B44, B46:B47, B49:B53
and B55:B56.

### Defects in the supplied form

These are in the source file and should be fixed there rather than worked around
here. The rule table is keyed on row number, so any fix changes the mapping.

- Five validated cells have no item text beside them: rows 13, 15, 46, 47, 51.
- Row 14 is a section header that was given a dropdown by mistake.
- Three different sections are all numbered "Section 3".
- Rows 55 and 56 are assessment items sitting under the Multimedia header.
- Row 26 refers students to "ISU", and row 44 says "Since Canvas is the main
  platform for course delivery". The form was adapted from another institution's
  Canvas checklist and not fully cleaned up.

Net of the blanks and the stray header, there are **38 real items**.

## Verdicts

The form's four values are kept, plus one addition:

| Verdict | Meaning |
|---|---|
| Yes | Rule passed |
| No | Rule failed, confirmed |
| Somewhat | Partially met. Only three rules can return it: course structure (row 10) when some sections match the dominant pattern and some do not, course links (row 12) when some links resolve and some do not, and assessment instructions (row 56) when some activities carry instructions and some do not. Every other rule is Yes, No, N/A or Unknown |
| N/A | Not applicable, or out of reach for this tool |
| **Unknown** | **We could not check** |

Unknown is the important one. A scanned syllabus the parser cannot read, a file
that 404s, a link that needs a login: if those collapse into "No", the ranking
puts courses at the bottom for our failures rather than theirs. These findings go
to the people who own the courses, so that distinction has to survive to the
output.

**The ranking sorts on confirmed No only.** Unknown counts are reported in their
own column so a course with many of them can be spotted and checked by hand.

## Rules

34 of the 38 items are in scope.

### Group A, decidable from Moodle structure (20 items)

| Row | Item | Test |
|---|---|---|
| 8 | Course Banner | `courseimage` / `overviewfiles` is set |
| 9 | Course Format | format is `topics` or `weeks`, and section names are not the defaults ("Topic 1", "Week 1" with nothing after it) |
| 10 | Course Structure | compare each content section's set of module types against the others, flag the outliers |
| 11 | Time Frame for Modules | section names or summaries carry dates or durations, and activity dates are set |
| 12 | Course Links | HTTP check every external URL, reusing `moodle-link-checkup` |
| 16 | Course name, number, section | fullname or shortname contains the section number |
| 17 | Course Syllabus Document | a resource in the intro section matches the syllabus pattern |
| 18 | Course Outline/Schedule | a resource matches schedule, outline or calendar |
| 19 | Course overview/introduction | a page or label matches overview or introduction |
| 20 | Welcome video/audio/message | a module in the intro section matches welcome. Presence only, quality is out of scope |
| 21 | Instructor bio, contact, office hours | module text matches instructor, contact or office hours |
| 22 | Course Navigation | module text matches navigation, getting started or how to |
| 23 | Communication Guidelines | module text matches communication or netiquette |
| 24 | Course Technology | module text matches technology or system requirements |
| 25 | Student office hours info | module text matches office hours with a meeting link or time |
| 26 | Link to Academic Support | a URL points at a known NCSU student support domain |
| 27 | Course and tech support | module text or URL matches tech support or Moodle support |
| 28 | Welcome Forum/Announcement | a forum exists in the intro section **and** has at least one discussion posted |
| 53 | Slide PDFs/PPTs included | PDF or PPTX resources exist in the content sections |
| 56 | Instructions/rubrics for assessments | assignments and quizzes have a non-empty intro or an attached advanced grading method |

The Section 2 presence rules (17 through 27) share one implementation: match a
pattern against module names, labels and section summaries in the intro section.
They differ only in their pattern, which lives in a data file, not in code.

### Group B, syllabus contents (14 items)

Rows 31 through 44 do not ask whether a syllabus exists, they ask what is inside
it. Each is a keyword presence check against text extracted from the syllabus and
outline documents: instructor information, office information, tech support,
catalog description, learning objectives, course format, required materials,
required technology, library information, learning activities and assessments,
grading policies including late work and academic integrity, virtual class
meetings, university policies including the accessibility statement, and Moodle
support.

This is deterministic presence detection, not judgment. It answers "is there an
accessibility statement" and deliberately does not answer "is it any good".

Keyword sets live in `references/syllabus-keywords.json` so they can be tuned
without touching code. A syllabus whose text cannot be extracted yields Unknown
for all 14, never No.

### Group C, out of reach (4 items)

| Row | Item | Why |
|---|---|---|
| 49 | Video length under 15 minutes | Panopto only, not in Moodle |
| 50 | Audio/video quality | Panopto, and a judgment call |
| 52 | Captions and transcripts | Panopto only |
| 55 | Expectations and instructions are clear | Genuine judgment call |

These report N/A. Captions are the item most likely to matter to someone outside
the team, since it is an accessibility obligation rather than a preference. If it
needs covering, it becomes a separate Panopto module with its own spec, not an
extension of this one.

## Architecture

Six components. Each does one thing and can be tested alone.

**Selector.** Term string plus section pattern, or an explicit ID list, to a list
of course IDs. Output is a manifest the rest of the run works from.

**Fetcher.** Per course: `core_course_get_contents`, `core_course_get_courses_by_field`
for format, image and summary, and `mod_forum_get_forums_by_courses` for the
welcome forum rule, which carries a discussion count in one call. Raw JSON is cached to disk keyed by course ID.

**Extractor.** Downloads syllabus and outline files and pulls text from PDF, DOCX
and PPTX. Extracted text is cached alongside the JSON.

**Link checker.** Lifted from `moodle-link-checkup`, not reimplemented.

**Rule table.** 34 functions, each taking the cached bundle for one course and
returning `(row, verdict, evidence)`. Evidence is a short string naming the thing
that decided it: the URL that failed, the section with no name, the keyword that
was missing.

**Reporter.** Writes the workbook. Optional per-course form fill.

### Data flow

    selector -> manifest -> fetcher -> cache -> extractor -> cache
                                                    |
                                            rule table (34)
                                                    |
                                                reporter -> xlsx

Caching sits between fetching and scoring so rule development reruns against
local data. A full refetch is an explicit flag.

## Output

One workbook, `MBA-standards-<term>.xlsx`, three sheets.

**Ranking.** One row per course, worst first: course, section, instructor, count
of No, count of Yes, count of Unknown, count of N/A, and the three worst failures
named. This is the sheet that answers the original question.

**Detail.** One row per course per item, 1,596 rows for a 42 course run. Filter by item to
invert the question and ask which courses are missing a syllabus, or which have
broken links.

**Evidence.** The specific trigger for every No and every Unknown. A finding
without this is an accusation.

`--forms` additionally writes one filled copy of the original checklist per
course, using the supplied file as the template so the dropdowns and the
pre-written RECOMMEND text survive. Off by default, because the stated
deliverable is the tool and not the paperwork.

## Error handling

- **Never turn a failure to check into a failure to comply.** Every extraction,
  download and HTTP path returns Unknown on error, with the reason in Evidence.
- **Authenticated links.** Panopto and similar return 403 to an anonymous
  checker. Known-auth domains are treated as reachable, not broken. The domain
  list is data, not code.
- **File downloads.** Moodle pluginfile URLs need the webservice token appended.
  This fails quietly and produces empty text, which would look like a missing
  syllabus. The extractor asserts non-empty content and raises otherwise.
- **The admin token is not enrolled in these courses.** Capability-checked calls
  work, enrollment-checked ones do not. `core_course_get_contents` is confirmed
  working; any new call must be verified against a real course before it is
  relied on.
- **Rate.** 42 courses times roughly 40 links is about 1,700 HTTP requests.
  Concurrency is bounded, results are cached, and a rerun does not recheck a URL
  already seen in this run.

## Testing

Per the repo convention on analysis scripts, the tool must reproduce a known-good
result before it reports any new one.

- **Golden fixtures.** Two courses are hand-scored against the checklist by a
  person. Those scores are committed alongside the courses' cached JSON. The test
  suite asserts the tool reproduces both, and hard-exits if it does not.
- **Offline.** Cached JSON means the suite runs without touching Moodle.
- **Per-rule unit tests** on synthetic course bundles, particularly for the
  Unknown paths, which are the easiest to get wrong and the most damaging.

## Out of scope

- Any LLM judgment of quality. Deliberate, and the reason Group C stays N/A.
- Weighting. The ranking counts failures equally until a real run shows that is
  wrong. Revisit after the first 42-course pass.
- A dashboard or config-driven rule format. A 44-row checklist supplied as a
  fixed spreadsheet is not volatile enough to earn either.
- Writing anything back to Moodle. This tool is read-only.

## Open questions

1. Fall 2026 exposes only one online MBA section to the search API while Fall
   2025 exposed 39. Either the term's courses are not built yet or they are
   hidden and the API skips them. This does not block the Spring 2026 run, but it
   has to be answered before the tool is pointed at a current term.
2. Who receives the output, and are courses named or anonymized in what goes out.
   This changes nothing in the build but changes how the Ranking sheet should be
   labeled.
