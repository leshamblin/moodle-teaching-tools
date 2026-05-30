# Installing Moodle Teaching Tools — Faculty Guide

A step-by-step walkthrough for installing the plugin in **Claude Desktop**. No coding required. About 15 minutes, once per computer.

> **Important — where to do this:** All the steps below happen in **Claude Code**, which is a tab inside Claude Desktop. Open Claude Desktop and click **Claude Code** in the left sidebar. The install command does **not** work in Cowork or Chat — if you see *"/plugin isn't available in this environment,"* you're in the wrong tab.

---

## Step 1 — Install the plugin

In Claude Code, type this and press Enter:

```
/plugin install github:leshamblin/moodle-teaching-tools
```

> If that gives an error, use these two lines instead (type the first, press Enter, then the second):
> ```
> /plugin marketplace add leshamblin/moodle-teaching-tools
> /plugin install moodle-teaching-tools@moodle-teaching-tools
> ```

When it finishes, you'll see the plugin listed as **enabled**.

---

## Step 2 — Get your Moodle token (you'll need it in Step 3)

This token is what lets Claude talk to Moodle *as you*. **Treat it like a password.**

1. Log into **NCSU Moodle** in your browser.
2. Click your **name** (top-right) and choose **Preferences**.
3. Under *User account*, click **Security keys**.
4. Copy the token shown next to **Moodle mobile web service**. If there isn't one, create it.
5. Paste it somewhere temporary (a sticky note or Notes app) — you'll use it in the next step.

You'll also need your **Moodle URL** — just the address at the top of your browser when you're logged into Moodle, for example:

```
https://moodle-courses2527.wolfware.ncsu.edu
```

> ⚠️ **The URL changes each semester.** NCSU's Moodle address has a term-specific number in it (the `2527` part) that updates every term. Copy whatever your browser actually shows you — don't reuse last semester's.

> 🔒 **Keep the token private.** Anyone who has it can read (and potentially change) anything in Moodle that you can. Don't paste it into a chat, an email, or a shared document.

---

## Step 3 — Run the one-time setup

Back in Claude Code, type this and press Enter:

```
/setup-moodle-mcp
```

It will ask for your **Moodle URL** and your **token** from Step 2, then set everything up automatically. You don't need to install Python, Node, or anything else — it checks for what's missing and handles it for you.

---

## Step 4 — Restart Claude Desktop

Fully **quit and reopen** Claude Desktop so the changes take effect.

---

## You're done — now use it

After restarting, switch to **Cowork** (in the Claude Desktop sidebar). The Moodle tools and both skills appear automatically. Just ask in plain language:

- *"Check course 9201 for struggling students"* → opens an at-risk-student dashboard in your browser
- *"Audit the links in course 9463"* → opens a broken-link report
- *"What's due in MBA 534 this week?"* → answered directly

---

## Troubleshooting

| Problem | Fix |
|---|---|
| *"/plugin isn't available in this environment"* | You're in Cowork or Chat. Switch to the **Claude Code** tab in Claude Desktop. |
| *"Invalid token" / "permission denied"* | The token is wrong or expired. Generate a fresh one (Step 2) and re-run `/setup-moodle-mcp`. Check for stray spaces. |
| *"Connection refused" / can't reach Moodle* | Confirm your Moodle URL works in your browser. Use the base URL (not a course or login page), with `https://` and no trailing slash. |
| The skills don't appear in Cowork | Make sure you fully **quit and reopened** Claude Desktop after setup. |

For the full manual walkthrough (every step by hand, plus more troubleshooting), see [`docs/setup-moodle-mcp.md`](docs/setup-moodle-mcp.md).
