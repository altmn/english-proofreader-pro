"""Exercise actual helper execution and rejected evidence at the acceptance boundary.

The event collector here is a test double for trusted CLI JSONL. Passing these
tests does not attest a live CLI host; measured stdout comes from real isolated
Python subprocesses, rather than handwritten successful measurement fixtures.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import capture_protocol as protocol


class CaptureProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=str(Path(tempfile.gettempdir()).resolve()))
        self.root = Path(self.temp.name)
        self.run = self.root / "generator with spaces"
        self.controller = self.root / "controller with spaces"
        self.run.mkdir()
        self.controller.mkdir()
        self.candidate = self.run / "candidate.json"
        self.plan_path = self.controller / "plan.json"
        self.accepted = self.controller / "accepted.json"
        self.receipt = self.controller / "result.json"
        self.events_path = self.controller / "events.jsonl"
        self.req = {"case_ids": ["shorten"], "fenced_case_ids": ["shorten"],
                    "shortening": {"shorten": {"source": "We are now ready to review the report.",
                                                "retained_ratios": [0.5, 0.5]}}}
        requirements_path = self.controller / "requirements.json"
        requirements_path.write_bytes(protocol.canonical(self.req))
        self.prepared = protocol.prepare(requirements_path, self.candidate, self.plan_path, self.accepted)
        self.plan, self.plan_hash = protocol.load_plan(self.plan_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def execute(self, phase: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(protocol.command(self.plan, self.plan_path, phase), cwd=self.run,
                              capture_output=True, text=True, timeout=15)

    def command_events(self, phase: str, result: subprocess.CompletedProcess[str]) -> list[dict]:
        item = {"id": phase, "type": "command_execution",
                "command": shlex.join(protocol.command(self.plan, self.plan_path, phase))}
        return [{"type": "item.started", "item": {**item, "status": "in_progress"}},
                {"type": "item.completed", "item": {**item, "status": "completed",
                                                       "exit_code": result.returncode,
                                                       "aggregated_output": result.stdout}}]

    def valid_events(self) -> list[dict]:
        source = self.execute("source")
        self.assertEqual(source.returncode, 0, source.stderr)
        capture = {"responses": [{"id": "shorten", "response": "```text\nReview the report now.\n```"}]}
        self.candidate.write_bytes(protocol.canonical(capture) + b"\n")
        final = self.execute("final")
        self.assertEqual(final.returncode, 0, final.stderr)
        return [{"type": "thread.started", "thread_id": "local-test-thread"},
                {"type": "turn.started"}, *self.command_events("source", source),
                *self.command_events("final", final), {"type": "turn.completed"}]

    def save_events(self, events: list[dict]) -> None:
        self.events_path.write_bytes(b"\n".join(protocol.canonical(x) for x in events) + b"\n")

    def reject(self, events: list[dict], reason: str) -> dict:
        self.save_events(events)
        receipt = protocol.verify(self.plan_path, self.events_path, self.receipt)
        self.assertEqual(receipt["outcome"], "failed")
        self.assertIn(reason, receipt["reason"])
        self.assertFalse(self.accepted.exists())
        self.assertEqual(json.loads(self.receipt.read_text()), receipt)
        return receipt

    def test_actual_executed_measurements_gate_exact_accepted_copy(self) -> None:
        events = self.valid_events()
        self.save_events(events)
        receipt = protocol.verify(self.plan_path, self.events_path, self.receipt)
        self.assertEqual(receipt["outcome"], "passed")
        self.assertEqual(self.accepted.read_bytes(), self.candidate.read_bytes())
        self.assertEqual(receipt["candidate_sha256"], protocol.digest(self.accepted.read_bytes()))
        self.assertEqual(receipt["matching_events"]["source"]["item_id"], "source")
        self.assertEqual(receipt["matching_events"]["final"]["item_id"], "final")
        self.assertEqual(json.loads(events[5]["item"]["aggregated_output"])["responses"][0]["final_words"], 4)
        for phase, event_index in (("source", 3), ("final", 5)):
            with self.subTest(phase=phase):
                measured = json.loads(events[event_index]["item"]["aggregated_output"])
                self.assertEqual(measured["metrics_helper_path"], str(protocol.METRICS_HELPER))
                self.assertEqual(measured["metrics_helper_sha256"],
                                 protocol.digest(protocol.read(protocol.METRICS_HELPER)))

    def clone_runtime(self) -> Path:
        """An isolated real helper/resource pair permits safe drift experiments."""
        clone = self.root / "reviewed runtime copy"
        helper = clone / "scripts/capture_protocol.py"
        resource = clone / "skills/proofreader-pro/scripts/text_metrics.py"
        helper.parent.mkdir(parents=True)
        resource.parent.mkdir(parents=True)
        helper.write_bytes(protocol.read(protocol.HELPER))
        resource.write_bytes(protocol.read(protocol.METRICS_HELPER))
        self.plan_path = self.controller / "cloned-plan.json"
        result = subprocess.run([
            sys.executable, "-I", "-B", str(helper), "prepare",
            "--requirements", str(self.controller / "requirements.json"),
            "--candidate", str(self.candidate), "--plan", str(self.plan_path),
            "--accepted", str(self.accepted)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.plan_path.read_bytes()
        self.plan, self.plan_hash = json.loads(data), protocol.digest(data)
        return resource

    def test_changed_production_resource_rejects_actual_measure_command(self) -> None:
        resource = self.clone_runtime()
        before = self.execute("source")
        self.assertEqual(before.returncode, 0, before.stderr)
        resource.write_bytes(resource.read_bytes() + b"\n# drift after frozen identity\n")
        result = self.execute("source")
        self.assertEqual(result.returncode, 2)
        self.assertIn("production metrics helper identity changed", result.stderr)
        self.assertFalse(self.accepted.exists())

    def test_resource_drift_after_successful_tool_events_cannot_be_promoted(self) -> None:
        resource = self.clone_runtime()
        events = self.valid_events()
        self.save_events(events)
        resource.write_bytes(resource.read_bytes() + b"\n# drift after real final measurement\n")
        result = subprocess.run([
            self.plan["python_path"], "-I", "-B", self.plan["helper_path"], "verify",
            "--plan", str(self.plan_path), "--events", str(self.events_path),
            "--receipt", str(self.receipt)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertIn("production metrics helper identity changed", result.stderr)
        self.assertFalse(self.accepted.exists())

    def test_offline_replay_loads_only_explicit_matching_trusted_resource(self) -> None:
        events = self.valid_events()
        trusted = self.controller / "trusted-current-text-metrics.py"
        trusted.write_bytes(protocol.read(protocol.METRICS_HELPER))
        replay_plan = dict(self.plan, metrics_helper_path="/historical/unavailable/text_metrics.py")
        measure = protocol.load_metrics(replay_plan, trusted)
        # Origin paths remain inert metadata during replay. Return exactly the
        # same path as recorded in actual stdout, without opening that origin.
        for event_index in (3, 5):
            output = json.loads(events[event_index]["item"]["aggregated_output"])
            output["metrics_helper_path"] = replay_plan["metrics_helper_path"]
            events[event_index]["item"]["aggregated_output"] = json.dumps(output)
        event_bytes = b"\n".join(protocol.canonical(event) for event in events)
        verified = protocol.verify_events(replay_plan, self.plan_path, self.plan_hash,
                                          event_bytes, self.candidate.read_bytes(), metrics_measure=measure)
        self.assertEqual(verified["candidate_sha256"], protocol.digest(self.candidate.read_bytes()))
        trusted.write_bytes(trusted.read_bytes() + b"\n# different code is not replay evidence\n")
        with self.assertRaisesRegex(protocol.ProtocolError, "identity changed"):
            protocol.load_metrics(replay_plan, trusted)

    def test_missing_final_event_rejects_even_with_fake_trace_and_correct_result(self) -> None:
        events = self.valid_events()
        (self.run / "counting-trace.json").write_text(events[5]["item"]["aggregated_output"])
        self.reject(events[:4] + events[6:], "final command")

    def test_echoing_correct_json_is_not_execution_of_the_measurement_helper(self) -> None:
        events = self.valid_events()
        for event in events[4:6]:
            event["item"]["command"] = "printf 'invented measurement output'"
        self.reject(events, "final command")

    def test_changed_output_rejects_old_final_measurement(self) -> None:
        events = self.valid_events()
        self.candidate.write_bytes(protocol.canonical({"responses": [
            {"id": "shorten", "response": "```text\nReview this report now.\n```"}]}))
        self.reject(events, "final stdout differs")

    def test_equal_json_with_different_candidate_bytes_is_stale(self) -> None:
        events = self.valid_events()
        self.candidate.write_bytes(self.candidate.read_bytes() + b"\n")
        self.reject(events, "final stdout differs")

    def test_old_run_challenge_is_rejected(self) -> None:
        events = self.valid_events()
        output = json.loads(events[5]["item"]["aggregated_output"])
        output["challenge"] = "0" * 64
        events[5]["item"]["aggregated_output"] = json.dumps(output)
        self.reject(events, "final stdout differs")

    def test_failed_measurement_command_cannot_be_graded_as_pass(self) -> None:
        events = self.valid_events()
        events[5]["item"]["exit_code"] = 1
        self.reject(events, "did not complete successfully")

    def test_final_before_source_is_rejected(self) -> None:
        events = self.valid_events()
        self.reject(events[:2] + events[4:6] + events[2:4] + events[6:], "out of order")

    def test_controller_posthoc_measurement_after_turn_cannot_replace_generator_execution(self) -> None:
        events = self.valid_events()
        self.reject(events[:4] + events[6:] + events[4:6], "out of order")

    def test_completed_command_without_started_event_is_rejected(self) -> None:
        events = self.valid_events()
        self.reject(events[:4] + events[5:], "final command")

    def test_incomplete_turn_is_rejected(self) -> None:
        events = self.valid_events()
        self.reject(events[:-1], "completed CLI turn")

    def test_json_number_type_is_not_coerced_to_boolean(self) -> None:
        events = self.valid_events()
        output = json.loads(events[5]["item"]["aggregated_output"])
        output["responses"][0]["blocks"][0]["start"] = False
        events[5]["item"]["aggregated_output"] = json.dumps(output)
        self.reject(events, "final stdout differs")

    def test_actual_final_command_rejects_wrong_budget_and_unsafe_fence(self) -> None:
        for response in ("```text\nReview now.\n```", "```text\nReview `the` report now.\n````"):
            with self.subTest(response=response):
                self.candidate.write_bytes(protocol.canonical({"responses": [{"id": "shorten", "response": response}]}))
                result = self.execute("final")
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.accepted.exists())

    def test_compact_empty_text_block_is_valid(self) -> None:
        measure = protocol.load_metrics(self.plan)
        parsed = protocol.blocks("```text\n```", measure)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["payload"], "")
        self.assertEqual(parsed[0]["payload_sha256"], protocol.digest(b""))

    def test_shipped_literal_block_roundtrips_exact_payload_bytes(self) -> None:
        measure = protocol.load_metrics(self.plan)
        payloads = ("", "\n", "\r", "\r\n", "Text", "Text\n", "Text\r", "Text\r\n",
                    "One\n\nTwo\n\n", "One\r\n\r\nTwo\r\n", "One\r\rTwo\r", "é\n\n",
                    "```text\ninner\n```\n", "Start ```` end\r\n")
        for payload in payloads:
            with self.subTest(payload=repr(payload)):
                block = measure({"text": payload, "include_presentation": True})["presentation"]["literal_block"]
                parsed = protocol.blocks(block, measure)
                self.assertEqual(len(parsed), 1)
                self.assertEqual(parsed[0]["start"], 0)
                self.assertEqual(parsed[0]["payload"].encode("utf-8"), payload.encode("utf-8"))
                self.assertEqual(parsed[0]["payload_sha256"], protocol.digest(payload.encode("utf-8")))

    def test_source_command_text_is_inert_json_data(self) -> None:
        canary = self.run / "must-not-exist"
        source = f"$(touch {canary}) remains literal."
        self.req["shortening"]["shorten"].update(source=source, retained_ratios=[1, 1])
        # A new trusted plan freezes the changed synthetic source; no old plan is mutated.
        requirements_path = self.controller / "inert-requirements.json"
        requirements_path.write_bytes(protocol.canonical(self.req))
        self.plan_path = self.controller / "inert-plan.json"
        protocol.prepare(requirements_path, self.candidate, self.plan_path, self.accepted)
        self.plan, self.plan_hash = protocol.load_plan(self.plan_path)
        first = self.execute("source")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.candidate.write_bytes(protocol.canonical({"responses": [{"id": "shorten", "response": "```text\n" + source + "\n```"}]}))
        final = self.execute("final")
        self.assertEqual(final.returncode, 0, final.stderr)
        self.assertFalse(canary.exists())

    def test_existing_outputs_and_receipts_are_preserved(self) -> None:
        events = self.valid_events()
        self.save_events(events)
        self.accepted.write_bytes(b"user-owned bytes")
        with self.assertRaisesRegex(protocol.ProtocolError, "new distinct"):
            protocol.verify(self.plan_path, self.events_path, self.receipt)
        self.assertEqual(self.accepted.read_bytes(), b"user-owned bytes")
        self.assertFalse(self.receipt.exists())

    def test_fresh_plan_challenge_and_controller_scope(self) -> None:
        req = self.controller / "new-requirements.json"
        req.write_bytes(protocol.canonical(self.req))
        result = protocol.prepare(req, self.candidate, self.controller / "second-plan.json", self.controller / "second-accepted.json")
        other, _ = protocol.load_plan(Path(result["plan"]))
        self.assertNotEqual(other["challenge"], self.plan["challenge"])
        with self.assertRaisesRegex(protocol.ProtocolError, "outside"):
            protocol.prepare(req, self.candidate, self.run / "untrusted-plan.json", self.accepted)

    def test_command_matching_accepts_only_direct_exact_argv_or_host_shell_wrapper(self) -> None:
        argv = protocol.command(self.plan, self.plan_path, "final")
        inner = shlex.join(argv)
        self.assertTrue(protocol.command_matches(inner, argv))
        self.assertTrue(protocol.command_matches(shlex.join(["/bin/sh", "-c", inner]), argv))
        for altered in (inner + " ; echo forged", "echo fake # " + inner, inner + " # ignored", "python3 " + inner):
            with self.subTest(command=altered):
                self.assertFalse(protocol.command_matches(altered, argv))

    def test_equal_lexical_tokens_do_not_authorize_shell_expansion(self) -> None:
        argv = ["/usr/bin/python3", "/safe/helper.py", "--plan", "/safe/$EXPAND;false.json"]
        unsafe = "/usr/bin/python3 /safe/helper.py --plan /safe/$EXPAND;false.json"
        self.assertEqual(shlex.split(unsafe), argv)
        self.assertFalse(protocol.command_matches(unsafe, argv))
        self.assertTrue(protocol.command_matches(shlex.join(argv), argv))

    def test_malformed_json_and_zero_case_requirements_cannot_pass(self) -> None:
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.subTest(data=data), self.assertRaises(protocol.ProtocolError):
                protocol.parse(data)
        with self.assertRaises(protocol.ProtocolError):
            protocol.requirements({"case_ids": [], "fenced_case_ids": [], "shortening": {}})


if __name__ == "__main__":
    unittest.main()
