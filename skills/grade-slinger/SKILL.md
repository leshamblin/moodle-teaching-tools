---
name: grade-slinger
description: Grade Slinger — Moodle gradebook setup and review for NCSU Poole College instructors. Use whenever the user says "gb", "set up a gradebook", "configure gradebook", "review gradebook for [course]", "gradebook help", or asks for help with Moodle category weights, aggregation, letter grade scales, or producing a gradebook configuration report. Produces a Configuration Report PDF, a sample User Report PDF, a customized Excel grade calculator, and a Best Practices PDF.
---

# Grade Slinger

A guided workflow for configuring a Moodle gradebook to match a course syllabus, then producing four deliverables for the instructor:

1. **Gradebook Configuration Report** (PDF) — what was configured, with category weights and effective course percentages
2. **Sample User Report** (PDF) — fake student "Jane Doe" showing how students will see the gradebook
3. **Grade Calculator** (Excel) — bespoke per course, with per-item input cells and weighted formulas
4. **Gradebook Best Practices** (PDF) — same body for every course, rendered from `templates/TEMPLATE-Best-Practices.html` with your own contact details in the footer

## When this skill triggers

Trigger phrases include: "gb", "set up gradebook", "configure gradebook", "review gradebook for [course]", "gradebook help", "I need a gradebook configured", or any mention of a Moodle gradebook task. The shorthand "gb" is the user's intentional shortcut — treat it as a full request to start the gradebook workflow.

## Step 0 — Load user config (first run only)

Before doing anything else, check for `~/Documents/Claude/Gradebooks/.gradebook-config.json`. If it doesn't exist, this is the user's first time running the skill — walk them through the one-time setup:

1. Ask for their full name (e.g., "Ms. Wuf")
2. Ask for their preferred contact email (e.g., "msWuf@ncsu.edu")
3. Ask for their department/college affiliation (e.g., "Instructional Design")
4. Confirm the default course folder root is `~/Documents/Claude/Gradebooks/` or let them override
5. Create `~/Documents/Claude/Gradebooks/` if it doesn't exist
6. Write the config file as JSON with keys `name`, `email`, `affiliation`, `course_folder_root`

A sample is in `config/user-config.example.json`. After config is written, proceed with the workflow.

For all subsequent runs, just load the config silently and use those values in disclaimers, footers, and the email template.

## Step 1 — Moodle MCP preflight (gentle)

Attempt to call `mcp__moodle__moodle_get_current_user` (or another lightweight Moodle MCP tool). Three possible outcomes:

- **Tool succeeds** — Moodle is connected. Mention this once: *"Moodle connector is connected — I can pull live gradebook state if you want me to verify anything."* Then continue with the normal PDF-based workflow.
- **Tool returns auth error** — Moodle MCP is installed but not authenticated. Say: *"Your Moodle connector is installed but not connected. We can proceed with PDFs as usual, or I can help you connect it if you'd like to spot-check anything live. Want to connect it first?"* Default to proceeding if they don't want to pause.
- **Tool not found / not installed** — Tell them: *"Heads up — installing the Moodle connector would let me query live gradebook state. Want to install it now, or shall I proceed with the PDF workflow?"* If they want to install, call `mcp__plugins__suggest_plugin_install` with the Moodle plugin. Otherwise proceed.

The PDF workflow is the default. The MCP is preferred for verification but never required.

## Step 2 — Course intake (the "gb" flow)

When the user says "gb" or asks to set up a gradebook:

1. **Ask which class** — Get the course name/number (e.g., "MIE 412" or "Chris Littel MIE 412")
2. **Create a folder** — Inside `course_folder_root` (from config), create a folder named for the class. Use a clean, hyphenated naming convention like `Chris-Littel-MIE412` or `Stefanie-Robinson-MBA561`.
3. **Ask for three files** — Tell the user to place these in the new folder:
   - **Gradebook setup PDF** — From Moodle: Grades → Gradebook setup → Print/Save as PDF
   - **Course grade settings PDF** — From Moodle: Grades → Gradebook setup → Course grade settings → Print/Save as PDF
   - **Syllabus** — Course syllabus (PDF, DOCX, or whatever they have)
4. **Wait** — Stop here and let them upload before proceeding.

## Step 3 — Compare syllabus to current gradebook

Once the three files are present:

1. Read the syllabus and extract the grading structure (categories, weights or point values, letter grade scale)
2. Read the gradebook setup PDF and extract the current Moodle configuration
3. Identify discrepancies between the two
4. Check for a hidden or 0%-weight **parking category** — usually named "Not Graded", "Not for Credit", or "LTI" — holding grade items the instructor didn't want in the gradebook. See the "Not Graded Parking Category" section of `references/common-issues.md` before writing it up: the fix is usually Grade → Type → None on the activity, not a hidden category
5. Decide which aggregation type fits (see `references/aggregation-rules.md`)
6. If the Moodle MCP is connected and the user wants live verification, offer to call `mcp__moodle__moodle_get_grade_items` to confirm the gradebook state matches the PDF

## Step 4 — Produce the four deliverables

Save all four files into the course folder created in Step 2.

### A. Gradebook Configuration Report (PDF)

Copy `templates/TEMPLATE-gradebook-recommended.html` and customize it for this course. Key rules:

- **Tone**: Written as a COMPLETED ACTION REPORT (past tense — "has been configured", "was set to", "was renamed"). It reports completed work, not recommendations.
- **Title**: "Gradebook Configuration Report"
- **Required disclaimer**: Insert the disclaimer (see `references/disclaimer.md`) immediately after the header, in a yellow warning box (`#fff3cd` background). The contact email comes from the user config.
- **Sections**: Course-level settings → "No Surprises" settings → **top-level category summary** (just the categories that divide the course grade, and their sum) → Gradebook Structure table with a **"COURSE %" column** showing each item's effective course contribution → **Effective Course Weights** section showing every individual item's calculation (e.g., "17.647% × 85% = 15%") → Letter Grade Scale → Configuration Notes
- **Nested sub-categories**: if any category contains a sub-category, its weight must be stated as a share of its parent ("RBIs — 50% of Participation"), never only as a course percentage — otherwise it reads as a top-level category. See the "Nested Sub-Categories" section of `references/aggregation-rules.md` for the six things to do.
- **Parking category**: if the gradebook has a hidden or 0%-weight category holding parked items ("Not Graded" and friends), the report must state that it is hidden and weighted 0%, note that students still see it listed in their user report, and tell the instructor to verify item by item that nothing genuinely graded is sitting in it. Ready-made report text is in the "Not Graded Parking Category" section of `references/common-issues.md`
- See `references/no-surprises-settings.md` for the required course grade settings and their wording
- See `references/aggregation-rules.md` for natural vs weighted specifics
- See `references/letter-grade-scale.md` for the default Moodle scale (only change if syllabus uses non-standard cutoffs)

Save as `[COURSE]-Gradebook-Configuration-Report.html` first, then convert to PDF using `scripts/html_to_pdf.sh`. Delete the HTML when done.

### B. Sample User Report (PDF)

Copy `templates/TEMPLATE-User-report.html` and customize for the course's actual grade items. Keep "Jane Doe" / `jadoe@ncsu.edu` as the fake student. Update the course title, category names, and grade items to match this course. Two-column layout (Grade item, Grade) with indentation classes `indent-1`, `indent-2`, `indent-3` for hierarchy.

Save as `[COURSE]-User-report.html`, convert with `scripts/html_to_pdf.sh`, delete the HTML.

### C. Grade Calculator (Excel)

Generate a bespoke Excel file using `scripts/build_calculator.py`. This is **not** a copy of the template — it's a fresh file customized to this course's categories, items, weights, and letter grade scale.

**Ask the instructor which version they want** (offer both options when introducing this step):

- **Full** (`mode="full"`) — one yellow input cell per individual grade item (every assignment, quiz, forum, etc.). Best for verifying final grades item-by-item or running detailed what-if scenarios. Save as `[COURSE]-grade-calculator.xlsx`.
- **Abbreviated** (`mode="abbreviated"`) — one yellow input cell per category (the instructor enters the category total like "Exams: 650 / 700"). Best for quick spot-checks and end-of-semester verifications without entering every individual score. Save as `[COURSE]-grade-calculator-abbreviated.xlsx`.

If the instructor isn't sure, recommend Full — it's more transparent and supports more use cases. They can always ask for the abbreviated version later.

See `references/excel-calculator-spec.md` for the column structure, formulas, styling, hover comment rules, and the differences between full and abbreviated modes.

### D. Best Practices (PDF)

Copy `templates/TEMPLATE-Best-Practices.html`, substitute the placeholders (see **Template
placeholders** below — this file uses `{AFFILIATION}` and `{CONTACT_EMAIL}`), then convert with
`scripts/html_to_pdf.sh` and delete the HTML. Save as `Gradebook-Best-Practices.pdf`.

The body is the same for every course; only the footer changes, and it comes from the user config so
the document carries **your** name and contact details rather than whoever built the skill. Do not
ship a pre-rendered Best Practices PDF — a baked-in footer is how another organization's contact
address ends up on your handout.

## Template placeholders

Every `templates/*.html` file uses curly-brace placeholders. Substitute all of them before
converting to PDF, and grep the HTML for a stray `{` before you delete it.

| Placeholder | Source | Appears in |
|-------------|--------|-----------|
| `{CONTACT_EMAIL}` | `email` from `~/Documents/Claude/Gradebooks/.gradebook-config.json` | Configuration Report disclaimer, Best Practices footer |
| `{AFFILIATION}` | `affiliation` from the same config | Best Practices footer |
| `{COURSE}` | the course being configured, e.g. "MIE 412 Fall 2026" | Configuration Report footer |
| `{INSTRUCTOR}` | the instructor's name, e.g. "Dr. Chris Littel" | Configuration Report footer |

The sample course content inside the templates (MBA 561, Consumer Behavior, the grade items) is
example material, not a placeholder — rewrite it wholesale for the course at hand as described in
sections A and B.

## Step 5 — Clean up

- Delete any intermediate HTML files (only the final PDFs should remain)
- Check generated PDFs for trailing blank pages. Chrome headless sometimes adds one. See `scripts/html_to_pdf.sh` for the blank-page trim logic, or use the Python snippet in `references/excel-calculator-spec.md`.
- List the four final files in the course folder so the user can confirm

## Step 6 — Email draft

Offer to draft the handoff email to the instructor using `references/email-template.md`. Substitute `[NAME]` and `[COURSE]`, and use the contact info from the user config for the signature.

## Reference files

Load these on demand — don't read them all upfront.

- `references/disclaimer.md` — The required disclaimer wording (with #fff3cd warning box)
- `references/no-surprises-settings.md` — Required course grade settings + wording (including the "two types of hidden" note)
- `references/aggregation-rules.md` — Natural (points-based) vs Weighted Mean specifics
- `references/letter-grade-scale.md` — Default Moodle plus/minus scheme
- `references/common-issues.md` — LTI grade sync, the hidden "Not Graded" parking category, unclear category weight distribution, orphaned items
- `references/excel-calculator-spec.md` — Column structure, formulas, styling, hover comments
- `references/best-practices.md` — The 6-point list (same content as the bundled PDF)
- `references/email-template.md` — The handoff email
- `references/moodle-mcp-usage.md` — When and how to use the Moodle MCP for live verification

## Available Moodle MCP tools (when connected)

For live verification or spot-checks, useful Moodle MCP tools include:

- `mcp__moodle__moodle_get_current_user` — preflight check
- `mcp__moodle__moodle_get_course_details` — confirm course info
- `mcp__moodle__moodle_get_grade_items` — list current grade items (catches orphans)
- `mcp__moodle__moodle_get_user_grades` — spot-check a real student's grades
- `mcp__moodle__moodle_get_enrolled_users` — for picking a sample student
- `mcp__moodle__moodle_search_courses` — find a course if user only gives a name

Don't automate gradebook *writes* (e.g., `moodle_update_grades`) — that's the instructor's job. Reads only.
