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

### Nested Sub-Categories: always frame the weight against its parent

A sub-category inside a weighted category (RBIs inside Participation, a Quizzes group inside
Assignments) must be reported as a **share of its parent**, not only as a course percentage.
Reporting only the course % puts it in the same column as the top-level categories and reads as
though it were one of them.

The failure looks like this. On BUS 462, RBIs sits inside Participation (15% of the course) with a
weight of 50 out of 100, so it is 7.50% of the course. Printed next to "Attendance 15.00%" in the
same column, "RBIs 7.50%" invites the instructor to compare the two as peers, when one is a top-level
category and the other is half of a different one.

**Do all of the following whenever a sub-category exists:**

1. **Lead with a top-level summary table** before the full structure table, listing only the
   categories that divide the course grade and their sum:

   > | Category | Weight |
   > |---|---|
   > | Marketing Research Project | 45% |
   > | Assignments | 25% |
   > | Attendance | 15% |
   > | Participation | 15% |
   > | **Total** | **100%** |

2. **Annotate the nested row with its share of the parent**, and say what it is not:

   > RBIs — 50% of Participation, not a fifth category

3. **Annotate the parent's other items the same way** so the category reads as a set of shares that
   add to the parent, not a list of course percentages: "In-class Contributions — 35% of
   Participation", "Syllabus Quiz — 5% of Participation".

4. **Write the calculation in terms of the parent** in Effective Course Weights, and express the
   sub-category's own children relative to it:

   > RBIs sub-category: **50% of Participation** × 15% = 7.50%
   > Discussion Forum #1: 1/3 of RBIs = 2.50%

5. **Add a Configuration Note explaining how the parent divides**, stating plainly which figure the
   nested weight should be read against:

   > Participation is worth 15% of the course, and RBIs is a sub-category inside it, not a fifth
   > top-level category. Its weight of 50 out of Participation's 100 means RBIs takes half of
   > Participation, or 7.50% of the course. So the 7.50% figure should be read against
   > Participation's 15%, not against Attendance's 15%.

6. **If you recommend putting the weight in the category name, phrase it as the share of the
   parent.** "RBIs (50% of Participation)" is honest; "RBIs (7.5% of grade)" sitting beside
   "Participation (15% of grade)" reads as though the two add to 22.5%.

When a parent category's internal weights happen to sum to 100, say so — each weight is then also its
percentage of the category, which makes the whole structure much easier to read.
