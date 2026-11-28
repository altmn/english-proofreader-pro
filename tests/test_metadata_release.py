"""Reject behavior/configuration drift when carrying forward baseline evidence."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts import check_metadata_release as checker, evaluate

ROOT = Path(__file__).resolve().parent.parent
RECEIPT = json.loads((ROOT / "tests/metadata-release-1.0.10.json").read_text())
SNAPSHOT = json.loads((ROOT / RECEIPT["baseline_snapshot"]["path"]).read_text())
BASELINE = json.loads(SNAPSHOT["manifest"]["text"])


class ManifestEquivalenceTests(unittest.TestCase):
    def candidate(self):
        candidate = copy.deepcopy(BASELINE)
        candidate["version"] = "1.0.10"
        candidate["extensions"]["com.openai"]["publication"]["release_notes"] = "Documentation update only."
        return candidate

    def test_only_version_and_release_notes_may_change(self):
        checker.verify_manifest(self.candidate(), BASELINE, "1.0.10")
        changes = [
            ("description", "A changed description"),
            ("keywords", []),
            ("skills", "./different-skills"),
            ("extensions", {"com.openai": {"interface": {}, "publication": {"release_notes": "new"}}}),
        ]
        for key, value in changes:
            with self.subTest(key=key):
                candidate = self.candidate()
                candidate[key] = value
                with self.assertRaises(ValueError):
                    checker.verify_manifest(candidate, BASELINE, "1.0.10")

    def test_prompt_and_other_publication_metadata_cannot_change(self):
        for section, key, value in (("interface", "defaultPrompt", ["Different prompt"]),
                                    ("interface", "longDescription", "Different instructions"),
                                    ("publication", "countries", ["US"])):
            with self.subTest(key=key):
                candidate = self.candidate()
                candidate["extensions"]["com.openai"][section][key] = value
                with self.assertRaises(ValueError):
                    checker.verify_manifest(candidate, BASELINE, "1.0.10")

    def test_receipt_target_and_increasing_stable_version_are_required(self):
        for version in ("1.0.8", "1.0.9", "1.0.9+docs", "1.0.10-beta", "01.0.10"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                candidate = self.candidate()
                candidate["version"] = version
                checker.verify_manifest(candidate, BASELINE, version)
        with self.assertRaises(ValueError):
            candidate = self.candidate()
            candidate["version"] = "1.0.11"
            checker.verify_manifest(candidate, BASELINE, "1.0.10")

    def test_bool_to_number_change_is_not_equivalent(self):
        candidate = self.candidate()
        candidate["extensions"]["com.openai"]["review"]["commerce"] = 0
        with self.assertRaises(ValueError):
            checker.verify_manifest(candidate, BASELINE, "1.0.10")


class MetadataReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(Path(tempfile.gettempdir()).resolve()))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("scripts", "tests", "skills", "assets"):
            shutil.copytree(ROOT / directory, self.root / directory, ignore=shutil.ignore_patterns("__pycache__"))
        for path in ("LICENSE", "PRIVACY.md"):
            shutil.copyfile(ROOT / path, self.root / path)
        candidate = ManifestEquivalenceTests().candidate()
        (self.root / "plugin.json").write_text(json.dumps(candidate))

    def test_baseline_checks_pass_without_changing_candidate_or_evidence(self):
        watched = [self.root / "plugin.json", self.root / RECEIPT["baseline_snapshot"]["path"]]
        before = [p.read_bytes() for p in watched]
        result = checker.check_release(self.root, RECEIPT)
        self.assertEqual(result["outcome"], "passed")
        self.assertEqual(result["baseline_version"], "1.0.9")
        self.assertIn("no new model runs", result["limits"])
        self.assertEqual(before, [p.read_bytes() for p in watched])

    def test_every_nonmanifest_runtime_change_is_rejected(self):
        for path in RECEIPT["baseline_runtime_sha256"]:
            if path == "plugin.json":
                continue
            with self.subTest(path=path):
                target = self.root / path
                original = target.read_bytes()
                target.write_bytes(original + b"\n")
                with self.assertRaisesRegex(ValueError, "runtime differs"):
                    checker.verify_candidate(self.root, RECEIPT)
                target.write_bytes(original)

    def test_changed_fixtures_are_rejected_by_strict_baseline_suite(self):
        fixture = self.root / "tests/cases.json"
        fixture.write_bytes(fixture.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "baseline evidence validation failed"):
            checker.check_release(self.root, RECEIPT)

    def test_changed_panel_and_record_cannot_substitute_evidence(self):
        panel_path = self.root / RECEIPT["baseline_panel"]["path"]
        panel = json.loads(panel_path.read_text())
        record = self.root / panel["captures"][0]["records"][0]["path"]
        record.write_bytes(record.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "reference SHA-256 mismatch"):
            checker.check_release(self.root, RECEIPT)
        panel_path.write_bytes(panel_path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "reference SHA-256 mismatch"):
            checker.verify_candidate(self.root, RECEIPT)

    def test_escaping_reference_is_rejected_before_read(self):
        with self.assertRaisesRegex(ValueError, "stay inside"):
            checker.read_ref(self.root, {"path": "../outside.json", "sha256": "0" * 64})

    def test_original_current_binding_remains_strict(self):
        original_root = evaluate.ROOT
        evaluate.ROOT = self.root
        self.addCleanup(setattr, evaluate, "ROOT", original_root)
        record_path = self.root / "tests/trials/resource-execution-v4-core-sol-1-2026-11-25.json"
        binding = evaluate.validate_record(record_path)
        self.assertEqual(binding, "historical")
        record = json.loads(record_path.read_text())
        with self.assertRaisesRegex(evaluate.EvaluationError, "historical"):
            evaluate.check_requirements(record, binding, require_current=True)


if __name__ == "__main__":
    unittest.main()
