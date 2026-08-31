# Grade Calculator Excel Spec

The Grade Calculator is a **bespoke** Excel file for each course — not a copy of the template. It's built fresh using `scripts/build_calculator.py` (openpyxl).

## Audience

For **instructor/admin use** — not student-facing. The instructor uses it to test "what-if" scenarios or verify final grades against Moodle's calculation.

## Two Modes: Full and Abbreviated

The calculator supports two modes. **Ask the instructor which they want** before generating.

### Full mode (`mode="full"`, default)

One yellow input cell per individual grade item (every assignment, quiz, forum, etc.). This is the most transparent option — the instructor enters each score and the spreadsheet shows every item's effective contribution.

Use when:
- Verifying final grades item-by-item
- Running detailed what-if scenarios on specific assignments
- The instructor wants full visibility into how each grade rolls up

### Abbreviated mode (`mode="abbreviated"`)

One yellow input cell per category. The instructor enters the category total (e.g., "Participation: 165 / 175") and the spreadsheet computes the category's contribution to the final grade.

Use when:
- The instructor wants a quick spot-check without entering every individual score
- End-of-semester verification when individual scores are already settled in Moodle
- The category has many items (e.g., 16 participation activities) and the totals are easier to copy from Moodle than re-enter

If the instructor isn't sure, recommend Full — it's more transparent and supports more use cases. The script's `mode` parameter accepts `"full"` or `"abbreviated"`.

## Critical Rule for Full Mode: List Individual Items, Not Just Categories

In full mode, every assignment, quiz, forum, etc. gets its own row with a yellow input cell. The spreadsheet must not collapse items into category totals only.

Formulas automatically:

- Sum/aggregate item scores within each category
- Calculate each item's contribution to the overall course grade using effective course weights
- Roll up category subtotals into the final course percentage

## Column Structure

| Column | Header | Contents |
|--------|--------|----------|
| A | Category / Item | Items indented with leading spaces (e.g., "  Exam 1") |
| B | Max Grade | Max points for each item |
| C | Student Score | Yellow input cells (FFF3CD) for each individual item |
| D | Course Points | Formula showing contribution to final course percentage |

## Course Points formulas

Use effective course weights so each item's contribution is clear:

- **Items in a weighted category**: `score / total_category_weight × category_course_percent`
- **Items with explicit course weights**: `score / max × effective_course_percent`
- **Category subtotal rows**: `SUM` of the item course points above
- **Wrap every formula** in `IF(C="","",formula)` to keep cells blank when no score is entered

## Styling

| Element | Fill color | Notes |
|---------|------------|-------|
| Input cells (Column C, item rows) | `FFF3CD` (yellow) | Where the instructor types scores |
| Final percentage and letter grade | `D4EDDA` (green) | The headline result |
| Subtotal rows | `E8E8E8` (gray) | Category totals |
| Section header rows | `F8F8F8` (light gray, bold) | Category dividers |
| Column headers and title | `CC0000` (NC State red) | Bold |

## Hover Comments (use `openpyxl.comments.Comment`)

Add explanatory comments to:

- **Column headers** — explain what Max Grade, Score, and Course Points mean
- **Each item name** — describe its weight and effective course percentage
- **Each Course Points cell** — show the formula used
- **Category subtotal** — show max possible contribution
- **Letter grade cell** — show the full grade scale breakdown

Add an instruction line near the top: *"Hover over cells with red corners to see notes and formulas."*

## Letter grade lookup

Build a small lookup table at the bottom (or on a hidden sheet) with the syllabus's letter grade scale. The final letter grade cell uses `VLOOKUP` or `INDEX/MATCH` against this table from the final course percentage.

## PDF blank-page trim (used elsewhere — keep here for reference)

```python
from PyPDF2 import PdfReader, PdfWriter
reader = PdfReader("input.pdf")
writer = PdfWriter()
# Keep only non-empty pages (or specify by index)
writer.add_page(reader.pages[0])
with open("output.pdf", "wb") as f:
    writer.write(f)
```
