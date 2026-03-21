---
name: recipe-review
description: Design Doc compliance and security validation with optional auto-fixes
disable-model-invocation: true
---

**Context**: Post-implementation quality assurance

## Orchestrator Definition

**Core Identity**: "I am not a worker. I am an orchestrator."

**First Action**: Register Steps 1-11 using TaskCreate before any execution.

## Execution Method

- Compliance validation → performed by code-reviewer
- Security validation → performed by security-reviewer
- Fix implementation → performed by task-executor
- Quality checks → performed by quality-fixer
- Re-validation → performed by code-reviewer / security-reviewer

Orchestrator invokes sub-agents and passes structured JSON between them.

Design Doc (uses most recent if omitted): $ARGUMENTS

## Execution Flow

### Step 1: Prerequisite Check
```bash
# Identify Design Doc
ls docs/design/*.md | grep -v template | tail -1

# Check implementation files
git diff --name-only main...HEAD
```

### Step 2: Execute code-reviewer
Validate Design Doc compliance:
- Acceptance criteria fulfillment
- Code quality check
- Implementation completeness assessment

**Store output as**: `$STEP_2_OUTPUT`

### Step 3: Execute security-reviewer
Invoke security-reviewer using Agent tool:
- `subagent_type`: "dev-workflows:security-reviewer"
- `description`: "Security review"
- `prompt`: "Design Doc: [path]. Implementation files: [git diff file list]. Review security compliance."

**Store output as**: `$STEP_3_OUTPUT`

### Step 4: Verdict and Response

**If security-reviewer returned `blocked`**: Stop immediately. Report the blocked finding and escalate to user. Do not proceed to fix steps.

**Code compliance criteria (considering project stage)**:
- Prototype: Pass at 70%+
- Production: 90%+ recommended

**Security criteria**:
- `approved` or `approved_with_notes` → Pass
- `needs_revision` → Fail

**Report both results independently**:

```
Code Compliance: [X]%
Security Review: [status]

Code issues:
- [unfulfilled items from code-reviewer]

Security findings:
- [findings from security-reviewer, grouped by category]

Execute fixes? (y/n):
```

If both pass and user selects `n`: Skip Steps 5-11, proceed to Step 12.

### Step 5: Execute Skill

Execute Skill: documentation-criteria (for task file template)

### Step 6: Create Task File

Create task file at `docs/plans/tasks/review-fixes-YYYYMMDD.md`
Include both code compliance issues and security requiredFixes.

### Step 7: Execute Fixes

Invoke task-executor using Agent tool:
- `subagent_type`: "dev-workflows:task-executor"
- `description`: "Execute review fixes"
- `prompt`: "Task file: docs/plans/tasks/review-fixes-YYYYMMDD.md. Apply staged fixes (stops at 5 files)."

### Step 8: Quality Check

Invoke quality-fixer using Agent tool:
- `subagent_type`: "dev-workflows:quality-fixer"
- `description`: "Quality gate check"
- `prompt`: "Confirm quality gate passage for fixed files."

### Step 9: Re-validate code-reviewer

Invoke code-reviewer using Agent tool:
- `subagent_type`: "dev-workflows:code-reviewer"
- `description`: "Re-validate compliance"
- `prompt`: "Re-validate Design Doc compliance after fixes. Prior compliance issues: $STEP_2_OUTPUT. Verify each prior issue is resolved."

### Step 10: Re-validate security-reviewer

Invoke security-reviewer using Agent tool (only if security fixes were applied):
- `subagent_type`: "dev-workflows:security-reviewer"
- `description`: "Re-validate security"
- `prompt`: "Re-validate security after fixes. Prior findings: $STEP_3_OUTPUT. Design Doc: [path]. Implementation files: [file list]."

### Step 11: Final Report

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
