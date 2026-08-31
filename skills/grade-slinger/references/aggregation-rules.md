# Aggregation Rules

Decide between Natural (Sum of Grades) and Weighted Mean of Grades based on how the syllabus expresses the grading structure.

## Natural (Sum of Grades) Aggregation

Use Natural aggregation when the syllabus defines grades in **points** rather than percentages.

### Required Settings for Natural/Points-Based Gradebooks

- Rename top-level category to **"Course Points (X available)"** where X is total points
- Rename course total aggregation row to **"Current Points Earned:"**
- Set "Exclude empty grades" to **No** (ALWAYS use this setting for points-based gradebooks)
- Show grade as **Real (points)**
- Hide percentages in Course Grade Settings (Show percentage = Hide)

### Why "Exclude empty grades" = No AND Hide Percentages for Points-Based Gradebooks

These two settings work together to create a clear, anxiety-free grade experience:

1. **Exclude empty grades = No**: Students see their points accumulate toward the total (e.g., 1000 points) throughout the semester. This creates a clear sense of progression and accrual — students watch their earned points grow toward the goal rather than seeing a misleading percentage that starts artificially high and drops as more assignments are graded.

2. **Hide percentages (Show percentage = Hide in Course Grade Settings)**: When "exclude empty grades" is off, Moodle calculates percentages against the full course total from day one. A student who has earned 150 out of 1000 points after the first few assignments would see "15%" — which looks like a failing grade, even though they're perfectly on track. Hiding percentages prevents this confusion. Students see their raw points (e.g., "150 / 1000"), which reinforces the accrual model: points go up as work is completed, and the grade scale in the syllabus tells them where they stand.

### Standard explanation for Configuration Reports (include in every points-based report)

> **Points Accrual Model**
>
> This gradebook is configured so students see their points accumulate toward [X] throughout the semester. The "Exclude empty grades" setting is set to No, meaning ungraded items count as zero until a score is entered. This gives students a realistic, running view of where they stand at all times.
>
> Percentages are hidden from the student view because they would be misleading in this model — early in the semester, a student on track might see a low percentage (e.g., 15%) simply because most assignments haven't been graded yet. Instead, students see their raw points earned out of [X] and can refer to the grade scale in the syllabus to understand their standing.

## Weighted Mean of Grades Aggregation

Use Weighted Mean when the syllabus defines grades as **percentages** for each category.

### Required Settings for Weighted Gradebooks

- Categories show percentage weights that sum to 100%
- Show grade as **percentage**
- "Exclude empty grades" can be left at default (Yes) — the percentage updates as graded work is added
- Each category's weight in the table reflects its course percentage directly

### Effective Course Weights

Even with weighted aggregation, the Configuration Report should show effective course weights for individual items inside each category. For example, if a category is worth 30% of the course and contains 3 equally-weighted assignments, each assignment contributes 10% to the course total.

Show the calculation explicitly:

> Assignment 1: 33.33% × 30% = 10%

This helps the instructor see exactly how much each item is worth.
