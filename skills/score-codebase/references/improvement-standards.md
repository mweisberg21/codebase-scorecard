# Standards-backed improvement guidance

Use this reference after scoring and before recommending changes. The goal is not to decorate opinions with links. Each recommendation must connect an observed repository gap to an applicable, authoritative target state and a verifiable first implementation slice.

## Source hierarchy

Prefer sources in this order:

1. **Repository contracts** — applicable `AGENTS.md`, architecture decisions, checked-in policies, generated contracts, schemas, and versioned configuration. These define local constraints and intended boundaries.
2. **Formal standards** — current normative or consensus sources such as ISO/IEC, IETF RFCs, OWASP ASVS, and NIST publications.
3. **Official framework or vendor documentation** — documentation that matches the detected product and major version, such as TypeScript, Next.js, React, Supabase, PostgreSQL, or GitHub Actions.
4. **Official tool documentation** — the installed compiler, linter, formatter, test runner, package manager, and build system.

Blogs, listicles, consultancy checklists, social posts, and personal preferences may help discovery, but they are not standards and must not be the authority for a recommendation.

When current standards or documentation could have changed, verify the live primary source. Record the source name, URL, version or section, authority type, and why it applies to this repository. If live verification is unavailable, write `Source not reverified during this audit` and avoid claims about the latest version.

## Applicability test

Include a standard only when all four statements are true:

1. The source applies to the detected language, framework, runtime, data store, delivery system, or risk class.
2. The cited section addresses the observed gap rather than a loosely related topic.
3. The target state is compatible with repository rules and existing system boundaries.
4. Compliance or improvement can be demonstrated with a concrete completion test.

If a repository contract conflicts with external guidance, disclose the conflict. Do not silently override local constraints. A repository rule does not excuse a security or correctness risk; describe the risk and the decision that would be required.

## Category source map

Use this map to find the right primary sources. It is a routing guide, not a requirement to cite every source listed.

### Overall quality and architecture

- Use **ISO/IEC 25010:2023** as a quality-model vocabulary for maintainability, modularity, reliability, performance efficiency, security, and related product-quality outcomes.
- Use repository architecture contracts and official framework guidance for concrete boundaries and supported patterns.
- Do not infer that a fashionable architecture is required. Recommend a boundary change only when dependency or change-coupling evidence shows the current boundary is costly or unsafe.

### Type Safety

- Use the official documentation for the detected type system: the **TypeScript TSConfig reference**, **mypy**/**pyright** configuration docs, or the language's own compiler and vet tooling documentation.
- Match advice to the installed checker version and current configuration.
- Treat type assertions, escape hatches (`any`, `Any`, `interface{}`), unsafe parsing, generated types, and external boundaries according to their actual risk. Do not recommend flags that the codebase already enforces.

### Security

- Use **OWASP ASVS** for testable application-security control requirements. Cite the ASVS version and requirement identifier when a requirement directly applies, for example `v5.0.0-1.2.5`.
- Use **NIST SP 800-218 Secure Software Development Framework (SSDF)** for secure-development process improvements and recurring root-cause prevention.
- Use official platform security guidance for framework-specific controls. Never claim that a static audit proves security.

### Data & Persistence

- Use the official documentation for the detected data platform — for example **Supabase** for RLS, client roles, service keys, and authentication, or the equivalent vendor documentation for another platform or ORM.
- Use the current official documentation for the detected database engine (for example **PostgreSQL**) for constraints, transactions, indexes, privileges, and row security.
- Prefer database-enforced invariants for data integrity, but respect deliberate application-authorization boundaries and explain bypass behavior such as service-role access.

### Error Handling

- Use **RFC 9457** for machine-readable HTTP API problem details when the system exposes appropriate HTTP APIs.
- Use official framework/runtime documentation for server actions, exceptions, retries, cancellation, and observability.
- Do not force RFC 9457 onto internal functions, UI-only state, or protocols where it does not fit.

### Code Consistency

- Use the repository's formatter and linter configuration as the immediate contract.
- Use official **ESLint**, formatter, compiler, and framework documentation to explain enforceable rules and failure behavior.
- Prefer automated enforcement over prose-only consistency rules.

### Build & Tooling

- Use the repository's manifests and lockfiles, then official package-manager, build-system, and CI-provider documentation for the detected versions.
- Use NIST SSDF for supply-chain and secure-build process recommendations where applicable.
- Recommend reproducible commands and version pinning only when current evidence shows drift or non-determinism.

### Client Performance

- For web clients, use the official **web.dev Core Web Vitals** definitions for LCP, INP, and CLS, including the 75th-percentile evaluation model.
- For mobile or desktop clients, use the platform's official performance guidance.
- Use official framework performance guidance for the detected version.
- Do not assign a runtime performance score from bundle heuristics alone. Recommend measurement when field or lab data is absent.

### Structural (God Files)

- Use ISO/IEC 25010 quality outcomes, repository architecture contracts, dependency analysis, responsibility count, churn, and change-coupling evidence.
- There is no universal maximum file length. Lines of code may select inspection targets but must not, by themselves, justify extraction.
- Recommend a seam only when it improves responsibility boundaries, testability, ownership, dependency direction, or change locality.

### Testing & CI

- Use official test-framework and CI-provider documentation plus the repository's risk model and release contract.
- There is no universal acceptable coverage percentage. Recommend specific behavior, boundary, failure mode, or regression tests rather than a context-free target.
- Use official CI security guidance for permissions, secret handling, third-party actions, environment protection, and artifact provenance when applicable.

## Recommendation contract

Produce three to five recommendations ordered by expected risk reduction per unit effort. Each recommendation must contain:

- **Title and priority** — a bounded system change, not a slogan.
- **Observed gap** — root cause and exact `path:line` or command evidence.
- **Target state** — the observable engineering property to establish.
- **Standards basis** — one or more primary sources with name, URL, version or section, authority type, and a one-sentence applicability explanation.
- **First slice** — the smallest coherent implementation that proves the direction without requiring a broad rewrite.
- **Dependencies** — prerequisites, migrations, ownership decisions, or `None`.
- **Effort** — `S`, `M`, or `L`, calibrated to this repository.
- **Affected cells** — the scorecard cells the root cause currently affects.
- **Expected effect** — risk or system behavior likely to improve, without promising a score increase.
- **Completion test** — a falsifiable definition of done.
- **Verification** — concrete repository commands, tests, measurements, or review evidence.
- **Confidence** — `High`, `Medium`, or `Low`, with uncertainty reflected in the wording.

The recommendation JSON contract is defined in [`html-report.md`](html-report.md).

## Quality gate

Reject or rewrite a recommendation when it:

- cites no authoritative source or cannot explain why the source applies;
- proposes a universal file-size, function-size, or coverage threshold;
- says only “add abstraction,” “improve tests,” “clean up,” or “follow best practices”;
- recommends a rewrite, framework migration, or new dependency without evidence that the existing system cannot meet the target state;
- duplicates another recommendation's root cause;
- cannot define a completion test and verification path;
- conflicts with a repository constraint without naming the conflict;
- treats a projected score increase as guaranteed.

When the evidence supports fewer than three standards-backed improvements, provide fewer and explain why. Do not manufacture recommendations to fill the quota.
