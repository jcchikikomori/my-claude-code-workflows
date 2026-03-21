---
name: recipe-front-review
description: Design Doc compliance and security validation with optional auto-fixes
disable-model-invocation: true
---

**Context**: Post-implementation quality assurance for React/TypeScript frontend

## Execution Method

- Compliance validation → performed by code-reviewer
- Security validation → performed by security-reviewer
- Rule analysis → performed by rule-advisor
- Fix implementation → performed by task-executor-frontend
- Quality checks → performed by quality-fixer-frontend
- Re-validation → performed by code-reviewer / security-reviewer

Orchestrator invokes sub-agents and passes structured JSON between them.

Design Doc (uses most recent if omitted): $ARGUMENTS

**Think deeply** Understand the essence of compliance validation and execute:

## Execution Flow

### 1. Prerequisite Check
```bash
# Identify Design Doc
ls docs/design/*.md | grep -v template | tail -1

# Check implementation files
git diff --name-only main...HEAD
```

### 2. Execute code-reviewer
Invoke code-reviewer using Agent tool:
- `subagent_type`: "dev-workflows-frontend:code-reviewer"
- `description`: "Code compliance review"
- `prompt`: "Design Doc: [path]. Implementation files: [git diff file list]. Review mode: full. Validate Design Doc compliance and return structured JSON report with complianceRate, verdict, unfulfilledItems, and qualityIssues."

**Store output as**: `$STEP_2_OUTPUT`

### 3. Execute security-reviewer
Invoke security-reviewer using Agent tool:
- `subagent_type`: "dev-workflows-frontend:security-reviewer"
- `description`: "Security review"
- `prompt`: "Design Doc: [path]. Implementation files: [git diff file list]. Review security compliance."

**Store output as**: `$STEP_3_OUTPUT`

### 4. Verdict and Response

**If security-reviewer returned `blocked`**: Stop immediately. Report the blocked finding and escalate to user. Do not proceed to fix steps.

**Code compliance criteria (considering project stage)**:
- Prototype: Pass at 70%+
- Production: 90%+ recommended

**Security criteria**:
- `approved` or `approved_with_notes` → Pass
- `needs_revision` → Fail

**Report both results independently using subagent output fields only** (do not add fields that are not in the subagent response):

```
Code Compliance: [complianceRate from code-reviewer]
  Verdict: [verdict from code-reviewer]
  Unfulfilled items:
  - [item] (priority) — [solution]

Security Review: [status from security-reviewer]
  Findings by category:
  - [confirmed_risk] [location]: [description] — [rationale]
  - [defense_gap] [location]: [description] — [rationale]
  - [hardening] [location]: [description] — [rationale]
  - [policy] [location]: [description] — [rationale]
  Notes: [notes from security-reviewer, if present]

Execute fixes? (y/n):
```

If both pass and user selects `n`: Skip fix steps, proceed to Final Report.

If user selects `y`:

## Pre-fix Metacognition
**Required**: `rule-advisor → TaskCreate → task-executor-frontend → quality-fixer-frontend`

1. **Execute rule-advisor**: Understand fix essence (symptomatic treatment vs root solution)
2. **Register tasks using TaskCreate**: Register work steps. Always include: first "Confirm skill constraints", final "Verify skill fidelity". Create task file following task template (see documentation-criteria skill) → `docs/plans/tasks/review-fixes-YYYYMMDD.md`. Include both code compliance issues and security requiredFixes.
3. **Execute task-executor-frontend**: Staged auto-fixes (stops at 5 files)
4. **Execute quality-fixer-frontend**: Confirm quality gate passage
5. **Re-validate code-reviewer**: Measure improvement
6. **Re-validate security-reviewer** (only if security fixes were applied)

### Final Report
```
Code Compliance:
  Initial: [X]%
  Final: [Y]% (if fixes executed)

Security Review:
  Initial: [status]
  Final: [status] (if fixes executed)
  Notes: [notes from approved_with_notes, if any]

Remaining issues:
- [items requiring manual intervention]
```

## Auto-fixable Items
- Simple unimplemented acceptance criteria
- Error handling additions
- Contract definition fixes
- Function splitting (length/complexity improvements)
- Security confirmed_risk and defense_gap fixes (input validation, auth checks, output encoding)

## Non-fixable Items
- Fundamental business logic changes
- Architecture-level modifications
- Design Doc deficiencies
- Committed secrets (blocked → human intervention)

**Scope**: Design Doc compliance validation, security review, and auto-fixes.
