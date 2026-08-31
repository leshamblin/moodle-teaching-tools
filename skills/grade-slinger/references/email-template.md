# Handoff Email Template

Use this template for the email to the instructor after the four deliverables are generated. Substitute `[COURSE]` and `[NAME]`. The signature comes from `~/Documents/Claude/Gradebooks/.gradebook-config.json` — use `name`, `email`, and `affiliation`.

## Template

```
Subject: [COURSE] Gradebook Setup Complete

Hello [NAME],

I've completed the gradebook setup for [COURSE]. Please find four files attached:

1. **Gradebook Configuration Report** – A summary of how your gradebook has been configured, including category weights, settings, and the letter grade scale. This document also explains the "No Surprises" settings I use to keep grade totals consistent and transparent for students throughout the semester.

2. **Sample User Report** – A preview of what students will see when they view their grades. This uses a fake student (Jane Doe) so you can see exactly how grade items, categories, and totals will appear from the student perspective.

3. **Grade Calculator** – An Excel spreadsheet I created specifically for your course, with your category weights and grade scale built in. Enter a student's scores to calculate their weighted total and letter grade, or use it to test "what-if" scenarios.

4. **Gradebook Best Practices** – A one-page guide with recommendations for maintaining transparent and accurate grade reporting throughout the semester.

Please look these over and let me know if you have any questions or would like any adjustments.

Best,
{config.name}
{config.affiliation}
{config.email}
```
