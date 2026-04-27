# Flag Analysis

A small companion tool that reads a Petra validation result JSON, summarizes
the flags (rules with verdict `fail` or `needs_review`), and asks Claude to
suggest areas of improvement.

## Usage

```bash
# 1. Produce a validation report (existing CLI)
python -m src.main validate --pdf ./my.pdf --out ./report.json

# 2. Analyze the flags
python flag_analysis/analyze_flags.py ./report.json

# Optional: write Claude's feedback to a file
python flag_analysis/analyze_flags.py ./report.json --out feedback.md

# Stats only, no LLM call
python flag_analysis/analyze_flags.py ./report.json --skip-llm
```

## Environment

- `ANTHROPIC_API_KEY` (required)
- `CLAUDE_TEXT_MODEL` (optional, defaults to `claude-sonnet-4-6`)

## Output

- A table of total rules, pass rate, and flag counts by verdict / group.
- A Markdown feedback block from Claude with: Overview, Top Issues,
  Areas for Improvement, and Quick Wins.
