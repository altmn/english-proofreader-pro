#!/usr/bin/env python3
"""Record and validate manually graded, provenance-bound model evaluations.

This tool checks evaluation provenance and record structure. It does not grade
model responses or certify that a human's semantic verdict is correct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 1
SNAPSHOT_SUFFIX = "-snapshot.json"
VERDICTS = {"pass", "fail", "not_run"}


class EvaluationError(Exception):
    """A malformed, incomplete, or inconsistent evaluation artifact."""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json(text: str, label: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise EvaluationError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"{label} must be a JSON object")
    return value


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        text = read_bytes(path, label).decode("utf-8")
    except UnicodeError as exc:
        raise EvaluationError(f"cannot read {label} as UTF-8 JSON: {exc}") from exc
    return parse_json(text, label)


def read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvaluationError(f"cannot read {label}: {exc}") from exc


def read_text(path: Path, label: str) -> str:
    try:
        return read_bytes(path, label).decode("utf-8")
    except UnicodeError as exc:
        raise EvaluationError(f"cannot read {label} as UTF-8: {exc}") from exc


def unique_ids(items: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise EvaluationError(f"{label} must be a list")
    if not items:
        raise EvaluationError(f"{label} must not be empty")
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise EvaluationError(f"{label} entries must have non-empty string IDs")
        if item["id"] in indexed:
            raise EvaluationError(f"duplicate {label} ID: {item['id']}")
        indexed[item["id"]] = item
    return indexed


def canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def compose_prompt(runner_context: str, case_context: str, user_input: str) -> str:
    parts = [runner_context.strip()]
    if case_context.strip():
        parts.append(case_context.strip())
    parts.append(user_input)
    return "\n\n".join(parts)


def project_fixture_cases(fixture: dict[str, Any], runner_context: str) -> list[dict[str, Any]]:
    fixture_cases = unique_ids(fixture.get("cases"), "fixture case")
    projected = []
    for case_id, case in fixture_cases.items():
        user_input = case.get("input")
        context = case.get("context", "")
        expectation = case.get("expect")
        if not isinstance(user_input, str) or not user_input:
            raise EvaluationError(f"fixture {case_id} must have a non-empty input")
        if not isinstance(context, str) or not isinstance(expectation, dict) or not expectation:
            raise EvaluationError(f"fixture {case_id} must have string context and non-empty expectation")
        full_prompt = compose_prompt(runner_context, context, user_input)
        projected.append({
            "id": case_id,
            "input": user_input,
            "input_sha256": sha256(user_input),
            "context": context,
            "context_sha256": sha256(context),
            "expectation": expectation,
            "expectation_sha256": canonical_hash(expectation),
            "full_prompt": full_prompt,
            "full_prompt_sha256": sha256(full_prompt),
        })
    return projected


def read_current_sources() -> tuple[str, str, dict[str, Any]]:
    skill = read_text(ROOT / "skills/proofread/SKILL.md", "current skill")
    manifest_text = read_text(ROOT / "plugin.json", "current plugin manifest")
    manifest = parse_json(manifest_text, "current plugin manifest")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("version"), str):
        raise EvaluationError("current plugin manifest must contain a string version")
    return skill, manifest_text, manifest


def create_snapshot(args: argparse.Namespace) -> Path:
    trial_dir = ROOT / "tests/trials"
    trial_dir.mkdir(parents=True, exist_ok=True)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.id):
        raise EvaluationError("snapshot ID must be a lowercase slug of up to 64 characters")
    output = trial_dir / f"{args.id}{SNAPSHOT_SUFFIX}"
    if output.exists():
        raise EvaluationError(f"refusing to overwrite existing snapshot: {output.relative_to(ROOT)}")

    skill, manifest_text, manifest = read_current_sources()
    runner_context = read_text(Path(args.runner_context), "runner context")
    fixture_bytes = read_bytes(ROOT / "tests/cases.json", "evaluation fixtures")
    try:
        fixture_text = fixture_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise EvaluationError(f"cannot read evaluation fixtures as UTF-8: {exc}") from exc
    fixture = parse_json(fixture_text, "evaluation fixtures")
    saved_cases = project_fixture_cases(fixture, runner_context)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "kind": "evaluation-snapshot",
        "id": args.id,
        "created_at": now,
        "fixture_source": "tests/cases.json",
        "fixture_sha256": sha256_bytes(fixture_bytes),
        "fixture_text": fixture_text,
        "fixture_schema_version": fixture.get("schema_version"),
        "skill": {"path": "skills/proofread/SKILL.md", "text": skill, "sha256": sha256(skill), "unicode_character_count": len(skill)},
        "manifest": {"path": "plugin.json", "text": manifest_text, "version": manifest["version"], "sha256": sha256(manifest_text)},
        "runner_context": {"text": runner_context, "sha256": sha256(runner_context)},
        "cases": saved_cases,
    }
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output.relative_to(ROOT))
    return output


def validate_snapshot(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if snapshot.get("schema_version") != SCHEMA_VERSION or snapshot.get("kind") != "evaluation-snapshot":
        raise EvaluationError("unsupported snapshot schema or kind")
    skill = snapshot.get("skill")
    manifest = snapshot.get("manifest")
    context = snapshot.get("runner_context")
    for name, obj, text_key in (("skill", skill, "text"), ("manifest", manifest, "text"), ("runner context", context, "text")):
        if not isinstance(obj, dict) or not isinstance(obj.get(text_key), str) or obj.get("sha256") != sha256(obj[text_key]):
            raise EvaluationError(f"snapshot {name} text/hash mismatch")
    if skill.get("unicode_character_count") != len(skill["text"]):
        raise EvaluationError("snapshot skill Unicode character count mismatch")
    manifest_data = parse_json(manifest["text"], "snapshot plugin manifest")
    if not isinstance(manifest.get("version"), str) or manifest_data.get("version") != manifest["version"]:
        raise EvaluationError("snapshot manifest version does not match manifest text")
    if not isinstance(snapshot.get("fixture_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", snapshot["fixture_sha256"]):
        raise EvaluationError("snapshot fixture SHA-256 is missing or malformed")
    if "fixture_text" not in snapshot:
        # A pre-projection schema-1 snapshot can be verified only against the
        # exact current fixture bytes. It cannot prove its own historical cases.
        fixture_bytes = read_bytes(ROOT / "tests/cases.json", "current evaluation fixtures")
        if snapshot["fixture_sha256"] != sha256_bytes(fixture_bytes):
            raise EvaluationError("snapshot has no embedded fixture text and its fixture hash is not current; case projection cannot be verified")
        try:
            fixture_text = fixture_bytes.decode("utf-8")
        except UnicodeError as exc:
            raise EvaluationError(f"current evaluation fixtures are not UTF-8: {exc}") from exc
    else:
        fixture_text = snapshot["fixture_text"]
        if not isinstance(fixture_text, str) or sha256(fixture_text) != snapshot["fixture_sha256"]:
            raise EvaluationError("snapshot fixture text/hash mismatch")
    fixture = parse_json(fixture_text, "snapshot fixture")
    projected_cases = project_fixture_cases(fixture, context["text"])
    if snapshot.get("cases") != projected_cases:
        raise EvaluationError("snapshot case projection does not match its hashed fixture")
    case_map = unique_ids(snapshot.get("cases"), "snapshot case")
    for case_id, case in case_map.items():
        for value_key, hash_key in (("input", "input_sha256"), ("context", "context_sha256"), ("full_prompt", "full_prompt_sha256")):
            if not isinstance(case.get(value_key), str) or case.get(hash_key) != sha256(case[value_key]):
                raise EvaluationError(f"snapshot case {case_id} {value_key}/hash mismatch")
        expectation = case.get("expectation")
        if not isinstance(expectation, dict) or not expectation or case.get("expectation_sha256") != canonical_hash(expectation):
            raise EvaluationError(f"snapshot case {case_id} expectation/hash mismatch")
        expected_prompt = compose_prompt(context["text"], case["context"], case["input"])
        if case["full_prompt"] != expected_prompt:
            raise EvaluationError(f"snapshot case {case_id} full prompt mismatch")
    return case_map


def create_record(args: argparse.Namespace) -> Path:
    try:
        snapshot_path = Path(args.snapshot).resolve()
    except (OSError, TypeError, ValueError) as exc:
        raise EvaluationError(f"invalid snapshot path: {exc}") from exc
    snapshot = load_json(snapshot_path, "snapshot")
    snapshot_cases = validate_snapshot(snapshot)
    response_bundle = load_json(Path(args.responses), "response bundle")
    responses = unique_ids(response_bundle.get("responses"), "response")
    missing = sorted(snapshot_cases.keys() - responses.keys())
    extra = sorted(responses.keys() - snapshot_cases.keys())
    if missing or extra:
        raise EvaluationError(f"response IDs do not match snapshot (missing: {missing}; extra: {extra})")
    metadata = {
        "model": args.model,
        "host": args.host,
        "host_version": args.host_version,
        "invocation_mode": args.invocation_mode,
        "date": args.date,
        "source": args.source,
        "reviewer": args.reviewer,
        "reviewer_context": args.reviewer_context,
    }
    validate_metadata(metadata, args.install_method, args.build_sha256, snapshot)
    output = Path(args.out)
    if output.exists():
        raise EvaluationError(f"refusing to overwrite existing record: {output}")

    record_cases = []
    for case_id, source_case in snapshot_cases.items():
        answer = responses[case_id]
        if answer.get("prompt") != source_case["full_prompt"]:
            raise EvaluationError(f"response prompt does not match snapshot for case {case_id}")
        response = answer.get("response")
        if not isinstance(response, str):
            raise EvaluationError(f"response for {case_id} must be a string")
        assertions = [{"name": name, "expected": value, "status": "not_run", "note": ""}
                      for name, value in source_case["expectation"].items()]
        record_cases.append({
            "id": case_id,
            "prompt": source_case["full_prompt"],
            "context": source_case["context"],
            "expectation": source_case["expectation"],
            "expectation_sha256": source_case["expectation_sha256"],
            "response": response,
            "response_sha256": sha256(response),
            "assertions": assertions,
        })
    binding = {
        "skill_sha256": snapshot["skill"]["sha256"],
        "manifest_version": snapshot["manifest"]["version"],
        "manifest_sha256": snapshot["manifest"]["sha256"],
        "runner_context_sha256": snapshot["runner_context"]["sha256"],
    }
    record = {
        "schema_version": SCHEMA_VERSION,
        "kind": "evaluation-record",
        "snapshot_file": str(snapshot_path.relative_to(ROOT)) if snapshot_path.is_relative_to(ROOT) else str(snapshot_path),
        "snapshot_sha256": sha256_bytes(read_bytes(snapshot_path, "snapshot")),
        "source_binding": binding,
        "metadata": metadata,
        "host_evidence": {"install_method": args.install_method, "build_sha256": args.build_sha256},
        "cases": record_cases,
        "aggregate": aggregate(record_cases),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return output


def validate_metadata(metadata: Any, install_method: Any, build_sha256: Any, snapshot: dict[str, Any]) -> None:
    fields = ("model", "host", "host_version", "invocation_mode", "date", "source", "reviewer", "reviewer_context")
    if not isinstance(metadata, dict):
        raise EvaluationError("metadata must be an object")
    missing = [key for key in fields if not isinstance(metadata.get(key), str) or not metadata[key].strip()]
    if missing:
        raise EvaluationError(f"metadata must include non-empty fields: {', '.join(missing)}")
    try:
        run_date = date.fromisoformat(metadata["date"])
        snapshot_date = date.fromisoformat(snapshot["created_at"][:10])
    except (ValueError, TypeError, KeyError) as exc:
        raise EvaluationError("metadata date and snapshot creation date must be ISO dates") from exc
    if run_date < snapshot_date:
        raise EvaluationError("record date predates snapshot; historical evidence cannot be rebranded as a new run")
    try:
        if run_date > datetime.now(timezone.utc).date():
            raise EvaluationError("record date cannot be in the future")
    except TypeError:
        pass
    if metadata["invocation_mode"] == "intended-host":
        if metadata["host_version"].lower() == "unknown":
            raise EvaluationError("intended-host records require the actual host version")
        if not isinstance(install_method, str) or not install_method.strip():
            raise EvaluationError("intended-host records require install_method")
        if not isinstance(build_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", build_sha256):
            raise EvaluationError("intended-host records require the installed build SHA-256")
    elif metadata["host_version"].lower() == "unknown" and "simulation" not in metadata["invocation_mode"].lower():
        raise EvaluationError("unknown host version is allowed only for a simulation invocation")


def aggregate(cases: list[dict[str, Any]]) -> str:
    statuses = [assertion.get("status") for case in cases for assertion in case.get("assertions", [])]
    if not statuses:
        return "not_run"
    if "fail" in statuses:
        return "fail"
    if "not_run" in statuses:
        return "not_run"
    return "pass"


def validate_record(record_path: Path) -> str:
    record = load_json(record_path, "evaluation record")
    required = {"schema_version", "kind", "snapshot_file", "snapshot_sha256", "source_binding", "metadata", "host_evidence", "cases", "aggregate"}
    if set(record) != required:
        raise EvaluationError(f"record fields must be exactly: {', '.join(sorted(required))}")
    if record.get("schema_version") != SCHEMA_VERSION or record.get("kind") != "evaluation-record":
        raise EvaluationError("unsupported evaluation record schema or kind")
    if not isinstance(record["snapshot_file"], str) or not record["snapshot_file"]:
        raise EvaluationError("snapshot_file must be a path string")
    try:
        snapshot_path = Path(record["snapshot_file"])
    except (TypeError, ValueError) as exc:
        raise EvaluationError(f"invalid snapshot_file path: {exc}") from exc
    try:
        if not snapshot_path.is_absolute():
            snapshot_path = (ROOT / snapshot_path).resolve()
        else:
            snapshot_path = snapshot_path.resolve()
    except (OSError, TypeError, ValueError) as exc:
        raise EvaluationError(f"invalid snapshot_file path: {exc}") from exc
    snapshot_bytes = read_bytes(snapshot_path, "bound snapshot")
    try:
        snapshot_text = snapshot_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise EvaluationError(f"cannot read bound snapshot as UTF-8: {exc}") from exc
    if record["snapshot_sha256"] != sha256_bytes(snapshot_bytes):
        raise EvaluationError("record snapshot SHA-256 mismatch")
    snapshot = load_json(snapshot_path, "bound snapshot")
    snapshot_cases = validate_snapshot(snapshot)
    binding = record.get("source_binding")
    expected_binding = {
        "skill_sha256": snapshot["skill"]["sha256"],
        "manifest_version": snapshot["manifest"]["version"],
        "manifest_sha256": snapshot["manifest"]["sha256"],
        "runner_context_sha256": snapshot["runner_context"]["sha256"],
    }
    if binding != expected_binding:
        raise EvaluationError("record source binding does not match its snapshot")
    metadata = record.get("metadata")
    host_evidence = record.get("host_evidence")
    if not isinstance(host_evidence, dict) or set(host_evidence) != {"install_method", "build_sha256"}:
        raise EvaluationError("host_evidence must contain install_method and build_sha256 fields")
    validate_metadata(metadata, host_evidence["install_method"], host_evidence["build_sha256"], snapshot)
    record_cases = unique_ids(record.get("cases"), "record case")
    missing = sorted(snapshot_cases.keys() - record_cases.keys())
    extra = sorted(record_cases.keys() - snapshot_cases.keys())
    if missing or extra:
        raise EvaluationError(f"record case IDs do not match snapshot (missing: {missing}; extra: {extra})")

    for case_id, source_case in snapshot_cases.items():
        case = record_cases[case_id]
        if (case.get("prompt") != source_case["full_prompt"] or case.get("context") != source_case["context"]
                or case.get("expectation") != source_case["expectation"]
                or case.get("expectation_sha256") != source_case["expectation_sha256"]
                or not isinstance(case.get("response"), str)
                or case.get("response_sha256") != sha256(case["response"])):
            raise EvaluationError(f"record case {case_id} does not match its snapshot or response shape")
        assertions = case.get("assertions")
        if not isinstance(assertions, list):
            raise EvaluationError(f"record case {case_id} assertions must be a list")
        by_name: dict[str, dict[str, Any]] = {}
        for assertion in assertions:
            if not isinstance(assertion, dict) or set(assertion) != {"name", "expected", "status", "note"}:
                raise EvaluationError(f"record case {case_id} assertion has invalid shape")
            name = assertion["name"]
            if not isinstance(name, str) or name in by_name:
                raise EvaluationError(f"record case {case_id} has a missing or duplicate assertion name")
            if not isinstance(assertion["status"], str) or assertion["status"] not in VERDICTS:
                raise EvaluationError(f"record case {case_id} assertion {name} has invalid manual verdict")
            if assertion["status"] == "fail" and (not isinstance(assertion["note"], str) or not assertion["note"].strip()):
                raise EvaluationError(f"failed assertion {case_id}.{name} requires a gap note")
            if not isinstance(assertion["note"], str):
                raise EvaluationError(f"record case {case_id} assertion {name} note must be a string")
            by_name[name] = assertion
        expected = source_case["expectation"]
        if set(by_name) != set(expected):
            raise EvaluationError(f"record case {case_id} assertions do not match expectation keys")
        for name, expected_value in expected.items():
            if by_name[name]["expected"] != expected_value:
                raise EvaluationError(f"record case {case_id} assertion {name} expected value mismatch")

    derived_aggregate = aggregate(list(record_cases.values()))
    if record.get("aggregate") != derived_aggregate:
        raise EvaluationError("record aggregate does not match assertion statuses")
    current_skill, current_manifest_text, current_manifest = read_current_sources()
    current_cases_bytes = read_bytes(ROOT / "tests/cases.json", "current evaluation fixtures")
    current = (
        snapshot["skill"]["sha256"] == sha256(current_skill)
        and snapshot["manifest"]["sha256"] == sha256(current_manifest_text)
        and snapshot["manifest"]["version"] == current_manifest["version"]
        and snapshot["fixture_sha256"] == sha256_bytes(current_cases_bytes)
    )
    return "current" if current else "historical"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot_parser = subparsers.add_parser("snapshot", help="capture immutable inputs for a fresh run")
    snapshot_parser.add_argument("--id", required=True)
    snapshot_parser.add_argument("--runner-context", required=True)
    record_parser = subparsers.add_parser("record", help="bind response text to a snapshot and manual-grading template")
    record_parser.add_argument("--snapshot", required=True)
    record_parser.add_argument("--responses", required=True, help="JSON object containing responses with exact prompts")
    record_parser.add_argument("--model", required=True)
    record_parser.add_argument("--host", required=True)
    record_parser.add_argument("--host-version", required=True, help="use unknown only for a simulation")
    record_parser.add_argument("--invocation-mode", required=True, help="use intended-host for installed host acceptance")
    record_parser.add_argument("--date", required=True, help="run date in YYYY-MM-DD format")
    record_parser.add_argument("--source", required=True, help="invocation provenance description")
    record_parser.add_argument("--reviewer", required=True, help="person or role that manually grades the assertions")
    record_parser.add_argument("--reviewer-context", required=True, help="how the manual reviewer assessed the responses")
    record_parser.add_argument("--install-method", help="required for intended-host records")
    record_parser.add_argument("--build-sha256", help="installed build SHA-256, required for intended-host records")
    record_parser.add_argument("--out", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate hashes, provenance, coverage, and manual verdict structure")
    validate_parser.add_argument("record")
    validate_parser.add_argument("--require-current", action="store_true", help="fail if the bound skill, manifest, or fixture source changed; runner context remains frozen in the snapshot")
    validate_parser.add_argument("--require-complete", action="store_true", help="fail if any assertion remains not_run")
    validate_parser.add_argument("--require-pass", action="store_true", help="fail unless every assertion passed")
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            create_snapshot(args)
        elif args.command == "record":
            create_record(args)
        else:
            binding = validate_record(Path(args.record))
            record = load_json(Path(args.record), "evaluation record")
            status = record["aggregate"]
            if args.require_current and binding != "current":
                raise EvaluationError("record is bound to historical skill or manifest inputs")
            if args.require_complete and any(
                assertion["status"] == "not_run"
                for case in record["cases"]
                for assertion in case["assertions"]
            ):
                raise EvaluationError("record has assertions that have not been graded")
            if args.require_pass and status != "pass":
                raise EvaluationError(f"record aggregate is {status}, not pass")
            print(f"valid evaluation record ({binding} source binding); assertion aggregate: {status}; semantic verdicts are manual")
    except EvaluationError as exc:
        print(f"evaluation error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
