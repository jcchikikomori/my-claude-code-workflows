---
name: recipe-backend-integration-test
description: Backend and integration testing workflow. Detects backend stack, tests API endpoints directly via HTTP, verifies frontend-backend integration via browser MCP, and checks database state. Use when backend API testing, backend-frontend integration verification, or full-stack integration QA is needed.
disable-model-invocation: true
---

**Context**: Backend and integration testing workflow combining direct API endpoint testing, browser-based frontend-backend verification, and database state checking.

## Orchestrator Definition

**Core Identity**: "I am an orchestrator."

**First Action**: Register Steps 0-7 using TaskCreate before any execution.

**Why Delegate**: API endpoint testing requires focused HTTP request execution and response validation. Browser integration verification requires Chrome DevTools context. Keeping these in separate subagents prevents context pollution and allows targeted error handling.

**Execution Method**:

- Workspace scan → orchestrator runs directly (Bash)
- User context gathering → orchestrator runs directly (conversation)
- API endpoint testing → delegate to api-endpoint-tester
- Frontend-backend integration → delegate to web-qa-reviewer
- Database verification → orchestrator runs directly (Bash)
- Report generation → orchestrator assembles from subagent outputs
- Test skeleton generation → delegate to acceptance-test-generator (conditional)

Arguments: $ARGUMENTS
(Format: `[API base URL] [Design Doc path]` — both optional)

## Execution Flow

### Step 0: Execute Skills

Execute Skill: testing-principles
Execute Skill: integration-e2e-testing

### Step 1: Workspace Scan and Stack Detection

Parse `$ARGUMENTS`:

- First token (if URL-shaped) → `$API_BASE_URL`
- Second token (or first if not URL-shaped) → `$DESIGN_DOC`

Read detection rules from `references/backend-stacks.md`. Run initial detection:

```bash
ls pom.xml build.gradle build.gradle.kts go.mod pyproject.toml setup.py manage.py Gemfile package.json composer.json artisan 2>/dev/null
```

Based on matches, run framework-specific detection commands from the reference to identify:

- **Framework**: Spring Boot, Django, FastAPI, Rails, Express, NestJS, Go, Laravel, etc.
- **Test runner**: JUnit, pytest, RSpec, Jest, Vitest, go test, PHPUnit, etc.
- **Database**: PostgreSQL, MySQL, MongoDB, SQLite, Redis (from docker-compose, .env, config files)
- **API style**: REST, GraphQL, gRPC (from route patterns, schema files, package dependencies)

Scan for documentation:

```bash
ls README.md README.rst docs/README.md 2>/dev/null
find . -maxdepth 3 -name 'openapi.*' -o -name 'swagger.*' 2>/dev/null | head -5
ls docs/design/*.md 2>/dev/null | head -10
```

If `$DESIGN_DOC` provided, verify it exists:

```bash
ls "$DESIGN_DOC"
```

Extract endpoint list using framework-specific patterns from `references/backend-stacks.md` Endpoint Extraction section.

Store all results as `$STACK_PROFILE`:

```
Framework: [detected]
Test Runner: [detected]
Database: [detected or "not detected"]
API Style: [detected]
Endpoints Found: [count]
OpenAPI Spec: [path or "none"]
Design Doc: [path or "none"]
```

Present `$STACK_PROFILE` to user before proceeding.

### Step 2: Gather User Context

Ask the user for additional context. Present detected defaults and ask for corrections/additions:

**Required:**

- **API base URL**: "[detected default or ask] — Is this correct? If not, what is the API base URL?"
- **Endpoints to test**: "Found [N] endpoints from [source]. Test all, or specify a subset?"
- **Authentication**: "How should API requests be authenticated? (Bearer token, API key, cookie, none)"

**Conditional:**

- **Frontend URL**: "Is there a frontend that calls this API? If so, what URL is it running on?" (enables Step 4)
- **Database access**: "Should we verify database state after mutation tests? If so, how to access the DB?" (enables Step 5)
  - Docker exec: provide container name
  - Local CLI: provide connection command
  - Skip DB verification

**Optional:**

- **Specific test scenarios**: "Any specific scenarios or areas of concern?"
- **Auth credentials**: "Provide auth token/key for testing (will be masked in output)"

Store responses as `$USER_CONTEXT`.

If user did not provide `$API_BASE_URL` in arguments or Step 2, stop: "API base URL is required. Please provide it."

### Step 3: API Endpoint Testing

Build endpoint list from:

1. Endpoints extracted in Step 1 (from route files or OpenAPI spec)
2. User-specified endpoints from Step 2
3. Merge: user-specified override auto-detected where paths overlap

Invoke api-endpoint-tester using Agent tool:

- `subagent_type`: "dev:api-endpoint-tester"
- `description`: "API endpoint testing"
- `prompt`: Build prompt with:

  ```
  Test the following API endpoints.
  Base URL: [$API_BASE_URL from Step 2]
  Authentication: [$AUTH_HEADERS from Step 2]
  OpenAPI Spec: [$OPENAPI_SPEC_PATH from Step 1, if found]
  
  Endpoints:
  [list of METHOD /path with expectedStatus for each]
  
  DB Verification:
  [list of DB checks from Step 2, if user enabled DB verification]
  ```

Store output as `$API_RESULTS`.

Check response:

- `status: "blocked"` → Report `blockedReason` to user. If server unreachable, suggest checking if server is running. Stop.
- `status: "completed"` → Proceed to Step 4.

Present a quick summary to user: "[passed]/[total] endpoints passed. [failed] failures, [errors] errors."

### Step 4: Frontend-Backend Integration Verification [CONDITIONAL]

**Skip condition**: User did not provide a frontend URL in Step 2. Log "Skipped: no frontend URL provided" and proceed to Step 5.

**4A: Browser Inspection**

Invoke web-qa-reviewer using Agent tool:

- `subagent_type`: "dev:web-qa-reviewer"
- `description`: "Frontend-backend integration inspection"
- `prompt`: "Inspect the following URL with focus on network requests to the backend API. URL: [$FRONTEND_URL from Step 2]. Scope: Verify that the frontend correctly calls the backend API at [$API_BASE_URL]. Pay special attention to: network request URLs, request methods, response status codes, and any failed API calls."

Store output as `$BROWSER_RESULTS`.

**4B: Cross-Reference Analysis**

Orchestrator compares `$API_RESULTS` and `$BROWSER_RESULTS`:

For each API endpoint tested in Step 3:

- Check if frontend made a corresponding network request (from `$BROWSER_RESULTS.findings` network category)
- Flag mismatches:
  - **Endpoint failed in Step 3 AND frontend calls it** → "Frontend depends on failing endpoint: [endpoint]" (severity: critical)
  - **Endpoint passed but frontend never calls it** → "Endpoint not called by frontend: [endpoint]" (severity: low, informational)
  - **Frontend calls endpoint not in test list** → "Untested endpoint called by frontend: [URL]" (severity: medium)

Store as `$INTEGRATION_RESULTS`.

### Step 5: Database Verification [CONDITIONAL]

**Skip condition**: User chose to skip DB verification in Step 2. Log "Skipped: DB verification not configured" and proceed to Step 6.

Run framework-specific migration status check (from `references/backend-stacks.md` Migration Status Commands):

```bash
# Example for Rails:
rails db:migrate:status 2>/dev/null

# Example for Django:
python manage.py showmigrations 2>/dev/null
```

Check for pending migrations. If found, warn: "Pending migrations detected. DB state may not match expected schema."

If the api-endpoint-tester returned `dbVerification` results, include those. Otherwise, run additional DB state checks based on mutation endpoints that were tested:

For each POST/PUT/PATCH/DELETE endpoint that passed in Step 3:

- If user provided DB access in Step 2, run a read-only query to verify the expected state change occurred
- Use the DB access method from Step 2 (docker exec or local CLI)

Store as `$DB_RESULTS`.

### Step 6: Generate Integration Test Report

Write `docs/qa/backend-integration-report-YYYYMMDD.md`:

```markdown
# Backend Integration Test Report

Generated: [date]

## Stack Profile

| Property | Value |
|----------|-------|
| Framework | [detected] |
| Test Runner | [detected] |
| Database | [detected] |
| API Style | [detected] |
| API Base URL | [tested URL] |
| Frontend URL | [if provided, else "N/A"] |

## API Endpoint Results

| Endpoint | Method | Expected | Actual | Time | Size | Status |
|----------|--------|----------|--------|------|------|--------|
| /api/users | GET | 200 | 200 | 45ms | 1.2KB | PASS |
| /api/users | POST | 201 | 500 | 120ms | 0.3KB | FAIL |

**Summary**: [passed]/[total] passed | Avg response: [avg]ms

### Failed Endpoints

[For each failed endpoint:]
#### [METHOD] [path]
- Expected: [expectedStatus]
- Actual: [actualStatus]
- Response time: [ms]
- Details: [error details from api-endpoint-tester]

### Slow Endpoints (> 5000ms)

[List or "None"]

## Frontend-Backend Integration

[If Step 4 ran:]

| Finding | Severity | Details |
|---------|----------|---------|
| Frontend depends on failing endpoint | critical | POST /api/users returns 500 |
| Untested endpoint called by frontend | medium | GET /api/config not in test list |

Lighthouse Scores: Performance [score] | Accessibility [score] | Best Practices [score] | SEO [score]

[If Step 4 skipped:]
Skipped: no frontend URL provided.

## Database Verification

[If Step 5 ran:]

Migration Status: [all applied / N pending]

| Check | After Endpoint | Status | Details |
|-------|---------------|--------|---------|
| User record created | POST /api/users | PASS | Row found in users table |

[If Step 5 skipped:]
Skipped: DB verification not configured.

## Summary

| Category | Result |
|----------|--------|
| API Tests | [passed]/[total] passed |
| Frontend Integration | [matched]/[total] verified (or "Skipped") |
| DB Checks | [passed]/[total] passed (or "Skipped") |
| **Overall** | **[PASS/FAIL/PARTIAL]** |

## Recommended Actions

[Generated based on failures:]
- [For each failed API endpoint: specific action to investigate/fix]
- [For each frontend integration mismatch: action to align frontend and backend]
- [For each DB verification failure: action to investigate data integrity]
- [If pending migrations: "Run pending migrations before next test cycle"]
```

Present to user:

```
Backend integration test complete.
- Report: docs/qa/backend-integration-report-YYYYMMDD.md
- API: [passed]/[total] | Frontend: [result] | DB: [result]
- Overall: [PASS/FAIL/PARTIAL]
```

### Step 7: Offer Test Skeleton Generation [CONDITIONAL]

**Skip condition**: No failures found in Steps 3-5. Report "All tests passed. No skeleton generation needed."

**Skip condition**: No Design Doc available (`$DESIGN_DOC` is empty). Report "Failures found but no Design Doc provided. Provide a Design Doc to generate test skeletons for failing areas."

If failures exist AND Design Doc available, ask user: "Found [N] failures. Generate test skeletons from Design Doc to cover these areas?"

If user approves:

Invoke acceptance-test-generator using Agent tool:

- `subagent_type`: "dev:acceptance-test-generator"
- `description`: "Generate test skeletons for backend failures"
- `prompt`: "Generate test skeletons targeting the following backend integration failures. Design Doc: [$DESIGN_DOC]. Focus on ACs related to these failing areas: [list failed endpoint descriptions and DB verification failures]"

Store output as `$SKELETON_OUTPUT`.

Report: "Test skeletons generated at [paths from generatedFiles]. Use `recipe-add-integration-tests` to implement them."
