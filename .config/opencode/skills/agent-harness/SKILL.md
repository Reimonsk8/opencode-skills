---
name: agent-harness
description: Use when the user runs /agent-harness or asks to create agents, bootstrap an agent harness, set up AGENTS.md, or generate an adversarial coding-agent workflow for a new or existing repository. Works in ANY repo from scratch: inspects the actual stack and scaffolds .agent/ (roles, adversaries, workflows, protocols, quality bar) + AGENTS.md.
---

# Agent Harness bootstrap

Scaffold a production-quality **adversarial coding-agent harness** in the current repository, adapted to its real stack, commands, and conventions. The output is repository files any AI coding agent (opencode, Claude Code, Codex) can follow without this skill.

Core principle: **the agent that writes the implementation must not be the only agent deciding it is correct.** Independent verification, adversarial testing, explicit quality bars, objective evidence.

## 1. Capture the goal

If a project goal was stated (command arguments, conversation), record it verbatim at the top of `.agent/README.md` and in `state.json`. Every role works toward it.

## 2. Inspect the repo first (mandatory)

- list root files
- detect language/framework
- detect package manager + lockfiles
- find build / test / lint / typecheck commands
- read existing config, CI, docs
- read existing agent instructions (AGENTS.md, CLAUDE.md, .opencode/)

Do NOT overwrite existing conventions. Where an equivalent file exists, integrate with it. If the repo is empty, create the generic structure so it adapts later.

## 3. Create `.agent/`

```
.agent/
  README.md          # what the harness is, roles, loop, workflows, quality bar, how to add adversaries, one full worked example
  state.json         # live state: task id, phase, plan, findings, iteration count, blockers, decision
  progress.md        # running log
  decisions.md       # architecture decisions
  blockers.md        # open blockers
  agents/            # planner, builder, tester, reviewer, adversary, triager, judge
  adversaries/       # security, edge-cases, reliability, performance, architecture
  protocols/         # finding-schema, task-schema, review-schema, completion-schema
  templates/         # task, plan, quality-bar, review, findings
  workflows/         # standard, complex, migration
```

Optional, only if the team wants shared procedures: `skills/` (planning, implementation, testing, debugging, code-review, adversarial-review). Each file a practical procedure under ~20 lines, not a generic essay. If they add no value here, delete the folder. Also create `docs/architecture/decisions/` if the repo has docs.

## 4. Role files (`agents/`) — authority + hard limits, one file each

- **planner.md** — MUST NOT modify production code. Produces: requirements, assumptions (explicitly marked, never confused with facts), affected areas, implementation steps, risks, verification strategy, quality bar. Saves a plan artifact.
- **builder.md** — implements the approved plan only. Inspects code before editing, follows repo conventions, reuses existing abstractions, no new dependencies for one-liners, incremental changes, runs tests while coding, never weakens/deletes tests to pass, never touches unrelated code. Reports files changed / summary / tests run + results / concerns. CANNOT declare completion.
- **tester.md** — independent of builder. Does NOT just rerun existing tests: first reasons about how the implementation could fail. Covers happy path, invalid inputs, boundaries, empty/null, error handling, state transitions, concurrency, retries/timeouts, persistence, backwards compatibility. Adds tests when coverage is thin. Every failure reports severity, reproduction, expected, actual, evidence, affected code, recommended fix. Real bugs become regression tests.
- **reviewer.md** — independent. Inspects the actual diff and source; never trusts the builder's explanation as evidence. Checks correctness, architecture, coupling/cohesion, duplication, error handling, security, performance, API compatibility, unnecessary complexity, conventions. Findings classified CRITICAL / HIGH / MEDIUM / LOW / INFO, concrete and actionable. "Code could be better" is not a finding.
- **adversary.md** — different objective: assume the implementation IS weak and break it. Hidden assumptions, edge cases, invalid state transitions, malformed input, unexpected operation sequences, race conditions, resource exhaustion, retry/timeout bugs, security, data corruption, backwards compatibility, dependency/config problems, partial system failure, unexpected user behavior. Prefer concrete demonstration over speculation: reproduce → create failing test → record finding → send to Triager.
- **triager.md** — does NOT auto-accept every criticism. Classifies: VALID / INVALID / DUPLICATE / ALREADY_FIXED / NOT_ACTIONABLE / NEEDS_MORE_EVIDENCE. For valid findings: severity, does it breach the quality bar, is a fix required; group and prioritize. Prevents wasted cycles on subjective or unsupported findings.
- **judge.md** — final gate, NEVER modifies code. Evaluates: original requirements, quality bar, implementation, tests, reviewer findings, adversarial findings, verification evidence. Returns exactly one of PASS / FAIL / ESCALATE.
  - PASS: requirements met, quality bar met, required tests pass, no unresolved critical/high findings, sufficient evidence.
  - FAIL: any required condition not satisfied.
  - ESCALATE: ambiguity agents cannot objectively resolve, conflicting requirements, human decision required.
  - Never PASS because it "looks good".

## 5. Specialized adversaries (`adversaries/`)

- **security.md** — authentication, authorization, injection, secrets, data exposure, unsafe deserialization, SSRF, path traversal, dependency vulnerabilities, privilege escalation, insecure defaults. No vulnerability claim without evidence when evidence is reasonably obtainable.
- **edge-cases.md** — empty / huge / malformed values, unexpected ordering, repeated operations, missing fields, null, duplicates, boundary values, unusual Unicode, unexpected state transitions.
- **reliability.md** — retries, timeouts, partial failures, network failures, process crashes, duplicate requests, idempotency, stale state, recovery.
- **performance.md** — O(n²) behavior, memory growth, excessive allocations, N+1 queries, unnecessary network calls, blocking operations, large payloads, latency regressions. Only report with a reasonable technical basis or measurable evidence.
- **architecture.md** — incorrect abstractions, coupling, boundary violations, leaky abstractions, future scalability problems, duplicated business logic, inappropriate dependencies, architectural inconsistencies.

## 6. Protocols (`protocols/`) — one source of truth for every artifact

- **finding-schema.md** — the single schema ALL findings use (machine-readable):

```yaml
id: F-001
severity: CRITICAL|HIGH|MEDIUM|LOW|INFO
category: correctness|security|performance|reliability|compat|architecture|style
title: short, specific
status: open|fixed|invalid|duplicate|escalated
location: file:line
description: what is wrong, concretely
impact: why it matters
reproduction: steps or test command
expected: what should happen
actual: what actually happens
evidence: test output / trace / measurements
recommended_fix: concrete change
regression_test: path or false
```

- **task-schema.md** — task id, goal, workflow kind, quality bar reference, status, current owner, iteration count.
- **review-schema.md** — reviewer output: summary + per-finding (schema above) + verdict on quality bar compliance.
- **completion-schema.md** — the ONLY valid completion proof: requirements checklist, quality bar items with evidence, tests run + results, findings disposition, judge decision. Completion requires a Judge PASS; no role writes it unilaterally.

## 7. Templates (`templates/`)

- **quality-bar.md** — reusable per task; define four sections:
  - Functional: what must work
  - Non-functional: performance, reliability, security, compatibility
  - Verification: exact commands/tests that prove correctness
  - Failure conditions: what automatically causes FAIL
  Include a complete worked example (e.g. an OAuth task) in the template.
- **task.md / plan.md / review.md / findings.md** — skeletons matching the schemas above.

Every non-trivial task defines a quality bar BEFORE building. No quality bar, no build.

## 8. Workflows (`workflows/`)

- **standard.md** — feature work: Planner → Builder → Tester → Reviewer → Judge. Adversary only when the task has meaningful complexity or risk.
- **complex.md** — architecture changes, auth, payments, DB changes, public APIs, concurrency, security-sensitive functionality, significant refactors: Planner → Builder → Tester → Reviewer → Security Adversary → Edge Case Adversary → Reliability Adversary → Triager → Builder → Tester → Judge.
- **migration.md** — large rewrites / technology migrations. Flow: Discovery → Behavioral Specification → Oracle Tests → Migration Plan → Incremental Builder → Differential Testing → Reviewer → Adversarial Testing → Performance Comparison → Triager → Fix → Regression → Judge. Route via OLD → OBSERVABLE BEHAVIOR → TEST/ORACLE → NEW → COMPARE. Preserve observable behavior, not implementation details; never translate code line-by-line.

## 9. Loop control (in `state.json` and README)

- MAX_ITERATIONS configurable (default 3).
- Same finding surviving N iterations without meaningful progress → ESCALATE.
- No new findings across multiple adversarial rounds → proceed to Judge.
- All quality-bar requirements satisfied → Judge.
Never endlessly rewrite working code.

## 10. Regression principle

Whenever an agent finds a real bug: reproduce → create a regression test → fix → rerun the regression test → rerun the broader suite. Goal: make the bug hard to reintroduce.

## 11. AGENTS.md at repo root

Concise, progressive disclosure — NOT an encyclopedia. Sections:
- project overview (2-3 lines)
- entry points: `.agent/README.md`, `docs/`, `skills/` (if it exists)
- key commands for this repo: build / test / lint / typecheck (taken from step 2, verify them)
- coding conventions (1-3 bullets)
- verification requirement: no completion without running the relevant commands + Judge PASS
- agent workflow: one-line pointer to `.agent/workflows/standard.md`
- completion rule: only via completion-schema; the Builder never self-declares done

If AGENTS.md or CLAUDE.md already exists, merge these sections in, keep pointers, never duplicate the whole harness into it.

## 12. Validate before reporting done

1. every generated file is readable and every referenced path is real
2. no role can unilaterally declare success
3. all findings use the one schema in finding-schema.md
4. loop termination is defined (MAX_ITERATIONS / ESCALATE)
5. build/test/lint commands in AGENTS.md really match the repo (verify configs, don't invent)
6. AGENTS.md pointers resolve
7. a fresh AI agent opening the repo can follow the workflow from AGENTS.md → .agent/ without this skill

## Optional — wire roles as real opencode subagents

If the repo uses opencode, ASK the user (don't decide): create `.opencode/agent/` files mapping roles to subagents — reviewer/triager/judge get `edit: deny`; one file per role whose body references the role doc rather than duplicating it (progressive disclosure). Model independence: design the protocol so Planner (reasoning model), Builder (coding model), Reviewer (independent), Adversary (security/reasoning), Judge (independent) CAN be different models. Do not hardcode model/provider names into the repository.

## Deliverables

Report: files created, files modified, commands detected, workflow to invoke, verification performed. The harness is only "done" when step 12 passes.