"""Provenance and structure checks for manually graded model evaluation records."""
from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import evaluate


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "skills/proofread").mkdir(parents=True)
        (self.root / "tests/trials").mkdir(parents=True)
        (self.root / "plugin.json").write_text('{"version":"1.2.3"}\n', encoding="utf-8")
        (self.root / "skills/proofread/SKILL.md").write_text("Synthetic skill v1\n", encoding="utf-8")
        fixture = {
            "schema_version": 1,
            "cases": [
                {"id": "case-a", "input": "Proofread: I has a typo.", "expect": {"task": "proofread", "fenced": True}},
                {"id": "case-b", "context": "Skill selected.", "input": "Proofread: All set.", "expect": {"task": "proofread", "no_op": True}},
            ],
        }
        (self.root / "tests/cases.json").write_text(json.dumps(fixture), encoding="utf-8")
        self.context_path = self.root / "runner.txt"
        self.context_path.write_text("Run the prompt and return the response only.", encoding="utf-8")
        self.snapshot_path = self.root / "tests/trials/run-snapshot.json"
        self.response_path = self.root / "responses.json"
        self.record_path = self.root / "tests/trials/run.json"
        self.patcher = patch.object(evaluate, "ROOT", self.root)
        self.patcher.start()
        evaluate.create_snapshot(argparse.Namespace(id="run", runner_context=str(self.context_path)))

    def tearDown(self) -> None:
        self.patcher.stop()
        self.temp.cleanup()

    def _snapshot(self) -> dict:
        return json.loads(self.snapshot_path.read_text(encoding="utf-8"))

    def _responses(self, *, missing: bool = False, duplicate: bool = False, bad_prompt: bool = False) -> None:
        snapshot = self._snapshot()
        cases = snapshot["cases"]
        responses = [{"id": case["id"], "prompt": case["full_prompt"], "response": "synthetic answer"}
                     for case in cases[:1 if missing else None]]
        if duplicate:
            responses.append(dict(responses[0]))
        if bad_prompt:
            responses[0]["prompt"] += " changed"
        self.response_path.write_text(json.dumps({"responses": responses}), encoding="utf-8")

    def _record_args(self, *, mode: str = "independent-agent-simulation", version: str = "unknown") -> argparse.Namespace:
        return argparse.Namespace(
            snapshot=str(self.snapshot_path), responses=str(self.response_path), model="gpt-6-luna",
            host="Codex collaboration subagent", host_version=version, invocation_mode=mode,
            date=evaluate.datetime.now(evaluate.timezone.utc).date().isoformat(),
            source="Synthetic evaluation input", reviewer="independent reviewer",
            reviewer_context="Manually compared each response with the listed expectation.",
            install_method=None, build_sha256=None, out=str(self.record_path),
        )

    def _record(self, *, mode: str = "independent-agent-simulation", version: str = "unknown") -> None:
        self._responses()
        args = self._record_args(mode=mode, version=version)
        evaluate.create_record(args)

    def _load_record(self) -> dict:
        return json.loads(self.record_path.read_text(encoding="utf-8"))

    def _save_record(self, record: dict) -> None:
        self.record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    def test_record_template_is_not_run_then_manual_verdicts_aggregate(self) -> None:
        self._record()
        record = self._load_record()
        self.assertEqual(record["aggregate"], "not_run")
        for case in record["cases"]:
            for assertion in case["assertions"]:
                assertion["status"] = "pass"
        record["aggregate"] = "pass"
        self._save_record(record)
        self.assertEqual(evaluate.validate_record(self.record_path), "current")

    def test_missing_and_duplicate_fixture_or_response_ids_are_rejected(self) -> None:
        fixture_path = self.root / "tests/cases.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["cases"].append(dict(fixture["cases"][0]))
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        with self.assertRaisesRegex(evaluate.EvaluationError, "duplicate fixture case ID"):
            evaluate.create_snapshot(argparse.Namespace(id="duplicate", runner_context=str(self.context_path)))

        self._responses(missing=True)
        args = argparse.Namespace(snapshot=str(self.snapshot_path), responses=str(self.response_path))
        with self.assertRaisesRegex(evaluate.EvaluationError, "do not match snapshot"):
            evaluate.create_record(args)
        self._responses(duplicate=True)
        with self.assertRaisesRegex(evaluate.EvaluationError, "duplicate response ID"):
            evaluate.create_record(args)

    def test_empty_fixture_and_record_sets_are_rejected_and_never_pass(self) -> None:
        self.assertEqual(evaluate.aggregate([]), "not_run")
        fixture_path = self.root / "tests/cases.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["cases"] = []
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        with self.assertRaisesRegex(evaluate.EvaluationError, "fixture case must not be empty"):
            evaluate.create_snapshot(argparse.Namespace(id="empty", runner_context=str(self.context_path)))
        self._record()
        record = self._load_record()
        record["cases"] = []
        record["aggregate"] = "not_run"
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "record case must not be empty"):
            evaluate.validate_record(self.record_path)

    def test_snapshot_projection_cannot_be_reduced_or_altered_with_same_fixture_hash(self) -> None:
        self._record()
        original_record = self._load_record()
        original_snapshot = self._snapshot()
        for mutate in (
            lambda snapshot: snapshot["cases"].pop(),
            lambda snapshot: snapshot["cases"][0].update(input="changed prompt"),
        ):
            snapshot = json.loads(json.dumps(original_snapshot))
            mutate(snapshot)
            self.snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            record = json.loads(json.dumps(original_record))
            record["snapshot_sha256"] = evaluate.sha256_bytes(self.snapshot_path.read_bytes())
            self._save_record(record)
            with self.assertRaisesRegex(evaluate.EvaluationError, "case projection does not match"):
                evaluate.validate_record(self.record_path)

    def test_historical_embedded_fixture_is_self_verifying_and_legacy_snapshot_requires_current_fixture(self) -> None:
        self._record()
        snapshot = self._snapshot()
        self.assertEqual(evaluate.validate_snapshot(snapshot), {case["id"]: case for case in snapshot["cases"]})
        del snapshot["fixture_text"]
        self.assertEqual(evaluate.validate_snapshot(snapshot), {case["id"]: case for case in snapshot["cases"]})

        self.record_path.unlink()
        self._record()
        (self.root / "tests/cases.json").write_text('{"schema_version":1,"cases":[]}', encoding="utf-8")
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        snapshot = self._snapshot()
        snapshot.pop("fixture_text", None)
        with self.assertRaisesRegex(evaluate.EvaluationError, "no embedded fixture text"):
            evaluate.validate_snapshot(snapshot)

    def test_record_rejects_missing_case_and_mismatched_prompt(self) -> None:
        self._responses(bad_prompt=True)
        with self.assertRaisesRegex(evaluate.EvaluationError, "prompt does not match"):
            evaluate.create_record(self._record_args())
        self._record()
        record = self._load_record()
        record["cases"].pop()
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "case IDs do not match"):
            evaluate.validate_record(self.record_path)

    def test_snapshot_source_hash_mismatch_is_rejected(self) -> None:
        self._record()
        snapshot = self._snapshot()
        snapshot["skill"]["sha256"] = "0" * 64
        self.snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        record = self._load_record()
        record["snapshot_sha256"] = evaluate.sha256(self.snapshot_path.read_text(encoding="utf-8"))
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "skill text/hash mismatch"):
            evaluate.validate_record(self.record_path)

    def test_snapshot_rejects_inaccurate_skill_count_or_manifest_version(self) -> None:
        snapshot = self._snapshot()
        snapshot["skill"]["unicode_character_count"] += 1
        with self.assertRaisesRegex(evaluate.EvaluationError, "character count mismatch"):
            evaluate.validate_snapshot(snapshot)
        snapshot = self._snapshot()
        snapshot["manifest"]["version"] = "9.9.9"
        with self.assertRaisesRegex(evaluate.EvaluationError, "version does not match"):
            evaluate.validate_snapshot(snapshot)

    def test_crlf_source_bytes_are_preserved_and_affect_current_binding(self) -> None:
        skill_bytes = b"Synthetic skill v1\r\n"
        manifest_bytes = b'{"version":"1.2.3"}\r\n'
        fixture_path = self.root / "tests/cases.json"
        fixture_bytes = fixture_path.read_bytes() + b"\r\n"
        (self.root / "skills/proofread/SKILL.md").write_bytes(skill_bytes)
        (self.root / "plugin.json").write_bytes(manifest_bytes)
        fixture_path.write_bytes(fixture_bytes)
        self.context_path.write_bytes(b"Keep line endings.\r\n")
        crlf_snapshot_path = self.root / "tests/trials/crlf-snapshot.json"
        evaluate.create_snapshot(argparse.Namespace(id="crlf", runner_context=str(self.context_path)))
        snapshot = json.loads(crlf_snapshot_path.read_bytes().decode("utf-8"))
        self.assertEqual(snapshot["skill"]["text"], skill_bytes.decode("utf-8"))
        self.assertEqual(snapshot["skill"]["sha256"], evaluate.sha256_bytes(skill_bytes))
        self.assertEqual(snapshot["skill"]["unicode_character_count"], len(skill_bytes.decode("utf-8")))
        self.assertEqual(snapshot["manifest"]["sha256"], evaluate.sha256_bytes(manifest_bytes))
        self.assertEqual(snapshot["fixture_sha256"], evaluate.sha256_bytes(fixture_bytes))

        responses = {"responses": [{"id": case["id"], "prompt": case["full_prompt"], "response": "answer"}
                                   for case in snapshot["cases"]]}
        self.response_path.write_text(json.dumps(responses), encoding="utf-8")
        args = self._record_args()
        args.snapshot = str(crlf_snapshot_path)
        args.out = str(self.root / "tests/trials/crlf-record.json")
        evaluate.create_record(args)
        self.assertEqual(evaluate.validate_record(Path(args.out)), "current")
        fixture_path.write_bytes(fixture_bytes.replace(b"\r\n", b"\n"))
        self.assertEqual(evaluate.validate_record(Path(args.out)), "historical")

    def test_response_hash_mismatch_is_rejected(self) -> None:
        self._record()
        record = self._load_record()
        record["cases"][0]["response"] = "edited after recording"
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "does not match its snapshot or response shape"):
            evaluate.validate_record(self.record_path)

    def test_invalid_verdict_shape_and_failed_assertion_without_note_are_rejected(self) -> None:
        self._record()
        record = self._load_record()
        assertion = record["cases"][0]["assertions"][0]
        assertion["status"] = "probably"
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "invalid manual verdict"):
            evaluate.validate_record(self.record_path)

        assertion["status"] = []
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "invalid manual verdict"):
            evaluate.validate_record(self.record_path)

        assertion["status"] = "fail"
        assertion["note"] = "  "
        record["aggregate"] = "fail"
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "requires a gap note"):
            evaluate.validate_record(self.record_path)

    def test_strict_complete_and_pass_flags_check_assertions_individually(self) -> None:
        self._record()
        record = self._load_record()
        assertions = [assertion for case in record["cases"] for assertion in case["assertions"]]
        assertions[0]["status"] = "fail"
        assertions[0]["note"] = "gap"
        record["aggregate"] = "fail"
        self._save_record(record)
        for flag in ("--require-complete", "--require-pass"):
            with self.subTest(flag=flag), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(evaluate.main(["validate", str(self.record_path), flag]), 2)

    def test_duplicate_json_keys_and_malformed_snapshot_path_are_rejected(self) -> None:
        duplicate_json = self.root / "duplicate.json"
        duplicate_json.write_text('{"a":1,"a":2}', encoding="utf-8")
        with self.assertRaisesRegex(evaluate.EvaluationError, "duplicate JSON key"):
            evaluate.load_json(duplicate_json, "duplicate fixture")
        self._record()
        record = self._load_record()
        record["snapshot_file"] = {"path": "bad"}
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "snapshot_file must be a path string"):
            evaluate.validate_record(self.record_path)
        record["snapshot_file"] = "missing-snapshot.json"
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "cannot read bound snapshot"):
            evaluate.validate_record(self.record_path)

    def test_historical_snapshot_is_valid_but_not_current(self) -> None:
        self._record()
        (self.root / "skills/proofread/SKILL.md").write_text("Synthetic skill v2\n", encoding="utf-8")
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")

    def test_intended_host_and_grader_metadata_are_required(self) -> None:
        self._responses()
        args = argparse.Namespace(
            snapshot=str(self.snapshot_path), responses=str(self.response_path), model="gpt-6-luna",
            host="ChatGPT", host_version="unknown", invocation_mode="intended-host",
            date=evaluate.datetime.now(evaluate.timezone.utc).date().isoformat(), source="test", reviewer="grader",
            reviewer_context="manual", install_method=None, build_sha256=None, out=str(self.record_path),
        )
        with self.assertRaisesRegex(evaluate.EvaluationError, "actual host version"):
            evaluate.create_record(args)
        args.host_version = "1.2.3"
        with self.assertRaisesRegex(evaluate.EvaluationError, "require install_method"):
            evaluate.create_record(args)

        args.invocation_mode = "independent-agent-simulation"
        args.host_version = "unknown"
        args.reviewer_context = ""
        with self.assertRaisesRegex(evaluate.EvaluationError, "reviewer_context"):
            evaluate.create_record(args)


if __name__ == "__main__":
    unittest.main()
