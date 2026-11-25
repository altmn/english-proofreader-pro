"""Bind retained calculation traces to their exact generated responses."""

from __future__ import annotations

import gzip
import json
import unittest
from pathlib import Path

from scripts import evaluate


ROOT = Path(__file__).resolve().parent.parent


class CountingEvidenceTests(unittest.TestCase):
    def test_audit_fix_captures_bind_actual_tool_events_and_all_three_suites(self) -> None:
        evidence = evaluate.load_json(ROOT / "tests/trials/audit-fixes-cli-counting-provenance-2026-11-25.json", "audit-fix counting provenance")
        self.assertEqual(len(evidence["captures"]), 3)
        run_ids: set[str] = set()
        for capture in evidence["captures"]:
            with self.subTest(run_id=capture["run_id"]):
                self.assertNotIn(capture["run_id"], run_ids)
                run_ids.add(capture["run_id"])
                trace_path = evaluate.fixture_source_path(capture["trace_file"])
                self.assertEqual(evaluate.sha256_bytes(trace_path.read_bytes()), capture["trace_sha256"])
                self.assertTrue(evaluate.load_json(trace_path, "calculation trace"))
                events_path = evaluate.fixture_source_path(capture["events_file"])
                self.assertEqual(evaluate.sha256_bytes(events_path.read_bytes()), capture["events_sha256"])
                with gzip.open(events_path, "rb") as stream:
                    raw = stream.read(4 * 1024 * 1024 + 1)
                self.assertLessEqual(len(raw), 4 * 1024 * 1024)
                events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
                self.assertTrue(any(event["type"] == "turn.completed" for event in events))
                self.assertTrue(any(event.get("item", {}).get("type") == "command_execution"
                                    and event["item"].get("status") == "completed"
                                    and event["item"].get("exit_code") == 0 for event in events))
                fixtures = set()
                for source in capture["source_records"]:
                    record_path = evaluate.fixture_source_path(source["path"])
                    evaluate.validate_record(record_path)
                    record = evaluate.load_json(record_path, "audit-fix record")
                    self.assertEqual(record["metadata"]["run_id"], capture["run_id"])
                    self.assertEqual(record["source_binding"], source["source_binding"])
                    self.assertEqual({case["id"]: case["response_sha256"] for case in record["cases"]}, source["response_hashes"])
                    snapshot = evaluate.load_json(ROOT / record["snapshot_file"], "audit-fix snapshot")
                    fixtures.add(snapshot["fixture_source"])
                self.assertEqual(fixtures, {"tests/cases.json", "tests/changes-markdown-cases.json", "tests/fragment-calibration-cases.json"})

    def test_fragment_calibration_binds_committed_judgments_to_the_frozen_rubric(self) -> None:
        result = evaluate.load_json(ROOT / "tests/trials/audit-fixes-fragment-calibration-result-2026-11-25.json", "calibration result")
        fixture_path = ROOT / "tests/fragment-calibration-cases.json"
        self.assertEqual(evaluate.sha256_bytes(fixture_path.read_bytes()), result["fixture_sha256"])
        fixture = evaluate.load_json(fixture_path, "calibration fixture")
        rubric = fixture["reviewer_rubric"]
        self.assertEqual(result["rubric_id"], rubric["id"])
        self.assertEqual(result["rubric_version"], rubric["version"])
        judgments_path = evaluate.fixture_source_path(result["judgments_file"])
        self.assertEqual(evaluate.sha256_bytes(judgments_path.read_bytes()), result["judgments_sha256"])
        judgments = evaluate.load_json(judgments_path, "committed calibration judgments")
        self.assertEqual(judgments["rubric_id"], rubric["id"])
        self.assertEqual(judgments["rubric_version"], rubric["version"])
        expected = {example["id"]: example["expected_verdict"] for example in rubric["calibration_examples"]}
        actual = {example["id"]: example["verdict"] for example in judgments["examples"]}
        self.assertEqual(len(judgments["examples"]), len(expected))
        self.assertEqual(actual, expected)
        self.assertTrue(all(example["rationale"].strip() for example in judgments["examples"]))

    def test_counting_trace_provenance_matches_captured_inputs_and_responses(self) -> None:
        evidence = evaluate.load_json(ROOT / "tests/trials/host-counting-provenance-2026-11-16.json", "counting provenance")
        self.assertEqual(evidence["kind"], "programmatic-counting-provenance")
        captures = evidence["captures"]
        expected_ids = {f"{phase}-ci-capture-{number}-20261116" for phase in ("host-behavior", "host-facts") for number in (1, 2, 3)}
        self.assertEqual({capture["run_id"] for capture in captures}, expected_ids)
        self.assertEqual(len(captures), len(expected_ids))
        for capture in captures:
            with self.subTest(run_id=capture["run_id"]):
                trace_path = evaluate.fixture_source_path(capture["trace_file"])
                self.assertEqual(evaluate.sha256_bytes(trace_path.read_bytes()), capture["trace_sha256"])
                trace = evaluate.load_json(trace_path, "retained calculation trace")
                self.assertIsInstance(trace, dict)
                self.assertTrue(trace)
                sources = capture["source_records"]
                self.assertEqual(len(sources), 2)
                fixtures = set()
                for source in sources:
                    record_path = evaluate.fixture_source_path(source["path"])
                    evaluate.validate_record(record_path)
                    record = evaluate.load_json(record_path, "bound record")
                    self.assertEqual(record["metadata"]["run_id"], capture["run_id"])
                    self.assertEqual(record["source_binding"], capture["source_binding"])
                    actual = {case["id"]: case["response_sha256"] for case in record["cases"]}
                    self.assertEqual(actual, source["response_hashes"])
                    snapshot = evaluate.load_json(ROOT / record["snapshot_file"], "bound snapshot")
                    fixtures.add(snapshot["fixture_source"])
                self.assertEqual(fixtures, {"tests/cases.json", "tests/changes-markdown-cases.json"})


if __name__ == "__main__":
    unittest.main()
