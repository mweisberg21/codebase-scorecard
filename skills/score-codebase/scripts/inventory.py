#!/usr/bin/env python3
"""Create a deterministic, dependency-free census of a codebase."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
import subprocess
from typing import Iterable


IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".output",
    ".turbo",
    ".venv",
    "__pycache__",
    "bower_components",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
}

SOURCE_EXTENSIONS = {
    ".astro",
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".cjs",
    ".cts",
    ".css",
    ".dart",
    ".ex",
    ".exs",
    ".go",
    ".graphql",
    ".gql",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".less",
    ".lua",
    ".m",
    ".mdx",
    ".mm",
    ".mjs",
    ".mts",
    ".php",
    ".prisma",
    ".py",
    ".rb",
    ".rs",
    ".sass",
    ".scss",
    ".scala",
    ".sh",
    ".sql",
    ".sol",
    ".svelte",
    ".swift",
    ".tsx",
    ".ts",
    ".vue",
    ".xml",
}

CONFIG_NAMES = {
    "biome.json",
    "bun.lock",
    "cargo.toml",
    "composer.json",
    "deno.json",
    "docker-compose.yml",
    "dockerfile",
    "eslint.config.js",
    "eslint.config.mjs",
    "flake.lock",
    "flake.nix",
    "gemfile",
    "go.mod",
    "justfile",
    "makefile",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "poetry.lock",
    "pyproject.toml",
    "requirements.txt",
    "turbo.json",
    "uv.lock",
    "yarn.lock",
}

MAX_TEXT_BYTES = 5 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Codebase root")
    parser.add_argument(
        "--top", type=int, default=30, help="Number of structural hotspots to show"
    )
    return parser.parse_args()


def git_files(root: Path) -> tuple[list[Path], str] | None:
    try:
        top = Path(
            subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        ).resolve()
        relative_root = root.relative_to(top)
        pathspec = "." if relative_root == Path(".") else relative_root.as_posix()
        raw = subprocess.check_output(
            [
                "git",
                "-C",
                str(top),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                pathspec,
            ]
        )
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None

    files: list[Path] = []
    for value in raw.split(b"\0"):
        if not value:
            continue
        path = top / os.fsdecode(value)
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.is_file() or path.is_symlink():
            files.append(path)
    return sorted(set(files)), "git tracked + untracked, respecting ignore rules"


def walked_files(root: Path) -> tuple[list[Path], str]:
    files: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
        )
        current_path = Path(current)
        files.extend(current_path / name for name in sorted(names))
    return files, "filesystem walk with standard generated/dependency directories excluded"


def collect_files(root: Path) -> tuple[list[Path], str]:
    return git_files(root) or walked_files(root)


def is_test(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    lowered = path.name.lower()
    return bool(
        lowered_parts.intersection({"test", "tests", "__tests__", "spec", "specs"})
        or ".test." in lowered
        or ".spec." in lowered
        or lowered.startswith("test_")
        or lowered.endswith("_test.py")
        or lowered.endswith("_test.go")
    )


def is_config(path: Path) -> bool:
    lowered = path.name.lower()
    return bool(
        lowered in CONFIG_NAMES
        or lowered.startswith(("tsconfig", ".eslintrc", ".prettierrc"))
        or lowered.endswith(
            (
                ".config.js",
                ".config.mjs",
                ".config.cjs",
                ".config.ts",
                ".config.json",
            )
        )
    )


def is_ci(path: Path) -> bool:
    lowered = path.as_posix().lower()
    return bool(
        lowered.startswith(".github/workflows/")
        or lowered.startswith(".circleci/")
        or lowered.startswith(".buildkite/")
        or path.name.lower() in {".gitlab-ci.yml", "azure-pipelines.yml", "jenkinsfile"}
    )


def is_database(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    lowered = path.name.lower()
    return bool(
        path.suffix.lower() in {".sql", ".prisma"}
        or lowered_parts.intersection(
            {"database", "db", "drizzle", "migrations", "prisma", "schema", "supabase"}
        )
        or lowered.startswith("schema.")
    )


def is_generated(path: Path, head: bytes) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    lowered = path.name.lower()
    header = head.decode("utf-8", errors="ignore").lower()
    return bool(
        lowered_parts.intersection({"generated", "gen"})
        or ".generated." in lowered
        or lowered.endswith((".g.dart", ".pb.go", ".designer.cs"))
        or any(
            marker in header
            for marker in (
                "@ds-bundle",
                "@generated",
                "auto-generated",
                "autogenerated",
                "automatically generated",
                "code generated",
            )
        )
        or ("generated" in header and "do not edit" in header)
    )


def git_state(root: Path) -> dict[str, object]:
    try:
        revision = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        status = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return {"revision": revision, "dirty": bool(status.strip())}
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {"revision": None, "dirty": None}


def safe_read(path: Path) -> tuple[bytes, str | None]:
    if path.is_symlink():
        return b"", "symlink"
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            head = handle.read(8192)
            if b"\0" in head:
                return head, "binary"
            if size > MAX_TEXT_BYTES:
                return head, "oversized"
            return head + handle.read(), None
    except OSError:
        return b"", "unreadable"


def classify(path: Path, root: Path) -> dict[str, object]:
    relative = path.relative_to(root)
    data, read_state = safe_read(path)
    suffix = path.suffix.lower() or "[none]"
    source = suffix in SOURCE_EXTENSIONS
    test = is_test(relative)
    config = is_config(relative)
    ci = is_ci(relative)
    database = is_database(relative)
    generated = is_generated(relative, data[:2048])
    text = read_state is None
    lines = (
        data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
        if text
        else None
    )
    nonblank = (
        sum(1 for line in data.splitlines() if line.strip()) if text else None
    )
    try:
        size = path.lstat().st_size
    except OSError:
        size = None

    kinds = []
    for enabled, name in (
        (source, "source"),
        (test, "test"),
        (config, "config"),
        (ci, "ci"),
        (database, "database"),
        (generated, "generated"),
    ):
        if enabled:
            kinds.append(name)
    if not kinds:
        kinds.append("other")

    return {
        "path": relative.as_posix(),
        "extension": suffix,
        "bytes": size,
        "lines": lines,
        "nonblank_lines": nonblank,
        "kinds": kinds,
        "read_state": read_state or "text",
    }


def count_where(records: Iterable[dict[str, object]], kind: str) -> int:
    return sum(kind in record["kinds"] for record in records)


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    paths, method = collect_files(root)
    records = [classify(path, root) for path in paths]
    extensions = Counter(record["extension"] for record in records)
    directories = Counter(
        record["path"].split("/", 1)[0]
        if "/" in record["path"]
        else "[root]"
        for record in records
    )
    source_records = [
        record
        for record in records
        if "source" in record["kinds"]
        and "generated" not in record["kinds"]
        and record["nonblank_lines"] is not None
    ]
    hotspots = sorted(
        source_records,
        key=lambda record: (-record["nonblank_lines"], record["path"]),
    )[: max(args.top, 0)]

    result = {
        "root": str(root),
        "collection_method": method,
        "git": git_state(root),
        "totals": {
            "files": len(records),
            "text_files": sum(record["read_state"] == "text" for record in records),
            "source_files": count_where(records, "source"),
            "authored_source_files": len(source_records),
            "authored_source_nonblank_lines": sum(
                record["nonblank_lines"] for record in source_records
            ),
            "test_files": count_where(records, "test"),
            "config_files": count_where(records, "config"),
            "ci_files": count_where(records, "ci"),
            "database_files": count_where(records, "database"),
            "generated_files": count_where(records, "generated"),
            "binary_files": sum(record["read_state"] == "binary" for record in records),
            "oversized_files": sum(
                record["read_state"] == "oversized" for record in records
            ),
            "symlinks": sum(record["read_state"] == "symlink" for record in records),
            "unreadable_files": sum(
                record["read_state"] == "unreadable" for record in records
            ),
        },
        "extension_counts": dict(sorted(extensions.items(), key=lambda item: (-item[1], item[0]))),
        "top_level_counts": dict(sorted(directories.items(), key=lambda item: (-item[1], item[0]))),
        "largest_authored_source_files": hotspots,
        "files": records,
    }
    json.dump(result, fp=os.sys.stdout, indent=2, sort_keys=False)
    os.sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
