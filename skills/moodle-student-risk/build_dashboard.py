#!/usr/bin/env python3
"""Moodle student risk dashboard generator. See SKILL.md for workflow."""

from dataclasses import dataclass
from typing import Optional, List

# --- Thresholds (tune here) ---
STALE_ACCESS_DAYS = 7
STALE_ACCESS_DAYS_EARLY = 4   # first 14 days of term
EARLY_TERM_DAYS = 14
LOW_GRADE_PCT = 70.0
SEVERE_GRADE_PCT = 60.0
SEVERE_MISSING_COUNT = 3
LOW_COMPLETION_RATIO = 0.5    # < 50% of cohort median
FORUM_SILENCE_DAYS = 14


@dataclass
class CourseContext:
    days_since_start: int
    has_graded_items: bool
    has_completion_tracking: bool
    has_graded_forums: bool
    cohort_completion_median: float  # 0-100


@dataclass
class StudentSignals:
    days_since_access: Optional[float]  # None if never accessed
    missing_assignments: int
    grade_pct: Optional[float]          # None if no graded items
    completion_pct: Optional[float]     # None if no completion tracking
    forum_posts_14d: int


def compute_flags(sig: StudentSignals, ctx: CourseContext) -> List[str]:
    flags = []
    early = ctx.days_since_start < EARLY_TERM_DAYS
    access_threshold = STALE_ACCESS_DAYS_EARLY if early else STALE_ACCESS_DAYS

    if ctx.days_since_start >= access_threshold:
        if sig.days_since_access is None or sig.days_since_access >= access_threshold:
            flags.append("stale_access")

    if sig.missing_assignments >= 1:
        flags.append("missing_work")

    if ctx.has_graded_items and sig.grade_pct is not None and sig.grade_pct < LOW_GRADE_PCT:
        flags.append("low_grade")

    low_completion = (
        ctx.has_completion_tracking
        and sig.completion_pct is not None
        and sig.completion_pct < ctx.cohort_completion_median * LOW_COMPLETION_RATIO
    )
    # forum_silent is intentionally disabled until per-student forum-post counts are
    # wired up; otherwise every student in a course with a graded forum fires the
    # flag because forum_posts_14d defaults to 0 in the data pipeline.
    forum_silent = False
    if low_completion or forum_silent:
        flags.append("low_engagement")

    return flags


def compute_tier(flags: List[str], sig: StudentSignals, ctx: CourseContext) -> str:
    severe = (
        (sig.grade_pct is not None and sig.grade_pct < SEVERE_GRADE_PCT)
        or sig.missing_assignments >= SEVERE_MISSING_COUNT
    )
    if severe or len(flags) >= 2:
        return "red"
    if len(flags) == 1:
        return "yellow"
    return "green"


# ---------------------------------------------------------------------------
# Task 3: Moodle REST client — token loading + HTTP client
# ---------------------------------------------------------------------------

import os
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request


def load_token(env_path: str = None):
    """Read MOODLE_PROD_TOKEN and MOODLE_PROD_URL from a .env file. Returns (token, base_url)."""
    if env_path is None:
        env_path = os.path.expanduser("~/Documents/Programming/MoodleAPI/.env")
    token = base = None
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k.strip() == "MOODLE_PROD_TOKEN":
                token = v
            elif k.strip() == "MOODLE_PROD_URL":
                base = v
    if not token:
        raise RuntimeError(f"MOODLE_PROD_TOKEN not found in {env_path}")
    if not base:
        base = "https://moodle-courses2527.wolfware.ncsu.edu"
    return token, base


class MoodleClient:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url.rstrip("/")

    def _call(self, function: str, **params):
        params.update({
            "wstoken": self.token,
            "wsfunction": function,
            "moodlewsrestformat": "json",
        })
        url = f"{self.base_url}/webservice/rest/server.php"
        req = Request(url, data=urlencode(params, doseq=True).encode())
        with urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())

    def get_grade_report(self, course_id: int, user_id: int, now_ts: int):
        data = self._call("gradereport_user_get_grade_items", courseid=course_id, userid=user_id)
        items = data.get("usergrades", [{}])[0].get("gradeitems", [])
        grade_pct = None
        missing = 0
        for it in items:
            if it.get("itemtype") == "course":
                if it.get("graderaw") is not None and it.get("grademax"):
                    grade_pct = round(100.0 * it["graderaw"] / it["grademax"], 1)
            elif it.get("itemmodule") == "assign":
                duedate = it.get("duedate") or 0
                if duedate and duedate < now_ts and it.get("graderaw") is None:
                    missing += 1
        return {"grade_pct": grade_pct, "missing_assignments": missing}

    def get_completion_pct(self, course_id: int, user_id: int):
        data = self._call("core_completion_get_activities_completion_status",
                          courseid=course_id, userid=user_id)
        statuses = data.get("statuses", [])
        if not statuses:
            return None
        done = sum(1 for s in statuses if s.get("state", 0) >= 1)
        return round(100.0 * done / len(statuses), 1)

    def count_graded_forums(self, course_id: int) -> int:
        """Count forums in the course where `assessed > 0` (i.e., posts are graded).
        Forums without grading (announcements, optional discussions) return assessed=0."""
        data = self._call("mod_forum_get_forums_by_courses", **{"courseids[0]": course_id})
        forums = data if isinstance(data, list) else data.get("forums", [])
        return sum(1 for f in forums if (f.get("assessed") or 0) > 0)


# ---------------------------------------------------------------------------
# Task 4: Parallel per-student fetch + cohort median completion
# ---------------------------------------------------------------------------

from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def fetch_all_students(client: MoodleClient, course_id: int, students: list, now_ts: int,
                       has_completion_tracking: bool, max_workers: int = 8):
    """students: list of dicts with at minimum {id, fullname, email, lastcourseaccess}.
    Returns list of dicts: per-student record ready for risk scoring."""
    def one(stu):
        uid = stu["id"]
        try:
            grade = client.get_grade_report(course_id, uid, now_ts)
            completion_pct = client.get_completion_pct(course_id, uid) if has_completion_tracking else None
            return {
                "id": uid,
                "name": stu["fullname"],
                "email": stu.get("email", ""),
                "groups": [g.get("name") for g in stu.get("groups", [])],
                "last_access_ts": stu.get("lastcourseaccess") or 0,
                "grade_pct": grade["grade_pct"],
                "missing_assignments": grade["missing_assignments"],
                "completion_pct": completion_pct,
                "forum_posts_14d": 0,  # populated by Task 5 if course has graded forums
                "data_complete": True,
                "error": None,
            }
        except Exception as e:
            return {
                "id": uid, "name": stu["fullname"], "email": stu.get("email", ""),
                "groups": [], "last_access_ts": stu.get("lastcourseaccess") or 0,
                "grade_pct": None, "missing_assignments": 0, "completion_pct": None,
                "forum_posts_14d": 0, "data_complete": False, "error": str(e),
            }

    out = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = [pool.submit(one, s) for s in students]
        for f in as_completed(futs):
            out.append(f.result())
    return out


def compute_cohort_median_completion(records: list) -> float:
    vals = sorted([r["completion_pct"] for r in records if r["completion_pct"] is not None])
    if not vals:
        return 0.0
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


# ---------------------------------------------------------------------------
# Task 5: Course-level metadata reader + assembly
# ---------------------------------------------------------------------------

import pathlib


def load_course_data(course_id: int, cache_dir: str = None):
    if cache_dir is None:
        cache_dir = f"/tmp/moodle-risk-{course_id}"
    p = pathlib.Path(cache_dir)
    files = ["course_details.json", "enrolled_users.json", "assignments.json", "course_events.json", "course_contents.json"]
    missing = [f for f in files if not (p / f).exists()]
    if missing:
        raise RuntimeError(f"Missing data files in {cache_dir}: {missing}. SKILL.md step 2 was not run.")
    out = {}
    for f in files:
        out[f.replace(".json", "")] = json.loads((p / f).read_text())
    return out


def build_course_context(raw: dict, now_ts: int) -> tuple:
    """Returns (CourseContext, course_meta_dict, student_list)."""
    details = raw["course_details"]
    contents = raw["course_contents"]
    events = raw["course_events"]

    start_ts = details.get("startdate", 0)
    days_since_start = max(0, (now_ts - start_ts) // 86400) if start_ts else 0

    # has_graded_items: any module with a grade item — proxy: any assign module exists
    has_graded_items = any(
        m.get("modname") in ("assign", "quiz")
        for sec in contents for m in sec.get("modules", [])
    )

    has_completion_tracking = any(
        m.get("completion", 0) > 0
        for sec in contents for m in sec.get("modules", [])
    )

    # has_graded_forums is set by process_course via MoodleClient.count_graded_forums,
    # because course_contents doesn't expose the forum's `assessed` setting.
    has_graded_forums = False

    students = [u for u in raw["enrolled_users"] if any(r.get("shortname") == "student" for r in u.get("roles", []))]

    ctx = CourseContext(
        days_since_start=int(days_since_start),
        has_graded_items=has_graded_items,
        has_completion_tracking=has_completion_tracking,
        has_graded_forums=has_graded_forums,
        cohort_completion_median=0.0,  # filled after fetch
    )
    meta = {
        "id": details["id"],
        "fullname": details["fullname"],
        "shortname": details["shortname"],
        "start_ts": start_ts,
        "days_since_start": int(days_since_start),
    }
    return ctx, meta, students


# ---------------------------------------------------------------------------
# Task 7: Render function + main() entry point
# ---------------------------------------------------------------------------

import datetime
import argparse


def humanize_last_access(ts: int, tz_name: str = "America/New_York") -> str:
    if not ts:
        return "never"
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = datetime.timezone.utc
    return datetime.datetime.fromtimestamp(ts, tz=tz).strftime("%a %b %-d, %Y %-I:%M %p %Z")


def render_dashboard(course_meta: dict, records: list, ctx: CourseContext, out_path: str):
    template_path = pathlib.Path(__file__).parent / "template.html"
    tpl = template_path.read_text()
    meta = {
        "id": course_meta["id"],
        "fullname": course_meta["fullname"],
        "days_since_start": course_meta["days_since_start"],
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %-I:%M %p"),
        "thresholds": {
            "stale_access": STALE_ACCESS_DAYS,
            "stale_access_early": STALE_ACCESS_DAYS_EARLY,
            "early_term": EARLY_TERM_DAYS,
            "low_grade": LOW_GRADE_PCT,
            "severe_grade": SEVERE_GRADE_PCT,
            "severe_missing": SEVERE_MISSING_COUNT,
        },
    }
    html = tpl.replace("{{DATA}}", json.dumps(records, default=str)) \
              .replace("{{META}}", json.dumps(meta, default=str))
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out_path).write_text(html)
    return out_path


def process_course(course_id: int, out_dir: str = None) -> dict:
    if out_dir is None:
        out_dir = os.path.expanduser("~/Documents/Programming/Demo")
    now_ts = int(time.time())

    raw = load_course_data(course_id)
    ctx, meta, students = build_course_context(raw, now_ts)
    if meta["start_ts"] and now_ts < meta["start_ts"]:
        raise RuntimeError(f"Course {course_id} has not started yet ({meta['fullname']}). Refusing to run.")

    token, base = load_token()
    client = MoodleClient(token, base)

    try:
        ctx.has_graded_forums = client.count_graded_forums(course_id) > 0
    except Exception:
        ctx.has_graded_forums = False

    records = fetch_all_students(client, course_id, students, now_ts, ctx.has_completion_tracking)

    ctx.cohort_completion_median = compute_cohort_median_completion(records)

    for r in records:
        sig = StudentSignals(
            days_since_access=((now_ts - r["last_access_ts"]) / 86400) if r["last_access_ts"] else None,
            missing_assignments=r["missing_assignments"],
            grade_pct=r["grade_pct"],
            completion_pct=r["completion_pct"],
            forum_posts_14d=r["forum_posts_14d"],
        )
        flags = compute_flags(sig, ctx)
        tier = compute_tier(flags, sig, ctx) if r["data_complete"] else "incomplete"
        r["flags"] = flags
        r["tier"] = tier
        r["days_since_access"] = round(sig.days_since_access, 1) if sig.days_since_access is not None else None
        r["last_access_human"] = humanize_last_access(r["last_access_ts"])

    out_path = pathlib.Path(out_dir) / f"{course_id}-risk.html"
    render_dashboard(meta, records, ctx, str(out_path))
    counts = {"red": 0, "yellow": 0, "green": 0, "incomplete": 0}
    for r in records:
        counts[r["tier"]] = counts.get(r["tier"], 0) + 1
    return {"course_id": course_id, "fullname": meta["fullname"], "out_path": str(out_path),
            "counts": counts, "students": len(records)}


def process_batch(course_ids: list, out_dir: str = None, open_in_chrome: bool = False) -> dict:
    if out_dir is None:
        date = datetime.date.today().isoformat()
        out_dir = os.path.expanduser(f"~/Documents/Programming/Demo/risk-{date}")
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    results = []
    for cid in course_ids:
        try:
            r = process_course(cid, out_dir=out_dir)
            results.append({"course_id": cid, "ok": True, **r})
        except Exception as e:
            results.append({"course_id": cid, "ok": False, "error": str(e), "fullname": f"Course {cid}", "counts": {}})
    index_path = pathlib.Path(out_dir) / "index.html"
    index_path.write_text(_render_index(results, out_dir))
    if open_in_chrome:
        os.system(f'open -a "Google Chrome" "{index_path}"')
    print(json.dumps({"index": str(index_path), "courses": results}, indent=2))
    return {"index": str(index_path), "courses": results}


def _render_index(results: list, out_dir: str) -> str:
    rows = []
    for r in results:
        if r["ok"]:
            c = r["counts"]
            rows.append(f"""
              <tr>
                <td><a href="{r['course_id']}-risk.html">{r['fullname']}</a></td>
                <td>{r.get('students', '?')}</td>
                <td class="tier-red">🔴 {c.get('red', 0)}</td>
                <td class="tier-yellow">🟡 {c.get('yellow', 0)}</td>
                <td class="tier-green">🟢 {c.get('green', 0)}</td>
              </tr>""")
        else:
            rows.append(f"""
              <tr>
                <td>{r['fullname']}</td>
                <td colspan="4" style="color:#c33">⚠ {r['error']}</td>
              </tr>""")
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Risk dashboards</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; padding: 24px; }}
  h1 {{ margin: 0 0 16px; font-size: 22px; }}
  table {{ border-collapse: collapse; }}
  th, td {{ padding: 8px 14px; border-bottom: 1px solid #eee; text-align: left; }}
  th {{ background: #f5f5f5; }}
  .tier-red {{ color: #c33; }} .tier-yellow {{ color: #c80; }} .tier-green {{ color: #393; }}
</style></head>
<body>
<h1>Student risk dashboards — {datetime.date.today().isoformat()}</h1>
<table>
<thead><tr><th>Course</th><th>Students</th><th>Red</th><th>Yellow</th><th>Green</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Generate Moodle student risk dashboard.")
    ap.add_argument("--course-id", type=int, action="append",
                    help="Course ID (repeat for batch). At least one required.")
    ap.add_argument("--out-dir", help="Output directory (default ~/Documents/Programming/Demo).")
    ap.add_argument("--open", action="store_true", help="Open the result in Chrome.")
    args = ap.parse_args()

    if not args.course_id:
        ap.error("--course-id is required (repeat for multiple courses).")

    if len(args.course_id) == 1:
        result = process_course(args.course_id[0], args.out_dir)
        print(json.dumps(result, indent=2))
        if args.open:
            out = result["out_path"]
            os.system(f'open -a "Google Chrome" "{out}"')
    else:
        # Batch mode: per-course folder + index.html (defined in Task 9)
        process_batch(args.course_id, args.out_dir, open_in_chrome=args.open)


if __name__ == "__main__":
    main()
