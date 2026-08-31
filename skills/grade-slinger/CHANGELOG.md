# Changelog

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
