---
name: markdown-format
description: Markdown writing standards for .md files. Teaches Claude to produce markdownlint-compliant markdown proactively. A PostToolUse hook auto-formats with markdownlint-cli2 --fix after every Write/Edit/MultiEdit on .md files.
---

# Markdown Format

A `PostToolUse` hook runs `markdownlint-cli2 --fix` automatically after every Write, Edit,
or MultiEdit on a `.md` file. Write clean markdown from the start to minimize fixup churn.

## Heading Structure

- Use ATX-style headings (`#`, `##`, `###`) — never Setext underlines
- H1 is optional (MD041 disabled) — fragments and skill files legitimately start without it
- Never skip heading levels (e.g., `##` directly under `#` is fine; `###` directly under `#` is not)

## Lists

- Prefer `-` as the list marker (consistent within a block)
- Add a blank line before a list when it follows a paragraph
- Indent continuation content 2 spaces

## Code Blocks

- Always use fenced code blocks (triple backtick) with a language identifier
- Never use indented code blocks

## Blank Lines

- One blank line before and after headings, code blocks, and lists
- No trailing spaces on any line

## Tables

- Align columns for readability
- Always include a header row and a separator row (`| --- |`)

## Inline HTML

MD033 is disabled — inline HTML is allowed. Use sparingly; prefer native markdown syntax.

## Duplicate Headings

MD024 is set to `siblings_only`. Same-name headings are allowed under different parent
headings (e.g., two "Usage" sections under different H2 parents). True duplicates at the
same level are still flagged.

## Disabled Rules Summary

| Rule | Reason disabled |
| ---- | --------------- |
| MD013 | Line length — LLMs don't wrap at 80 chars; enforcing creates noisy diffs |
| MD041 | First heading — fragments and skill files legitimately lack H1 |
| MD033 | Inline HTML — Claude emits valid HTML (badges, `<details>`, tables) |
| MD024 | Duplicate headings — loosened to `siblings_only` (same level still enforced) |
