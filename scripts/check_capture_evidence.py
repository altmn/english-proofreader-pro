#!/usr/bin/env python3
"""Read-only portable audit of accepted CLI captures and their execution evidence.

The panel lists repository-relative {path, sha256} references for each plan,
host-collected events (plain JSONL or gzip), accepted JSON, runtime receipt, and
three graded records, plus run_id and the original absolute plan path. The
original paths identify recorded commands; this checker never executes or reads
the original host interpreter, helper, controller, or generator paths.

This trusts the original host event collector and its protected controller. It
checks integrity, observed helper execution, exact output, and source bindings;
it does not authenticate a collector, attest the recorded interpreter binary on
another OS, grade semantics, or certify native ChatGPT behavior.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any
import zlib

try:
    from . import capture_protocol as protocol, evaluate
except ImportError:  # Direct CLI invocation.
    import capture_protocol as protocol
    import evaluate


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ("tests/cases.json", "tests/changes-markdown-cases.json",
            "tests/fragment-calibration-cases.json")
# Explicit adapter for these reviewed fixtures. Every other case must begin
# with a measured text block; adding a no-block case requires an adapter review.
NO_REQUIRED_BLOCK = {
    "no-op-exact-response", "source-injection-is-inert", "missing-source-text",
    "starter-help", "direct-meta-question", "unrelated-conversation-negative",
    "fragment-labels-no-op",
}
RETAINED_RATIOS = {"about 5-10%": [0.90, 0.95], "about 30%": [0.70, 0.70],
                   "about 40%": [0.60, 0.60], "about 50-60%": [0.40, 0.50]}
SHA = re.compile(r"[0-9a-f]{64}\Z")
PLAN_FIELDS = {"schema_version", "kind", "challenge", "helper_path", "helper_sha256",
               "metrics_helper_path", "metrics_helper_sha256",
               "python_path", "python_sha256", "candidate_path", "accepted_path",
               "requirements", "requirements_sha256"}


class EvidenceError(Exception):
    """Missing, changed, unsafe, or inconsistent capture evidence."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise EvidenceError(reason)


def relative_path(value: Any) -> Path:
    require(isinstance(value, str) and bool(value) and len(value) <= 4096
            and "\\" not in value and "\0" not in value, "invalid evidence path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts
            and path.as_posix() == value and value != ".", "evidence paths must stay inside the repository")
    target = ROOT / value
    protocol.no_symlinks(target)
    require(target.resolve().is_relative_to(ROOT.resolve()), "evidence path escapes repository")
    return target


def absolute_origin(value: Any) -> Path:
    require(isinstance(value, str) and bool(value) and "\0" not in value
            and len(value) <= 4096, "invalid recorded host path")
    path = PurePosixPath(value)
    require(path.is_absolute() and ".." not in path.parts and path.as_posix() == value,
            "recorded host paths must be normalized absolute POSIX paths")
    return Path(value)


def read_ref(reference: Any, *, events: bool = False) -> tuple[Path, bytes]:
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"}
            and isinstance(reference["sha256"], str) and bool(SHA.fullmatch(reference["sha256"])),
            "evidence references need path and SHA-256")
    path = relative_path(reference["path"])
    data = protocol.read(path)
    require(protocol.digest(data) == reference["sha256"], f"evidence SHA-256 mismatch: {reference['path']}")
    if events and path.suffix == ".gz":
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                data = stream.read(protocol.MAX_BYTES + 1)
        except (OSError, EOFError, zlib.error) as exc:
            raise EvidenceError("invalid compressed event stream") from exc
        require(len(data) <= protocol.MAX_BYTES, "decompressed event stream exceeds limit")
    return path, data


def derive_requirements(snapshots: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Derive the full mechanical contract from all three frozen fixtures."""
    require(set(snapshots) == set(FIXTURES), "capture needs all three frozen fixture suites")
    result: dict[str, Any] = {"case_ids": [], "fenced_case_ids": [], "shortening": {}}
    for fixture in FIXTURES:
        snapshot = snapshots[fixture]
        for case in snapshot["cases"]:
            case_id, expectation = case["id"], case["expectation"]
            result["case_ids"].append(case_id)
            if case_id not in NO_REQUIRED_BLOCK:
                result["fenced_case_ids"].append(case_id)
            target = expectation.get("requested_reduction_target")
            if expectation.get("task") == "proofread_and_shorten_supplied_text":
                require(target in RETAINED_RATIOS, "unsupported frozen shortening target")
                user_input = case["input"]
                if "Source:\n" in user_input:
                    source = user_input.rsplit("Source:\n", 1)[1]
                else:
                    require(": " in user_input, "shortening source boundary is missing")
                    source = user_input.split(": ", 1)[1]
                require(bool(source), "shortening source is empty")
                result["shortening"][case_id] = {
                    "source": source, "retained_ratios": RETAINED_RATIOS[target][:]}
            else:
                require(target is None, "shortening target has an unsupported task")
    return protocol.requirements(result)


def portable_plan(plan: dict[str, Any], origin: Path) -> None:
    require(set(plan) == PLAN_FIELDS and type(plan.get("schema_version")) is int
            and plan["schema_version"] == 1 and plan.get("kind") == "cli-capture-plan",
            "unsupported capture plan")
    for key in ("challenge", "helper_sha256", "metrics_helper_sha256", "python_sha256", "requirements_sha256"):
        require(isinstance(plan.get(key), str) and bool(SHA.fullmatch(plan[key])),
                f"invalid plan identity: {key}")
    for key in ("helper_path", "metrics_helper_path", "python_path", "candidate_path", "accepted_path"):
        absolute_origin(plan.get(key))
    require(plan["helper_sha256"] == protocol.digest(protocol.read(protocol.HELPER)),
            "plan does not bind the current reviewed measurement helper")
    req = protocol.requirements(plan["requirements"])
    require(protocol.digest(protocol.canonical(req)) == plan["requirements_sha256"],
            "plan requirements identity changed")
    protocol.outside_generator(origin, Path(plan["candidate_path"]))
    protocol.outside_generator(Path(plan["accepted_path"]), Path(plan["candidate_path"]))
    require(origin != Path(plan["accepted_path"]), "plan and accepted output must be distinct")


def bound_records(references: Any, run_id: str) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, Any]]:
    require(isinstance(references, list) and len(references) == 3, "capture needs exactly three graded records")
    snapshots: dict[str, dict[str, Any]] = {}
    responses: dict[str, str] = {}
    binding: dict[str, Any] | None = None
    profile: dict[str, str] | None = None
    paths: set[Path] = set()
    for reference in references:
        path, record_bytes = read_ref(reference)
        require(path not in paths, "duplicate record path")
        paths.add(path)
        record = protocol.parse(record_bytes)
        # Check every path and bound byte container before the existing validator
        # follows its snapshot/fixture references. Stable checkout inputs are assumed.
        snapshot_path = relative_path(record.get("snapshot_file"))
        snapshot_bytes = protocol.read(snapshot_path)
        require(protocol.digest(snapshot_bytes) == record.get("snapshot_sha256"), "record snapshot SHA-256 mismatch")
        snapshot = protocol.parse(snapshot_bytes)
        fixture = snapshot.get("fixture_source")
        require(fixture in FIXTURES and fixture not in snapshots, "duplicate or unsupported fixture suite")
        protocol.read(relative_path(fixture))
        evaluate.validate_snapshot(snapshot)
        state = evaluate.validate_record(path)
        evaluate.check_requirements(record, state, require_current=True, require_complete=True, require_pass=True)
        require(record.get("schema_version") == evaluate.RECORD_SCHEMA_VERSION,
                "execution evidence requires structured current records")
        metadata = record["metadata"]
        require(metadata["run_id"] == run_id, "record run ID differs from capture")
        require(metadata["invocation_mode"] == "independent-agent-simulation"
                and metadata["host"] == "Codex CLI", "records must declare the CLI simulation surface")
        current_profile = {key: metadata[key] for key in ("model", "reasoning_effort", "host", "host_version", "invocation_mode")}
        if binding is not None:
            require(record["source_binding"] == binding and current_profile == profile,
                    "capture records disagree on source or execution profile")
        binding, profile = record["source_binding"], current_profile
        for case in record["cases"]:
            require(case["id"] not in responses, "duplicate case ID across fixture suites")
            responses[case["id"]] = case["response"]
        snapshots[fixture] = snapshot
    assert binding is not None and profile is not None
    return snapshots, responses, {"binding": binding, "profile": profile}


def check_panel(panel_path: Path) -> dict[str, Any]:
    if panel_path.is_absolute():
        try:
            panel_path = panel_path.relative_to(ROOT)
        except ValueError as exc:
            raise EvidenceError("panel must stay inside the repository") from exc
    panel = protocol.parse(protocol.read(relative_path(panel_path.as_posix())))
    require(set(panel) == {"schema_version", "kind", "captures"}
            and type(panel.get("schema_version")) is int and panel["schema_version"] == 1
            and panel.get("kind") == "executed-capture-panel", "unsupported execution panel")
    captures = panel["captures"]
    require(isinstance(captures, list) and 3 <= len(captures) <= 16,
            "execution panel requires 3 to 16 distinct captures")
    # Existing validators read these current source files; bound them before reuse.
    for source in ("skills/proofreader-pro/SKILL.md", "plugin.json"):
        protocol.read(relative_path(source))
    run_ids: set[str] = set()
    challenges: set[str] = set()
    thread_ids: set[str] = set()
    common_identity = None
    checked = []
    fields = {"run_id", "original_plan_path", "plan", "events", "accepted", "receipt", "records"}
    for capture in captures:
        require(isinstance(capture, dict) and set(capture) == fields, "invalid capture fields")
        run_id = capture["run_id"]
        require(isinstance(run_id, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", run_id))
                and run_id not in run_ids, "missing or duplicate capture run ID")
        origin = absolute_origin(capture["original_plan_path"])
        _, plan_bytes = read_ref(capture["plan"])
        plan = protocol.parse(plan_bytes)
        portable_plan(plan, origin)
        require(plan["challenge"] not in challenges, "duplicate capture challenge")
        snapshots, responses, identity = bound_records(capture["records"], run_id)
        resource_path = relative_path(evaluate.RESOURCE_PATHS[0])
        resource_sha = protocol.digest(protocol.read(resource_path))
        require(plan["metrics_helper_sha256"] == resource_sha
                and identity["binding"]["resources"] == {evaluate.RESOURCE_PATHS[0]: resource_sha},
                "plan does not bind the current production metrics resource")
        if common_identity is not None:
            require(identity == common_identity, "panel source or execution profile differs between captures")
        common_identity = identity
        expected = derive_requirements(snapshots)
        actual = plan["requirements"]
        require(set(actual["case_ids"]) == set(expected["case_ids"])
                and set(actual["fenced_case_ids"]) == set(expected["fenced_case_ids"])
                and protocol.canonical(actual["shortening"]) == protocol.canonical(expected["shortening"]),
                "plan omits or changes frozen case, fence, source, or shortening requirements")
        _, event_bytes = read_ref(capture["events"], events=True)
        _, accepted = read_ref(capture["accepted"])
        _, receipt_bytes = read_ref(capture["receipt"])
        # The independent recount inside verify_events checks identity only;
        # matching actual source/final command events remain mandatory.
        # Only the reviewed current on-disk helper may be loaded. The old host
        # origin path and embedded historical resource text remain inert data.
        metrics_measure = protocol.load_metrics(plan, path=resource_path)
        verified = protocol.verify_events(plan, origin, protocol.digest(plan_bytes), event_bytes, accepted,
                                          metrics_measure=metrics_measure)
        receipt = protocol.parse(receipt_bytes)
        expected_receipt = {"kind": "cli-capture-protocol-result", "plan_sha256": protocol.digest(plan_bytes),
                            "outcome": "passed", "accepted_path": plan["accepted_path"],
                            **verified, "reason": None}
        require(protocol.canonical(receipt) == protocol.canonical(expected_receipt), "runtime acceptance receipt differs from verified evidence")
        bundle = protocol.parse(accepted)
        accepted_responses = {row["id"]: row["response"] for row in bundle["responses"]}
        require(accepted_responses == responses, "graded record responses differ from exact accepted output")
        thread_id = verified["thread_id"]
        require(isinstance(thread_id, str) and bool(thread_id) and thread_id not in thread_ids,
                "missing or duplicate captured CLI thread ID")
        run_ids.add(run_id)
        challenges.add(plan["challenge"])
        thread_ids.add(thread_id)
        checked.append({"run_id": run_id, "cases": len(responses), "candidate_sha256": verified["candidate_sha256"],
                        "events_sha256": verified["events_sha256"]})
    return {"kind": "executed-capture-panel-check", "outcome": "passed", "captures": checked,
            "limits": "Trusts protected original host collection; checks recorded execution and exact output, not semantic truth, binary attestation on this OS, or native behavior."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel", type=Path, help="repository-relative execution panel JSON")
    args = parser.parse_args(argv)
    try:
        result = check_panel(args.panel)
    except (EvidenceError, protocol.ProtocolError, evaluate.EvaluationError, OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"outcome": "failed", "reason": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
