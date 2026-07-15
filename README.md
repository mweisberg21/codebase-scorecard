# Codebase Scorecard

An evidence-backed Agent Skill that audits an entire codebase across three engineering pillars and ten operational categories, then produces a standards-backed improvement plan and a self-contained dark-neon HTML report.

![Codebase Scorecard report](assets/codebase-scorecard-preview.png)

## Install

Install globally for Codex and Claude Code:

```bash
npx skills add mweisberg21/codebase-scorecard \
  --skill score-codebase \
  --global \
  --agent codex \
  --agent claude-code \
  --yes
```

Or use the interactive installer:

```bash
npx skills add mweisberg21/codebase-scorecard
```

Restart Codex or open a fresh Claude Code session after installation.

## Use

Invoke the skill directly:

```text
$score-codebase
```

You can also ask your agent to audit the current repository, establish a technical-debt baseline, compare two revisions, or generate an engineering health scorecard.

The audit scores:

- Maintainability
- Modularity
- Predictability

Across:

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

## Output

The skill produces:

- a reproducible 30-cell score matrix;
- evidence-linked findings and confidence levels;
- standards-backed improvements with a target state, first slice, completion test, and verification path;
- a self-contained responsive HTML report;
- explicit coverage and limitations.

The audit is read-only unless you separately ask the agent to implement improvements.

## Update

```bash
npx skills update score-codebase --global --yes
```

## Requirements

- An Agent Skills-compatible coding agent
- Node.js 18 or newer for the `skills` installer
- Python 3.10 or newer when running the bundled inventory, scoring, and report scripts

The report generator uses only the Python standard library and does not load external assets at runtime.
