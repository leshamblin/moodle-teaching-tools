---
name: moodle-link-checkup
description: Use when asked to audit, check, list, or verify resource links (PDFs, PowerPoints, documents, videos, external URLs) in a Moodle course. Triggers on "check links in course X", "audit course resources", "list all PDFs/documents in Moodle course", or "make sure the links work".
---

# Moodle Link Checkup

Builds a Google-Docs-friendly HTML report of every resource link in a Moodle course, with each link automatically marked ✓ working or ✗ broken.

## When to Use

- "Check the links in course 9463"
- "List all the documents/PowerPoints in this course"
- "Audit course resources"
- Any pre-semester verification of course materials
- After a course restore, to spot stale Google Doc/Slide links

## What It Produces

A single HTML file at `~/Documents/Programming/Demo/<course_id>-resources.html` with:
- Resources grouped by section/week (PDFs, PPTX, DOC, Google Docs, Panopto, YouTube, etc.)
- ✓ green check or ✗ red X next to every link
- Red-highlighted summary box listing any broken links at the top
- HTML tables (paste cleanly into Google Docs, see "Sharing" below)

## Prerequisites

- Moodle MCP tool available (`mcp__moodle__moodle_get_course_contents`)
- Course ID (find via `moodle_search_courses` if user only gives a course name)
- `curl`, `jq`, `python3` available in shell

## Steps

### 1. Get course contents

```
mcp__moodle__moodle_get_course_contents(course_id=<ID>, format='json')
```

Result will likely exceed the token limit and be saved to a file — that's expected. Note the file path it returns.

### 2. Extract resources + URL modules with `jq`

```bash
FILE="<path returned by step 1>"
jq -r '
.result | fromjson | .[] | . as $sec
| .modules[]?
| select(.modname=="resource" or .modname=="url")
| {
    section: $sec.name,
    modname: .modname,
    cmid: .id,
    name: .name,
    filename: (.contents[0]?.filename // null),
    mimetype: (.contents[0]?.mimetype // null),
    filesize: (.contents[0]?.filesize // 0),
    fileurl: (.contents[0]?.fileurl // null),
    external: (if .modname=="url" then (.contents[0]?.fileurl // .url) else null end)
  }
' "$FILE" | jq -s '.' > /tmp/moodle-resources.json
```

### 3. Run the link-check + report builder

Use `build_report.py` in this skill directory. It:
- Classifies each resource (PDF / PowerPoint / Word / Panopto / YouTube / Google Doc / etc.)
- HEAD-checks external links with curl (parallel, ~8 workers)
- Treats Moodle-hosted files as ✓ if `filesize > 0` (Moodle's metadata is the verification — we can't fetch the file from this environment without a session cookie)
- Converts Moodle file URLs from `/webservice/pluginfile.php/` → `/pluginfile.php/` and strips `forcedownload=1` so PDFs open inline in the user's logged-in browser
- Writes the HTML report and opens it in Chrome

```bash
python3 ~/.claude/skills/moodle-link-checkup/build_report.py \
  --input /tmp/moodle-resources.json \
  --course-id <ID> \
  --moodle-base https://moodle-courses2527.wolfware.ncsu.edu
```

(Adjust `--moodle-base` if the course is on a different Moodle host — confirm by looking at any `fileurl` in the JSON.)

### 4. Report findings to the user

Summarize:
- Total resources, split by in-Moodle vs external
- ✓ count and ✗ count
- Bullet list of broken links (section + name + HTTP code) — these need their attention

## Critical Details (don't skip)

### Moodle file URL gotcha

The course-contents API returns `/webservice/pluginfile.php/...?forcedownload=1` URLs. **These require an API token** — clicking them in a logged-in browser fails. Always rewrite to `/pluginfile.php/...` (no `/webservice/` prefix) and drop `forcedownload=1`. This is what makes the Moodle links actually clickable for the user.

### Pop-up display mode

If a resource is set to display mode 4 ("pop-up") in Moodle, the `/mod/resource/view.php?id=<cmid>` URL triggers a pop-up the browser blocks → user sees the page "bounce back." That's why we link directly to the file URL, not the resource view page.

### Google Docs paste compatibility

Use HTML **tables** (not styled `<li>` items) for each section. Inline-block CSS padding on `<span>` badges does **not** survive copy/paste into Google Docs — the type label collides with the link text. Tables with `<td>` background colors paste cleanly with all spacing preserved.

### External link false negatives

- Google Forms with `?ouid=...` often return 401 — flag but don't assume broken; user should manually confirm.
- Panopto/YouTube usually return 200 even for invalid IDs. HEAD checks only catch obvious 4xx/5xx/410-gone cases.

## Quick Reference

| Step | Tool/Command |
|------|--------------|
| Find course ID | `mcp__moodle__moodle_search_courses` |
| Get contents | `mcp__moodle__moodle_get_course_contents` (use `format='json'`) |
| Extract | `jq` filter on the saved file |
| Check + build | `build_report.py` |
| View | Chrome opens automatically |

## Sharing the report with the user

The HTML is built so that **Cmd+A → Cmd+C in Chrome → Cmd+V in Google Docs** preserves the tables, links, and colored type labels. Tell the user to copy/paste — *don't* drag the .html file into Docs (that uploads it as an attachment, not content).
