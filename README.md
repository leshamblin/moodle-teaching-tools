# Moodle Teaching Tools

Claude skills for NCSU faculty, with a built-in Moodle connection: an at-risk-student dashboard, a resource-link audit, an online course standards audit, and Moodle gradebook setup with instructor deliverables.

## The skills

| Skill | What it does | Just say |
|---|---|---|
| `moodle-student-risk` | Builds an interactive HTML dashboard of at-risk students in a course | "Check course 9201 for struggling students" |
| `moodle-link-checkup` | Audits every resource link (PDFs, slide decks, external URLs, Google Docs) and reports a pass or fail per link | "Audit the links in course 9463" |
| `moodle-course-standards` | Scores every online MBA course in a term against the course review checklist and ranks them worst first | "Audit the Fall 2026 online MBA courses" |
| `grade-slinger` | Configures a Moodle gradebook to match the syllabus, then produces four instructor deliverables: a Configuration Report PDF, a sample User Report PDF, a bespoke Excel grade calculator, and a Best Practices PDF | "gb" or "set up a gradebook for MIE 412" |

Dashboards and link reports are written to `~/Documents/Programming/Demo/` and open in your browser.
Grade Slinger asks where to put course folders the first time you run it and defaults to
`~/Documents/Claude/Gradebooks/`.

## Install

The plugin includes its own Moodle connection, so there is no separate server to set up.

1. **Get a Moodle web services token.** A Moodle site administrator issues it for your account on the
   same web service the rest of the team uses. Treat it like a password.
2. **Install the plugin.** In a terminal:

   ```
   claude plugin marketplace add leshamblin/moodle-teaching-tools
   claude plugin install moodle-teaching-tools@moodle-teaching-tools
   ```

   or, inside a Claude Code session, `/plugin install github:leshamblin/moodle-teaching-tools`.
3. **Enter your Moodle details** when Claude asks: the site address (pre-filled for this academic year)
   and your token. The token is stored in the Mac keychain, not in a settings file. To change either
   later, run `/plugin`, pick Moodle Teaching Tools, and choose Configure.
4. **Restart Claude**, then ask "What Moodle courses can I see?" to check the connection.

The first start downloads the server and, if needed, [uv](https://docs.astral.sh/uv/), which runs it.
That takes a minute; later starts are quick.

Claude is **read-only** on Moodle unless you turn on "Allow changes to Moodle" in the plugin settings.

If you already run the Moodle MCP server yourself with `~/Documents/Programming/MoodleAPI/.env`, the
skills keep using that file. Leave the token blank and the plugin's own connection stays off.

## Requirements

- Claude Code
- For the Moodle skills: a Moodle web services token (see Install above)
- For `grade-slinger`: Google Chrome or Chromium (HTML-to-PDF), and `python3` with `openpyxl`.
  `PyPDF2` is optional and only trims trailing blank pages from generated PDFs.

## License

MIT. See [LICENSE](LICENSE).
