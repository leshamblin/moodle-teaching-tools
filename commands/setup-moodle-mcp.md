---
description: Install and configure the Moodle MCP server so Claude Desktop can read NCSU Moodle. Run this once per machine, then restart Claude Desktop.
---

You are guiding a non-technical NCSU faculty member through a one-time install of the Moodle MCP server. Do every shell step yourself — they should never have to type a terminal command.

## Before you start

Confirm two things from the user (ask if not already provided in the conversation):
1. Their **Moodle base URL** — typically `https://moodle-courses2527.wolfware.ncsu.edu` but the term-number subdomain changes each semester. Tell them to copy whatever's in their browser's address bar when they're logged into Moodle.
2. Their **Moodle Web Services token** — if they don't have one, walk them through finding it in Moodle: log in → click name (top-right) → **Preferences** → **User account** → **Security keys** → copy the token next to *Moodle mobile web service*. Treat this like a password.

Do NOT echo the token in your responses or commit it anywhere.

## Detect the operating system

Run `uname -s` first. `Darwin` → macOS path. `Linux`/anything else with `MINGW`/`CYGWIN`/`MSYS` in `uname` → Windows path (PowerShell). If ambiguous, ask.

---

## macOS workflow

1. **Verify Homebrew.** Run `brew --version`. If missing, install with the official one-liner from brew.sh.
2. **Verify git.** Run `git --version`. If missing, run `xcode-select --install` and STOP — wait for the OS dialog to finish (several minutes). Don't proceed until git is available.
3. **Verify uv.** Run `uv --version`. If missing, `brew install uv`.
4. **Clone the MoodleMCP server.** Ensure `~/Documents/Programming` exists (`mkdir -p`), then:
   ```bash
   cd ~/Documents/Programming
   git clone https://github.com/leshamblin/MoodleMCP.git
   ```
   If the folder already exists and is a checkout of the same repo, `git pull` instead.
5. **Install dependencies.** `cd ~/Documents/Programming/MoodleMCP && uv sync`.
6. **Create `.env`.** Copy `.env.example` to `.env`, then write the user's values:
   ```
   MOODLE_DEV_URL=<their URL>
   MOODLE_DEV_TOKEN=<their token>
   ```
   Leave every other line at its default.
7. **Patch `claude_desktop_config.json`** at `~/Library/Application Support/Claude/claude_desktop_config.json`.
   - If the file doesn't exist: create it with valid JSON containing an `mcpServers` object and a single `"moodle"` entry.
   - If it exists: **READ it first, parse it, PRESERVE every existing key, and ADD** a `"moodle"` entry under `mcpServers`. Do not overwrite or remove any existing server.
   - Use the **absolute path** (no `~`). Get it with `pwd` from inside the MoodleMCP folder.
   - The entry to add:
     ```json
     "moodle": {
       "command": "uv",
       "args": ["--directory", "<absolute path>", "run", "python", "-m", "moodle_mcp.main"]
     }
     ```
   - Show the user the final JSON before writing it.
8. **Tell the user to quit and reopen Claude Desktop** — Cmd+Q with Claude focused (closing the window is not enough), then relaunch. That's the only step they do themselves.

---

## Windows workflow

1. **Verify git.** `git --version`. If missing, `winget install Git.Git` from an admin PowerShell, or send them to gitforwindows.org.
2. **Verify uv.** `uv --version`. If missing:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
3. **Clone the MoodleMCP server.** Ensure the Documents\Programming folder exists, then clone:
   ```powershell
   mkdir $env:USERPROFILE\Documents\Programming -Force
   cd $env:USERPROFILE\Documents\Programming
   git clone https://github.com/leshamblin/MoodleMCP.git
   ```
   If the folder already exists and is a checkout of the same repo, `git pull` instead.
4. **Install dependencies.** `cd` into the cloned folder, then `uv sync`.
5. **Create `.env`.** Copy `.env.example` to `.env`, then write:
   ```
   MOODLE_DEV_URL=<their URL>
   MOODLE_DEV_TOKEN=<their token>
   ```
   Leave every other line alone.
6. **Patch `claude_desktop_config.json`** at `%APPDATA%\Claude\claude_desktop_config.json`. Same READ-then-MERGE rule as macOS — preserve any existing servers, just add the `"moodle"` entry. Use the absolute path from `Get-Location` inside the MoodleMCP folder, escaping backslashes (`\\`) for JSON. Show the user the final JSON before writing.
7. **Tell the user to quit and reopen Claude Desktop** — right-click the system tray icon → Quit, then relaunch from the Start menu.

---

## After the user restarts Claude Desktop

Tell them to verify the install by switching to a regular Chat in Claude Desktop and asking:

> Run moodle_test_connection, then list all of my Moodle courses.

If they see their actual course list, setup is done. They can now use this plugin's skills:
- **moodle-student-risk** — "Check course 9201 for struggling students"
- **moodle-link-checkup** — "Verify resource links in course 9463"

Both skills appear in Cowork's right-hand sidebar automatically once the MCP is connected.

## Hard rules

- Never run `git push` or `git commit` to GitHub during this setup.
- Never modify files outside `~/Documents/Programming/MoodleMCP` and the single Claude config file.
- Never echo the user's Moodle token back in chat.
- If any step fails, stop and explain the failure. Don't guess your way around it.
