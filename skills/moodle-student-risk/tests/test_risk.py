import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from build_dashboard import compute_flags, compute_tier, StudentSignals, CourseContext


def make_ctx(days_since_start=30, has_graded_items=True, has_completion_tracking=True, has_graded_forums=False):
    return CourseContext(
        days_since_start=days_since_start,
        has_graded_items=has_graded_items,
        has_completion_tracking=has_completion_tracking,
        has_graded_forums=has_graded_forums,
        cohort_completion_median=80.0,
    )


def test_stale_access_flag_fires_after_7_days():
    sig = StudentSignals(days_since_access=8, missing_assignments=0, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    flags = compute_flags(sig, make_ctx())
    assert "stale_access" in flags


def test_stale_access_flag_does_not_fire_at_6_days():
    sig = StudentSignals(days_since_access=6, missing_assignments=0, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    flags = compute_flags(sig, make_ctx())
    assert "stale_access" not in flags


def test_missing_work_flag_fires_with_one_overdue():
    sig = StudentSignals(days_since_access=1, missing_assignments=1, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    assert "missing_work" in compute_flags(sig, make_ctx())


def test_missing_work_flag_does_not_fire_with_zero():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    assert "missing_work" not in compute_flags(sig, make_ctx())


def test_low_grade_flag_fires_below_70():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=68.0, completion_pct=80.0, forum_posts_14d=1)
    assert "low_grade" in compute_flags(sig, make_ctx())


def test_low_grade_flag_skipped_when_no_graded_items():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=None, completion_pct=80.0, forum_posts_14d=1)
    assert "low_grade" not in compute_flags(sig, make_ctx(has_graded_items=False))


def test_low_grade_flag_does_not_fire_at_70():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=70.0, completion_pct=80.0, forum_posts_14d=1)
    assert "low_grade" not in compute_flags(sig, make_ctx())


def test_low_completion_flag_fires_below_half_of_median():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=85.0, completion_pct=30.0, forum_posts_14d=1)
    # ctx median is 80, so threshold is 40
    assert "low_engagement" in compute_flags(sig, make_ctx())


def test_low_completion_skipped_when_neither_tracking_nor_forums():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=85.0, completion_pct=None, forum_posts_14d=0)
    flags = compute_flags(sig, make_ctx(has_completion_tracking=False, has_graded_forums=False))
    assert "low_engagement" not in flags


def test_forum_silence_does_not_fire_until_per_student_counts_wired_up():
    # forum_silent path is intentionally disabled until forum_posts_14d is populated
    # with real per-student counts; otherwise every student in a course with a graded
    # forum would fire the flag (forum_posts_14d defaults to 0 in the pipeline).
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=0)
    assert "low_engagement" not in compute_flags(sig, make_ctx(has_graded_forums=True))


def test_tier_green_when_no_flags():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    assert compute_tier([], sig, make_ctx()) == "green"


def test_tier_yellow_with_one_flag():
    sig = StudentSignals(days_since_access=8, missing_assignments=0, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    assert compute_tier(["stale_access"], sig, make_ctx()) == "yellow"


def test_tier_red_with_two_flags():
    sig = StudentSignals(days_since_access=8, missing_assignments=1, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    assert compute_tier(["stale_access", "missing_work"], sig, make_ctx()) == "red"


def test_tier_red_severe_grade_alone():
    sig = StudentSignals(days_since_access=1, missing_assignments=0, grade_pct=55.0, completion_pct=80.0, forum_posts_14d=1)
    assert compute_tier(["low_grade"], sig, make_ctx()) == "red"


def test_tier_red_severe_missing_alone():
    sig = StudentSignals(days_since_access=1, missing_assignments=3, grade_pct=85.0, completion_pct=80.0, forum_posts_14d=1)
    assert compute_tier(["missing_work"], sig, make_ctx()) == "red"


def test_tier_yellow_in_early_term_with_stale_access_alone():
    # 9201 case: day 5 of term, student hasn't accessed in 5 days
    sig = StudentSignals(days_since_access=5, missing_assignments=0, grade_pct=None, completion_pct=None, forum_posts_14d=0)
    ctx = make_ctx(days_since_start=5, has_graded_items=False, has_completion_tracking=False, has_graded_forums=False)
    flags = compute_flags(sig, ctx)
    assert flags == ["stale_access"]
    assert compute_tier(flags, sig, ctx) == "yellow"


# ---------------------------------------------------------------------------
# Task 3 tests: load_token and MoodleClient
# ---------------------------------------------------------------------------

import os, tempfile
from unittest.mock import patch, MagicMock
from build_dashboard import load_token, MoodleClient


def test_load_token_reads_from_env_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("MOODLE_PROD_TOKEN=abc123\nMOODLE_PROD_URL=https://moodle-courses2527.wolfware.ncsu.edu\n")
    token, base = load_token(str(env))
    assert token == "abc123"
    assert base == "https://moodle-courses2527.wolfware.ncsu.edu"


def test_load_token_strips_quotes(tmp_path):
    env = tmp_path / ".env"
    env.write_text('MOODLE_PROD_TOKEN="abc123"\nMOODLE_PROD_URL="https://x.example"\n')
    token, base = load_token(str(env))
    assert token == "abc123"


def test_grade_report_extracts_total_and_missing(monkeypatch):
    fake_response = {
        "usergrades": [{
            "courseid": 9201,
            "userid": 554,
            "gradeitems": [
                {"itemtype": "course", "graderaw": 82.5, "grademax": 100.0, "itemname": None, "duedate": 0},
                {"itemtype": "mod", "itemmodule": "assign", "itemname": "A1", "graderaw": 90.0, "grademax": 100.0, "duedate": 1781495940},
                {"itemtype": "mod", "itemmodule": "assign", "itemname": "A2", "graderaw": None, "grademax": 100.0, "duedate": 1700000000},  # past due, no grade
            ]
        }]
    }
    client = MoodleClient(token="t", base_url="https://x")
    monkeypatch.setattr(client, "_call", lambda fn, **p: fake_response)
    result = client.get_grade_report(course_id=9201, user_id=554, now_ts=1780000000)
    assert result["grade_pct"] == 82.5
    assert result["missing_assignments"] == 1


def test_completion_pct_computed_from_statuses(monkeypatch):
    fake = {
        "statuses": [
            {"state": 1}, {"state": 1}, {"state": 0}, {"state": 1}, {"state": 0},
        ]
    }
    client = MoodleClient(token="t", base_url="https://x")
    monkeypatch.setattr(client, "_call", lambda fn, **p: fake)
    pct = client.get_completion_pct(course_id=9201, user_id=554)
    assert pct == 60.0  # 3/5


def test_count_graded_forums_counts_only_assessed_above_zero(monkeypatch):
    fake_forums = [
        {"id": 1, "name": "Announcements", "assessed": 0},
        {"id": 2, "name": "Graded Discussion 1", "assessed": 1},
        {"id": 3, "name": "Optional Chat", "assessed": 0},
        {"id": 4, "name": "Graded Discussion 2", "assessed": 2},
        {"id": 5, "name": "Forum with null assessed", "assessed": None},
    ]
    client = MoodleClient(token="t", base_url="https://x")
    monkeypatch.setattr(client, "_call", lambda fn, **p: fake_forums)
    assert client.count_graded_forums(course_id=9201) == 2
