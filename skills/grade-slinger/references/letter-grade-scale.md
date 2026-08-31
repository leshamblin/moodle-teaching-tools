# Letter Grade Scale

Moodle converts points to percentages internally, so letter grades are based on percentage ranges.

## Default Moodle Grade-Letter Scheme (plus/minus style)

| Grade | Range |
|-------|-------|
| A+ | 97–100% |
| A | 93–96.99% |
| A- | 90–92.99% |
| B+ | 87–89.99% |
| B | 83–86.99% |
| B- | 80–82.99% |
| C+ | 77–79.99% |
| C | 73–76.99% |
| C- | 70–72.99% |
| D+ | 67–69.99% |
| D | 63–66.99% |
| D- | 60–62.99% |
| F | 0–59.99% |

## When to change the grade letters

**Only change grade letter settings if the syllabus uses a NON-standard scale.** If the syllabus percentages match the typical plus/minus scheme above, no changes are needed.

If changes ARE needed, configure in: **Gradebook → Setup → Course grade settings → Grade letters**

## For points-based courses

When the syllabus expresses cutoffs in points (e.g., A+ at 970+, A at 930–969 out of 1000), convert to percentages using `cutoff_points / total_points × 100` and configure the letter grade scale with those percentages. The Configuration Report should show both — the percentage cutoffs (which Moodle uses) and the points (which the syllabus and student-facing materials reference).
