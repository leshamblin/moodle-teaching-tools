# Moodle Teaching Tools

Three Claude skills for NCSU faculty: an at-risk-student dashboard, a resource-link audit, and Moodle gradebook setup with instructor deliverables.

## The skills

| Skill | What it does | Just say |
|---|---|---|
| `moodle-student-risk` | Builds an interactive HTML dashboard of at-risk students in a course | "Check course 9201 for struggling students" |
| `moodle-link-checkup` | Audits every resource link (PDFs, slide decks, external URLs, Google Docs) and reports a pass or fail per link | "Audit the links in course 9463" |
| `grade-slinger` | Configures a Moodle gradebook to match the syllabus, then produces four instructor deliverables: a Configuration Report PDF, a sample User Report PDF, a bespoke Excel grade calculator, and a Best Practices PDF | "gb" or "set up a gradebook for MIE 412" |

Dashboards and link reports are written to `~/Documents/Programming/Demo/` and open in your browser.
Grade Slinger asks where to put course folders the first time you run it and defaults to
`~/Documents/Claude/Gradebooks/`.

## Prerequisite: the Moodle MCP server

`moodle-student-risk` and `moodle-link-checkup` read Moodle through the **Moodle MCP server**, so set
that up first. **Grade Slinger does not need it** — it works from the syllabus and a gradebook-setup
PDF you export yourself, and only uses the MCP to spot-check live gradebook state if it happens to be
connected.

Installing the server is a separate, one-time step. Follow the **"Install the Moodle MCP in Claude Code"** guide, or see the [MoodleMCP repo](https://github.com/leshamblin/MoodleMCP). When `claude mcp list` shows `moodle` as Connected, you are ready.

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
- For `moodle-student-risk` and `moodle-link-checkup`: the Moodle MCP server installed and connected
  (see Prerequisite above), and an NCSU Moodle account with a Web Services token
- For `grade-slinger`: Google Chrome or Chromium (HTML-to-PDF), and `python3` with `openpyxl`.
  `PyPDF2` is optional and only trims trailing blank pages from generated PDFs.

## License

MIT. See [LICENSE](LICENSE).
