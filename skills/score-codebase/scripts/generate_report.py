#!/usr/bin/env python3
"""Generate a self-contained codebase scorecard HTML report from JSON."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from string import Template
import sys
from typing import Any
from urllib.parse import urlparse

from calculate_score import CATEGORIES, PILLARS, calculate, validate_payload


PILLAR_COLORS = {
    "Maintainability": "#62f4ff",
    "Modularity": "#ff4ecd",
    "Predictability": "#b7ff3c",
}

PILLAR_ABBREVIATIONS = {
    "maintainability": "MA",
    "modularity": "MO",
    "predictability": "PR",
}

SEVERITIES = {"critical", "high", "medium", "low"}
RESULTS = {"pass", "fail", "skipped"}
METRIC_COLORS = ("#62f4ff", "#ff4ecd", "#b7ff3c", "#ffb454", "#a78bfa", "#ff5c70")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to report JSON")
    parser.add_argument("output", type=Path, help="Path to output HTML")
    return parser.parse_args()


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def confidence(value: Any) -> str:
    normalized = str(value or "Unrated").strip().title()
    return normalized if normalized in {"High", "Medium", "Low"} else "Unrated"


def required_text(payload: dict[str, Any], key: str, context: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"{context} is missing required field: {key}")
    return value


def safe_http_url(value: Any, context: str) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{context} must use an http or https URL")
    return url


def metric_value(value: Any, context: str) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{context} is missing required field: value")
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.0f}" if value.is_integer() else f"{value:,.1f}"
    return str(value).strip()


def render_repository_metrics(value: Any) -> str:
    metrics = [entry for entry in items(value) if isinstance(entry, dict)]
    if not 4 <= len(metrics) <= 6:
        raise ValueError("repository_metrics must contain four to six metrics")

    rendered = []
    for index, metric in enumerate(metrics, 1):
        context = f"repository metric {index}"
        label = required_text(metric, "label", context)
        display_value = metric_value(metric.get("value"), context)
        detail = str(metric.get("detail", "Repository census")).strip()
        color = METRIC_COLORS[index - 1]
        rendered.append(
            f"""
            <article class="repo-metric" style="--metric-accent:{color}">
              <span>{esc(label)}</span>
              <strong>{esc(display_value)}</strong>
              <small>{esc(detail)}</small>
            </article>
            """
        )
    return "".join(rendered)


def score_text(value: float | None) -> str:
    if value is None:
        return "N/A"
    return str(int(value)) if value.is_integer() else f"{value:.1f}"


def score_class(value: float | None) -> str:
    if value is None:
        return "score-na"
    if value >= 4.5:
        return "score-5"
    if value >= 3.5:
        return "score-4"
    if value >= 2.5:
        return "score-3"
    if value >= 1.5:
        return "score-2"
    if value >= 0.5:
        return "score-1"
    return "score-0"


def render_pillars(
    rollups: dict[str, Any], reasons: dict[str, Any], confidences: dict[str, Any]
) -> str:
    cards = []
    for name, score in rollups["pillars"].items():
        color = PILLAR_COLORS[name]
        reason = reasons.get(name, "Evidence rationale supplied in the category matrix.")
        conf = confidence(confidences.get(name))
        cards.append(
            f"""
            <article class="pillar" style="--pillar:{color};--value:{score}%">
              <div class="pillar-rail" aria-hidden="true"><i></i></div>
              <div>
                <span class="utility">{esc(conf)} confidence</span>
                <h3>{esc(name)}</h3>
                <p>{esc(reason)}</p>
              </div>
              <strong>{score}<small>/100</small></strong>
            </article>
            """
        )
    return "".join(cards)


def render_matrix(
    rows: dict[str, dict[str, float | None]],
    rollups: dict[str, Any],
    confidences: dict[str, Any],
) -> str:
    rendered = []
    for category in CATEGORIES:
        cells = []
        for pillar in PILLARS:
            value = rows[category][pillar]
            label = score_text(value)
            cells.append(
                f'<td><span class="heat {score_class(value)}" '
                f'aria-label="{esc(pillar.title())}: {esc(label)} out of 5">'
                f"{esc(label)}<small>{'/5' if value is not None else ''}</small></span></td>"
            )
        row_score = rollups["subcategories"][category]
        row_label = f"{row_score}/100" if isinstance(row_score, int) else "N/A"
        conf = confidence(confidences.get(category))
        rendered.append(
            f"""
            <tr>
              <th scope="row">{esc(category)}</th>
              {''.join(cells)}
              <td class="row-score">{esc(row_label)}</td>
              <td><span class="confidence confidence-{conf.lower()}">{esc(conf)}</span></td>
            </tr>
            """
        )
    return "".join(rendered)


def render_findings(value: Any) -> str:
    findings = [item for item in items(value) if isinstance(item, dict)]
    if not findings:
        return '<div class="empty">No critical findings met the reporting threshold.</div>'

    cards = []
    for finding in findings:
        severity = str(finding.get("severity", "medium")).strip().lower()
        if severity not in SEVERITIES:
            raise ValueError(f"unknown finding severity: {severity}")
        evidence = "".join(
            f"<li><code>{esc(item)}</code></li>" for item in items(finding.get("evidence"))
        )
        cells = "".join(
            f"<span class=\"tag\">{esc(item)}</span>" for item in items(finding.get("cells"))
        )
        cards.append(
            f"""
            <article class="finding finding-{severity}">
              <header><span class="severity">{esc(severity)}</span><span class="confidence confidence-{confidence(finding.get('confidence')).lower()}">{esc(confidence(finding.get('confidence')))}</span></header>
              <h3>{esc(finding.get('title', 'Untitled finding'))}</h3>
              <p>{esc(finding.get('summary', ''))}</p>
              <div class="root-cause"><span>Root cause</span>{esc(finding.get('root_cause', 'Not supplied.'))}</div>
              <div class="tags">{cells}</div>
              <details><summary>Evidence</summary><ul class="evidence-list">{evidence or '<li>No evidence supplied.</li>'}</ul></details>
            </article>
            """
        )
    return "".join(cards)


def render_categories(
    value: Any,
    rows: dict[str, dict[str, float | None]],
    rollups: dict[str, Any],
    confidences: dict[str, Any],
) -> str:
    category_data = mapping(value)
    rendered = []
    for category in CATEGORIES:
        data = mapping(category_data.get(category))
        evidence = "".join(
            f"<li><code>{esc(item)}</code></li>" for item in items(data.get("evidence"))
        )
        trio = "".join(
            f"<span><small>{PILLAR_ABBREVIATIONS[pillar]}</small><b>{esc(score_text(rows[category][pillar]))}</b></span>"
            for pillar in PILLARS
        )
        row_score = rollups["subcategories"][category]
        rendered.append(
            f"""
            <details class="category">
              <summary>
                <span><i aria-hidden="true"></i>{esc(category)}</span>
                <span class="category-trio">{trio}</span>
                <strong>{esc(row_score)}<small>{'/100' if isinstance(row_score, int) else ''}</small></strong>
                <span class="confidence confidence-{confidence(confidences.get(category)).lower()}">{esc(confidence(confidences.get(category)))}</span>
              </summary>
              <div class="category-body">
                <div><span class="utility">Strength</span><p>{esc(data.get('strength', 'No strength narrative supplied.'))}</p></div>
                <div><span class="utility">Risk</span><p>{esc(data.get('risk', 'No risk narrative supplied.'))}</p></div>
                <div class="category-rationale"><span class="utility">Score rationale</span><p>{esc(data.get('rationale', 'See the raw evidence and matrix scores.'))}</p></div>
                <div class="category-evidence"><span class="utility">Evidence</span><ul class="evidence-list">{evidence or '<li>No evidence narrative supplied.</li>'}</ul></div>
              </div>
            </details>
            """
        )
    return "".join(rendered)


def render_improvements(value: Any) -> str:
    improvements = [item for item in items(value) if isinstance(item, dict)]
    if not improvements:
        return (
            '<div class="empty">No standards-backed improvement met the quality gate. '
            "See the category evidence and limitations for what was assessed.</div>"
        )
    rendered = []
    for index, item in enumerate(improvements, 1):
        context = f"improvement {index}"
        title = required_text(item, "title", context)
        why = required_text(item, "why", context)
        target_state = required_text(item, "target_state", context)
        first_slice = required_text(item, "first_slice", context)
        completion_test = required_text(item, "completion_test", context)
        evidence = [str(entry).strip() for entry in items(item.get("evidence")) if str(entry).strip()]
        if not evidence:
            raise ValueError(f"{context} must include at least one evidence location")
        verification = [str(entry).strip() for entry in items(item.get("verification")) if str(entry).strip()]
        if not verification:
            raise ValueError(f"{context} must include at least one verification step")

        standards = [entry for entry in items(item.get("standards")) if isinstance(entry, dict)]
        if not standards:
            raise ValueError(f"{context} must include at least one standards source")
        rendered_standards = []
        for standard_index, standard in enumerate(standards, 1):
            standard_context = f"{context} standard {standard_index}"
            name = required_text(standard, "name", standard_context)
            url = safe_http_url(required_text(standard, "url", standard_context), standard_context)
            fit = required_text(standard, "fit", standard_context)
            section = str(standard.get("section", "Section not specified")).strip()
            authority = str(standard.get("authority", "Official source")).strip()
            rendered_standards.append(
                f"""
                <li class="standard">
                  <a href="{esc(url)}" target="_blank" rel="noreferrer">{esc(name)}<span aria-hidden="true"> ↗</span></a>
                  <span class="standard-meta">{esc(section)} · {esc(authority)}</span>
                  <p>{esc(fit)}</p>
                </li>
                """
            )

        cells = "".join(
            f'<span class="tag">{esc(cell)}</span>' for cell in items(item.get("cells"))
        )
        dependencies = [str(entry).strip() for entry in items(item.get("dependencies")) if str(entry).strip()]
        dependency_text = "; ".join(dependencies) if dependencies else "None"
        evidence_items = "".join(f"<li><code>{esc(entry)}</code></li>" for entry in evidence)
        verification_steps = "".join(f"<li><code>{esc(step)}</code></li>" for step in verification)
        conf = confidence(item.get("confidence"))
        rendered.append(
            f"""
            <article class="improvement">
              <div class="improvement-index">{index:02d}</div>
              <div class="improvement-copy">
                <div class="improvement-kicker"><span class="utility">Priority {index:02d} · Effort {esc(item.get('effort', '?'))}</span><span class="confidence confidence-{conf.lower()}">{esc(conf)}</span></div>
                <h3>{esc(title)}</h3>
                <p class="improvement-why">{esc(why)}</p>
                <div class="improvement-grid">
                  <div><span class="utility">Target state</span><p>{esc(target_state)}</p></div>
                  <div><span class="utility">First slice</span><p>{esc(first_slice)}</p></div>
                  <div><span class="utility">Expected effect</span><p>{esc(item.get('expected_effect', 'Not supplied.'))}</p></div>
                  <div><span class="utility">Dependencies</span><p>{esc(dependency_text)}</p></div>
                </div>
                <div class="improvement-evidence"><span class="utility">Observed evidence</span><ul>{evidence_items}</ul></div>
                <div class="standards"><span class="utility">Standards basis</span><ul>{''.join(rendered_standards)}</ul></div>
                <div class="completion"><span>Completion test</span>{esc(completion_test)}</div>
                <div class="verification-steps"><span class="utility">Verification</span><ul>{verification_steps}</ul></div>
                <div class="tags">{cells}</div>
              </div>
            </article>
            """
        )
    return "".join(rendered)


def render_verification(value: Any) -> str:
    checks = [item for item in items(value) if isinstance(item, dict)]
    if not checks:
        return '<tr><td colspan="3">No verification commands supplied.</td></tr>'
    rows = []
    for item in checks:
        result = str(item.get("result", "skipped")).strip().lower()
        if result not in RESULTS:
            raise ValueError(f"unknown verification result: {result}")
        rows.append(
            f"""
            <tr><td><code>{esc(item.get('command', ''))}</code></td><td><span class="result result-{result}">{esc(result)}</span></td><td>{esc(item.get('established', ''))}</td></tr>
            """
        )
    return "".join(rows)


def render_coverage(value: Any) -> tuple[str, str, str]:
    coverage = mapping(value)
    stats = "".join(
        f'<div><span class="utility">{esc(item.get("label", "Metric"))}</span><strong>{esc(item.get("value", "—"))}</strong></div>'
        for item in items(coverage.get("stats"))
        if isinstance(item, dict)
    )
    details = "".join(
        f"<li>{esc(item)}</li>" for item in items(coverage.get("details"))
    )
    return esc(coverage.get("summary", "Coverage summary not supplied.")), stats, details


def render_limitations(value: Any) -> str:
    limitations = "".join(f"<li>{esc(item)}</li>" for item in items(value))
    return limitations or "<li>No limitations supplied.</li>"


CSS = """
:root {
  color-scheme: dark;
  --paper: #05070d;
  --paper-strong: #0c111b;
  --ink: #f6f8ff;
  --muted: #8e9ab3;
  --line: #273149;
  --night: #070a12;
  --blue: #62f4ff;
  --magenta: #ff4ecd;
  --teal: #b7ff3c;
  --amber: #ffb454;
  --red: #ff5c70;
  --shadow: 0 24px 70px rgba(0, 0, 0, .42);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle at 82% 7%, rgba(98,244,255,.10), transparent 24%),
    radial-gradient(circle at 12% 28%, rgba(255,78,205,.08), transparent 22%),
    linear-gradient(rgba(98,244,255,.032) 1px, transparent 1px),
    linear-gradient(90deg, rgba(98,244,255,.032) 1px, transparent 1px),
    var(--paper);
  background-size: auto, auto, 42px 42px, 42px 42px, auto;
  font-family: Inter, "Avenir Next", "Segoe UI", system-ui, sans-serif;
  line-height: 1.55;
}
a { color: inherit; }
button, summary { font: inherit; }
button:focus-visible, summary:focus-visible, a:focus-visible { outline: 3px solid var(--blue); outline-offset: 4px; }
.skip { position: absolute; left: -9999px; }
.skip:focus { left: 18px; top: 18px; z-index: 20; color: #05070d; background: var(--teal); padding: 10px 14px; border-radius: 8px; }
.shell { width: min(1220px, calc(100% - 40px)); margin: 0 auto; }
.utility { display: block; color: var(--muted); font: 750 10px/1.35 ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; letter-spacing: .12em; }
.topbar { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 22px 0; border-bottom: 1px solid var(--line); }
.wordmark { display: flex; align-items: center; gap: 12px; font-weight: 800; letter-spacing: -.02em; }
.wordmark-mark { display: grid; grid-template-columns: repeat(3, 4px); gap: 3px; height: 26px; align-items: end; }
.wordmark-mark i { display: block; width: 4px; border-radius: 4px; }
.wordmark-mark i:nth-child(1) { height: 16px; background: var(--blue); box-shadow: 0 0 14px var(--blue); }
.wordmark-mark i:nth-child(2) { height: 25px; background: var(--magenta); box-shadow: 0 0 14px var(--magenta); }
.wordmark-mark i:nth-child(3) { height: 20px; background: var(--teal); box-shadow: 0 0 14px var(--teal); }
.topmeta { display: flex; align-items: center; gap: 8px; }
.chip, .confidence, .tag, .result, .severity { display: inline-flex; align-items: center; border: 1px solid var(--line); border-radius: 999px; padding: 5px 9px; font: 750 10px/1 ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; letter-spacing: .06em; white-space: nowrap; background: rgba(255,255,255,.018); }
.hero { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(300px, .55fr); gap: 64px; align-items: end; padding: 72px 0 34px; }
.hero h1 { margin: 12px 0 22px; max-width: 850px; font-family: "Avenir Next Condensed", "Arial Narrow", sans-serif; font-size: clamp(52px, 8.6vw, 112px); line-height: .86; letter-spacing: -.06em; text-wrap: balance; text-shadow: 0 0 34px rgba(98,244,255,.08); }
.verdict { max-width: 820px; margin: 0; color: #cbd3e4; font-size: clamp(18px, 2.1vw, 26px); line-height: 1.42; }
.diagnostic-core { position: relative; min-height: 320px; overflow: hidden; padding: 28px; border: 1px solid #34415f; border-radius: 22px; background: linear-gradient(145deg, rgba(17,24,39,.96), rgba(5,7,13,.98)); box-shadow: var(--shadow), inset 0 0 60px rgba(98,244,255,.04); }
.diagnostic-core::before { content: ""; position: absolute; inset: 0; pointer-events: none; background: repeating-linear-gradient(0deg, transparent 0 23px, rgba(98,244,255,.045) 24px), repeating-linear-gradient(90deg, transparent 0 23px, rgba(98,244,255,.045) 24px); }
.core-readout { position: relative; z-index: 1; display: flex; align-items: baseline; gap: 8px; padding-bottom: 22px; border-bottom: 1px solid var(--line); }
.core-readout span { position: absolute; top: 3px; right: 0; color: var(--blue); font: 750 10px ui-monospace, monospace; text-transform: uppercase; letter-spacing: .12em; }
.core-readout strong { color: var(--ink); font: 850 104px/.8 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: -.11em; text-shadow: 0 0 26px rgba(98,244,255,.18); }
.core-readout small { color: var(--muted); font: 750 12px ui-monospace, monospace; }
.core-signals { position: relative; z-index: 1; display: grid; gap: 12px; margin-top: 25px; }
.core-signal { --signal: var(--blue); --value: 0%; display: grid; grid-template-columns: 105px 1fr 34px; align-items: center; gap: 10px; color: var(--muted); font: 700 9px ui-monospace, monospace; text-transform: uppercase; letter-spacing: .08em; }
.core-track { height: 7px; overflow: hidden; border: 1px solid #2d3953; background: #090d16; }
.core-track i { display: block; width: var(--value); height: 100%; background: var(--signal); box-shadow: 0 0 16px var(--signal); }
.core-signal b { color: var(--signal); text-align: right; }
.repository-readout { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 1px; overflow: hidden; margin: 0 0 16px; padding: 1px; border-radius: 16px; background: var(--line); box-shadow: var(--shadow); }
.repo-metric { --metric-accent: var(--blue); position: relative; min-height: 132px; padding: 20px; background: #090d16; }
.repo-metric::before { content: ""; position: absolute; inset: 0 0 auto; height: 2px; background: var(--metric-accent); box-shadow: 0 0 16px var(--metric-accent); }
.repo-metric span { display: block; color: var(--muted); font: 750 9px/1.35 ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; letter-spacing: .11em; }
.repo-metric strong { display: block; margin: 12px 0 7px; color: var(--metric-accent); font: 850 clamp(25px, 3vw, 38px)/1 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: -.06em; text-shadow: 0 0 20px color-mix(in srgb, var(--metric-accent) 22%, transparent); }
.repo-metric small { display: block; color: #727f99; font-size: 10px; line-height: 1.35; }
.signals { display: grid; grid-template-columns: repeat(3, 1fr); overflow: hidden; border: 1px solid var(--line); border-radius: 16px; background: rgba(12,17,27,.9); box-shadow: var(--shadow); }
.signal { min-height: 120px; padding: 20px; }
.signal + .signal { border-left: 1px solid var(--line); }
.signal:nth-child(1) { box-shadow: inset 0 3px 0 var(--blue); }
.signal:nth-child(2) { box-shadow: inset 0 3px 0 var(--magenta); }
.signal:nth-child(3) { box-shadow: inset 0 3px 0 var(--teal); }
.signal p { margin: 9px 0 0; color: #d7ddeb; font-weight: 650; }
.pillars { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 18px 0 82px; }
.pillar { --pillar: var(--blue); --value: 0%; display: grid; grid-template-columns: 8px minmax(0,1fr) auto; gap: 18px; min-height: 188px; padding: 23px; background: rgba(12,17,27,.94); border: 1px solid var(--line); border-radius: 18px; box-shadow: inset 0 0 34px rgba(255,255,255,.012); }
.pillar-rail { position: relative; overflow: hidden; border-radius: 8px; background: #171e2d; }
.pillar-rail i { position: absolute; inset: auto 0 0; height: var(--value); background: var(--pillar); box-shadow: 0 0 18px var(--pillar); }
.pillar h3 { margin: 8px 0 7px; font-size: 24px; letter-spacing: -.035em; }
.pillar p { margin: 0; color: var(--muted); font-size: 14px; }
.pillar > strong { color: var(--pillar); font-size: 38px; letter-spacing: -.06em; }
.pillar > strong small { font-size: 12px; letter-spacing: 0; }
.section { --section-accent: var(--blue); margin: 0 0 88px; }
.section-matrix { --section-accent: var(--blue); }
.section-findings { --section-accent: var(--red); }
.section-categories { --section-accent: var(--magenta); }
.section-improvements { --section-accent: var(--teal); }
.section-verification { --section-accent: var(--amber); }
.section-head { display: grid; grid-template-columns: 1fr minmax(260px, .55fr); gap: 40px; align-items: end; margin-bottom: 22px; padding: 4px 0 18px 20px; border-left: 3px solid var(--section-accent); border-bottom: 1px solid var(--line); box-shadow: -12px 0 26px -22px var(--section-accent); }
.section-head h2 { margin: 0; font-family: "Avenir Next Condensed", "Arial Narrow", sans-serif; font-size: clamp(38px, 5.4vw, 70px); line-height: .94; letter-spacing: -.05em; }
.section-head p { margin: 0; color: var(--muted); }
.matrix-wrap { overflow-x: auto; background: var(--night); border: 1px solid #26324a; border-radius: 18px; box-shadow: var(--shadow); }
.matrix { width: 100%; min-width: 900px; border-collapse: collapse; color: white; }
.matrix th, .matrix td { padding: 15px 14px; border-bottom: 1px solid rgba(255,255,255,.11); text-align: center; }
.matrix thead th { color: #b8c3e3; font: 700 10px ui-monospace, monospace; text-transform: uppercase; letter-spacing: .08em; }
.matrix th:first-child { position: sticky; left: 0; z-index: 1; width: 27%; text-align: left; background: var(--night); }
.matrix thead th:first-child { z-index: 2; }
.matrix tbody th { font-size: 14px; }
.heat { display: inline-grid; min-width: 62px; min-height: 48px; place-content: center; border: 1px solid currentColor; border-radius: 10px; font-weight: 850; box-shadow: inset 0 0 16px rgba(255,255,255,.035); }
.heat small { margin-left: 2px; font-size: 10px; opacity: .75; }
.score-5 { background: rgba(183,255,60,.16); color: var(--teal); box-shadow: 0 0 18px rgba(183,255,60,.08); }
.score-4 { background: rgba(98,244,255,.14); color: var(--blue); }
.score-3 { background: rgba(255,180,84,.14); color: var(--amber); }
.score-2 { background: rgba(255,128,82,.15); color: #ff8052; }
.score-1, .score-0 { background: rgba(255,92,112,.15); color: var(--red); box-shadow: 0 0 18px rgba(255,92,112,.08); }
.score-na { color: #aeb8d7; border: 1px dashed #536083; }
.row-score { font-weight: 850; }
.confidence-high { color: var(--teal); border-color: rgba(183,255,60,.38); background: rgba(183,255,60,.07); }
.confidence-medium { color: var(--amber); border-color: rgba(255,180,84,.38); background: rgba(255,180,84,.07); }
.confidence-low { color: var(--red); border-color: rgba(255,92,112,.38); background: rgba(255,92,112,.07); }
.confidence-unrated { color: var(--muted); }
.matrix .confidence { color: #d3dbf3; border-color: #4d5b81; background: transparent; }
.findings { display: grid; grid-template-columns: repeat(2, 1fr); gap: 13px; }
.finding { --severity: var(--amber); padding: 24px; background: rgba(12,17,27,.94); border: 1px solid var(--line); border-top: 4px solid var(--severity); border-radius: 16px; box-shadow: 0 -14px 38px -32px var(--severity); }
.finding-critical { --severity: #8f1523; }
.finding-high { --severity: var(--red); }
.finding-medium { --severity: var(--amber); }
.finding-low { --severity: var(--teal); }
.finding header { display: flex; justify-content: space-between; gap: 12px; }
.finding .severity { color: white; border-color: var(--severity); background: var(--severity); }
.finding h3 { margin: 18px 0 8px; font-size: 25px; line-height: 1.12; letter-spacing: -.035em; }
.finding p { color: #b6c0d3; }
.root-cause, .completion { padding: 13px 15px; background: #101624; border-left: 3px solid var(--blue); }
.root-cause span, .completion span { display: block; margin-bottom: 4px; color: var(--muted); font: 750 10px ui-monospace, monospace; text-transform: uppercase; letter-spacing: .08em; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }
details summary { cursor: pointer; }
.finding details { margin-top: 12px; }
.evidence-list { margin: 12px 0 0; padding-left: 20px; }
.evidence-list li + li { margin-top: 8px; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .9em; overflow-wrap: anywhere; }
.categories { border-top: 1px solid var(--line); background: rgba(8,11,19,.55); }
.category { border-bottom: 1px solid var(--line); }
.category > summary { display: grid; grid-template-columns: minmax(240px,1fr) auto 90px 92px; gap: 18px; align-items: center; padding: 18px 4px; list-style: none; }
.category > summary::-webkit-details-marker { display: none; }
.category > summary > span:first-child { display: flex; align-items: center; gap: 12px; font-weight: 800; }
.category > summary > span:first-child i { width: 10px; height: 10px; border: 2px solid var(--blue); border-radius: 50%; transition: .2s ease; }
.category[open] > summary > span:first-child i { background: var(--blue); transform: scale(1.25); }
.category-trio { display: flex; gap: 5px; }
.category-trio span { display: grid; grid-template-columns: auto auto; gap: 4px; align-items: baseline; min-width: 42px; padding: 5px 7px; border: 1px solid var(--line); border-radius: 8px; }
.category-trio small { color: var(--muted); }
.category > summary > strong { font-size: 20px; text-align: right; }
.category > summary > strong small { font-size: 10px; }
.category-body { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 0 0 22px 22px; }
.category-body > div { padding: 17px; background: rgba(14,20,32,.95); border: 1px solid var(--line); border-radius: 12px; }
.category-body p { margin: 7px 0 0; }
.category-rationale, .category-evidence { grid-column: 1 / -1; }
.improvements { display: grid; gap: 12px; counter-reset: priority; }
.improvement { --improvement-accent: var(--teal); display: grid; grid-template-columns: 80px 1fr; overflow: hidden; background: rgba(12,17,27,.96); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 0 42px -38px var(--improvement-accent); }
.improvement:nth-child(2) { --improvement-accent: var(--blue); }
.improvement:nth-child(3) { --improvement-accent: var(--magenta); }
.improvement:nth-child(4) { --improvement-accent: var(--amber); }
.improvement:nth-child(5) { --improvement-accent: var(--red); }
.improvement-index { display: grid; place-content: center; color: var(--improvement-accent); background: #070a12; border-right: 1px solid var(--line); font: 800 26px ui-monospace, monospace; text-shadow: 0 0 18px var(--improvement-accent); }
.improvement-copy { padding: 22px; }
.improvement-kicker { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.improvement h3 { margin: 7px 0 6px; font-size: 24px; letter-spacing: -.03em; }
.improvement p { margin: 0; color: var(--muted); }
.improvement-why { margin-bottom: 16px !important; max-width: 900px; }
.improvement-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin-bottom: 12px; }
.improvement-grid > div { padding: 14px; border: 1px solid var(--line); border-radius: 12px; background: #101624; }
.improvement-grid p { margin-top: 6px; color: var(--ink); }
.standards { margin: 12px 0; padding: 15px; border: 1px solid rgba(98,244,255,.24); border-radius: 14px; background: rgba(98,244,255,.035); }
.standards > ul { display: grid; gap: 9px; margin: 10px 0 0; padding: 0; list-style: none; }
.standard { padding: 12px; border-left: 3px solid var(--blue); background: #0b101a; }
.standard a { color: var(--blue); font-weight: 800; text-decoration-thickness: 1px; text-underline-offset: 3px; }
.standard-meta { display: block; margin-top: 3px; color: var(--muted); font: 700 10px/1.4 ui-monospace, monospace; text-transform: uppercase; letter-spacing: .05em; }
.standard p { margin-top: 6px; }
.improvement-evidence, .verification-steps { margin-top: 12px; }
.improvement-evidence ul, .verification-steps ul { margin: 8px 0 0; padding-left: 20px; }
.improvement-evidence li + li, .verification-steps li + li { margin-top: 5px; }
.verification { width: 100%; border-collapse: collapse; background: #0a0e17; border: 1px solid var(--line); }
.verification th, .verification td { padding: 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
.verification th { color: var(--muted); font: 750 10px ui-monospace, monospace; text-transform: uppercase; letter-spacing: .08em; }
.result-pass { color: var(--teal); background: rgba(183,255,60,.07); }
.result-fail { color: var(--red); background: rgba(255,92,112,.07); }
.result-skipped { color: var(--amber); background: rgba(255,180,84,.07); }
.coverage { display: grid; grid-template-columns: .9fr 1.1fr; gap: 14px; }
.coverage-card { padding: 26px; color: white; background: #080c15; border: 1px solid rgba(98,244,255,.26); border-radius: 18px; box-shadow: inset 0 3px 0 var(--blue); }
.coverage-card h3, .limits-card h3 { margin: 0 0 10px; font-size: 28px; letter-spacing: -.04em; }
.coverage-card p { color: #c4cee9; }
.coverage-stats { display: grid; grid-template-columns: repeat(2,1fr); gap: 8px; margin: 20px 0; }
.coverage-stats div { padding: 13px; border: 1px solid #3c496f; border-radius: 12px; }
.coverage-stats .utility { color: #aeb9d8; }
.coverage-stats strong { display: block; margin-top: 6px; font-size: 23px; }
.limits-card { padding: 26px; background: rgba(255,180,84,.055); border: 1px solid rgba(255,180,84,.3); border-radius: 18px; box-shadow: inset 0 3px 0 var(--amber); }
.limits-card li + li { margin-top: 9px; }
.empty { padding: 28px; color: var(--muted); border: 1px dashed var(--line); border-radius: 16px; }
footer { display: flex; justify-content: space-between; gap: 20px; padding: 28px 0 44px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; }
@media (max-width: 860px) {
  .shell { width: min(100% - 24px, 1220px); }
  .hero, .section-head, .coverage { grid-template-columns: 1fr; }
  .hero { gap: 28px; padding-top: 46px; }
  .diagnostic-core { min-height: 280px; }
  .signals, .pillars, .findings { grid-template-columns: 1fr; }
  .signal + .signal { border-left: 0; border-top: 1px solid var(--line); }
  .category > summary { grid-template-columns: 1fr auto; }
  .category-trio, .category > summary > .confidence { display: none; }
}
@media (max-width: 560px) {
  .topmeta .chip { display: none; }
  .hero h1 { font-size: 54px; }
  .category-body { grid-template-columns: 1fr; padding-left: 0; }
  .category-rationale, .category-evidence { grid-column: auto; }
  .improvement { grid-template-columns: 54px 1fr; }
  .improvement-grid { grid-template-columns: 1fr; }
  .coverage-stats { grid-template-columns: 1fr; }
  footer { flex-direction: column; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { transition: none !important; }
}
@media print {
  body { background: var(--paper); }
  .shell { width: 100%; }
  .skip { display: none; }
  .hero { padding-top: 30px; }
  .diagnostic-core, .matrix-wrap, .coverage-card, .improvement-index { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .section, .pillar, .finding, .improvement, .category { break-inside: avoid; }
  details { display: block; }
  details > * { display: block; }
  details:not([open]) > *:not(summary) { display: block !important; }
  footer { padding-bottom: 0; }
}
"""


HTML = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <link rel="icon" href="data:,">
  <title>$title</title>
  <style>$css</style>
</head>
<body>
  <a class="skip" href="#main">Skip to scorecard</a>
  <div class="shell">
    <header class="topbar">
      <div class="wordmark"><span class="wordmark-mark" aria-hidden="true"><i></i><i></i><i></i></span> Codebase scorecard</div>
      <div class="topmeta"><span class="chip">$revision</span><span class="chip">$worktree_state</span></div>
    </header>
    <main id="main">
      <section class="hero">
        <div><span class="utility">Engineering system readout · $generated_at</span><h1>$repository</h1><p class="verdict">$verdict</p></div>
        <aside class="diagnostic-core" aria-label="Overall score $overall out of 100">
          <div class="core-readout"><span>Overall · $overall_label</span><strong>$overall</strong><small>/100 · $overall_confidence confidence</small></div>
          <div class="core-signals" aria-label="Pillar score signals">
            <div class="core-signal" style="--signal:#62f4ff;--value:$maintainability%"><span>Maintain</span><i class="core-track"><i></i></i><b>$maintainability</b></div>
            <div class="core-signal" style="--signal:#ff4ecd;--value:$modularity%"><span>Modular</span><i class="core-track"><i></i></i><b>$modularity</b></div>
            <div class="core-signal" style="--signal:#b7ff3c;--value:$predictability%"><span>Predict</span><i class="core-track"><i></i></i><b>$predictability</b></div>
          </div>
        </aside>
      </section>
      <section class="repository-readout" aria-label="Repository scale">$repository_metrics</section>
      <section class="signals" aria-label="Executive summary">
        <div class="signal"><span class="utility">Systemic strength</span><p>$strength</p></div>
        <div class="signal"><span class="utility">Dominant risk</span><p>$risk</p></div>
        <div class="signal"><span class="utility">Change readiness</span><p>$readiness</p></div>
      </section>
      <section class="pillars" aria-label="Pillar scores">$pillars</section>
      <section class="section section-matrix">
        <header class="section-head"><h2>Three rails.<br>Ten stress points.</h2><p>Every cell is scored from direct evidence. Read across to see whether each engineering area is easy to change, cleanly bounded, and consistently enforced.</p></header>
        <div class="matrix-wrap"><table class="matrix"><thead><tr><th scope="col">Subcategory</th><th scope="col">Maintainability</th><th scope="col">Modularity</th><th scope="col">Predictability</th><th scope="col">Row score</th><th scope="col">Confidence</th></tr></thead><tbody>$matrix</tbody></table></div>
      </section>
      <section class="section section-findings">
        <header class="section-head"><h2>What can hurt.</h2><p>Findings are ordered by consequence and tied back to the exact scorecard cells they affect.</p></header>
        <div class="findings">$findings</div>
      </section>
      <section class="section section-categories">
        <header class="section-head"><h2>Evidence, by system.</h2><p>Open a row to see the strongest property, most important counter-evidence, score rationale, and traceable locations.</p></header>
        <div class="categories">$categories</div>
      </section>
      <section class="section section-improvements">
        <header class="section-head"><h2>Move the system,<br>not the symptoms.</h2><p>Priorities are grounded in repository constraints and authoritative standards, then reduced to a first slice, completion test, and verification path.</p></header>
        <div class="improvements">$improvements</div>
      </section>
      <section class="section section-verification">
        <header class="section-head"><h2>Checks actually run.</h2><p>Passing, failing, and skipped checks are all part of the evidence record.</p></header>
        <div class="matrix-wrap"><table class="verification"><thead><tr><th>Command</th><th>Result</th><th>What it established</th></tr></thead><tbody>$verification</tbody></table></div>
      </section>
      <section class="section coverage">
        <article class="coverage-card"><span class="utility">Coverage</span><h3>How much was seen</h3><p>$coverage_summary</p><div class="coverage-stats">$coverage_stats</div><ul>$coverage_details</ul></article>
        <article class="limits-card"><span class="utility">Limitations</span><h3>What remains unknown</h3><ul>$limitations</ul></article>
      </section>
    </main>
    <footer><span>Generated by $$score-codebase</span><span>Repository-wide static assessment with targeted execution.</span></footer>
  </div>
</body>
</html>
"""
)


def build_html(data: dict[str, Any]) -> str:
    meta = mapping(data.get("meta"))
    verdict = mapping(data.get("verdict"))
    required = {
        "meta": (meta, ("repository", "revision", "generated_at")),
        "verdict": (verdict, ("summary", "strength", "risk", "readiness")),
    }
    for section, (payload, keys) in required.items():
        missing = [key for key in keys if not str(payload.get(key, "")).strip()]
        if missing:
            raise ValueError(f"{section} is missing required fields: {', '.join(missing)}")
    confidence_data = mapping(data.get("confidence"))
    pillar_confidence = mapping(confidence_data.get("pillars"))
    category_confidence = mapping(confidence_data.get("subcategories"))
    rows = validate_payload(data.get("scores"))
    rollups = calculate(rows)
    coverage_summary, coverage_stats, coverage_details = render_coverage(
        data.get("coverage")
    )
    repository_metrics = render_repository_metrics(data.get("repository_metrics"))

    repository = meta.get("repository", "Codebase")
    revision = str(meta.get("revision", "revision unknown"))
    if len(revision) > 12:
        revision = revision[:12]
    dirty = meta.get("dirty")
    worktree_state = "Dirty worktree" if dirty is True else "Clean worktree"
    if dirty is None:
        worktree_state = "Worktree unknown"

    return HTML.substitute(
        title=esc(meta.get("title", f"{repository} engineering scorecard")),
        css=CSS,
        revision=esc(revision),
        worktree_state=esc(worktree_state),
        generated_at=esc(meta.get("generated_at", "date not supplied")),
        repository=esc(repository),
        verdict=esc(verdict.get("summary", "No verdict supplied.")),
        overall=rollups["overall"]["score"],
        overall_label=esc(rollups["overall"]["label"]),
        overall_confidence=esc(confidence(confidence_data.get("overall"))),
        maintainability=rollups["pillars"]["Maintainability"],
        modularity=rollups["pillars"]["Modularity"],
        predictability=rollups["pillars"]["Predictability"],
        strength=esc(verdict.get("strength", "Not supplied.")),
        risk=esc(verdict.get("risk", "Not supplied.")),
        readiness=esc(verdict.get("readiness", "Not supplied.")),
        repository_metrics=repository_metrics,
        pillars=render_pillars(
            rollups, mapping(data.get("pillar_reasons")), pillar_confidence
        ),
        matrix=render_matrix(rows, rollups, category_confidence),
        findings=render_findings(data.get("findings")),
        categories=render_categories(
            data.get("categories"), rows, rollups, category_confidence
        ),
        improvements=render_improvements(data.get("improvements")),
        verification=render_verification(data.get("verification")),
        coverage_summary=coverage_summary,
        coverage_stats=coverage_stats,
        coverage_details=coverage_details or "<li>No coverage details supplied.</li>",
        limitations=render_limitations(data.get("limitations")),
    )


def main() -> int:
    args = parse_args()
    try:
        with args.input.expanduser().open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("top-level report JSON must be an object")
        output = args.output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(build_html(data), encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"report error: {error}", file=sys.stderr)
        return 2
    print(f"Created report: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
