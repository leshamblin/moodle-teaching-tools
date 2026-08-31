# Using the Moodle MCP

The Moodle MCP is **preferred but not required**. The default workflow is PDF-driven — the user exports gradebook setup PDFs from Moodle and uploads them. The MCP is for live verification.

## When to reach for the MCP

Offer these to the user at the relevant moment — don't run them silently. Each one should be framed as an opt-in.

### Confirming the PDF is current

After the user uploads the Gradebook setup PDF, ask: *"Want me to confirm this matches the current state in Moodle?"* Use `mcp__moodle__moodle_get_grade_items` to compare.

Useful when there's been a gap between exporting the PDF and processing it, or when categories have been edited since.

### Catching orphaned items

Before finalizing the Configuration Report, call `mcp__moodle__moodle_get_grade_items` and flag any items not under a known category. See `common-issues.md` for the orphan recommendation text.

### Spot-checking a real student

Instead of (or in addition to) the fake Jane Doe sample User Report, offer to pull a real student's user report. Use `mcp__moodle__moodle_get_enrolled_users` to find a sample student, then `mcp__moodle__moodle_get_user_grades` to fetch their grade view.

This is a great sanity check that the configuration is actually behaving correctly — the displayed total should make sense given the entered grades.

### Finding the course

If the user gives a course name but not an ID, use `mcp__moodle__moodle_search_courses` to disambiguate.

## What NOT to do

**Do not automate gradebook writes.** The instructor's job is to click the settings in Moodle. The skill writes reports about what was configured (past tense), but the human does the actual configuration in the UI.

Specifically, do not call:

- `mcp__moodle__moodle_update_grades`
- `mcp__moodle__moodle_save_assignment_grade`
- `mcp__moodle__moodle_update_course`
- Any other write tool

The Configuration Report's "completed action" tone is intentional — it reflects work the instructor has already done in Moodle's UI based on the skill's recommendations.

## Preflight (already in SKILL.md Step 1)

The preflight call at the start of every run is `mcp__moodle__moodle_get_current_user`. It's lightweight and reveals connection status. Handle three states gracefully — see SKILL.md.
