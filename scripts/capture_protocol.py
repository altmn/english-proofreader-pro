#!/usr/bin/env python3
"""Gate CLI simulation captures on observed execution of exact measurement commands.

Controller: prepare a NEW plan outside the generator's writable directory, then
collect the host-owned JSONL event stream and run verify after the CLI finishes.
Generator: run the two commands printed by prepare, with the final command after
writing candidate.json. Only the controller may promote it to accepted output.

Requirements JSON contains case_ids, fenced_case_ids, and shortening, for example:
{"case_ids":["edit"],"fenced_case_ids":["edit"],"shortening":{
 "edit":{"source":"The literal source.","retained_ratios":[0.7,0.7]}}}
Sources/requirements come from the controller's frozen fixtures, never a generator.

This trusts the host event collector, reviewed interpreter/helper, a read-only plan
and stable local files. The challenge prevents stale-run reuse; it is not a secret
or signature. This is neither an OS sandbox nor universal execution attestation,
and ordering tool events does not prove when hidden composition occurred. A
controller's later recount is deliberately not accepted as generator execution.
Only the reviewed local production metrics resource is loaded as code; candidate
and fixture strings stay inert data. No network, models, installation, or
subprocesses occur here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import secrets
import shlex
import stat
import sys
import types
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

MAX_BYTES = 16 * 1024 * 1024
HELPER = Path(__file__).resolve()
METRICS_HELPER = HELPER.parent.parent / "skills/proofreader-pro/scripts/text_metrics.py"
SHELLS = {"/bin/sh", "/bin/bash", "/bin/zsh", "/opt/homebrew/bin/zsh"}


class ProtocolError(Exception):
    """Invalid input, missing execution evidence, or an output conflict."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def parse(data: bytes) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def finite(value: str) -> Any:
        raise ValueError("nonfinite JSON number")

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                           parse_constant=finite)
        canonical(value)  # Also refuses exponent overflow such as 1e999.
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("invalid or nonfinite UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ProtocolError("JSON must be an object")
    return value


def no_symlinks(path: Path) -> None:
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ProtocolError("symbolic links are not protocol inputs or outputs")


def read(path: Path) -> bytes:
    no_symlinks(path)
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            raise ProtocolError("protocol input must be a regular file")
        with path.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ProtocolError(f"cannot read protocol input: {path.name}") from exc
    if len(data) > MAX_BYTES:
        raise ProtocolError("protocol input exceeds 16 MiB")
    return data


def write_new(path: Path, data: bytes) -> None:
    no_symlinks(path)
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except OSError as exc:
        raise ProtocolError(f"cannot exclusively create output: {path.name}") from exc


def ids(value: Any) -> list[str]:
    if (not isinstance(value, list) or len(value) > 128
            or any(not isinstance(x, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,127}", x) for x in value)
            or len(set(value)) != len(value)):
        raise ProtocolError("case IDs must be a unique bounded list of identifiers")
    return value


def requirements(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"case_ids", "fenced_case_ids", "shortening"}:
        raise ProtocolError("requirements need case_ids, fenced_case_ids and shortening")
    cases, fenced = ids(value["case_ids"]), ids(value["fenced_case_ids"])
    shortened = value["shortening"]
    if not cases or not set(fenced) <= set(cases) or not isinstance(shortened, dict):
        raise ProtocolError("empty or inconsistent case requirements")
    if not set(shortened) <= set(fenced):
        raise ProtocolError("shortening cases require a leading text block")
    for row in shortened.values():
        if not isinstance(row, dict) or set(row) != {"source", "retained_ratios"} or not isinstance(row["source"], str):
            raise ProtocolError("invalid shortening source")
        ratios = row["retained_ratios"]
        if (not isinstance(ratios, list) or len(ratios) != 2
                or any(type(x) not in (int, float) or not math.isfinite(x) or not 0 < x <= 1 for x in ratios)
                or ratios[0] > ratios[1]):
            raise ProtocolError("invalid retained-word ratios")
    return value


def outside_generator(path: Path, candidate: Path) -> None:
    if path == candidate or path.is_relative_to(candidate.parent):
        raise ProtocolError("controller files must stay outside the generator directory")


def prepare(requirements_path: Path, candidate: Path, plan_path: Path,
            accepted: Path) -> dict[str, Any]:
    # Resolve caller-selected roots once; subsequent reads reject new symlinks.
    if any(p.is_symlink() for p in (requirements_path, candidate, plan_path, accepted)):
        raise ProtocolError("symbolic links are not protocol inputs or outputs")
    candidate, plan_path, accepted = (p.resolve() for p in (candidate, plan_path, accepted))
    outside_generator(plan_path, candidate)
    outside_generator(accepted, candidate)
    if plan_path == accepted or any(p.exists() for p in (plan_path, accepted, candidate)):
        raise ProtocolError("prepare requires new plan, candidate and accepted paths")
    req = requirements(parse(read(requirements_path.resolve())))
    metrics_path = METRICS_HELPER
    metrics_hash = digest(read(metrics_path))
    interpreter = Path(sys.executable).resolve()
    plan = {"schema_version": 1, "kind": "cli-capture-plan", "challenge": secrets.token_hex(32),
            "helper_path": str(HELPER), "helper_sha256": digest(read(HELPER)),
            "metrics_helper_path": str(metrics_path), "metrics_helper_sha256": metrics_hash,
            "python_path": str(interpreter), "python_sha256": digest(read(interpreter)),
            "candidate_path": str(candidate), "accepted_path": str(accepted),
            "requirements": req, "requirements_sha256": digest(canonical(req))}
    write_new(plan_path, canonical(plan) + b"\n")
    return {"plan": str(plan_path), "commands": {
        phase: shlex.join(command(plan, plan_path, phase)) for phase in ("source", "final")}}


def load_plan(path: Path) -> tuple[dict[str, Any], str]:
    data = read(path)
    plan = parse(data)
    if (plan.get("schema_version") != 1 or plan.get("kind") != "cli-capture-plan"
            or not isinstance(plan.get("challenge"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", plan["challenge"])):
        raise ProtocolError("invalid protocol plan")
    req = requirements(plan.get("requirements", {}))
    if digest(canonical(req)) != plan.get("requirements_sha256"):
        raise ProtocolError("requirements identity changed")
    if plan.get("helper_path") != str(HELPER) or digest(read(HELPER)) != plan.get("helper_sha256"):
        raise ProtocolError("measurement helper identity changed")
    metrics_path = Path(plan.get("metrics_helper_path", ""))
    if (metrics_path != METRICS_HELPER
            or digest(read(metrics_path)) != plan.get("metrics_helper_sha256")):
        raise ProtocolError("production metrics helper identity changed")
    python = Path(plan.get("python_path", ""))
    if not python.is_absolute() or digest(read(python)) != plan.get("python_sha256"):
        raise ProtocolError("measurement interpreter identity changed")
    for field in ("candidate_path", "accepted_path"):
        if not isinstance(plan.get(field), str) or not Path(plan[field]).is_absolute():
            raise ProtocolError("plan paths must be absolute")
    outside_generator(path, Path(plan["candidate_path"]))
    outside_generator(Path(plan["accepted_path"]), Path(plan["candidate_path"]))
    return plan, digest(data)


def command(plan: dict[str, Any], plan_path: Path, phase: str) -> list[str]:
    return [plan["python_path"], "-I", "-B", plan["helper_path"], "measure",
            "--plan", str(plan_path), "--phase", phase]


def load_metrics(plan: dict[str, Any], path: Path | None = None) -> Callable[[dict], dict]:
    """Load only an explicit reviewed local resource, never snapshot text.

    The offline checker supplies its trusted current resource path. A historical
    origin path is inert metadata there; changed/current code cannot replay as
    the old resource identity. Compile the exact bytes already checked, avoiding
    an import loader's second read after hashing.
    """
    path = path or METRICS_HELPER
    if not path.is_absolute():
        raise ProtocolError("production metrics helper path is missing")
    data = read(path)
    if digest(data) != plan.get("metrics_helper_sha256"):
        raise ProtocolError("production metrics helper identity changed")
    module = types.ModuleType("proofreader_verified_text_metrics")
    module.__file__ = str(path)
    exec(compile(data, str(path), "exec"), module.__dict__)
    if not callable(getattr(module, "measure", None)):
        raise ProtocolError("production metrics helper has no measure API")
    return module.measure


def metrics_request(row: dict[str, Any], candidate: str | None = None) -> dict[str, Any]:
    # Convert retained ratios to the production API's percent units. Budget
    # rounding and every text metric belong to that API, not this controller.
    request = {"text": row["source"], "remaining_percent": [
        float(Decimal(str(ratio)) * 100) for ratio in row["retained_ratios"]]}
    if candidate is not None:
        request["candidate"] = candidate
    return request


def source_counts(req: dict[str, Any], metrics_measure: Callable[[dict], dict]) -> list[dict[str, Any]]:
    result = []
    for case_id, row in req["shortening"].items():
        measured = metrics_measure(metrics_request(row))
        budget = measured["budget"]
        result.append({"id": case_id, "source_sha256": digest(row["source"].encode()),
                       "source_words": measured["metrics"]["words"],
                       "budget_words": [budget["min_words"], budget["max_words"]]})
    return result


def blocks(response: str, metrics_measure: Callable[[dict], dict]) -> list[dict[str, Any]]:
    result, offset = [], 0
    while match := re.search(r"(?m)^(`{3,})text\n", response[offset:]):
        start, payload_start = offset + match.start(), offset + match.end()
        marker = match[1]
        close = re.search(r"(?m)^" + re.escape(marker) + r"(?:\n|\Z)", response[payload_start:])
        if close is None:
            raise ProtocolError("unclosed text block")
        payload_end = payload_start + close.start()
        framed_payload = response[payload_start:payload_end]
        # A compact empty fenced block has no payload or separator bytes. The
        # production helper always appends one separate wrapper LF, even when
        # the exact payload is empty or already ends in LF/CR/CRLF. Remove only
        # that LF; stripping or splitlines() would corrupt literal payloads.
        if framed_payload and not framed_payload.endswith("\n"):
            raise ProtocolError("text block needs a closing line")
        payload = framed_payload[:-1] if framed_payload else ""
        metrics = metrics_measure({"text": payload})["metrics"]
        if len(marker) != metrics["fence_length"]:
            raise ProtocolError("text block fence is not the computed safe marker")
        result.append({"start": start, "payload": payload,
                       "longest_backtick_run": metrics["longest_backtick_run"],
                       "fence_length": len(marker), "payload_sha256": digest(payload.encode())})
        offset = payload_start + close.end()
    return result


def measurement(plan: dict[str, Any], plan_hash: str, phase: str,
                candidate_bytes: bytes | None = None, *,
                metrics_measure: Callable[[dict], dict] | None = None) -> dict[str, Any]:
    req = plan["requirements"]
    metrics_measure = metrics_measure or load_metrics(plan)
    conventions = metrics_measure({"text": ""})["conventions"]
    result = {"kind": "cli-capture-measurement", "phase": phase, "challenge": plan["challenge"],
              "plan_sha256": plan_hash, "helper_sha256": plan["helper_sha256"],
              "metrics_helper_path": plan["metrics_helper_path"],
              "metrics_helper_sha256": plan["metrics_helper_sha256"],
              "requirements_sha256": plan["requirements_sha256"],
              "source_counts": source_counts(req, metrics_measure),
              "word_convention": conventions["words"], "budget_convention": conventions["budgets"]}
    if phase == "source":
        return result
    if phase != "final" or candidate_bytes is None:
        raise ProtocolError("final measurement requires candidate bytes")
    capture = parse(candidate_bytes)
    if set(capture) != {"responses"} or not isinstance(capture["responses"], list):
        raise ProtocolError("candidate needs a responses array")
    rows = capture["responses"]
    if any(not isinstance(x, dict) or set(x) != {"id", "response"} for x in rows):
        raise ProtocolError("candidate responses need id and response only")
    actual_ids = ids([x["id"] for x in rows])
    if set(actual_ids) != set(req["case_ids"]):
        raise ProtocolError("candidate case coverage differs from plan")
    measurements = []
    counts = {x["id"]: x for x in result["source_counts"]}
    for row in rows:
        case_id, response = row["id"], row["response"]
        if not isinstance(response, str) or not response:
            raise ProtocolError("candidate responses must be nonempty text")
        parsed = blocks(response, metrics_measure)
        if case_id in req["fenced_case_ids"] and (not parsed or parsed[0]["start"] != 0):
            raise ProtocolError("required leading text block is missing")
        item = {"id": case_id, "response_sha256": digest(response.encode()),
                "blocks": [{k: v for k, v in block.items() if k != "payload"} for block in parsed]}
        if case_id in counts:
            compared = metrics_measure(metrics_request(req["shortening"][case_id],
                                                       parsed[0]["payload"]))["comparison"]
            item.update(source_words=compared["source_words"], final_words=compared["candidate_words"],
                        reduction=compared["reduction"], within_budget=compared["within_budget"])
            if not item["within_budget"]:
                raise ProtocolError("shortened result is outside the frozen whole-word budget")
        measurements.append(item)
    result.update(candidate_sha256=digest(candidate_bytes), responses=measurements)
    return result


def command_matches(text: Any, expected: list[str]) -> bool:
    if not isinstance(text, str):
        return False
    try:
        argv = shlex.split(text)
        if len(argv) == 3 and argv[0] in SHELLS and argv[1] in ("-c", "-lc"):
            text = argv[2]
        # shlex.split alone is not shell validation: an unquoted $VAR or ; in
        # a path can retain the same lexical token while changing execution.
        # Require the exact safely quoted command printed by prepare.
        return text.strip() == shlex.join(expected)
    except ValueError:
        return False


def verify_events(plan: dict[str, Any], plan_path: Path, plan_hash: str,
                  event_bytes: bytes, candidate_bytes: bytes, *,
                  metrics_measure: Callable[[dict], dict] | None = None) -> dict[str, Any]:
    metrics_measure = metrics_measure or load_metrics(plan)
    events = [parse(line) for line in event_bytes.splitlines() if line.strip()]
    if (sum(x.get("type") == "thread.started" for x in events) != 1
            or sum(x.get("type") == "turn.started" for x in events) != 1
            or sum(x.get("type") == "turn.completed" for x in events) != 1
            or any(x.get("type") in ("error", "turn.failed") for x in events)):
        raise ProtocolError("one completed CLI turn without error is required")
    matches = {}
    for phase in ("source", "final"):
        expected = command(plan, plan_path, phase)
        found = [(n, x) for n, x in enumerate(events)
                 if x.get("type") in ("item.started", "item.completed")
                 and isinstance(x.get("item"), dict)
                 and x["item"].get("type") == "command_execution"
                 and command_matches(x["item"].get("command"), expected)]
        if len(found) != 2 or [x[1]["type"] for x in found] != ["item.started", "item.completed"]:
            raise ProtocolError(f"one observed started/completed {phase} command is required")
        (start, first), (end, last) = found
        item = last["item"]
        if (not isinstance(item.get("id"), str) or first["item"].get("id") != item["id"]
                or item.get("status") != "completed" or type(item.get("exit_code")) is not int
                or item["exit_code"] != 0):
            raise ProtocolError(f"{phase} command did not complete successfully")
        stdout = item.get("aggregated_output")
        if not isinstance(stdout, str):
            raise ProtocolError("command stdout is missing")
        observed = parse(stdout.encode())
        expected_result = measurement(plan, plan_hash, phase, candidate_bytes if phase == "final" else None,
                                      metrics_measure=metrics_measure)
        if canonical(observed) != canonical(expected_result):
            raise ProtocolError(f"{phase} stdout differs from exact candidate measurements")
        matches[phase] = {"start": start, "end": end, "item_id": item["id"],
                          "measurement_sha256": digest(canonical(observed))}
    completed = next(n for n, x in enumerate(events) if x.get("type") == "turn.completed")
    started = next(n for n, x in enumerate(events) if x.get("type") == "turn.started")
    thread_started = next(n for n, x in enumerate(events) if x.get("type") == "thread.started")
    if (matches["source"]["item_id"] == matches["final"]["item_id"]
            or not (thread_started < started < matches["source"]["start"] < matches["source"]["end"]
                    < matches["final"]["start"] < matches["final"]["end"] < completed)):
        raise ProtocolError("source, final measurement and completion events are out of order")
    return {"matching_events": matches, "candidate_sha256": digest(candidate_bytes),
            "events_sha256": digest(event_bytes), "thread_id": next(x.get("thread_id") for x in events if x.get("type") == "thread.started")}


def verify(plan_path: Path, events_path: Path, receipt_path: Path) -> dict[str, Any]:
    plan, plan_hash = load_plan(plan_path)
    candidate, accepted = Path(plan["candidate_path"]), Path(plan["accepted_path"])
    outside_generator(events_path, candidate)
    outside_generator(receipt_path, candidate)
    if accepted == receipt_path or accepted.exists() or receipt_path.exists():
        raise ProtocolError("accepted output and receipt must be new distinct controller files")
    receipt: dict[str, Any] = {"kind": "cli-capture-protocol-result", "plan_sha256": plan_hash,
                               "outcome": "failed", "accepted_path": None}
    try:
        data, event_bytes = read(candidate), read(events_path)
        receipt.update(verify_events(plan, plan_path, plan_hash, event_bytes, data))
        if load_plan(plan_path)[1] != plan_hash:
            raise ProtocolError("plan changed before acceptance")
    except ProtocolError as exc:
        receipt["reason"] = str(exc)
    else:
        write_new(accepted, data)
        receipt.update(outcome="passed", accepted_path=str(accepted), reason=None)
    write_new(receipt_path, canonical(receipt) + b"\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare", help="freeze requirements and fresh challenge outside the generator directory")
    for flag in ("requirements", "candidate", "plan", "accepted"):
        prep.add_argument("--" + flag, type=Path, required=True)
    measure = sub.add_parser("measure", help="generator executes this exact command; JSON stdout is the evidence")
    measure.add_argument("--plan", type=Path, required=True)
    measure.add_argument("--phase", choices=("source", "final"), required=True)
    check = sub.add_parser("verify", help="controller gates acceptance on the completed host-owned event stream")
    for flag in ("plan", "events", "receipt"):
        check.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "prepare":
            result = prepare(args.requirements, args.candidate, args.plan, args.accepted)
        elif args.action == "measure":
            plan, plan_hash = load_plan(args.plan)
            if str(Path(sys.executable).resolve()) != plan["python_path"]:
                raise ProtocolError("measure must use the frozen interpreter")
            result = measurement(plan, plan_hash, args.phase,
                                 read(Path(plan["candidate_path"])) if args.phase == "final" else None)
        else:
            if any(p.is_symlink() for p in (args.plan, args.events, args.receipt)):
                raise ProtocolError("symbolic links are not protocol inputs or outputs")
            result = verify(args.plan.resolve(), args.events.resolve(), args.receipt.resolve())
        print(canonical(result).decode())
        return 1 if result.get("outcome") == "failed" else 0
    except (ProtocolError, OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"outcome": "blocked", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
