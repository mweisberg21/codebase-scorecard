# Codebase scorecard rubric

## Contents

1. Scoring anchors
2. Rollup arithmetic
3. Confidence
4. Subcategory rubric
5. Evidence rules

## Scoring anchors

Score each applicable cell from 0 to 5:

| Score | Meaning | Evidence standard |
| ---: | --- | --- |
| 5 | Exemplary | The property is systemic, simple to follow, and enforced. Broad inspection and current checks found no material counterexample. |
| 4 | Strong | The property is established and usually enforced, with localized gaps that do not dominate change risk. |
| 3 | Mixed | Sound patterns exist, but important paths rely on convention, contain inconsistency, or lack enforcement. |
| 2 | Weak | Repeated weaknesses materially raise change cost, coupling, or surprise; controls are partial or mostly manual. |
| 1 | Critical | The area is broadly hazardous, opaque, tightly coupled, or unreliable, with only isolated protection. |
| 0 | Absent/unsafe | An applicable control is absent or direct evidence shows systemic unsafe behavior. Reserve this for exceptional cases. |
| N/A | Not applicable | The technology or surface does not exist. Exclude the cell from all means. |

Scores describe the repository today. Documentation earns credit only when code and enforcement agree with it.

## Rollup arithmetic

Use equal weighting unless the user sets weights before inspection.

- **Subcategory score:** arithmetic mean of its applicable pillar cells, multiplied by 20.
- **Pillar score:** arithmetic mean of its applicable subcategory cells, multiplied by 20.
- **Overall score:** arithmetic mean of every applicable cell, multiplied by 20.
- Round displayed `/100` scores to the nearest whole number. Preserve unrounded values until the final calculation.

Interpret rollups:

| Score | Label |
| ---: | --- |
| 90–100 | Excellent |
| 75–89 | Solid |
| 60–74 | Mixed |
| 40–59 | Weak |
| 0–39 | High risk |

Do not hide a critical cell behind a healthy average. Surface every 0–1 cell in the verdict.

## Confidence

Assign one confidence level to each subcategory and to the overall result:

- **High:** broad direct inspection plus current relevant checks; important flows were traced end to end.
- **Medium:** direct code/config evidence is broad, but one meaningful check or runtime surface was unavailable.
- **Low:** the score depends materially on sampling, inference, missing dependencies, or checks that could not run.

Confidence measures evidence quality, not code quality. A high score with low confidence is provisional.

## Subcategory rubric

### 1. TypeScript Safety

Use `N/A` when TypeScript is absent.

- **Maintainability:** strict, expressive types reduce casts, `any`, suppression comments, unsafe non-null assertions, and duplicated shapes; generated types have a clear update path.
- **Modularity:** contracts are owned at their seams, public types are narrow, domain types do not leak storage/framework details, and dependency direction is visible in imports.
- **Predictability:** strict compiler options, runtime validation at untyped boundaries, exhaustive state handling, and CI typechecks make invalid states fail consistently.
- **Probe:** `tsconfig*`, package scripts, boundary schemas, generated types, `any`, `unknown`, `@ts-ignore`, `@ts-expect-error`, assertions, duplicate interfaces, and actual typecheck output.

### 2. Architecture

- **Maintainability:** major flows are legible, responsibilities have obvious homes, dependencies are understandable, and documentation matches implementation.
- **Modularity:** modules have cohesive responsibilities, small interfaces, clean dependency direction, local change impact, and few cycles or pass-through layers.
- **Predictability:** invariants and architectural rules are explicit and consistently followed or mechanically enforced across packages and features.
- **Probe:** entry points, package boundaries, public exports, import graph/cycles, feature slices, shared layers, cross-cutting helpers, and representative end-to-end flows.

### 3. Security

- **Maintainability:** sensitive behavior is centralized in auditable helpers; authentication, authorization, validation, secrets, and side effects do not have scattered alternate paths.
- **Modularity:** trust boundaries sit at server/data seams, privileged clients are contained, and callers cannot bypass authorization or validation contracts.
- **Predictability:** deny-by-default behavior, environment guards, tests, secret handling, dependency policy, audit trails, rate limits, and signature/CSRF/replay controls make failure modes consistent.
- **Probe:** request handlers, server actions, authn/authz, tenant isolation, input/output validation, secrets/logging, uploads, webhooks, external fetches, unsafe rendering, production guards, dependency audit, and security tests.

### 4. Database/Supabase

Use the equivalent rubric for another database. Use `N/A` only when no persistent database exists.

- **Maintainability:** schema changes, queries, generated types, policies, indexes, and data lifecycle rules have clear ownership and a usable local workflow.
- **Modularity:** data access is localized behind appropriate seams; tenant, RLS, service-role, transaction, and domain boundaries do not leak into unrelated callers.
- **Predictability:** constraints, policies, transactions, idempotent/backward-compatible migrations, deterministic seeds, typed results, and guarded production workflows preserve invariants.
- **Probe:** schema/migrations, Supabase clients and RLS policies, query sites, generated types, transactions, indexes, cascade behavior, seeds, migration CI, N+1 patterns, and environment protections.

### 5. Error Handling

- **Maintainability:** failures use a coherent vocabulary, retain useful context, avoid swallowed exceptions, and produce actionable logs without exposing sensitive data.
- **Modularity:** low-level errors are translated at boundaries; retry, timeout, fallback, and user-message policy live at the layer that owns them.
- **Predictability:** expected failures have typed/stable outcomes and unexpected failures propagate, report, and recover consistently across async and side-effecting paths.
- **Probe:** `try/catch`, promise rejections, empty catches, console/logging calls, API/action error shapes, error boundaries, timeouts, retries, transactions, queues, and failure-path tests.

### 6. Code Consistency

- **Maintainability:** naming, file layout, state patterns, formatting, and common operations are consistent enough that new code is easy to place and read.
- **Modularity:** equivalent features expose equivalent interfaces and reuse a canonical implementation instead of accumulating parallel helpers or duplicate abstractions.
- **Predictability:** lint, formatting, generators, import rules, and review/CI ratchets enforce the conventions that matter.
- **Probe:** lint/format config, suppression baselines, naming/layout outliers, duplicate utilities/types, competing patterns, dead code, generated conventions, and check output.

### 7. Build & Tooling

- **Maintainability:** canonical setup and development commands are few, documented, current, and local failures are diagnosable.
- **Modularity:** packages own their dependencies and tasks; workspace boundaries, cache inputs, code generation, and build outputs are isolated and composable.
- **Predictability:** tool/runtime versions, lockfiles, environment validation, clean builds, caches, and release workflows produce reproducible results.
- **Probe:** manifests, scripts, lockfiles, version managers, workspace/task config, environment schemas, generated artifacts, clean build behavior, dependency health, and setup docs.

### 8. Frontend Performance

Use `N/A` when no frontend exists. Score evidence and safeguards, not speculative micro-optimizations.

- **Maintainability:** performance-sensitive data, rendering, assets, and caching patterns are understandable and centralized rather than patched per component.
- **Modularity:** client/server and async boundaries minimize shipped code, waterfalls, rerender coupling, global state, and oversized route/component dependencies.
- **Predictability:** budgets, measurements, bundle analysis, caching rules, image/font policy, and regression checks make performance visible before users report it.
- **Probe:** client entry points, bundle/code splitting, route loading, fetch waterfalls, caching, large dependencies, images/fonts, render loops, list virtualization, Web Vitals, performance tests, and build output.

### 9. Structural (God Files)

- **Maintainability:** files and functions are cohesive and navigable; large files earn their size rather than mixing policy, orchestration, persistence, UI, and utilities.
- **Modularity:** dependency hubs have intentional interfaces, responsibilities split at real seams, and changes stay local rather than radiating from god modules.
- **Predictability:** size/complexity/import guardrails, ownership conventions, and review practices prevent hotspots from regrowing.
- **Probe:** inventory hotspots, nonblank lines, import/export fan-in/fan-out where tools exist, long functions, mixed concerns, barrel files, dependency cycles, and structural tests.

Size is a lead, not a verdict. Generated files, declarative schemas, fixtures, and cohesive registries are not god files merely because they are long.

### 10. Testing & CI

- **Maintainability:** tests describe behavior, use stable fixtures/helpers, fail clearly, and can change with the code without excessive mocking or duplication.
- **Modularity:** seams permit the right unit/integration/end-to-end split; critical boundaries and failure paths are tested at their owning layer.
- **Predictability:** local and hosted checks agree, tests are deterministic, critical paths and regressions are covered, skips are controlled, and required gates block bad changes.
- **Probe:** test layout/config, representative tests, coverage if configured, mocks/fixtures, skipped/flaky tests, CI workflows, branch gates, migration checks, artifact checks, and actual test/CI-equivalent output.

## Evidence rules

1. Cite exact `path:line` locations for code claims and exact commands for runtime claims.
2. Seek confirming and contradicting evidence. One good helper does not prove systemic quality; one ugly file does not prove systemic failure.
3. Separate presence from enforcement. A convention documented but not checked usually caps predictability at 3.
4. Separate code quality from check availability. Missing execution lowers confidence; a failing current check lowers the relevant score.
5. Keep findings causal. Prefer a shared root cause with its affected cells over ten repetitions of the same symptom.
6. Treat security and performance as evidence-based disciplines. Do not certify security or invent performance impact without tracing or measurement.
7. Calibrate scores to the anchors, not to other repositories or personal style.
