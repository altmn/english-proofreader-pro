"""Provenance and structure checks for manually graded model evaluation records."""
from __future__ import annotations

import argparse
import io
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import evaluate


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "skills/proofreader-pro").mkdir(parents=True)
        (self.root / "tests/trials").mkdir(parents=True)
        (self.root / "plugin.json").write_text('{"version":"1.2.3"}\n', encoding="utf-8")
        (self.root / "skills/proofreader-pro/SKILL.md").write_text("Synthetic skill v1\n", encoding="utf-8")
        self.resource_path = self.root / evaluate.RESOURCE_PATHS[0]
        self.resource_path.parent.mkdir(parents=True)
        self.resource_bytes = b"raise RuntimeError('the evaluator must not execute resource code')\n"
        self.resource_path.write_bytes(self.resource_bytes)
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
            reasoning_effort="high", run_id="run-1",
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

    def _legacy_record(self, record: dict, version: int = 1) -> dict:
        source = Path(record["snapshot_file"])
        if not source.is_absolute():
            source = self.root / source
        snapshot = json.loads(source.read_text(encoding="utf-8"))
        snapshot["schema_version"] = 1
        snapshot.pop("resources", None)
        suffix = record["metadata"].get("run_id", "unprofiled")
        legacy = self.root / f"tests/trials/legacy-{version}-{suffix}-snapshot.json"
        legacy.write_text(json.dumps(snapshot), encoding="utf-8")
        record["schema_version"] = version
        record["snapshot_file"] = str(legacy.relative_to(self.root))
        record["snapshot_sha256"] = evaluate.sha256_bytes(legacy.read_bytes())
        record["source_binding"].pop("resources", None)
        return record

    def _competing_creates(self, target: Path, calls: list) -> list:
        barrier = threading.Barrier(2)
        original_open = Path.open

        def simultaneous_open(path: Path, mode: str = "r", *args, **kwargs):
            if path == target and ("x" in mode or "w" in mode):
                barrier.wait(timeout=5)
            return original_open(path, mode, *args, **kwargs)

        def attempt(call):
            try:
                return call()
            except evaluate.EvaluationError as exc:
                return exc

        with patch.object(Path, "open", simultaneous_open), ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, calls))
        self.assertEqual(sum(isinstance(result, Path) for result in results), 1)
        errors = [result for result in results if isinstance(result, evaluate.EvaluationError)]
        self.assertEqual(len(errors), 1)
        self.assertIn("refusing to overwrite", str(errors[0]))
        return results

    def _suite_records(self, snapshot_path: Path | None = None) -> list[Path]:
        snapshot_path = snapshot_path or self.snapshot_path
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        bundle = {"responses": [{"id": case["id"], "prompt": case["full_prompt"], "response": "Synthetic answer."}
                                for case in snapshot["cases"]]}
        self.response_path.write_text(json.dumps(bundle), encoding="utf-8")
        paths = []
        for index in range(3):
            responses = json.loads(self.response_path.read_text(encoding="utf-8"))
            responses["responses"][0]["response"] = f"distinct synthetic response {index}"
            self.response_path.write_text(json.dumps(responses), encoding="utf-8")
            args = self._record_args()
            args.snapshot = str(snapshot_path)
            args.run_id = f"{snapshot_path.stem}-run-{index}"
            args.out = str(self.root / f"suite-{snapshot_path.stem}-{index}.json")
            path = evaluate.create_record(args)
            record = json.loads(path.read_text(encoding="utf-8"))
            for case in record["cases"]:
                for assertion in case["assertions"]:
                    assertion["status"] = "pass"
            record["aggregate"] = "pass"
            path.write_text(json.dumps(record), encoding="utf-8")
            paths.append(path)
        return paths

    def _validate_suite(self, paths: list[Path], **overrides) -> int:
        options = dict(model="gpt-6-luna", reasoning_effort="high", invocation_mode="independent-agent-simulation",
                       min_runs=3, require_current=True, require_complete=True, require_pass=True)
        options.update(overrides)
        return evaluate.validate_suite(paths, **options)

    def test_concurrent_snapshot_creation_does_not_overwrite_winner(self) -> None:
        second_context = self.root / "other-runner.txt"
        second_context.write_text("A different synthetic runner.", encoding="utf-8")
        contexts = [self.context_path, second_context]
        target = self.root / "tests/trials/parallel-snapshot.json"
        calls = [lambda context=context: evaluate.create_snapshot(
            argparse.Namespace(id="parallel", runner_context=str(context))) for context in contexts]
        results = self._competing_creates(target, calls)
        winner = next(index for index, result in enumerate(results) if isinstance(result, Path))
        snapshot = json.loads(target.read_text(encoding="utf-8"))
        evaluate.validate_snapshot(snapshot)
        self.assertEqual(snapshot["runner_context"]["text"], contexts[winner].read_text(encoding="utf-8"))

    def test_concurrent_record_creation_does_not_overwrite_winner(self) -> None:
        self._responses()
        calls = []
        for index in range(2):
            args = self._record_args()
            args.run_id = f"parallel-run-{index}"
            bundle = json.loads(self.response_path.read_text(encoding="utf-8"))
            bundle["responses"][0]["response"] = f"captured response {index}"
            args.responses = str(self.root / f"responses-{index}.json")
            Path(args.responses).write_text(json.dumps(bundle), encoding="utf-8")
            calls.append(lambda args=args: evaluate.create_record(args))
        results = self._competing_creates(self.record_path, calls)
        winner = next(index for index, result in enumerate(results) if isinstance(result, Path))
        self.assertEqual(evaluate.validate_record(self.record_path), "current")
        record = self._load_record()
        self.assertEqual(record["metadata"]["run_id"], f"parallel-run-{winner}")
        self.assertEqual(record["cases"][0]["response"], f"captured response {winner}")

    def test_existing_evidence_and_dangling_symlinks_are_not_overwritten(self) -> None:
        original = self.snapshot_path.read_bytes()
        with self.assertRaisesRegex(evaluate.EvaluationError, "refusing to overwrite"):
            evaluate.create_snapshot(argparse.Namespace(id="run", runner_context=str(self.context_path)))
        self.assertEqual(self.snapshot_path.read_bytes(), original)
        self._responses()
        missing_target = self.root / "must-not-create.json"
        self.record_path.symlink_to(missing_target)
        with self.assertRaisesRegex(evaluate.EvaluationError, "refusing to overwrite"):
            evaluate.create_record(self._record_args())
        self.assertFalse(missing_target.exists())

    def test_new_records_require_structured_profile_but_legacy_records_remain_valid(self) -> None:
        self._responses()
        for field in ("reasoning_effort", "run_id"):
            args = self._record_args()
            setattr(args, field, None)
            with self.subTest(field=field), self.assertRaisesRegex(evaluate.EvaluationError, field):
                evaluate.create_record(args)
        self._record()
        record = self._load_record()
        self.assertEqual(record["schema_version"], evaluate.RECORD_SCHEMA_VERSION)
        for field in ("reasoning_effort", "run_id"):
            record["metadata"].pop(field)
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "reasoning_effort"):
            evaluate.validate_record(self.record_path)
        record = self._legacy_record(record)
        self._save_record(record)
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        with self.assertRaisesRegex(evaluate.EvaluationError, "schema-2 records"):
            self._validate_suite([self.record_path], min_runs=1, require_complete=False, require_pass=False)

    def test_suite_rejects_legacy_records_even_with_structured_profile_fields(self) -> None:
        paths = self._suite_records()
        record = json.loads(paths[1].read_text(encoding="utf-8"))
        record = self._legacy_record(record)
        paths[1].write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(evaluate.validate_record(paths[1]), "historical")
        with self.assertRaisesRegex(evaluate.EvaluationError, "schema-2 records"):
            self._validate_suite(paths)

    def test_suite_requires_declared_profile_and_minimum_run_count(self) -> None:
        paths = self._suite_records()
        self.assertEqual(self._validate_suite(paths), 3)
        with self.assertRaisesRegex(evaluate.EvaluationError, "at least 3"):
            self._validate_suite(paths[:2])
        with self.assertRaisesRegex(evaluate.EvaluationError, "positive integer"):
            self._validate_suite(paths, min_runs=0)
        original = json.loads(paths[1].read_text(encoding="utf-8"))
        for field, value in (("model", "different-model"), ("reasoning_effort", "low"),
                             ("invocation_mode", "different-simulation")):
            record = json.loads(json.dumps(original))
            record["metadata"][field] = value
            paths[1].write_text(json.dumps(record), encoding="utf-8")
            with self.subTest(field=field), self.assertRaisesRegex(evaluate.EvaluationError, field):
                self._validate_suite(paths)

    def test_suite_rejects_duplicate_run_ids_and_reordered_response_copies(self) -> None:
        paths = self._suite_records()
        first = json.loads(paths[0].read_text(encoding="utf-8"))
        second = json.loads(paths[1].read_text(encoding="utf-8"))
        second["metadata"]["run_id"] = first["metadata"]["run_id"]
        paths[1].write_text(json.dumps(second), encoding="utf-8")
        with self.assertRaisesRegex(evaluate.EvaluationError, "duplicate suite run_id"):
            self._validate_suite(paths)
        copied = json.loads(json.dumps(first))
        copied["metadata"]["run_id"] = "different-id-for-the-same-capture"
        copied["cases"].reverse()
        paths[1].write_text(json.dumps(copied), encoding="utf-8")
        with self.assertRaisesRegex(evaluate.EvaluationError, "identical complete response sets require provenance review"):
            self._validate_suite(paths)

    def test_identical_responses_require_explicit_review_and_distinct_run_ids(self) -> None:
        paths = self._suite_records()
        first = json.loads(paths[0].read_text(encoding="utf-8"))
        second = json.loads(json.dumps(first))
        second["metadata"]["run_id"] = "separate-capture-with-matching-output"
        paths[1].write_text(json.dumps(second), encoding="utf-8")
        note = "Reviewed distinct capture identities and original logs; complete outputs independently match."
        self.assertEqual(self._validate_suite(paths, identical_responses_note=note), 3)
        for empty_note in ("", "  \n"):
            with self.subTest(note=empty_note), self.assertRaisesRegex(evaluate.EvaluationError, "note must be non-empty"):
                self._validate_suite(paths, identical_responses_note=empty_note)
        command = ["validate-suite", *(str(path) for path in paths), "--model", "gpt-6-luna",
                   "--reasoning-effort", "high", "--invocation-mode", "independent-agent-simulation",
                   "--min-runs", "3", "--require-current", "--require-complete", "--require-pass"]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(evaluate.main(command), 2)
            self.assertEqual(evaluate.main([*command, "--identical-responses-note", " "]), 2)
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(evaluate.main([*command, "--identical-responses-note", note]), 0)
        self.assertIn(note, output.getvalue())
        second["metadata"]["run_id"] = first["metadata"]["run_id"]
        paths[1].write_text(json.dumps(second), encoding="utf-8")
        with self.assertRaisesRegex(evaluate.EvaluationError, "duplicate suite run_id"):
            self._validate_suite(paths, identical_responses_note=note)

    def test_suite_does_not_count_different_inputs_as_repeated_runs(self) -> None:
        paths = self._suite_records()
        self.context_path.write_text("A different evaluation protocol.", encoding="utf-8")
        snapshot_path = evaluate.create_snapshot(argparse.Namespace(id="other", runner_context=str(self.context_path)))
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        bundle = {"responses": [{"id": case["id"], "prompt": case["full_prompt"], "response": "Other response."}
                                for case in snapshot["cases"]]}
        self.response_path.write_text(json.dumps(bundle), encoding="utf-8")
        args = self._record_args()
        args.snapshot = str(snapshot_path)
        args.run_id = "other-run"
        paths[2] = evaluate.create_record(args)
        with self.assertRaisesRegex(evaluate.EvaluationError, "same source, runner context, complete fixture bytes, prompts, and expectations"):
            self._validate_suite(paths, require_complete=False, require_pass=False)

    def test_suite_default_fixture_gate_rejects_smaller_alternate_suite(self) -> None:
        alternate = self.root / "tests/smaller.json"
        fixture = {"schema_version": 1, "cases": [{"id": "small", "input": "One prompt.",
                                                 "expect": {"facts_preserved": True}}]}
        alternate.write_text(json.dumps(fixture), encoding="utf-8")
        snapshot_path = evaluate.create_snapshot(argparse.Namespace(
            id="smaller", runner_context=str(self.context_path), fixtures="tests/smaller.json"))
        paths = self._suite_records(snapshot_path)
        with self.assertRaisesRegex(evaluate.EvaluationError, "fixture_source must match"):
            self._validate_suite(paths)
        self.assertEqual(self._validate_suite(paths, fixtures="./tests/smaller.json"), 3)
        command = ["validate-suite", *(str(path) for path in paths), "--model", "gpt-6-luna",
                   "--reasoning-effort", "high", "--invocation-mode", "independent-agent-simulation",
                   "--min-runs", "3", "--require-current", "--require-complete", "--require-pass"]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(evaluate.main(command), 2)
            self.assertEqual(evaluate.main([*command, "--fixtures", "tests/smaller.json"]), 0)

    def test_suite_rejects_changed_shared_contract_even_without_current_requirement(self) -> None:
        paths = self._suite_records()
        fixture_path = self.root / "tests/cases.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["shared_output_contract"] = {"new_rule": "A changed rubric outside individual case expectations."}
        fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
        snapshot_path = evaluate.create_snapshot(argparse.Namespace(
            id="changed-contract", runner_context=str(self.context_path)))
        new_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(self._snapshot()["cases"], new_snapshot["cases"])
        new_paths = self._suite_records(snapshot_path)
        self.assertEqual(evaluate.validate_record(paths[0]), "historical")
        self.assertEqual(evaluate.validate_record(new_paths[2]), "current")
        with self.assertRaisesRegex(evaluate.EvaluationError, "complete fixture bytes"):
            self._validate_suite([paths[0], paths[1], new_paths[2]], require_current=False)

    def test_suite_cli_enforces_current_complete_and_passing_requirements(self) -> None:
        paths = self._suite_records()
        command = ["validate-suite", *(str(path) for path in paths), "--model", "gpt-6-luna",
                   "--reasoning-effort", "high", "--invocation-mode", "independent-agent-simulation",
                   "--min-runs", "3", "--require-current", "--require-complete", "--require-pass"]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(evaluate.main(command), 0)
        original = json.loads(paths[1].read_text(encoding="utf-8"))
        for status in ("not_run", "fail"):
            record = json.loads(json.dumps(original))
            record["cases"][0]["assertions"][0].update(status=status, note="synthetic gap")
            record["aggregate"] = status
            paths[1].write_text(json.dumps(record), encoding="utf-8")
            with self.subTest(status=status), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(evaluate.main(command), 2)
        paths[1].write_text(json.dumps(original), encoding="utf-8")
        (self.root / "skills/proofreader-pro/SKILL.md").write_text("Changed source.", encoding="utf-8")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(evaluate.main(command), 2)

    def test_alternate_fixture_source_controls_current_binding(self) -> None:
        alternate = self.root / "tests/supplemental.json"
        fixture = {"schema_version": 1, "cases": [{"id": "extra", "input": "A supplemental prompt.",
                                                 "expect": {"facts_preserved": True}}]}
        alternate.write_text(json.dumps(fixture), encoding="utf-8")
        snapshot_path = evaluate.create_snapshot(argparse.Namespace(
            id="alternate", runner_context=str(self.context_path), fixtures="tests/supplemental.json"))
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(snapshot["fixture_source"], "tests/supplemental.json")
        bundle = {"responses": [{"id": case["id"], "prompt": case["full_prompt"], "response": "Synthetic answer."}
                                for case in snapshot["cases"]]}
        self.response_path.write_text(json.dumps(bundle), encoding="utf-8")
        args = self._record_args()
        args.snapshot = str(snapshot_path)
        evaluate.create_record(args)
        self.assertEqual(evaluate.validate_record(self.record_path), "current")
        (self.root / "tests/cases.json").write_text("changed unrelated fixtures", encoding="utf-8")
        self.assertEqual(evaluate.validate_record(self.record_path), "current")
        alternate.write_text(json.dumps(fixture) + "\n", encoding="utf-8")
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        alternate.unlink()
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")

    def test_fixture_sources_cannot_escape_repository(self) -> None:
        external = self.root.parent / "external-fixtures.json"
        (self.root / "tests/escape.json").symlink_to(external)
        for source in ("../outside.json", str(external), "tests/escape.json"):
            with self.subTest(source=source), self.assertRaisesRegex(evaluate.EvaluationError, "inside the repository"):
                evaluate.create_snapshot(argparse.Namespace(id="escape", runner_context=str(self.context_path), fixtures=source))
        snapshot = self._snapshot()
        snapshot["fixture_source"] = "../outside.json"
        with self.assertRaisesRegex(evaluate.EvaluationError, "inside the repository"):
            evaluate.validate_snapshot(snapshot)

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
        snapshot["schema_version"] = 1
        snapshot.pop("resources")
        del snapshot["fixture_text"]
        self.assertEqual(evaluate.validate_snapshot(snapshot), {case["id"]: case for case in snapshot["cases"]})

        self.record_path.unlink()
        self._record()
        (self.root / "tests/cases.json").write_text('{"schema_version":1,"cases":[]}', encoding="utf-8")
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        snapshot = self._snapshot()
        snapshot["schema_version"] = 1
        snapshot.pop("resources")
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
        (self.root / "skills/proofreader-pro/SKILL.md").write_bytes(skill_bytes)
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
        (self.root / "skills/proofreader-pro/SKILL.md").write_text("Synthetic skill v2\n", encoding="utf-8")
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")

    def test_resource_bytes_are_embedded_and_bound_without_executing_them(self) -> None:
        self._record()
        snapshot, record = self._snapshot(), self._load_record()
        self.assertEqual(snapshot["schema_version"], 2)
        self.assertEqual(record["schema_version"], 3)
        expected = {"path": evaluate.RESOURCE_PATHS[0], "text": self.resource_bytes.decode("utf-8"),
                    "sha256": evaluate.sha256_bytes(self.resource_bytes), "utf8_byte_count": len(self.resource_bytes)}
        self.assertEqual(snapshot["resources"], [expected])
        self.assertEqual(record["source_binding"]["resources"], {expected["path"]: expected["sha256"]})
        # The synthetic helper raises immediately if executed. Validation treats
        # its bytes only as data and still succeeds.
        self.assertEqual(evaluate.validate_record(self.record_path), "current")

    def test_changed_or_missing_resource_is_historical_without_losing_saved_bytes(self) -> None:
        self._record()
        original_record = self.record_path.read_bytes()
        original_snapshot = self.snapshot_path.read_bytes()
        self.resource_path.write_text("A changed resource.\n", encoding="utf-8")
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        with self.assertRaisesRegex(evaluate.EvaluationError, "resource"):
            evaluate.check_requirements(self._load_record(), "historical", require_current=True)
        self.resource_path.unlink()
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        evaluate.validate_snapshot(self._snapshot())
        self.assertEqual(self.snapshot_path.read_bytes(), original_snapshot)
        self.assertEqual(self.record_path.read_bytes(), original_record)
        self.resource_path.write_bytes(self.resource_bytes)
        self.assertEqual(evaluate.validate_record(self.record_path), "current")

    def test_new_snapshots_require_present_regular_nonempty_bounded_utf8_resource(self) -> None:
        cases = [(None, "cannot read current resource"), (b" \n", "empty"), (b"\xff", "not UTF-8"),
                 (b"x" * (evaluate.MAX_RESOURCE_BYTES + 1), "byte limit"), ("directory", "regular file")]
        for index, (data, message) in enumerate(cases):
            with self.subTest(case=message):
                self.resource_path.unlink()
                if data == "directory":
                    self.resource_path.mkdir()
                elif data is not None:
                    self.resource_path.write_bytes(data)
                try:
                    with self.assertRaisesRegex(evaluate.EvaluationError, message):
                        evaluate.create_snapshot(argparse.Namespace(id=f"missing-resource-{index}", runner_context=str(self.context_path)))
                    self.assertFalse((self.root / f"tests/trials/missing-resource-{index}-snapshot.json").exists())
                finally:
                    if self.resource_path.is_dir():
                        self.resource_path.rmdir()
                    elif self.resource_path.exists():
                        self.resource_path.unlink()
                    self.resource_path.write_bytes(self.resource_bytes)

    def test_resource_file_and_ancestor_symlinks_are_not_followed(self) -> None:
        self._record()
        outside = self.root / "unlisted-resource.py"
        outside.write_bytes(self.resource_bytes)
        self.resource_path.unlink()
        self.resource_path.symlink_to(outside)
        with self.assertRaisesRegex(evaluate.EvaluationError, "symbolic links"):
            evaluate.read_current_resources()
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        self.resource_path.unlink()
        self.resource_path.write_bytes(self.resource_bytes)
        original_dir = self.resource_path.parent
        held = self.root / "held-scripts"
        original_dir.rename(held)
        original_dir.symlink_to(held, target_is_directory=True)
        try:
            with self.assertRaisesRegex(evaluate.EvaluationError, "symbolic links"):
                evaluate.read_current_resources()
            self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        finally:
            original_dir.unlink()
            held.rename(original_dir)
        self.assertEqual(outside.read_bytes(), self.resource_bytes)

    def test_embedded_resource_hash_count_and_paths_cannot_be_falsified(self) -> None:
        original = self._snapshot()
        changes = [
            (lambda resource: resource.update(text=resource["text"] + "changed"), "byte count"),
            (lambda resource: resource.update(sha256="0" * 64), "text/hash"),
            (lambda resource: resource.update(utf8_byte_count=True), "byte count"),
            (lambda resource: resource.update(path="../outside.py"), "unlisted"),
            (lambda resource: resource.update(path="/outside.py"), "unlisted"),
            (lambda resource: resource.update(path="skills/other.py"), "unlisted"),
        ]
        for mutate, reason in changes:
            snapshot = json.loads(json.dumps(original))
            mutate(snapshot["resources"][0])
            with self.subTest(reason=reason), self.assertRaisesRegex(evaluate.EvaluationError, reason):
                evaluate.validate_snapshot(snapshot)
        for resources in ([], original["resources"] * 2):
            snapshot = json.loads(json.dumps(original))
            snapshot["resources"] = resources
            with self.assertRaisesRegex(evaluate.EvaluationError, "complete resource allowlist"):
                evaluate.validate_snapshot(snapshot)

    def test_record_resource_binding_must_match_embedded_snapshot(self) -> None:
        self._record()
        record = self._load_record()
        record["source_binding"]["resources"][evaluate.RESOURCE_PATHS[0]] = "0" * 64
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "source binding"):
            evaluate.validate_record(self.record_path)

    def test_resource_crlf_and_unicode_bytes_have_exact_identity(self) -> None:
        data = "# café\r\nraise RuntimeError('data only')\r\n".encode("utf-8")
        self.resource_path.write_bytes(data)
        snapshot_path = evaluate.create_snapshot(argparse.Namespace(id="resource-crlf", runner_context=str(self.context_path)))
        snapshot = json.loads(snapshot_path.read_bytes())
        self.assertEqual(snapshot["resources"][0]["text"].encode("utf-8"), data)
        self.assertEqual(snapshot["resources"][0]["sha256"], evaluate.sha256_bytes(data))
        self.assertEqual(snapshot["resources"][0]["utf8_byte_count"], len(data))

    def test_legacy_schema_two_remains_valid_but_cannot_accept_resources(self) -> None:
        self._record()
        record = self._legacy_record(self._load_record(), version=2)
        self._save_record(record)
        self.assertEqual(evaluate.validate_record(self.record_path), "historical")
        record["metadata"].pop("run_id")
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "run_id"):
            evaluate.validate_record(self.record_path)
        snapshot = self._snapshot()
        snapshot["schema_version"] = 1
        with self.assertRaisesRegex(evaluate.EvaluationError, "legacy snapshots"):
            evaluate.validate_snapshot(snapshot)

    def test_legacy_schema_two_suites_remain_historically_verifiable(self) -> None:
        paths = self._suite_records()
        for path in paths:
            record = self._legacy_record(json.loads(path.read_text(encoding="utf-8")), version=2)
            path.write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(self._validate_suite(paths, require_current=False), 3)
        with self.assertRaisesRegex(evaluate.EvaluationError, "historical"):
            self._validate_suite(paths)

    def test_resource_aware_schema_cannot_be_downgraded_or_omit_source_content(self) -> None:
        snapshot = self._snapshot()
        for field in ("resources", "fixture_text"):
            changed = dict(snapshot)
            changed.pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(evaluate.EvaluationError, "resource-aware"):
                evaluate.validate_snapshot(changed)
        self._record()
        record = self._load_record()
        record["schema_version"] = 2
        self._save_record(record)
        with self.assertRaisesRegex(evaluate.EvaluationError, "incompatible resource bindings"):
            evaluate.validate_record(self.record_path)

    def test_new_records_cannot_be_created_from_an_unbound_legacy_snapshot(self) -> None:
        snapshot = self._snapshot()
        snapshot["schema_version"] = 1
        snapshot.pop("resources")
        self.snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        self._responses()
        with self.assertRaisesRegex(evaluate.EvaluationError, "new records require a resource-aware snapshot"):
            evaluate.create_record(self._record_args())
        self.assertFalse(self.record_path.exists())

    def test_intended_host_and_grader_metadata_are_required(self) -> None:
        self._responses()
        args = argparse.Namespace(
            snapshot=str(self.snapshot_path), responses=str(self.response_path), model="gpt-6-luna",
            reasoning_effort="high", run_id="run-1",
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
