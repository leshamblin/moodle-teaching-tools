#!/bin/bash
# SessionStart hook. The audit and dashboard scripts call the Moodle REST API
# directly and cannot read the token from secure storage, so copy the
# configured URL and token into a private file in the plugin's data folder.

[ -n "$CLAUDE_PLUGIN_OPTION_MOODLE_TOKEN" ] || exit 0
[ -n "$CLAUDE_PLUGIN_DATA" ] || exit 0

mkdir -p "$CLAUDE_PLUGIN_DATA"
umask 077
{
  printf 'MOODLE_PROD_URL=%s\n' "$CLAUDE_PLUGIN_OPTION_MOODLE_URL"
  printf 'MOODLE_PROD_TOKEN=%s\n' "$CLAUDE_PLUGIN_OPTION_MOODLE_TOKEN"
} > "$CLAUDE_PLUGIN_DATA/moodle.env"
chmod 600 "$CLAUDE_PLUGIN_DATA/moodle.env"
exit 0
