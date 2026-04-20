# Coverage Quality Report Format

## Severity Rules

### Overall Coverage

| Condition | Emoji | Status |
|-----------|-------|--------|
| `current >= threshold` AND `delta >= 0` | ✅ | MAINTAINED |
| `current >= threshold` AND `delta < 0` | ⚠️ | DEGRADED |
| `current < threshold` OR `delta <= -10%` | 🔴 | CRITICAL |

### Per-File Coverage

| Condition | Emoji | Status |
|-----------|-------|--------|
| `delta > 0` | ✅ | IMPROVED |
| `delta == 0` | — | UNCHANGED |
| `-10% < delta < 0` | 🟡 | DEGRADED |
| `delta <= -10%` OR `current < 50%` | 🔴 | MISSING |
| File deleted from current | 🔴 | REMOVED |
| File not in baseline | ℹ️ | NEW FILE |

Default threshold: **80%**. Override via `.coverage-snapshot/config.json`:
```json
{ "threshold": 75 }
```

---

## Missing Lines Formatting

Collapse consecutive integers into ranges:

- `[12, 13, 14, 20, 21]` → `12-14, 20-21`
- `[45, 67, 68, 69, 70, 71, 72, 89]` → `45, 67-72, 89`
- `[45]` → `45`

---

## Column Alignment

Pad file paths and percentages so `→` symbols align:
- File path: left-aligned, padded to longest path + 2 spaces
- Baseline pct: right-aligned, 6 chars
- Current pct: right-aligned, 6 chars
- Delta: right-aligned, 8 chars (includes sign and `%`)

---

## Diff-Check Report (changed files only)

```
Coverage Quality Report
=======================
Date: <ISO date>    Stack: <stack>
Commit: <current SHA> (vs baseline: <baseline SHA>)

Overall: <baseline>% → <current>% (<delta>%) <emoji> <STATUS>

Changed Files (since baseline):
  <path>    <baseline>% → <current>%  (<delta>%)  <emoji> <STATUS>
    Missing lines: <collapsed ranges>
  ...

Files Below Threshold (<threshold>%):
  <path>: <current>%
  ...

Actions:
  • <one bullet per degraded file>
  • <N> file(s) degraded. Run /coverage-quality update to set new baseline.
```

---

## First-Run Report (no baseline)

```
Coverage Quality Report (Initial Baseline)
==========================================
Date: <ISO date>    Stack: <stack>
Commit: <current SHA>

Overall: <current>% <emoji>

All Files:
  <path>    <current>%  <emoji>
    Missing lines: <collapsed ranges>
  ...

Files Below Threshold (<threshold>%):
  <path>: <current>%
  ...

Baseline saved to .coverage-snapshot/baseline.json
Run tests again after changes to compare coverage.
```

---

## Full Report (all files, worst-first)

Same as diff-check but replace "Changed Files" section with "All Files" sorted by `current_pct` ascending (worst first).

---

## Update Confirmation

```
Coverage Quality Report (Baseline Updated)
==========================================
Date: <ISO date>    Stack: <stack>
Commit: <current SHA> (previous baseline: <old SHA>)

Overall: <current>% <emoji>

Baseline updated. Previous: <old>% → Current: <current>% (<delta>%)
Saved to .coverage-snapshot/baseline.json
```

---

## Actions Section Rules

- One bullet per file with status `MISSING` or `DEGRADED`:
  `• Add tests for <path> lines <collapsed missing lines>`
- Final bullet always present:
  - If degraded: `• <N> file(s) degraded. Run /coverage-quality update to set new baseline.`
  - If none degraded: `• Coverage maintained or improved. No action required.`

---

## Example: Diff-Check

```
Coverage Quality Report
=======================
Date: 2026-04-20    Stack: Python
Commit: abc1234 (vs baseline: def5678)

Overall: 82.3% → 79.1% (-3.2%) ⚠️ DEGRADED

Changed Files (since baseline):
  src/auth/middleware.py    100.0% →  71.4%  (-28.6%)  🔴 MISSING
    Missing lines: 45, 67-72, 89
  src/utils/helpers.py       85.0% →  90.0%   (+5.0%)  ✅ IMPROVED

Files Below Threshold (80%):
  src/auth/middleware.py: 71.4%

Actions:
  • Add tests for src/auth/middleware.py lines 45, 67-72, 89
  • 1 file(s) degraded. Run /coverage-quality update to set new baseline.
```

---

## Example: First-Run

```
Coverage Quality Report (Initial Baseline)
==========================================
Date: 2026-04-20    Stack: JavaScript (Jest)
Commit: abc1234

Overall: 74.3% 🟡

All Files:
  src/auth/login.js       100.0%  ✅
  src/utils/format.js      88.0%  ✅
  src/api/client.js        71.0%  🟡
    Missing lines: 34-41, 88, 102-105
  src/components/Form.js   60.2%  🟡
    Missing lines: 12, 45-52, 78

Files Below Threshold (80%):
  src/api/client.js: 71.0%
  src/components/Form.js: 60.2%

Baseline saved to .coverage-snapshot/baseline.json
Run tests again after changes to compare coverage.
```
