# Changelog

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
