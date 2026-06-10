# Moodle Teaching Tools

Two Claude skills for NCSU faculty: an at-risk-student dashboard and a resource-link audit for any Moodle course.

## The skills

| Skill | What it does | Just say |
|---|---|---|
| `moodle-student-risk` | Builds an interactive HTML dashboard of at-risk students in a course | "Check course 9201 for struggling students" |
| `moodle-link-checkup` | Audits every resource link (PDFs, slide decks, external URLs, Google Docs) and reports a pass or fail per link | "Audit the links in course 9463" |

Dashboards and reports are written to `~/Documents/Programming/Demo/` and open in your browser.

## Prerequisite: the Moodle MCP server

These skills read Moodle through the **Moodle MCP server**, so set that up first. Installing the server is a separate, one-time step. Follow the **"Install the Moodle MCP in Claude Code"** guide, or see the [MoodleMCP repo](https://github.com/leshamblin/MoodleMCP). When `claude mcp list` shows `moodle` as Connected, you are ready.

## Install the plugin

Plugins install from the **Claude Code CLI** (the `claude` command in a terminal). Note: the Claude Code surface inside the Claude Desktop app does not support `/plugin`, so the plugin is currently for CLI users.

```
claude plugin marketplace add leshamblin/moodle-teaching-tools
claude plugin install moodle-teaching-tools@moodle-teaching-tools
```

Inside an interactive `claude` session you can also run:

```
/plugin install github:leshamblin/moodle-teaching-tools
```

If you installed from a running session, run `/reload-plugins` or restart Claude Code.

## Requirements

- Claude Code CLI
- The Moodle MCP server installed and connected (see Prerequisite above)
- An NCSU Moodle account with a Web Services token

## License

MIT. See [LICENSE](LICENSE).
