#!/usr/bin/env python3
"""Verify inventory and Git blob fingerprints for projects connected to Triangle Framework."""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTER = ROOT / "PROJECTS/triangle-framework/continuity/CONNECTED_PROJECTS_READING_REGISTER.csv"
PREFIXES = (
    "PROJECTS/prism-engine/",
    "PROJECTS/cosmic-triangle-rebalance-118/",
    "PROJECTS/element-mass-doubling/",
    "PROJECTS/C-G-Z-Test-v1.0/",
    "PROJECTS/cosmic-triangle-framework/v1.0/",
    "triangle-lab/",
)
ALLOWED = {"READ_FULL", "READ_PARTIAL"}


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    if not REGISTER.is_file():
        print(f"FAIL: register missing: {REGISTER}")
        return 1

    with REGISTER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"path", "size_bytes", "git_blob_sha1", "project", "read_status", "review_note"}
        if not required.issubset(reader.fieldnames or []):
            print(f"FAIL: register columns missing: {sorted(required - set(reader.fieldnames or []))}")
            return 1
        rows = list(reader)

    registered = {}
    duplicates = []
    for row in rows:
        path = row["path"].strip()
        if path in registered:
            duplicates.append(path)
        registered[path] = row

    actual = {}
    for prefix in PREFIXES:
        base = ROOT / prefix
        if not base.is_dir():
            print(f"FAIL: expected project directory missing: {prefix}")
            return 1
        for file in base.rglob("*"):
            if file.is_file():
                rel = file.relative_to(ROOT).as_posix()
                actual[rel] = file

    missing = sorted(set(registered) - set(actual))
    unregistered = sorted(set(actual) - set(registered))
    hash_errors = []
    size_errors = []
    status_errors = []
    counts = {"READ_FULL": 0, "READ_PARTIAL": 0}
    for rel, file in actual.items():
        row = registered.get(rel)
        if row is None:
            continue
        data = file.read_bytes()
        expected_sha = row["git_blob_sha1"].strip()
        actual_sha = git_blob_sha1(data)
        if expected_sha != actual_sha:
            hash_errors.append((rel, expected_sha, actual_sha))
        try:
            expected_size = int(row["size_bytes"])
        except (TypeError, ValueError):
            expected_size = -1
        if expected_size != len(data):
            size_errors.append((rel, expected_size, len(data)))
        status = row["read_status"].strip()
        if status not in ALLOWED:
            status_errors.append((rel, status))
        else:
            counts[status] += 1

    print(f"Tracked connected-project files: {len(actual)}")
    print(f"Register rows: {len(rows)}")
    print(f"Reading status: READ_FULL={counts['READ_FULL']}, READ_PARTIAL={counts['READ_PARTIAL']}")
    print(f"Missing files: {len(missing)}")
    print(f"Unregistered files: {len(unregistered)}")
    print(f"Duplicate register paths: {len(duplicates)}")
    print(f"Fingerprint errors: {len(hash_errors)}")
    print(f"Size errors: {len(size_errors)}")
    print(f"Invalid reading statuses: {len(status_errors)}")

    for label, items in (
        ("MISSING", missing),
        ("UNREGISTERED", unregistered),
        ("DUPLICATE", duplicates),
        ("HASH", hash_errors),
        ("SIZE", size_errors),
        ("STATUS", status_errors),
    ):
        for item in items[:20]:
            print(f"{label}: {item}")

    if missing or unregistered or duplicates or hash_errors or size_errors or status_errors:
        print("RESULT: FAIL — connected-project inventory/register mismatch.")
        return 1

    print("PARTIAL REVIEW ITEMS:")
    for rel, row in sorted(registered.items()):
        if row["read_status"].strip() == "READ_PARTIAL":
            print(f"- {rel}: {row['review_note']}")
    print("RESULT: PASS — connected-project inventory and fingerprints match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
