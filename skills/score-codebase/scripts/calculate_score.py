#!/usr/bin/env python3
"""Validate a 33-cell scorecard and calculate equal-weight rollups."""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys
from typing import TextIO


CATEGORIES = (
    "Type Safety",
    "Architecture",
    "Security",
    "Data & Persistence",
    "Error Handling",
    "Code Consistency",
    "Build & Tooling",
    "Performance",
    "Structural (God Files)",
    "Testing & CI",
    "Observability & Operations",
)

PILLARS = ("maintainability", "modularity", "predictability")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            'Input: {"Type Safety": {"maintainability": 4, '
            '"modularity": 3, "predictability": 4}, ...}. '
            "Cells are whole numbers from 0 to 5. "
            'Use null or "N/A" for all three cells of an inapplicable category.'
        ),
    )
    parser.add_argument("scores", help="JSON file, or - for standard input")
    return parser.parse_args()


def open_input(value: str) -> TextIO:
    if value == "-":
        return sys.stdin
    return Path(value).expanduser().open(encoding="utf-8")


def is_na(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.upper() == "N/A")


def validated_score(value: object, location: str) -> float | None:
    if is_na(value):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{location} must be a whole number from 0 to 5 or N/A")
    score = float(value)
    if not 0 <= score <= 5 or not score.is_integer():
        raise ValueError(f"{location} must be a whole number between 0 and 5")
    return score


def rounded(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Solid"
    if score >= 60:
        return "Mixed"
    if score >= 40:
        return "Weak"
    return "High risk"


def validate_payload(payload: object) -> dict[str, dict[str, float | None]]:
    if not isinstance(payload, dict):
        raise ValueError("top-level JSON value must be an object")

    missing = [category for category in CATEGORIES if category not in payload]
    extra = [category for category in payload if category not in CATEGORIES]
    if missing or extra:
        messages = []
        if missing:
            messages.append(f"missing categories: {', '.join(missing)}")
        if extra:
            messages.append(f"unknown categories: {', '.join(extra)}")
        raise ValueError("; ".join(messages))

    result: dict[str, dict[str, float | None]] = {}
    for category in CATEGORIES:
        raw_row = payload[category]
        if not isinstance(raw_row, dict):
            raise ValueError(f"{category} must be an object")
        missing_pillars = [pillar for pillar in PILLARS if pillar not in raw_row]
        extra_pillars = [pillar for pillar in raw_row if pillar not in PILLARS]
        if missing_pillars or extra_pillars:
            raise ValueError(
                f"{category} must contain exactly: {', '.join(PILLARS)}"
            )
        row = {
            pillar: validated_score(raw_row[pillar], f"{category}.{pillar}")
            for pillar in PILLARS
        }
        na_count = sum(value is None for value in row.values())
        if na_count not in (0, len(PILLARS)):
            raise ValueError(f"{category} must mark all three cells N/A or none")
        result[category] = row
    return result


def calculate(rows: dict[str, dict[str, float | None]]) -> dict[str, object]:
    category_rollups: dict[str, int | str] = {}
    pillar_values: dict[str, list[float]] = {pillar: [] for pillar in PILLARS}
    all_values: list[float] = []

    for category in CATEGORIES:
        values = [
            value for value in rows[category].values() if value is not None
        ]
        if not values:
            category_rollups[category] = "N/A"
            continue
        category_rollups[category] = rounded(sum(values) / len(values) * 20)
        for pillar, value in rows[category].items():
            if value is not None:
                pillar_values[pillar].append(value)
                all_values.append(value)

    if not all_values:
        raise ValueError("at least one category must be applicable")

    pillar_rollups = {
        pillar.title(): rounded(sum(values) / len(values) * 20)
        for pillar, values in pillar_values.items()
        if values
    }
    overall_score = rounded(sum(all_values) / len(all_values) * 20)
    return {
        "subcategories": category_rollups,
        "pillars": pillar_rollups,
        "overall": {"score": overall_score, "label": label(overall_score)},
        "applicable_cells": len(all_values),
    }


def main() -> int:
    args = parse_args()
    try:
        with open_input(args.scores) as handle:
            payload = json.load(handle)
        rows = validate_payload(payload)
        json.dump(calculate(rows), sys.stdout, indent=2)
        sys.stdout.write("\n")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"scorecard error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
