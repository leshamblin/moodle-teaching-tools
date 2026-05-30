---
name: moodle-student-risk
description: Use when asked to identify struggling, behind, or at-risk students in a Moodle course. Triggers on "check course X for struggling students", "who's behind in course X", "find at-risk students", "run the risk dashboard", or "show me the dashboard". Produces an interactive HTML dashboard with charts, filters, and per-student drill-down.
---

# Moodle Student Risk Dashboard

Produces a self-contained interactive HTML dashboard identifying at-risk students in a Moodle course, intended for a non-technical professor.

## When to Use

- "Check course 9201 for struggling students"
- "Who's behind in MBA 553?"
- "Find at-risk students"
- "Run the risk dashboard on all my courses"

## What It Produces

- Single course: `~/Documents/Programming/Demo/<course_id>-risk.html` (opens in Chrome)
- Batch: `~/Documents/Programming/Demo/risk-YYYY-MM-DD/{index.html, <id>-risk.html, ...}` (index opens)

Each dashboard includes:
- 🚨 callout listing red-tier students
- Donut chart (tier counts), grade histogram, grade-vs-engagement scatter
- Sortable/filterable/searchable student table with per-student drill-down

## Risk Model (read this before changing thresholds)

Four signals; each that fires adds a flag. Tier is a function of flag count.

| Signal | Threshold |
|---|---|
| Stale access | No login in 7d (4d in first 14d of term) |
| Missing work | ≥ 1 past-due assignment with no submission |
| Low grade | Course total < 70% (skipped if no graded items yet) |
| Low engagement | Completion < 50% of cohort median OR zero posts in graded forums in last 14d |

Tier: 2+ flags = 🔴, 1 = 🟡, 0 = 🟢. Severe overrides → red: grade < 60% or ≥ 3 missing.

Constants live at the top of `build_dashboard.py` — edit there, not here.

## Workflow

### 1. Resolve course

If user gave a name not a number → `mcp__moodle__moodle_search_courses(search="<name>")`.
If user said "all my courses" → `mcp__moodle__moodle_list_user_courses(user_id=<your_id>)`.

### 2. Stage course metadata into /tmp

For each course_id, make these MCP calls in parallel and save each result as JSON under `/tmp/moodle-risk-<course_id>/`:

```
mkdir -p /tmp/moodle-risk-<course_id>
```

| File to save | MCP function | Notes |
|---|---|---|
| `course_details.json` | `mcp__moodle__moodle_get_course_details(course_id, format='json')` | parse `.result` (it's a JSON string) |
| `enrolled_users.json` | `mcp__moodle__moodle_get_enrolled_users(course_id, format='json', limit=100)` | paginate with offset if >100; extract the `users` array and save just that array |
| `assignments.json` | `mcp__moodle__moodle_list_assignments(course_id, format='json')` | |
| `course_events.json` | `mcp__moodle__moodle_get_course_events(course_id, days_ahead=365, format='json')` | |
| `course_contents.json` | `mcp__moodle__moodle_get_course_contents(course_id, format='json')` | parse `.result` |

The MCP responses are wrapped — most return `{"result": "<json string>"}`. Use `jq` to unwrap:

```bash
echo "$RESPONSE" | jq -r '.result | fromjson' > /tmp/moodle-risk-<course_id>/<file>.json
```

For `enrolled_users.json`, additionally extract just the `users` array:

```bash
echo "$RESPONSE" | jq -r '.result | fromjson | .users' > /tmp/moodle-risk-<course_id>/enrolled_users.json
```

**Faster alternative — direct curl:** If MCP responses are exceeding token limits, hit the REST API directly. The token is in `~/Documents/Programming/MoodleAPI/.env` as `MOODLE_PROD_TOKEN`/`MOODLE_PROD_URL`. See the smoke-test commands in `docs/superpowers/plans/2026-05-30-moodle-student-risk.md` Task 7 Step 4 for the exact curl invocations.

### 3. Run the renderer

Single course:

```bash
python3 ~/.claude/skills/moodle-student-risk/build_dashboard.py --course-id <id> --open
```

Batch:

```bash
python3 ~/.claude/skills/moodle-student-risk/build_dashboard.py --course-id <id1> --course-id <id2> --open
```

The script:
1. Reads the staged JSON files.
2. Reads `MOODLE_PROD_TOKEN` + `MOODLE_PROD_URL` from `~/Documents/Programming/MoodleAPI/.env`.
3. Hits Moodle REST in parallel (8 workers) for per-student grade + completion data.
4. Computes risk per the model above.
5. Writes the HTML and opens Chrome (if `--open`).

### 4. Summarize for the user

Print the top-line counts and the names in the red tier. Keep it short — they're about to look at the dashboard.

## Gotchas

- **Token name:** the `.env` file is shared with the MCP server. Keys are `MOODLE_PROD_TOKEN` and `MOODLE_PROD_URL`.
- **Empty grades early in term:** the low-grade signal is auto-skipped when there are no graded items. The early-term stale-access tightening (4d threshold) is what catches at-risk students in week 1.
- **Permissions:** the token needs teacher role on each course. If `gradereport_user_get_grade_items` returns "access denied," the user isn't teaching that course.
- **Course hasn't started:** the script refuses to run and prints why.
- **Forum-silence flag disabled:** the `low_engagement` flag currently only fires on low completion-tracking ticks, not on forum silence. Per-student forum-post counts aren't wired into the pipeline yet (`forum_posts_14d` is always 0), so enabling the forum-silence path would flag every student in any course with a graded forum. The `count_graded_forums` call is still made so `ctx.has_graded_forums` is accurate; wire up per-student post counts (`mod_forum_get_discussions_paginated` per graded forum, then filter by user + timestamp) to re-enable.

## Files in This Skill

- `build_dashboard.py` — entry point, REST client, risk scoring, HTML rendering
- `template.html` — dashboard skeleton (Chart.js from CDN)
- `tests/test_risk.py` — pytest unit tests for the pure risk-scoring functions
