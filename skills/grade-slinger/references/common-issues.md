# Common Issues and Recommendations

## LTI Tools with Manual Grade Entry (e.g., Connect, McGraw-Hill)

When an instructor manually enters a total grade for LTI assignments (like "Connect Homework Assignments Total"), recommend **disabling grade sync** from the LTI tools entirely. This prevents:

- Duplicate grade entries (LTI grades + manual total)
- Need for a hidden 0% weight category to hold the LTI items
- Confusion about which grades "count"

### Recommendation text for reports

> Since you manually enter the "[Tool] Assignments Total" grade, I recommend **disabling grade sync** from the [Tool] LTI activities. In each activity's settings, set "Grade > Type" to "None" or uncheck "Accept grades from the tool." Students can view their individual assignment grades directly in [Tool].

## Category Items with Unclear Weight Distribution

When a category has multiple items (e.g., Team Project with Plan, Update, and Final), and the syllabus doesn't specify individual weights, flag this as an **Action Needed** item in the report. Preliminary deliverables (plans, updates) typically should weigh less than final deliverables.

### Example text for reports

> **Action Needed: [Category] Weight Distribution**
>
> The [Category] category currently weights all items equally. However, preliminary items like [Plan] and [Update] are likely worth less than the [Final] deliverable. Please let me know how you'd like these distributed.

## Orphaned Grade Items

After gradebook setup, verify that all grade items are inside their proper categories. New grade items often appear at the bottom of the gradebook and uncategorized — this happens when an activity is created without selecting a category, or when an LTI tool syncs a grade item automatically. Orphaned items can affect weight calculations and student visibility.

If the Moodle MCP is connected, call `mcp__moodle__moodle_get_grade_items` and check for items that aren't under a known category — flag any to the instructor in the Configuration Report.

## Two Types of "Hidden"

See `no-surprises-settings.md` — this is the most common source of confusion. When something seems "wrong" with a student's view, check whether the activity itself is hidden at the course level (not just the gradebook item).
