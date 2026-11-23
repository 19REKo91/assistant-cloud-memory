#!/usr/bin/env python3
"""Validate the Triangle Framework reading register against the checked-out Git tree.

This checks inventory completeness and Git blob fingerprints. It cannot prove that
a source was semantically read; READ_FULL/READ_PARTIAL remain explicit review claims.
The register file itself is exempt from its own hash comparison to avoid recursion.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

REGISTER_REL = Path("PROJECTS/triangle-framework/continuity/SOURCE_READING_REGISTER.csv")
FRAMEWORK_PREFIX = "PROJECTS/triangle-framework/"
VALID_STATUSES = {"READ_FULL", "READ_PARTIAL", "NOT_YET_READ"}


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-full",
        action="store_true",
        help="Fail if any registered file is READ_PARTIAL or NOT_YET_READ.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    register_path = root / REGISTER_REL
    if not register_path.is_file():
        print(f"ERROR: reading register not found: {REGISTER_REL}")
        return 2

    tracked = {
        item
        for item in git(root, "ls-files", "-z", "--", FRAMEWORK_PREFIX).split("\0")
        if item
    }

    with register_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    registered: dict[str, dict[str, str]] = {}
    duplicate_paths: list[str] = []
    malformed: list[str] = []
    for row in rows:
        path = (row.get("path") or "").strip()
        status = (row.get("read_status") or "").strip()
        sha = (row.get("git_blob_sha1") or "").strip()
        if not path or not path.startswith(FRAMEWORK_PREFIX) or status not in VALID_STATUSES or not sha:
            malformed.append(path or "<empty path>")
            continue
        if path in registered:
            duplicate_paths.append(path)
        registered[path] = row

    registered_paths = set(registered)
    missing_rows = sorted(tracked - registered_paths)
    stale_rows = sorted(registered_paths - tracked)
    hash_mismatches: list[tuple[str, str, str]] = []
    for path, row in registered.items():
        if path == REGISTER_REL.as_posix() or path not in tracked:
            continue
        actual = git(root, "hash-object", "--", path).strip()
        expected = row["git_blob_sha1"].strip()
        if actual != expected:
            hash_mismatches.append((path, expected, actual))

    counts = {status: 0 for status in VALID_STATUSES}
    for row in registered.values():
        counts[row["read_status"].strip()] += 1

    print("Triangle Framework continuity check")
    print(f"Tracked files: {len(tracked)}")
    print(f"Register rows: {len(rows)}")
    print(
        "Reading status: "
        f"READ_FULL={counts['READ_FULL']}, "
        f"READ_PARTIAL={counts['READ_PARTIAL']}, "
        f"NOT_YET_READ={counts['NOT_YET_READ']}"
    )
    print("Register self-hash: exempt (self-referential file)")
    print("Semantic reading: not machine-verifiable; status remains a review assertion.")

    problems = False
    for label, values in (
        ("Missing register rows", missing_rows),
        ("Stale register rows", stale_rows),
        ("Duplicate paths", sorted(set(duplicate_paths))),
        ("Malformed rows", malformed),
    ):
        if values:
            problems = True
            print(f"\n{label}:")
            for value in values:
                print(f"  - {value}")

    if hash_mismatches:
        problems = True
        print("\nContent changed since the recorded review:")
        for path, expected, actual in hash_mismatches:
            print(f"  - {path}: register={expected}, current={actual}")

    if counts["NOT_YET_READ"]:
        problems = True
        print("\nFiles still not read:")
        for path, row in registered.items():
            if row["read_status"].strip() == "NOT_YET_READ":
                print(f"  - {path}")

    if args.require_full and counts["READ_PARTIAL"]:
        problems = True
        print("\n--require-full requested, but partial files remain:")
        for path, row in registered.items():
            if row["read_status"].strip() == "READ_PARTIAL":
                print(f"  - {path}")

    if problems:
        print("\nRESULT: FAIL — update/review the register before treating continuity as current.")
        return 1

    print("\nRESULT: PASS — inventory and fingerprints match the register.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
