# "No Surprises" Settings

These settings minimize end-of-semester surprises, keep totals consistent even if items are hidden during the term, and prevent students from seeing an "F" early in the semester just because not much has been graded yet.

## Required Settings (Grades → Course Grade Settings)

| Setting | Value | Why |
|---------|-------|-----|
| **Show hidden items** | Show hidden | Students can see the grade item listed in their gradebook, even if the grade value itself is hidden |
| **Exclude hidden items** | Do not exclude | Hidden items are still included in the Course total calculation, so totals don't suddenly change later when something is unhidden |
| **Hide totals if they contain hidden items** | Show totals including hidden items | Students always see a running Course total, even when some items are hidden |

## Required User Report Settings (Grades → Course grade settings → User report)

These two are set to **Hide** in every gradebook, without exception. Never turn them on, and never
propose turning them on.

| Setting | Value | Why |
|---------|-------|-----|
| **Show feedback** | Hide | The User report feedback column duplicates feedback students already read in the activity itself, and it surfaces instructor comments in a stripped-of-context table where they read as terse or harsh. Feedback belongs with the submission. |
| **Show ranges** | Hide | Ranges display the low-to-high spread of the class on each item. Students read their position in that spread as a grade, argue from it, and it exposes classmates' performance in a course where the grade is individual. |

If an instructor asks for either one, explain the reason above and leave both on Hide. Do not list
them as changes in the Configuration Report unless they were found switched on and you turned them
off — in that case report it as a correction.

## Standard wording for the Configuration Report

> "Students always see their course total, even when some grade items are hidden from view."

**Do NOT say** "including graded items that are hidden" — this is confusing when instructors have hidden items that are weighted zero (like LTI grade sync items). The zero weight is what excludes them from the total, not visibility.

## Important: Two Types of "Hidden" in Moodle

These gradebook settings **only apply to items hidden within the gradebook** (via Grades → Gradebook setup → clicking the eye icon on a grade item).

They **do NOT apply to activities hidden at the course level** (via the course page → Edit → Hide). When an activity is hidden on the course page, its grade item is completely invisible to students regardless of gradebook settings.

**To show a grade item while keeping the activity restricted:**

1. Make the activity **visible** on the course page (eye icon open)
2. Use **Restrict Access** settings to control when students can submit
3. Hide the **grade value** in the gradebook if needed (not the activity itself)

This way students can see the assignment exists and see the grade item in their gradebook, but can't submit until the restriction date.

## Instructor Note: Preventing the "Early-Semester F" Look

**The correct technique depends on the aggregation type — the two are opposites. Do not mix them up.**

### Weighted / percentage gradebooks (Exclude empty grades = Yes)

A blank grade is *excluded* from the total, so the running percentage reflects only graded work. Here the blank-vs-zero technique applies — include this note in the Configuration Report:

> **While an activity is still open**: Leave grades blank so the total reflects what has actually been graded so far.
>
> **After the activity closes**: Enter zeros for missing work so the total reflects the student's true standing.

### Points-based / Natural gradebooks (Exclude empty grades = No)

**Do NOT include the note above** — it does not apply and will mislead. With Exclude empty grades = No, a blank grade *already counts as 0* toward the fixed total (e.g., 1000). A blank and a zero are identical in the course total, so "leaving it blank" changes nothing. The early-F look is prevented a different way: percentages are hidden and points accrue out of the total (e.g., 150 / 1000). Include this instead:

> Because ungraded items already count as 0 and percentages are hidden, you don't need to leave items blank or hand-enter zeros to keep the total honest. Just **grade submitted work promptly** — anything ungraded shows as 0 and can temporarily understate a student who is actually on track. At the end of the term, genuinely missing work already counts as 0, so the final total reflects each student's true standing automatically.
