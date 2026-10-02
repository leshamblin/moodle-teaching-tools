#!/bin/bash
# Starts the Moodle MCP server bundled with this plugin.
# Claude Code passes the URL, token and write setting from the plugin's
# configuration dialog as MTT_* variables (see .mcp.json).

if [ -z "$MTT_MOODLE_TOKEN" ]; then
  echo "Moodle Teaching Tools: no Moodle token set. Add one in the plugin's settings, then restart Claude." >&2
  exit 1
fi

# GUI apps start servers without the login shell's PATH, so look for uv where its installers put it.
UV=""
for candidate in "$HOME/.local/bin/uv" /opt/homebrew/bin/uv /usr/local/bin/uv "$HOME/.cargo/bin/uv"; do
  if [ -x "$candidate" ]; then UV="$candidate"; break; fi
done
if [ -z "$UV" ]; then
  echo "Moodle Teaching Tools: installing uv (one time)..." >&2
  curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh >&2 || {
    echo "Moodle Teaching Tools: could not install uv. See https://docs.astral.sh/uv/" >&2
    exit 1
  }
  UV="$HOME/.local/bin/uv"
fi

# Read-only on live Moodle unless the user turned writes on.
export MOODLE_ENV=prod
export MOODLE_PROD_URL="$MTT_MOODLE_URL"
export MOODLE_PROD_TOKEN="$MTT_MOODLE_TOKEN"
export MOODLE_PROD_ALLOW_WRITES="${MTT_ALLOW_WRITES:-false}"
# The server also requires dev settings; point them at the same site.
export MOODLE_DEV_URL="$MTT_MOODLE_URL"
export MOODLE_DEV_TOKEN="$MTT_MOODLE_TOKEN"
unset MTT_MOODLE_TOKEN

# Pinned to a MoodleMCP commit so every install runs the same server.
MOODLE_MCP_SOURCE="https://github.com/leshamblin/MoodleMCP/archive/f9d4fa5add33a44f293eb4f0a37f3950772b413d.zip"
exec "$UV" tool run --from "$MOODLE_MCP_SOURCE" moodle-mcp
