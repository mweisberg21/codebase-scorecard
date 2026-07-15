# Scorecard report template

Use the smallest format that preserves traceability. Omit empty sections, never the coverage or limitations sections.

## Chat TL;DR

Keep the final chat response under 200 words unless the user asks for the full narrative. Use this order:

1. **Verdict** — overall `/100`, label, and confidence in one line.
2. **Scale** — authored LOC, files inventoried, and one or two useful repository-specific counts.
3. **What is working** — the strongest systemic property.
4. **Biggest risk** — the dominant shared root cause and consequence.
5. **Next moves** — the top three improvement titles with effort (`S`, `M`, `L`).
6. **Checks** — pass/fail/skipped counts and the most consequential failure or limitation.
7. **Full report** — a clickable absolute path to the HTML and whether it was visually inspected or structurally validated.

Do not paste the score matrix, category-by-category rationale, exhaustive evidence, or standards bibliography into chat. Those belong in the HTML. Include a 0–1 cell in the verdict line when one exists.

Use this compact shape:

```markdown
**TL;DR — 71/100 (Mixed, high confidence).**

Scale: 50,382 authored LOC · 1,558 files · 1,202 source files · 235 tests.

Working: Pinned tooling and enforced checks keep delivery repeatable.
Risk: A few dependency hubs combine policy, persistence, and side effects.

Next: (1) Split feedback policy from orchestration — M. (2) Add a measured performance gate — S. (3) Standardize public error contracts — M.

Checks: 3 passed, 0 failed, 1 skipped; production telemetry was unavailable.
Full report: [Open the HTML scorecard](/absolute/path/to/report.html) — visually inspected.
```

## Full HTML report

The following sections define the complete report artifact.

## Verdict

State the overall score and label, the dominant strength, the dominant risk, and whether the repository is safe to evolve at its current pace. Name any 0–1 cell immediately.

## Pillar rollup

| Pillar | Score | Confidence | Short reason |
| --- | ---: | --- | --- |
| Maintainability | _/100 | High/Medium/Low | ... |
| Modularity | _/100 | High/Medium/Low | ... |
| Predictability | _/100 | High/Medium/Low | ... |
| **Overall** | **_/100** | **High/Medium/Low** | ... |

## Score matrix

Show raw 0–5 cell scores so the rollup is reproducible.

| Subcategory | Maintainability | Modularity | Predictability | Row /100 | Confidence |
| --- | ---: | ---: | ---: | ---: | --- |
| Type Safety | | | | | |
| Architecture | | | | | |
| Security | | | | | |
| Data & Persistence | | | | | |
| Error Handling | | | | | |
| Code Consistency | | | | | |
| Build & Tooling | | | | | |
| Client Performance | | | | | |
| Structural (God Files) | | | | | |
| Testing & CI | | | | | |

## Critical findings

Order by consequence. For each finding include:

- consequence and affected surface;
- root cause;
- exact evidence links;
- affected scorecard cells;
- confidence and any needed validation.

Say “No critical findings” when none meet the bar.

## Category evidence

For each subcategory, give a compact score rationale: strongest evidence, most important counter-evidence, and why those facts map to the three cell scores. Keep exhaustive search logs out of the report.

## Standards-backed improvements

List three to five improvements, ordered by risk reduction per unit effort. For each improvement include:

- priority and a bounded title;
- observed root cause with exact evidence;
- target state;
- primary standard or official documentation, including source name, URL, version or section, authority type, and why it applies here;
- smallest coherent first slice;
- dependencies or `None`;
- effort (`S`, `M`, `L`) and affected scorecard cells;
- expected risk or behavior improvement, without guaranteeing a score change;
- falsifiable completion test;
- verification commands, tests, measurements, or review evidence;
- confidence.

Follow [`improvement-standards.md`](improvement-standards.md). Do not use blogs as standards, arbitrary file-size or coverage thresholds, or vague recommendations such as “add abstraction” or “improve tests.”

## Verification

| Command | Result | What it established |
| --- | --- | --- |

Include skipped checks and reasons.

## Coverage

Report revision and dirty state; file counts; packages/apps; source, test, config, database, CI, generated, and excluded surfaces; flows traced; and hotspot selection. Distinguish census/search coverage from files read deeply.

## Limitations

State unavailable runtime systems, credentials, browsers, production telemetry, dependency intelligence, coverage data, or checks. End with a calibrated claim such as “repository-wide static assessment with targeted execution,” never “fully secure” or “bug-free.”

## HTML deliverable

Generate the HTML from the same raw cells and evidence data by following [`html-report.md`](html-report.md). Put the complete score matrix and evidence in the HTML, then report its final absolute path in the chat TL;DR.
