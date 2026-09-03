# Common Issues and Recommendations

## LTI Tools with Manual Grade Entry (e.g., Connect, McGraw-Hill)

When an instructor manually enters a total grade for LTI assignments (like "Connect Homework Assignments Total"), recommend **disabling grade sync** from the LTI tools entirely. This prevents:

- Duplicate grade entries (LTI grades + manual total)
- Need for a hidden 0% weight category to hold the LTI items
- Confusion about which grades "count"

### Recommendation text for reports

> Since you manually enter the "[Tool] Assignments Total" grade, I recommend **disabling grade sync** from the [Tool] LTI activities. In each activity's settings, set "Grade > Type" to "None" or uncheck "Accept grades from the tool." Students can view their individual assignment grades directly in [Tool].

## The "Not Graded" Parking Category

Instructors sometimes create a 0%-weight category — named "Not Graded", "Not for Credit", "LTI", or
similar — hide it in Gradebook setup, and park unwanted grade items in it. This is almost always
about LTI/External tool links: the instructor needs the link on the course page, the tool
auto-creates a grade item, and the item clutters the gradebook.

### The real fix: don't create the grade item

In each External tool activity, set **Grade → Type → None**. Moodle then creates no grade item at
all, so it is absent from Gradebook setup *and* from the student user report, while the link stays
on the course page and students use it normally. Nothing needs to be hidden, so the "No Surprises"
settings stay exactly as configured.

The parking category is a workaround for grade items that already exist and can't be removed. When
the items don't need to exist, delete the grade item rather than hide it.

Two things to check before switching an existing activity to Type = None:

1. **Existing grades are destroyed.** Removing the grade item removes any grades stored in it. If
   there is anything in the item, export the gradebook first.
2. **The tool may push the item back.** Some LTI tools re-create their grade item on the next sync.
   Also uncheck **"Accept grades from the tool"** in the activity settings so Type = None sticks.

### If the instructor keeps the category anyway

Two things must go in the Configuration Report.

**It is still visible to students.** Because **Show hidden items = Show hidden** (a required "No
Surprises" setting), a hidden category still appears in the student user report — the name and its
items show, the grades don't. Hiding it removes it from the instructor's working view, not the
student's. Do **not** propose switching Show hidden items to Hide to suppress it; that trades a
cosmetic annoyance for the end-of-semester surprises the setting exists to prevent.

**Anything real parked inside it scores zero, silently.** A graded assignment in a 0%-weight
category contributes nothing to the course total, and because the category is collapsed and hidden
the instructor won't trip over it while working the gradebook. Verify item by item that everything
in there is genuinely meant to be ungraded.

### Report text

> **Double-check the "Not Graded" category**
>
> The "Not Graded" category is hidden in Gradebook setup and carries a weight of 0%, so nothing
> inside it counts toward the course total. Two things to know:
>
> Students still see this category listed in their grade report. Because your gradebook shows
> hidden items (so course totals never jump unexpectedly), the category name and its contents
> appear in the student view, though the grades themselves do not.
>
> Please review every item in this category and confirm each one is genuinely not graded. An
> assignment parked here earns no credit no matter what score you enter, and because the category
> is hidden it is easy to miss. If any of these are External tool links you simply don't want in
> the gradebook, the cleaner fix is to set Grade → Type → None on the activity itself, which
> removes the grade item entirely while leaving the link in place.

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
