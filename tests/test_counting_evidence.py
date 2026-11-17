"""Bind retained calculation traces to their exact generated responses."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts import evaluate


ROOT = Path(__file__).resolve().parent.parent


class CountingEvidenceTests(unittest.TestCase):
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
