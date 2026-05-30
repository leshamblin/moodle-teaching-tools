# Setting up the Moodle MCP for Claude Desktop

A step-by-step guide for NCSU faculty and staff. About 15 minutes if it's your first time; less if you've done it before.

> **What this gets you:** When you finish, you can ask Claude Desktop things like *"List my Moodle courses"* or *"What assignments are due this week?"* and Claude will read your NCSU Moodle directly and answer. This is also the prerequisite for the `moodle-student-risk` and `moodle-link-checkup` skills shipped in this plugin.

---

## ★ Faster path — let Claude Code do the setup for you

If you've already installed this plugin (`/plugin install github:leshamblin/moodle-teaching-tools` in Claude Code), just run:

```
/setup-moodle-mcp
```

Claude will detect your OS and run every command for you. You'll only need:
- Your Moodle Web Services token (see [Step 1](#step-1-generate-your-moodle-web-services-token) below for where to find it)
- Your NCSU Moodle base URL (typically `https://moodle-courses2527.wolfware.ncsu.edu`)

After it finishes, fully quit and reopen Claude Desktop. Done.

If you don't yet have this plugin installed, you can paste either of these prompts directly into Claude Code instead — same outcome:

### Mac prompt

```
Set up the Moodle MCP server on my Mac so Claude Desktop can connect
to NCSU Moodle. Do everything from your side — I don't want to run
terminal commands myself.

Repo:           https://github.com/leshamblin/MoodleMCP
Where to put:   ~/Documents/Programming/MoodleMCP

Run these steps in order. Confirm each one before moving on. If
anything fails, stop and tell me what went wrong.

1. Verify Homebrew is installed (`brew --version`). If not, install
   it from brew.sh using the official one-liner.

2. Verify git is installed (`git --version`). If not, run
   `xcode-select --install` and WAIT for the system dialog to finish
   (can take several minutes — don't proceed until it completes).

3. Verify uv is installed. If not, run: `brew install uv`.

4. Make sure ~/Documents/Programming exists
   (`mkdir -p ~/Documents/Programming`). Then clone the repo:
     cd ~/Documents/Programming
     git clone https://github.com/leshamblin/MoodleMCP.git
   If the folder already exists and is a checkout of the same repo,
   `git pull` instead.

5. Inside ~/Documents/Programming/MoodleMCP, run `uv sync`.

6. Copy `.env.example` to `.env`. Then ask me for my Moodle base URL
   and my Moodle Web Services token. Write them into `.env`:
     MOODLE_DEV_URL=<url I give you>
     MOODLE_DEV_TOKEN=<token I give you>
   Leave the other lines alone.

7. Update ~/Library/Application Support/Claude/claude_desktop_config.json:
   - If missing, create with valid JSON containing an mcpServers
     object and a single "moodle" entry.
   - If it exists, READ first, PRESERVE every existing key, and ADD
     a "moodle" entry under mcpServers. Do not overwrite or remove
     any existing server.
   - Use the ABSOLUTE path (no `~`). Get it with `pwd` from inside
     the folder.

   The entry to add:
     "moodle": {
       "command": "uv",
       "args": ["--directory", "<absolute path>", "run",
                "python", "-m", "moodle_mcp.main"]
     }

   Show me the final JSON before writing it.

8. When the file is saved, tell me to fully quit Claude Desktop
   (Cmd+Q) and reopen it. That's the only step I'll do myself.

Rules:
- Do not push or commit anything to GitHub.
- Do not modify any other files in ~/Documents/Programming.
- If a step fails, stop and explain — do not guess.
```

### Windows prompt

```
Set up the Moodle MCP server on my Windows PC so Claude Desktop can
connect to NCSU Moodle. Do everything from your side — I don't want
to run PowerShell commands myself.

Repo:           https://github.com/leshamblin/MoodleMCP
Where to put:   %USERPROFILE%\Documents\Programming\MoodleMCP

Run these steps in order. Confirm each one before moving on. If
anything fails, stop and tell me what went wrong.

1. Verify git is installed (`git --version`). If not, run
   `winget install Git.Git` from an admin PowerShell, or install
   Git for Windows from gitforwindows.org.

2. Verify uv is installed. If not, install with PowerShell:
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

3. Make sure the Documents\Programming folder exists. Create it if
   it doesn't:
     mkdir $env:USERPROFILE\Documents\Programming -Force
   Then clone the repo:
     cd $env:USERPROFILE\Documents\Programming
     git clone https://github.com/leshamblin/MoodleMCP.git
   If the folder already exists and is a checkout of the same repo,
   `git pull` instead.

4. Inside the cloned folder, run `uv sync`.

5. Copy `.env.example` to `.env`. Then ask me for my Moodle base URL
   and my Moodle Web Services token. Write them into `.env`:
     MOODLE_DEV_URL=<url I give you>
     MOODLE_DEV_TOKEN=<token I give you>
   Leave the other lines alone.

6. Update %APPDATA%\Claude\claude_desktop_config.json:
   - If missing, create with valid JSON containing an mcpServers
     object and a single "moodle" entry.
   - If it exists, READ first, PRESERVE every existing key, and ADD
     a "moodle" entry under mcpServers. Do not overwrite or remove
     any existing server.
   - Use the ABSOLUTE path. Get it with `Get-Location` from inside
     the folder. Remember to escape backslashes (\\) in JSON.

   The entry to add:
     "moodle": {
       "command": "uv",
       "args": ["--directory", "<absolute path>", "run",
                "python", "-m", "moodle_mcp.main"]
     }

   Show me the final JSON before writing it.

7. When the file is saved, tell me to fully quit Claude Desktop
   (right-click the system tray icon → Quit) and reopen it. That's
   the only step I'll do myself.

Rules:
- Do not push or commit anything to GitHub.
- Do not modify any other files in Documents\Programming.
- If a step fails, stop and explain — do not guess.
```

---

## Manual path — do each step yourself

Skip this section if the faster path worked.

**Before you start:**
- Claude Desktop installed and signed into your Pro account at least once.
- You can log into NCSU Moodle in a browser as yourself.
- Terminal access.
- About 15 minutes uninterrupted the first time.

### Step 1: Generate your Moodle Web Services token

This token is what lets the Moodle MCP server talk to Moodle as you. Treat it like a password.

1. Log into NCSU Moodle in your browser.
2. Click your name (top-right) and choose **Preferences**.
3. Under *User account*, click **Security keys**.
4. Copy the token shown next to *Moodle mobile web service*. If there isn't one, create it.
5. Paste it into a temporary note. You'll use it in Step 5.

> ⚠ **Treat this like a password.** Anyone with this token can read (and potentially modify) anything in Moodle you can. Don't paste it into a chat, an email, or a public document.

### Step 2: Install uv

The Moodle MCP server is written in Python and uses uv to install its dependencies. Once per computer.

**macOS** (Terminal):
```bash
# Option A — Homebrew
brew install uv

# Option B — direct
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows** (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify with `uv --version`. If you get "command not found," close the terminal and reopen it before trying again.

### Step 3: Download the Moodle MCP server

**Option A — git** (recommended, easier to update later):

macOS:
```bash
mkdir -p ~/Documents/Programming
cd ~/Documents/Programming
git clone https://github.com/leshamblin/MoodleMCP.git
```

Windows:
```powershell
mkdir $env:USERPROFILE\Documents\Programming -Force
cd $env:USERPROFILE\Documents\Programming
git clone https://github.com/leshamblin/MoodleMCP.git
```

Either way, you end up with a folder named `MoodleMCP` inside `Documents/Programming`.

**Option B — ZIP**: Visit github.com/leshamblin/MoodleMCP, click the green **Code** button, choose **Download ZIP**, and unzip it anywhere you'll remember.

> 📝 **Write down where you put it.** You'll need the full path in Step 6.

### Step 4: Install dependencies

From your terminal, `cd` into the folder you just downloaded and run `uv sync`. This downloads everything the server needs.

macOS:
```bash
cd ~/Documents/Programming/MoodleMCP
uv sync
```

Windows:
```powershell
cd $env:USERPROFILE\Documents\Programming\MoodleMCP
uv sync
```

You'll see progress lines, then a summary like *"Installed 23 packages in 4.2s."* That's it.

### Step 5: Create your `.env` file

The repo ships with an example. Copy it, then edit the copy to add your real values.

```bash
# still inside the MoodleMCP folder
cp .env.example .env
```

Open `.env` in any text editor. The two values that matter:

```
MOODLE_DEV_URL=https://moodle-courses2527.wolfware.ncsu.edu
MOODLE_DEV_TOKEN=paste_your_token_from_step_1_here
```

Replace the placeholder with your actual NCSU Moodle URL and the token from Step 1. No quotes, no extra spaces. Save the file.

> 💡 **Pick the right URL — watch out for the term suffix.** Use the base URL — what you actually see at the top of your browser when you're logged into Moodle. NCSU's Moodle URL includes a term-specific subdomain (the number changes each semester). Copy whatever your browser shows you.

### Step 6: Tell Claude Desktop about the server

This is the step most people get stuck on. Claude doesn't auto-detect the server — you have to register it in Claude's config file.

> **Why am I editing a second file?** The `.env` lives inside the MoodleMCP folder and tells the server what URL and token to use. The `claude_desktop_config.json` lives in Claude Desktop's settings folder and tells Claude Desktop how to launch the server when the app starts. Don't put your token in both places — keep it in `.env` only.

**Find Claude's config file:**

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

If the file doesn't exist, create it. If it exists with content, you'll be **adding** the moodle entry to the `mcpServers` object, not replacing the whole file.

Paste this in, fixing the path on line 7:

```json
{
  "mcpServers": {
    "moodle": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR-USERNAME/Documents/Programming/MoodleMCP",
        "run",
        "python",
        "-m",
        "moodle_mcp.main"
      ]
    }
  }
}
```

> ⚠ **This path is the single most common source of failure.** It must be the absolute path to the folder from Step 3 — not relative, not `~/`. Claude's MCP loader does not expand `~`. On Mac, run `pwd` while inside that folder and paste exactly what comes out. On Windows, copy the path from File Explorer's address bar and replace `\` with `\\` (JSON escapes backslashes).

> 🔄 **Already have other MCPs?** If your `claude_desktop_config.json` already lists other servers under `mcpServers`, just add a comma after the previous entry and paste the `"moodle": { … }` block beside them. Valid JSON, one `mcpServers` object, multiple keys inside it.

Save the file.

### Step 7: Fully quit Claude Desktop and reopen it

Claude only reads its MCP config at startup. Closing the window is not enough.

- macOS: Cmd+Q with Claude focused, or right-click dock icon → Quit. Then reopen.
- Windows: Right-click the Claude tray icon (bottom-right) → Quit. Then relaunch.

### Step 8: Confirm it's working

Open a new chat in Claude Desktop. Look for the tool indicator (small icon near the input box) — clicking it should show `moodle` with a count of available tools.

Then try:

> Run moodle_test_connection, then list all of my Moodle courses.

If Claude returns site info and your actual course list, you're done.

> The first time you call a Moodle tool, Claude will ask permission — that's the app being careful. Approve, and it'll remember for the rest of the session.

---

## Troubleshooting

**Claude doesn't see the "moodle" tools after restart.** Three usual causes:
1. The path in `claude_desktop_config.json` is wrong. Open a terminal, `cd` into the folder, run `pwd`, compare character-for-character.
2. JSON is malformed. A missing comma or unescaped backslash makes Claude silently ignore the whole file. Paste your config into jsonlint.com to check.
3. Claude wasn't fully quit. Use Cmd+Q (Mac) or quit from the tray (Windows).

**"Invalid token" or "permission denied."** Token wrong or expired. Generate a fresh one (Step 1), paste into `.env`, restart Claude. Also check for stray spaces or quotes around the token in `.env`.

**"Connection refused" / server can't reach Moodle.** Confirm the URL in `.env` works in your browser. Use the base URL, not a course URL or login page. If you're on VPN or a campus network with restrictions, make sure your machine can actually reach Moodle. URL must include `https://` and not end with a slash.

**"Module not found" / "no module named moodle_mcp."** Step 4 (`uv sync`) didn't complete cleanly, or you ran it from the wrong folder. `cd` to MoodleMCP and run `uv sync` again.

**Claude says it can't write to Moodle.** By design. Writes are blocked unless you whitelist the course in `.env`. Open `.env`, find `MOODLE_DEV_COURSE_WHITELIST`, add the course IDs comma-separated, save, restart Claude.

**Undoing everything.** Delete the `"moodle": { … }` block from `claude_desktop_config.json` (or delete the file if that was your only MCP), restart Claude, delete the MoodleMCP folder, revoke the token in Moodle's Security keys page.

---

## Quick reference

Once you've done this once, the workflow for future tweaks is short:

- **Changed your Moodle token?** Edit `.env`, save, restart Claude.
- **Want to whitelist another course for writes?** Edit `MOODLE_DEV_COURSE_WHITELIST` in `.env`, save, restart Claude.
- **Server updated on GitHub?** `cd` into the folder, `git pull && uv sync`, restart Claude.
- **Moving to a new computer?** Repeat Steps 2–7. The token stays the same.
