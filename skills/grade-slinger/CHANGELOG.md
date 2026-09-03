# Changelog

## 1.4 — 2026-09-02

- **Added** a "Not Graded Parking Category" section to `references/common-issues.md`. Instructors
  park unwanted LTI grade items in a hidden 0%-weight category so the links can stay on the course
  page without cluttering the gradebook. Two problems go unreported today. First, the category is
  not actually hidden from students: **Show hidden items = Show hidden** is a required "No
  Surprises" setting, so the category name and its items appear in the student user report even
  though the grades don't — hiding it removes it from the instructor's working view, not the
  student's, and turning that setting off to suppress it is not an acceptable trade. Second, a
  genuinely graded assignment parked in a 0%-weight category earns nothing no matter what score is
  entered, and because the category is hidden and collapsed nobody trips over it. The section
  carries the preferred fix (Grade → Type → None on the External tool activity, which creates no
  grade item at all and leaves the No Surprises settings untouched), the two caveats to check first
  (existing grades are destroyed with the item, and some LTI tools re-create it unless "Accept
  grades from the tool" is also unchecked), and ready-made report text.
- **Changed** SKILL.md Step 3: reviewing a gradebook now includes an explicit check for a hidden or
  0%-weight parking category, before the aggregation decision.
- **Changed** SKILL.md section A: the Configuration Report must report a parking category's hidden
  status and 0% weight, note that students still see it listed, and instruct the professor to
  verify item by item that nothing graded is inside.
- **Changed** the identity examples in SKILL.md Step 0 and `config/user-config.example.json` from
  the skill author's real name, live email alias and department to a generic "Ms. Wuf" /
  `msWuf@ncsu.edu` / "Instructional Design". They were only examples of what to ask during first-run
  setup, never substituted into a deliverable, but a real working address shipped to everyone who
  installed the public plugin. Same category as the v1.2 footer leak, one layer earlier.

## 1.3 — 2026-08-31

- **Added** a "Nested Sub-Categories" section to `references/aggregation-rules.md`. A sub-category
  inside a weighted category must be reported as a share of its **parent**, not only as a course
  percentage. Printing "RBIs 7.50%" in the same column as "Attendance 15.00%" reads as though the
  two were peer categories, when one is top-level and the other is half of Participation. The
  section specifies six things to do: lead with a top-level category summary table, annotate the
  nested row with its share of the parent and what it is not, annotate the parent's other items the
  same way, write the calculation in terms of the parent, add a Configuration Note explaining how
  the parent divides, and phrase any name-embedded weight as the share of the parent.
- **Changed** SKILL.md section A: the Configuration Report now leads with a top-level category
  summary table before the full structure table, and carries an explicit rule for nested
  sub-categories.

## 1.2 — 2026-08-31

- **Fixed** the Best Practices footer, which was hardcoded to
  `Poole College Instructional Design | poole_instructional_design@ncsu.edu` and baked into the
  pre-rendered `templates/Gradebook-Best-Practices.pdf`. Every instructor who received that handout
  got Poole's contact details, and any other institution installing the skill would have too. The
  footer is now `{AFFILIATION} | {CONTACT_EMAIL}`, substituted from the user config.
- **Changed** SKILL.md section D: Best Practices is now rendered from
  `templates/TEMPLATE-Best-Practices.html` per course, the same way the Configuration Report and
  User report are, instead of copying a pre-rendered PDF. Copying a baked binary is what made the
  footer unfixable. No new dependency — sections A and B already need Chrome.
- **Removed** `templates/Gradebook-Best-Practices.pdf`. It was a second source of truth for the same
  content, and the stale one.
- **Fixed** the Configuration Report footer, which held the sample course and instructor
  (`MBA 561 Spring 2026 - Dr. Stefanie Robinson`). Now `{COURSE} - {INSTRUCTOR}`. No real report had
  leaked it, but nothing prevented it.
- **Added** a **Template placeholders** table to SKILL.md documenting `{CONTACT_EMAIL}`,
  `{AFFILIATION}`, `{COURSE}` and `{INSTRUCTOR}`, their sources, and where each appears.

## 1.1 — 2026-08-31

- **Added** required User report settings to `references/no-surprises-settings.md`: **Show feedback**
  and **Show ranges** are always set to **Hide**, with the reasoning and instructions not to enable
  them on request.
- **Added** `references/no-surprises-settings.md` guidance on the two types of "hidden" in Moodle
  (gradebook eye icon vs. course-level activity hiding) and the aggregation-dependent technique for
  preventing the early-semester "F" look.
- **Added** explicit per-item `course_percent` support to `scripts/build_calculator.py`. Weighted-mean
  gradebooks give each item its own weight independent of max points; the calculator now honours an
  explicit weight when the spec supplies one and falls back to the points-proportional split for
  natural/points-based courses. Formula notes and the effective-percentage column follow suit.
- **Fixed** `SKILL.md` Step 3 citing `references/natural-aggregation.md` and
  `references/weighted-aggregation.md`, neither of which exists. Both topics live in
  `references/aggregation-rules.md`.
- **Removed** `scripts/build_calculator.py.bak-1328` and checked-in `__pycache__`.

## 1.0 — 2026-05-30

Initial release. Renamed from "AlcheMoodle GB".
