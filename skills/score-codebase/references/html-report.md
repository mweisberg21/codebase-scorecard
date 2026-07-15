# HTML scorecard data

Use `scripts/generate_report.py` to turn one JSON object into a self-contained, responsive, printable HTML report. The generator validates and recalculates `scores`; it never trusts supplied rollups.

## Required fields

The `scores` object below shows one row's shape; the real input must repeat it for all ten rows.

```json
{
  "meta": {
    "title": "Acme engineering scorecard",
    "repository": "acme",
    "revision": "abc1234",
    "dirty": false,
    "generated_at": "2026-07-14"
  },
  "verdict": {
    "summary": "One direct paragraph.",
    "strength": "The strongest systemic property.",
    "risk": "The dominant shared root cause.",
    "readiness": "What the score means for safe change."
  },
  "scores": {
    "TypeScript Safety": {
      "maintainability": 4,
      "modularity": 3,
      "predictability": 4
    }
  }
}
```

Include all ten exact subcategory keys from `references/rubric.md`. Each row contains the exact lowercase pillar keys `maintainability`, `modularity`, and `predictability`. Use `null` for all three cells of an inapplicable row.

## Evidence and improvement fields

```json
{
  "confidence": {
    "overall": "High",
    "pillars": {
      "Maintainability": "High",
      "Modularity": "Medium",
      "Predictability": "High"
    },
    "subcategories": {
      "TypeScript Safety": "High"
    }
  },
  "pillar_reasons": {
    "Maintainability": "Short score rationale."
  },
  "findings": [
    {
      "severity": "high",
      "title": "Authorization is scattered",
      "summary": "Consequence and affected surface.",
      "root_cause": "The shared cause.",
      "evidence": ["apps/api/action.ts:42 — privileged client bypass"],
      "cells": ["Security / Modularity"],
      "confidence": "High"
    }
  ],
  "categories": {
    "TypeScript Safety": {
      "strength": "Strongest direct evidence.",
      "risk": "Most important counter-evidence.",
      "rationale": "Why the evidence maps to the three scores.",
      "evidence": ["tsconfig.json:8 — strict mode enabled"]
    }
  },
  "improvements": [
    {
      "title": "Centralize authorization",
      "why": "Privileged actions duplicate authorization decisions and can drift.",
      "evidence": ["apps/api/action.ts:42 — privileged client bypasses row policies"],
      "target_state": "Every privileged action crosses one enforced authorization boundary.",
      "first_slice": "Extract one guard and migrate the highest-risk action group with regression tests.",
      "dependencies": ["Confirm the canonical workspace-role matrix"],
      "standards": [
        {
          "name": "OWASP Application Security Verification Standard",
          "url": "https://owasp.org/www-project-application-security-verification-standard/",
          "section": "v5.0.0 access-control requirement",
          "authority": "OWASP standard",
          "fit": "The repository exposes authenticated application actions with role-based authorization."
        }
      ],
      "cells": ["Security / Modularity", "Architecture / Predictability"],
      "effort": "M",
      "expected_effect": "Reduces authorization drift and makes privileged behavior easier to review.",
      "completion_test": "Every privileged action passes one enforced guard and direct bypass tests fail.",
      "verification": ["pnpm test -- authorization", "rg privileged-client apps/"],
      "confidence": "High"
    }
  ],
  "verification": [
    {
      "command": "pnpm typecheck",
      "result": "pass",
      "established": "Current TypeScript graph compiles."
    }
  ],
  "coverage": {
    "summary": "Repository-wide census with targeted deep reads.",
    "stats": [
      {"label": "Files inventoried", "value": "1,558"},
      {"label": "Source files", "value": "1,205"}
    ],
    "details": ["10 packages/apps", "5 representative flows traced"]
  },
  "limitations": ["Production telemetry was unavailable."]
}
```

Use plain strings for evidence so the HTML remains portable. Put exact `path:line` locations at the start of each evidence string. Allowed verification results are `pass`, `fail`, and `skipped`; allowed finding severities are `critical`, `high`, `medium`, and `low`.

`improvements` is required and must contain at least one standards-backed recommendation. Every improvement requires non-empty `title`, `why`, `evidence`, `target_state`, `first_slice`, `completion_test`, `standards`, and `verification`. Start every improvement evidence string with an exact `path:line` or the native check that exposed the gap. Each standards entry requires `name`, an `http` or `https` `url`, and `fit`; include `section` or version and `authority` whenever available. The generator rejects incomplete improvements and unsafe standard URLs.

## Output check

Confirm the HTML contains the same overall, pillar, row, and raw cell scores as `scripts/calculate_score.py`. Inspect the score matrix, long evidence strings, collapsed category details, mobile layout, keyboard focus, print layout, and reduced-motion behavior.
