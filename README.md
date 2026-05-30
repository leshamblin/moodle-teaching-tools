# Moodle Teaching Tools

Two Claude skills + a guided installer for the Moodle MCP server. Built for NCSU faculty using Claude Desktop with the [MoodleMCP](https://github.com/leshamblin/MoodleMCP) server.

## What's in the plugin

| Component | What it does |
|---|---|
| `/setup-moodle-mcp` | One-time slash command that installs and configures the Moodle MCP server. Run once per machine, then restart Claude Desktop. |
| `moodle-student-risk` skill | Generates an interactive HTML dashboard identifying at-risk students in any Moodle course. Triggers on phrases like *"check course X for struggling students"* or *"who's behind in MBA 553?"* |
| `moodle-link-checkup` skill | Audits every resource link in a Moodle course (PDFs, slide decks, external URLs, Google Docs) and produces an HTML report with ✓/✗ per link. Triggers on *"check the links in course X"* or *"audit course resources."* |

## Install

In **Claude Code** (find it in the Claude Desktop sidebar):

```
/plugin install github:leshamblin/moodle-teaching-tools
```

Then run the prerequisite installer (one time per machine):

```
/setup-moodle-mcp
```

This installs the Moodle MCP server, asks you for your Moodle URL and Web Services token, patches your `claude_desktop_config.json` (preserving any other MCPs you have), and tells you to restart Claude Desktop.

## Day-to-day use

After setup, switch to **Claude Cowork** (the structured-task mode in Claude Desktop). The `moodle` connector and both skills appear automatically in the right-hand Context panel. Use natural language:

- *"Check course 9201 for struggling students"* → opens the risk dashboard in your browser
- *"Audit the links in course 9463"* → opens the link-checkup report
- *"What's due in MBA 534 this week?"* → answered directly via the Moodle MCP

The dashboards land at `~/Documents/Programming/Demo/`.

You can also use the regular Chat side of Claude Desktop for quick Moodle questions ("list my courses", "show me overdue assignments") — anything that doesn't need the dashboard skills.

## Prerequisites

- **Claude Desktop** signed into a Pro account
- **Claude Code** enabled (this is how plugins install)
- **macOS** with Homebrew, **OR** **Windows** with PowerShell
- An **NCSU Moodle account** with a Web Services token

You don't need to install Python, Node, or git separately — the setup command checks for what's missing and installs it.

## Full setup walkthrough

If you'd rather follow each step by hand, see [`docs/setup-moodle-mcp.md`](docs/setup-moodle-mcp.md) — the same guide the slash command automates.

## Compatibility

| Mode | Install plugin | Run `/setup-moodle-mcp` | Use skills |
|---|---|---|---|
| Claude Code | ✓ | ✓ | ✓ |
| Cowork | ✗ | ✗ | ✓ (skills appear in right panel) |
| Chat | ✗ | ✗ | ✗ (but Moodle MCP queries work) |

Set up once in Code, then live in Cowork.

## Built on

- [MoodleMCP](https://github.com/leshamblin/MoodleMCP) — the underlying MCP server that talks to Moodle's Web Services API
- [Chart.js](https://www.chartjs.org/) (CDN-loaded by the dashboard skill)

## License

MIT — see [LICENSE](LICENSE).
