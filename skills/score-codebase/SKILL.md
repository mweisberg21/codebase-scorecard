---
name: score-codebase
description: Score a whole codebase across maintainability, modularity, predictability, and ten engineering subcategories, then produce a concise chat TL;DR, standards-backed improvement plan, and modern HTML report with a repository-scale readout. Use when the user asks for a codebase health audit, engineering quality scorecard, technical-debt baseline, architecture assessment, improvement roadmap, or before-and-after quality comparison.
---

# Score Codebase

Produce an evidence-backed **scorecard**. Inventory the whole repository, inspect every first-party surface, deepen on risk signals, run the repository's own checks, then score only what the evidence supports.

This is an assessment workflow. Preserve the worktree unless the user separately asks for fixes.

## Scorecard contract

Score these pillars:

- **Maintainability** — how safely and economically the system can be understood, changed, and debugged.
- **Modularity** — how well responsibilities, interfaces, dependencies, and change locality are bounded.
- **Predictability** — how consistently contracts, runtime behavior, and delivery checks prevent surprises.

Score each pillar across these subcategories:

1. TypeScript Safety
2. Architecture
3. Security
4. Database/Supabase
5. Error Handling
6. Code Consistency
7. Build & Tooling
8. Frontend Performance
9. Structural (God Files)
10. Testing & CI

Use `N/A` only when the technology is genuinely absent. Missing controls in an applicable area earn a low score, not `N/A`.

## Workflow

### 1. Fix the audit boundary

Read the applicable repository instructions and root documentation. Record the target root, current revision, dirty state, packages/apps, first-party exclusions, and any checks that repository policy forbids or requires. Treat generated code, vendored dependencies, build output, fixtures, and migrations as distinct surfaces rather than silently mixing them with authored application code.

Completion criterion: the audit notes name the exact revision and every included or excluded top-level surface.

### 2. Build the census

Run `scripts/inventory.py` from this skill against the target root and save its JSON outside the repository, for example:

```bash
python3 <skill-directory>/scripts/inventory.py <repository-root> > /tmp/codebase-inventory.json
```

Use the census to map languages, packages, entry points, configs, source directories, tests, CI, database assets, generated files, and structural hotspots. Preserve the generated `report_metrics` definitions so repository-scale numbers remain reproducible. Supplement the default metrics with a confirmed packages/apps count when manifests or workspace configuration establish one; do not infer packages from folder names alone. Keep four to six headline metrics. The inventory is orientation, not a verdict.

Completion criterion: every first-party file belongs to a visited source, test, database, configuration, CI, documentation, asset, generated, or explicit exclusion surface, and the audit records authored nonblank LOC, total files, authored source files, test files, plus any confidently established package/app or platform-specific counts.

### 3. Inspect breadth before depth

Read root manifests and configs first, then package entry points and representative feature paths end to end. Inspect tests beside the behavior they claim to cover. Open every high-risk search hit and structural hotspot; trace important flows across UI/API, authorization, data access, persistence, and side effects where present.

Define “entire codebase” as every file covered by the census and broad searches, every major surface sampled directly, and every material signal followed to evidence. Reserve line-by-line reading for the files that carry the strongest signals.

Completion criterion: each applicable subcategory has direct evidence from at least two independent locations or mechanisms, and no discovered high-risk signal remains uninspected.

### 4. Gather category evidence

Read [`references/rubric.md`](references/rubric.md) in full before scoring. For each applicable subcategory, record:

- strengths that are demonstrably implemented or enforced;
- risks with exact `path:line` evidence;
- the pillar-specific inference for maintainability, modularity, and predictability;
- confidence limits and evidence not obtained.

The same fact may affect multiple cells only when the report explains the distinct inference. Consolidate shared root causes instead of presenting them as unrelated defects.

Completion criterion: all 30 cells are supported by evidence or explicitly marked `N/A`; unknowns are identified rather than guessed.

### 5. Run the native checks

Discover canonical commands from repository instructions, manifests, and CI. Run the safest relevant typecheck, lint, test, build, format-check, dependency audit, and migration/schema validation commands that the repository already defines. Prefer committed scripts over invented commands. Record command, result, duration when available, and the reason for every skipped check.

A failed check is evidence, not permission to edit. A check not run reduces confidence; it does not automatically prove poor quality.

Completion criterion: every relevant native check is pass, fail, or skipped-with-reason.

### 6. Score after the evidence gate

Apply the anchors in `references/rubric.md`. Put the 30 raw cells into the JSON shape accepted by `scripts/calculate_score.py`, then use that script for equal-weight rollups:

```bash
python3 <skill-directory>/scripts/calculate_score.py /tmp/codebase-scores.json
```

Use custom arithmetic only when the user supplied different weights before the audit. Score current repository state, not stated intent, ticket plans, or hypothetical fixes.

Completion criterion: arithmetic recomputes exactly from the displayed cells, and every score above 3 or below 3 has concrete supporting evidence.

### 7. Derive standards-backed improvements

Read [`references/improvement-standards.md`](references/improvement-standards.md) in full. Turn the strongest shared root causes into three to five bounded improvements ordered by risk reduction per unit effort. Verify current primary sources online when current standards or version-specific official documentation are relevant. Prefer repository contracts, formal standards, and official documentation; do not present blogs or personal preferences as standards.

For every recommendation, name the observed gap, target state, standards basis and applicability, smallest coherent first slice, dependencies, effort, affected scorecard cells, expected effect, completion test, verification commands or measurements, and confidence. Do not invent universal file-size or coverage thresholds, recommend a rewrite without evidence, or guarantee a future score increase.

If live source verification is unavailable, label the source `Source not reverified during this audit` and avoid claims about the latest version.

Completion criterion: every recommendation passes the applicability and quality gates in `references/improvement-standards.md`, cites an authoritative source with URL and section or version, and can be implemented and verified without another discovery pass.

### 8. Deliver the scorecard

Read [`references/report-template.md`](references/report-template.md) before writing the final report. In chat, return only the required executive TL;DR: overall score, confidence, repository scale, systemic strength, dominant risk, top three improvements with effort, verification summary, and the HTML path. Keep it under 200 words unless the user asks for detail. Do not duplicate the full matrix or category evidence in chat.

Put the complete verdict, repository-scale readout, three pillar rollups, 10-row matrix, critical findings, category evidence, standards-backed improvements, verification results, coverage, and limitations in the HTML. Link each improvement to its primary standards or official documentation.

Produce a self-contained HTML report alongside the in-chat scorecard. Read [`references/html-report.md`](references/html-report.md), write the report data JSON outside the audited worktree, and run:

```bash
python3 <skill-directory>/scripts/generate_report.py /tmp/codebase-report.json /tmp/<repo-slug>-codebase-scorecard.html
```

Use a user-specified output path when provided. Otherwise keep both generated artifacts in `/tmp` so an assessment leaves the repository clean. Open the HTML in an available browser and inspect desktop and narrow layouts; when no browser is available, parse the document and check that every required section and score is present.

Bound every correctness and security conclusion to the inspected evidence. State what was inspected and what remained unverified.

Completion criterion: the chat TL;DR is decision-ready without becoming a second report, and a reader can open the verified HTML artifact to reproduce the totals, trace each material claim, understand why each recommended standard applies, and start the next three improvements without another discovery pass.

## Comparison branch

When comparing two revisions, audit both with the same exclusions, weights, checks, and rubric. Report cell-level deltas, distinguish code changes from confidence changes, and calibrate conclusions to the lower-confidence revision.
