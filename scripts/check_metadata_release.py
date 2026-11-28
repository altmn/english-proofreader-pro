#!/usr/bin/env python3
"""Check a reviewed metadata-only release against unchanged baseline behavior.

This does not turn old captures into current evidence. It checks the candidate
separately, then runs the unmodified strict validators in an isolated baseline
checkout. Only version and publication release_notes may differ. The receipt is
reviewed repository data, not proof of a remote release or native acceptance.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

try:
    from . import capture_protocol as protocol, check_capture_evidence as evidence, evaluate, release
except ImportError:
    import capture_protocol as protocol
    import check_capture_evidence as evidence
    import evaluate
    import release

ROOT = Path(__file__).resolve().parent.parent
RECEIPT_FIELDS = {"schema_version", "kind", "version", "baseline_version", "baseline_commit",
                  "baseline_archive_sha256", "baseline_release_url", "baseline_snapshot", "baseline_panel", "baseline_runtime_sha256"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_ref(root: Path, reference: Any) -> tuple[Path, bytes]:
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}, "invalid baseline reference")
    value = reference["path"]
    require(isinstance(value, str) and value and "\\" not in value, "invalid baseline path")
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == value,
            "baseline paths must stay inside the repository")
    data = protocol.read(root / path)
    require(protocol.digest(data) == reference["sha256"], "baseline reference SHA-256 mismatch")
    return path, data


def verify_manifest(candidate: dict[str, Any], baseline: dict[str, Any], version: str) -> None:
    """Keep every effective manifest value except the two named metadata fields."""
    versions = (baseline.get("version"), version)
    require(all(isinstance(v, str) and re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", v)
                for v in versions), "metadata-only receipt requires stable semantic versions")
    require(tuple(map(int, version.split("."))) > tuple(map(int, versions[0].split("."))),
            "metadata-only version must increase")
    require(candidate.get("version") == version, "candidate version differs from the reviewed receipt")
    normalized = copy.deepcopy(candidate)
    normalized["version"] = baseline["version"]
    publication = normalized["extensions"]["com.openai"]["publication"]
    require(isinstance(publication.get("release_notes"), str) and publication["release_notes"].strip(),
            "candidate release notes must be nonblank")
    publication["release_notes"] = baseline["extensions"]["com.openai"]["publication"]["release_notes"]
    require(protocol.canonical(normalized) == protocol.canonical(baseline),
            "metadata-only release changes other manifest configuration")


def verify_candidate(root: Path, receipt: dict[str, Any]) -> tuple[bytes, Path]:
    require(set(receipt) == RECEIPT_FIELDS and type(receipt["schema_version"]) is int
            and receipt["schema_version"] == 1 and receipt["kind"] == "metadata-only-release",
            "invalid metadata-only receipt")
    require(isinstance(receipt["baseline_commit"], str)
            and re.fullmatch(r"[0-9a-f]{40}", receipt["baseline_commit"]) is not None,
            "invalid baseline commit identity")
    require(isinstance(receipt["baseline_archive_sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", receipt["baseline_archive_sha256"]) is not None,
            "invalid baseline archive identity")
    require(receipt["baseline_release_url"] ==
            "https://github.com/altmn/english-proofreader-pro/releases/tag/v" + receipt["baseline_version"],
            "invalid baseline release URL")
    _, snapshot_bytes = read_ref(root, receipt["baseline_snapshot"])
    snapshot = protocol.parse(snapshot_bytes)
    evaluate.validate_snapshot(snapshot)
    baseline_bytes = snapshot["manifest"]["text"].encode("utf-8")
    baseline = protocol.parse(baseline_bytes)
    require(baseline["version"] == receipt["baseline_version"], "baseline version mismatch")
    hashes = receipt["baseline_runtime_sha256"]
    require(isinstance(hashes, dict) and set(hashes) == set(release.RUNTIME_FILES), "incomplete baseline runtime inventory")
    for path, expected in hashes.items():
        require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
                "invalid baseline runtime digest")
        data = baseline_bytes if path == "plugin.json" else protocol.read(root / path)
        require(protocol.digest(data) == expected, f"runtime differs from the baseline: {path}")
    candidate = protocol.parse(protocol.read(root / "plugin.json"))
    verify_manifest(candidate, baseline, receipt["version"])
    panel, _ = read_ref(root, receipt["baseline_panel"])
    return baseline_bytes, panel


def check_release(root: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    baseline_bytes, panel_path = verify_candidate(root, receipt)
    # Never overwrite the actual candidate or retained evidence. Symlinks are
    # rejected before copying so isolation cannot silently change their meaning.
    with tempfile.TemporaryDirectory(dir=str(Path(tempfile.gettempdir()).resolve())) as temp:
        baseline_root = Path(temp)
        for directory in ("scripts", "tests", "skills", "assets"):
            source = root / directory
            for path in (source, *source.rglob("*")):
                require(not path.is_symlink(), "baseline-copy inputs cannot be symbolic links")
            shutil.copytree(source, baseline_root / directory, ignore=shutil.ignore_patterns("__pycache__"))
        for path in ("LICENSE", "PRIVACY.md"):
            shutil.copyfile(root / path, baseline_root / path)
        (baseline_root / "plugin.json").write_bytes(baseline_bytes)
        panel = protocol.parse(protocol.read(baseline_root / panel_path))
        grouped: dict[str, list[str]] = {fixture: [] for fixture in evidence.FIXTURES}
        for capture in panel["captures"]:
            for reference in capture["records"]:
                _, record_bytes = read_ref(baseline_root, reference)
                record = protocol.parse(record_bytes)
                _, snapshot_bytes = read_ref(baseline_root, {
                    "path": record["snapshot_file"], "sha256": record["snapshot_sha256"]})
                snapshot = protocol.parse(snapshot_bytes)
                grouped[snapshot["fixture_source"]].append(reference["path"])
        commands = [
            [sys.executable, "scripts/evaluate.py", "validate-suite", *records,
             "--fixtures", fixture, "--model", "gpt-6.1-sol", "--reasoning-effort", "high",
             "--invocation-mode", "independent-agent-simulation", "--min-runs", "3",
             "--require-current", "--require-complete", "--require-pass"]
            for fixture, records in grouped.items()
        ]
        commands.append([sys.executable, "scripts/check_capture_evidence.py", panel_path.as_posix()])
        for command in commands:
            result = subprocess.run(command, cwd=baseline_root, capture_output=True, text=True, check=False)
            require(result.returncode == 0, "baseline evidence validation failed: " + result.stdout + result.stderr)
    return {"kind": "metadata-only-release-check", "outcome": "passed", "version": receipt["version"],
            "baseline_version": receipt["baseline_version"], "baseline_commit": receipt["baseline_commit"],
            "baseline_archive_sha256": receipt["baseline_archive_sha256"],
            "limits": "Unchanged runtime checked against retained baseline captures; no new model runs or native acceptance. Strict current-source validators remain unchanged."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        result = check_release(ROOT, protocol.parse(protocol.read(args.receipt)))
    except (ValueError, OSError, KeyError, TypeError, evaluate.EvaluationError, protocol.ProtocolError) as exc:
        print(json.dumps({"outcome": "failed", "reason": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
