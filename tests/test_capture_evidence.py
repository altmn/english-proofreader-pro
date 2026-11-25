"""Portable evidence checks with real helper stdout and synthetic collector events.

These temporary records are mechanical test doubles, not model evaluation or
native acceptance receipts. No model, account, browser, or network is used.
"""
from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import capture_protocol as protocol, check_capture_evidence as checker, evaluate


class CaptureEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=str(Path(tempfile.gettempdir()).resolve()))
        self.work = Path(self.temp.name)
        self.root, self.original = self.work / "repository", self.work / "original-host"
        self.root.mkdir()
        self.original.mkdir()
        self.root_patch = patch.object(checker, "ROOT", self.root)
        self.eval_patch = patch.object(evaluate, "ROOT", self.root)
        self.root_patch.start()
        self.eval_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.eval_patch.stop)
        self.addCleanup(self.temp.cleanup)
        (self.root / "tests/trials").mkdir(parents=True)
        (self.root / "skills/proofreader-pro").mkdir(parents=True)
        self.skill = "Frozen synthetic skill for mechanical tests only.\n"
        self.manifest = '{"version":"1.0.1"}\n'
        (self.root / "skills/proofreader-pro/SKILL.md").write_text(self.skill)
        (self.root / "plugin.json").write_text(self.manifest)
        resource = self.root / evaluate.RESOURCE_PATHS[0]
        resource.parent.mkdir(parents=True)
        resource.write_bytes(protocol.read(protocol.METRICS_HELPER))
        source = "one two three four five six seven eight nine ten."
        fixtures = {
            checker.FIXTURES[0]: [{"id": "less-wordy", "input": "Proofread and make it less wordy: " + source,
                "expect": {"task": "proofread_and_shorten_supplied_text", "requested_reduction_target": "about 30%"}}],
            checker.FIXTURES[1]: [{"id": "shorten-markdown-changes-quotes", "input": "Make it less wordy. Source:\n" + source,
                "expect": {"task": "proofread_and_shorten_supplied_text", "requested_reduction_target": "about 30%"}}],
            checker.FIXTURES[2]: [
                {"id": "fragment-labels-no-op", "input": "Proofread: A correct label.",
                 "expect": {"task": "proofread_intentional_noun_phrase_labels", "response_exactly": "The text does not require any adjustments."}},
                {"id": "finite-clause-agreement", "input": "Proofread: The phrase link readers.",
                 "expect": {"task": "proofread_explicit_finite_clause", "synthetic_mechanical_case": True}},
            ],
        }
        self.snapshots = {}
        for number, (path, cases) in enumerate(fixtures.items()):
            fixture_text = json.dumps({"schema_version": 1, "cases": cases})
            (self.root / path).write_text(fixture_text)
            context = "Synthetic mechanical fixture; no model or semantic acceptance."
            snapshot = {
                "schema_version": evaluate.SCHEMA_VERSION, "kind": "evaluation-snapshot", "id": f"synthetic-{number}",
                "created_at": "2026-11-25T00:00:00Z", "fixture_source": path,
                "fixture_sha256": evaluate.sha256(fixture_text), "fixture_text": fixture_text,
                "fixture_schema_version": 1,  # pregate-literal: SCHEMA_VERSION=1 fixture format is independent of evaluation snapshot version
                "skill": {"text": self.skill, "sha256": evaluate.sha256(self.skill), "unicode_character_count": len(self.skill)},
                "manifest": {"text": self.manifest, "sha256": evaluate.sha256(self.manifest), "version": "1.0.1"},
                "runner_context": {"text": context, "sha256": evaluate.sha256(context)},
                "resources": evaluate.read_current_resources(),
                "cases": evaluate.project_fixture_cases({"cases": cases}, context),
            }
            relative = f"tests/trials/synthetic-{number}-snapshot.json"
            self.write(relative, protocol.canonical(snapshot))
            self.snapshots[path] = (relative, snapshot)
        req = checker.derive_requirements({key: value[1] for key, value in self.snapshots.items()})
        self.panel = {"schema_version": 1, "kind": "executed-capture-panel", "captures": []}
        for number in (1, 2, 3):
            self.panel["captures"].append(self.capture(number, req))
        self.panel_path = self.root / "tests/trials/panel.json"
        self.save_panel()

    def write(self, relative: str, data: bytes) -> dict:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {"path": relative, "sha256": protocol.digest(data)}

    def save_panel(self) -> None:
        self.panel_path.write_bytes(protocol.canonical(self.panel))

    def refresh(self, reference: dict, data: bytes) -> None:
        (self.root / reference["path"]).write_bytes(data)
        reference["sha256"] = protocol.digest(data)

    def capture(self, number: int, req: dict) -> dict:
        home = self.original / f"capture-{number}"
        controller, generator = home / "controller with spaces", home / "generator with spaces"
        controller.mkdir(parents=True)
        generator.mkdir()
        candidate, accepted = generator / "candidate.json", controller / "accepted.json"
        plan_path, event_path, receipt_path = controller / "plan.json", controller / "events.jsonl", controller / "receipt.json"
        requirement_path = controller / "requirements.json"
        requirement_path.write_bytes(protocol.canonical(req))
        protocol.prepare(requirement_path, candidate, plan_path, accepted)
        plan, _ = protocol.load_plan(plan_path)
        events = [{"type": "thread.started", "thread_id": f"synthetic-thread-{number}"}, {"type": "turn.started"}]

        def execute(phase: str) -> None:
            result = subprocess.run(protocol.command(plan, plan_path, phase), cwd=generator,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            item = {"id": phase, "type": "command_execution",
                    "command": shlex.join(protocol.command(plan, plan_path, phase))}
            events.extend([
                {"type": "item.started", "item": {**item, "status": "in_progress"}},
                {"type": "item.completed", "item": {**item, "status": "completed", "exit_code": 0,
                                                      "aggregated_output": result.stdout}},
            ])

        execute("source")
        responses = [
            {"id": "less-wordy", "response": "```text\none two three four five six seven.\n```"},
            {"id": "shorten-markdown-changes-quotes", "response": "```text\none two three four five six seven.\n```"},
            {"id": "fragment-labels-no-op", "response": "The text does not require any adjustments."},
            {"id": "finite-clause-agreement", "response": f"```text\nSynthetic corrected text {number}.\n```"},
        ]
        candidate.write_bytes(protocol.canonical({"responses": responses}) + b"\n")
        execute("final")
        events.append({"type": "turn.completed"})
        event_path.write_bytes(b"\n".join(protocol.canonical(row) for row in events) + b"\n")
        receipt = protocol.verify(plan_path, event_path, receipt_path)
        self.assertEqual(receipt["outcome"], "passed")
        prefix = f"tests/trials/capture-{number}"
        run_id = f"synthetic-run-{number}"
        row = {"run_id": run_id, "original_plan_path": str(plan_path),
               "plan": self.write(prefix + "-plan.json", plan_path.read_bytes()),
               "accepted": self.write(prefix + "-accepted.json", accepted.read_bytes()),
               "events": self.write(prefix + "-events.jsonl.gz", gzip.compress(event_path.read_bytes(), mtime=0)),
               "receipt": self.write(prefix + "-receipt.json", receipt_path.read_bytes()), "records": []}
        answers = {item["id"]: item["response"] for item in responses}
        for index, (fixture, (snapshot_file, snapshot)) in enumerate(self.snapshots.items()):
            cases = []
            for case in snapshot["cases"]:
                response = answers[case["id"]]
                cases.append({"id": case["id"], "prompt": case["full_prompt"], "context": case["context"],
                              "expectation": case["expectation"], "expectation_sha256": case["expectation_sha256"],
                              "response": response, "response_sha256": evaluate.sha256(response),
                              "assertions": [{"name": key, "expected": value, "status": "pass",
                                              "note": "Synthetic structural test double; not a model verdict."}
                                             for key, value in case["expectation"].items()]})
            record = {"schema_version": evaluate.RECORD_SCHEMA_VERSION, "kind": "evaluation-record", "snapshot_file": snapshot_file,
                      "snapshot_sha256": protocol.digest((self.root / snapshot_file).read_bytes()),
                      "source_binding": evaluate.source_binding(snapshot),
                      "metadata": {"model": "synthetic-test", "reasoning_effort": "high", "run_id": run_id,
                                   "host": "Codex CLI", "host_version": "synthetic-test", "invocation_mode": "independent-agent-simulation",
                                   "date": "2026-11-25", "source": "Mechanical fixture, no model inference",
                                   "reviewer": "Synthetic test double", "reviewer_context": "No semantic acceptance claimed"},
                      "host_evidence": {"install_method": None, "build_sha256": None},
                      "cases": cases, "aggregate": "pass"}
            row["records"].append(self.write(prefix + f"-record-{index}.json", protocol.canonical(record)))
        return row

    def assert_rejected(self, pattern: str) -> None:
        self.save_panel()
        with self.assertRaisesRegex((checker.EvidenceError, protocol.ProtocolError, evaluate.EvaluationError), pattern):
            checker.check_panel(self.panel_path)

    def events(self, index: int = 0) -> list[dict]:
        reference = self.panel["captures"][index]["events"]
        return [json.loads(line) for line in gzip.decompress((self.root / reference["path"]).read_bytes()).splitlines()]

    def replace_events(self, events: list[dict], index: int = 0) -> None:
        self.refresh(self.panel["captures"][index]["events"], gzip.compress(
            b"\n".join(protocol.canonical(row) for row in events) + b"\n", mtime=0))

    def test_real_helper_outputs_are_portable_after_original_host_files_are_removed(self) -> None:
        shutil.rmtree(self.original)
        result = checker.check_panel(self.panel_path)
        self.assertEqual(result["outcome"], "passed")
        self.assertEqual(len(result["captures"]), 3)
        self.assertEqual([row["cases"] for row in result["captures"]], [4, 4, 4])

    def test_missing_final_event_rejects_correct_output_and_generator_claim(self) -> None:
        events = self.events()
        claim = {"type": "item.completed", "item": {"type": "agent_message", "text": events[5]["item"]["aggregated_output"]}}
        self.replace_events(events[:4] + [claim, events[-1]])
        self.assert_rejected("final command")

    def test_fake_echoed_measurement_is_not_executed_helper(self) -> None:
        events = self.events()
        for event in events[4:6]:
            event["item"]["command"] = "printf 'claimed measurement'"
        self.replace_events(events)
        self.assert_rejected("final command")

    def test_failed_or_posthoc_tool_execution_cannot_be_accepted(self) -> None:
        events = self.events()
        events[5]["item"]["exit_code"] = 1
        self.replace_events(events)
        self.assert_rejected("did not complete successfully")
        events[5]["item"]["exit_code"] = 0
        self.replace_events(events[:4] + events[6:] + events[4:6])
        self.assert_rejected("out of order")

    def test_changed_accepted_bytes_reject_stale_execution(self) -> None:
        ref = self.panel["captures"][0]["accepted"]
        self.refresh(ref, (self.root / ref["path"]).read_bytes() + b"\n")
        self.assert_rejected("final stdout differs")

    def test_graded_response_cannot_differ_from_accepted_bytes(self) -> None:
        ref = self.panel["captures"][0]["records"][2]
        record = json.loads((self.root / ref["path"]).read_bytes())
        case = record["cases"][1]
        case["response"] = "```text\nA different answer.\n```"
        case["response_sha256"] = evaluate.sha256(case["response"])
        self.refresh(ref, protocol.canonical(record))
        self.assert_rejected("graded record responses differ")

    def test_runtime_receipt_cannot_disagree_with_actual_events(self) -> None:
        ref = self.panel["captures"][0]["receipt"]
        receipt = json.loads((self.root / ref["path"]).read_bytes())
        receipt["matching_events"]["final"]["item_id"] = "invented"
        self.refresh(ref, protocol.canonical(receipt))
        self.assert_rejected("runtime acceptance receipt differs")

    def test_plan_cannot_omit_frozen_shortening_requirements(self) -> None:
        ref = self.panel["captures"][0]["plan"]
        plan = json.loads((self.root / ref["path"]).read_bytes())
        del plan["requirements"]["shortening"]["less-wordy"]
        plan["requirements_sha256"] = protocol.digest(protocol.canonical(plan["requirements"]))
        self.refresh(ref, protocol.canonical(plan))
        self.assert_rejected("plan omits or changes")

    def test_plan_cannot_change_source_or_target_under_valid_hashes(self) -> None:
        ref = self.panel["captures"][0]["plan"]
        plan = json.loads((self.root / ref["path"]).read_bytes())
        plan["requirements"]["shortening"]["less-wordy"]["retained_ratios"] = [0.5, 0.5]
        plan["requirements_sha256"] = protocol.digest(protocol.canonical(plan["requirements"]))
        self.refresh(ref, protocol.canonical(plan))
        self.assert_rejected("plan omits or changes")

    def test_fewer_than_three_or_duplicate_runs_are_rejected(self) -> None:
        saved = copy.deepcopy(self.panel)
        self.panel["captures"].pop()
        self.assert_rejected("3 to 16")
        self.panel = saved
        self.panel["captures"][1]["run_id"] = self.panel["captures"][0]["run_id"]
        self.assert_rejected("duplicate capture run ID")

    def test_duplicate_challenge_cannot_claim_another_fresh_capture(self) -> None:
        first, second = (row["plan"] for row in self.panel["captures"][:2])
        plan = json.loads((self.root / second["path"]).read_bytes())
        plan["challenge"] = json.loads((self.root / first["path"]).read_bytes())["challenge"]
        self.refresh(second, protocol.canonical(plan))
        self.assert_rejected("duplicate capture challenge")

    def test_duplicate_thread_cannot_claim_another_independent_run(self) -> None:
        events = self.events(1)
        events[0]["thread_id"] = self.events()[0]["thread_id"]
        self.replace_events(events, 1)
        reference = self.panel["captures"][1]["receipt"]
        receipt = json.loads((self.root / reference["path"]).read_bytes())
        receipt["thread_id"] = events[0]["thread_id"]
        receipt["events_sha256"] = protocol.digest(b"\n".join(protocol.canonical(row) for row in events) + b"\n")
        self.refresh(reference, protocol.canonical(receipt))
        self.assert_rejected("duplicate captured CLI thread ID")

    def test_incomplete_record_coverage_and_ungraded_assertions_are_rejected(self) -> None:
        saved = copy.deepcopy(self.panel)
        self.panel["captures"][0]["records"].pop()
        self.assert_rejected("exactly three")
        self.panel = saved
        ref = self.panel["captures"][0]["records"][0]
        record = json.loads((self.root / ref["path"]).read_bytes())
        record["cases"][0]["assertions"][0]["status"] = "not_run"
        record["aggregate"] = "not_run"
        self.refresh(ref, protocol.canonical(record))
        self.assert_rejected("have not been graded")

    def test_historical_source_and_changed_helper_are_not_current_acceptance(self) -> None:
        (self.root / "skills/proofreader-pro/SKILL.md").write_text(self.skill + "Changed.\n")
        self.assert_rejected("historical")
        (self.root / "skills/proofreader-pro/SKILL.md").write_text(self.skill)
        changed = self.work / "changed-helper.py"
        changed.write_text("Different helper bytes.\n")
        with patch.object(protocol, "HELPER", changed):
            self.assert_rejected("current reviewed measurement helper")

    def test_current_production_resource_cannot_drift_after_capture(self) -> None:
        marker = self.root / "must-not-execute-resource"
        resource = self.root / evaluate.RESOURCE_PATHS[0]
        resource.write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n")
        self.assert_rejected("historical")
        self.assertFalse(marker.exists())

    def test_plan_resource_identity_must_match_current_snapshot_binding(self) -> None:
        reference = self.panel["captures"][0]["plan"]
        plan = json.loads((self.root / reference["path"]).read_bytes())
        plan["metrics_helper_sha256"] = "0" * 64
        self.refresh(reference, protocol.canonical(plan))
        self.assert_rejected("current production metrics resource")

    def test_path_traversal_and_symlink_evidence_are_rejected(self) -> None:
        ref = self.panel["captures"][0]["accepted"]
        original = ref["path"]
        ref["path"] = "../outside.json"
        self.assert_rejected("inside the repository")
        ref["path"] = original
        link = self.root / "tests/trials/link.json"
        link.symlink_to(self.root / original)
        ref["path"] = "tests/trials/link.json"
        self.assert_rejected("symbolic links")

    def test_snapshot_path_is_checked_before_existing_validator_follows_it(self) -> None:
        ref = self.panel["captures"][0]["records"][0]
        record = json.loads((self.root / ref["path"]).read_bytes())
        record["snapshot_file"] = str(self.original / "outside.json")
        self.refresh(ref, protocol.canonical(record))
        self.assert_rejected("inside the repository")

    def test_reference_hash_and_compressed_event_limits_are_enforced(self) -> None:
        ref = self.panel["captures"][0]["events"]
        ref["sha256"] = "0" * 64
        self.assert_rejected("SHA-256 mismatch")
        compressed = gzip.compress(b"x" * 1024, mtime=0)
        bomb = self.write("tests/trials/oversized.jsonl.gz", compressed)
        with patch.object(protocol, "MAX_BYTES", 100), self.assertRaisesRegex(checker.EvidenceError, "decompressed"):
            checker.read_ref(bomb, events=True)
        oversized = self.write("tests/trials/oversized.json", b"x" * 101)
        with patch.object(protocol, "MAX_BYTES", 100), self.assertRaisesRegex(protocol.ProtocolError, "exceeds"):
            checker.read_ref(oversized)

    def test_corrupt_deflate_stream_is_a_rejected_evidence_input(self) -> None:
        data = bytearray(gzip.compress(b"synthetic events", mtime=0))
        data[10] = 0xff
        reference = self.write("tests/trials/corrupt.jsonl.gz", bytes(data))
        with self.assertRaisesRegex(checker.EvidenceError, "invalid compressed"):
            checker.read_ref(reference, events=True)

    def test_original_interpreter_is_not_read_or_executed_by_portable_checker(self) -> None:
        read = protocol.read
        interpreters = {json.loads((self.root / row["plan"]["path"]).read_bytes())["python_path"]
                        for row in self.panel["captures"]}

        def checked_read(path: Path) -> bytes:
            self.assertNotIn(str(path), interpreters)
            return read(path)

        with patch.object(protocol, "read", side_effect=checked_read), patch.object(protocol, "load_plan", side_effect=AssertionError("not portable")):
            self.assertEqual(checker.check_panel(self.panel_path)["outcome"], "passed")


if __name__ == "__main__":
    unittest.main()
