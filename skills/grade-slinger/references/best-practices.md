# Gradebook Best Practices

These are the same six practices included in the bundled `templates/Gradebook-Best-Practices.pdf`. Refer to the PDF for the polished version delivered to instructors. This markdown copy is for reference inside the skill.

## 1. View Grades from the Student Perspective

During the semester, use Moodle's "User report" feature to view a live version of any student's grade report. This is the best way to verify grades and catch issues early — you'll see exactly what students see.

[How to View a User Report in Moodle](https://ncsu.service-now.com/delta?id=kb_article_ml&sys_id=8e510ede83e92610a35714326daad3be)

## 2. Unhide All Graded Categories

Any category that contributes to the final grade should be visible to students throughout the semester. This allows students to track their actual standing and address concerns before final grades are calculated. Hidden categories create a disconnect between what students see and what is actually calculated.

## 3. Understand the Two Types of "Hidden" in Moodle

There are two ways to hide items, and they behave differently:

- **Gradebook-level hiding** (Grades → Gradebook setup → eye icon): The "No Surprises" settings control this. Students can see the grade item listed but not the grade value.
- **Activity/Section-level hiding** (course page → Edit → Hide): When an activity or section is hidden on the course page, its grade item is **completely invisible** to students regardless of gradebook settings.

**Recommended:** To show a grade item while restricting submissions, make the activity (and its section) visible on the course page, then use **Restrict Access** settings to control when students can submit.

## 4. Check for Orphaned Items

After gradebook setup, verify that all grade items are inside their proper categories. New grade items often appear at the bottom of the gradebook and uncategorized — this happens when an activity is created without selecting a category, or when an LTI tool syncs a grade item automatically. Orphaned items can affect weight calculations and student visibility.

## 5. Audit Gradebook and Establish a Review Period

Before calculating final grades, review the gradebook setup to verify: (a) all categories are visible, (b) weights match the syllabus, (c) no grade items are unexpectedly hidden or excluded, and (d) the displayed course total matches expectations for sample students. Publish preliminary final grades in Moodle several days before submitting to SIS. This creates a window for students to review their grades and raise questions while corrections can still be made easily. A 3-5 day review period is recommended.

## 6. Communicate Grade Visibility to Students

If certain categories must be hidden temporarily (e.g., pending grade entry), communicate this to students so they understand the displayed total may not reflect their complete grade. A course announcement or gradebook note can set appropriate expectations.
