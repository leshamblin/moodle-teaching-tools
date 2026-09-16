"""Moodle REST calls and the on disk raw JSON cache.

Read only. Never add a function here that writes to Moodle.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Tuple

import requests

ENV_PATH = os.path.expanduser('~/Documents/Programming/MoodleAPI/.env')


class MoodleError(RuntimeError):
    pass


def load_token(env_path: str = ENV_PATH) -> Tuple[str, str]:
    """Read MOODLE_PROD_URL and MOODLE_PROD_TOKEN out of the .env file.

    The last uncommented assignment wins, which matches shell sourcing and is
    what makes the commented out user token in that file harmless.
    """
    values = {}  # type: Dict[str, str]
    with open(env_path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'([A-Z_]+)=(.*)$', line)
            if m:
                values[m.group(1)] = m.group(2).strip()
    base = values.get('MOODLE_PROD_URL', '').rstrip('/')
    token = values.get('MOODLE_PROD_TOKEN', '')
    if not base or not token:
        raise MoodleError('MOODLE_PROD_URL or MOODLE_PROD_TOKEN missing from ' + env_path)
    return base, token


def moodle_call(base: str, token: str, wsfunction: str, **params):
    """POST one web service call and return the decoded result.

    Moodle returns HTTP 200 with an 'exception' key on failure, so the status
    code alone never tells you whether the call worked.
    """
    data = {'wstoken': token, 'wsfunction': wsfunction, 'moodlewsrestformat': 'json'}
    for k, v in params.items():
        data[k] = v
    resp = requests.post(base + '/webservice/rest/server.php', data=data, timeout=60)
    if resp.status_code != 200:
        raise MoodleError('HTTP %s from %s' % (resp.status_code, wsfunction))
    payload = resp.json()
    if isinstance(payload, dict) and 'exception' in payload:
        raise MoodleError('%s: %s' % (wsfunction, payload.get('message', 'unknown')))
    return payload


def cache_path(cache_dir: str, course_id: int) -> str:
    return os.path.join(cache_dir, '%s.json' % course_id)


def fetch_bundle(base: str, token: str, course_id: int, cache_dir: str,
                 refresh: bool = False) -> Dict:
    """Return everything the rules need for one course, cached to disk.

    Keys: course (metadata incl. format and courseimage), contents (sections
    and modules), forums (forum instances with discussion counts).
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = cache_path(cache_dir, course_id)
    if not refresh and os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)

    by_field = moodle_call(base, token, 'core_course_get_courses_by_field',
                           field='id', value=course_id)
    course = (by_field.get('courses') or [{}])[0]
    contents = moodle_call(base, token, 'core_course_get_contents', courseid=course_id)

    try:
        forums = moodle_call(base, token, 'mod_forum_get_forums_by_courses',
                             **{'courseids[0]': course_id})
    except MoodleError:
        # Not fatal. The welcome forum rule reports UNKNOWN when this is empty.
        forums = []

    bundle = {'course': course, 'contents': contents, 'forums': forums}
    with open(path, 'w') as fh:
        json.dump(bundle, fh)
    return bundle
