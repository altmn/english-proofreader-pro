"""Check release evidence references and metadata-only gates without a model."""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import unittest
from pathlib import Path

from scripts import check_metadata_release


ROOT = Path(__file__).resolve().parent.parent


def expand_record_paths(token: str) -> list[str]:
    """Expand the workflow's literal comma-list braces, never execute its shell."""
    match = re.search(r"\{([^{}]+)\}", token)
    if match is None:
        return [token]
    return [path for item in match[1].split(",")
            for path in expand_record_paths(token[:match.start()] + item + token[match.end():])]


class WorkflowEvidenceTests(unittest.TestCase):
    # Value: protects=CI and documented acceptance commands select existing evidence;
    # fails_when=an intermediate or mistyped evidence path is wired into release CI;
    # why_new=validator unit tests exercise synthetic inputs rather than workflow references;
    # seam=none; no_claim=GitHub execution or the truth of manual semantic grades.
    def test_workflow_evidence_paths_and_documented_panel_agree(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        documentation = (ROOT / "tests/README.md").read_text(encoding="utf-8")
        commands = re.findall(r"^\s*python scripts/evaluate\.py validate-suite (.+)$", workflow, re.MULTILINE)
        metadata_receipts = re.findall(r"python scripts/check_metadata_release\.py (\S+)", workflow)
        workflow_panels = re.findall(r"python scripts/check_capture_evidence\.py (\S+)", workflow)
        documented_panels = re.findall(r"python3 scripts/check_capture_evidence\.py (\S+)", documentation)
        if metadata_receipts:
            self.assertEqual(len(metadata_receipts), 1, "CI must select one reviewed metadata-only receipt")
            self.assertFalse(commands, "metadata-only CI must not label historical records current")
            self.assertFalse(workflow_panels, "the metadata-only gate owns strict baseline panel validation")
            self.assertEqual(re.findall(r"python3 scripts/check_metadata_release\.py (\S+)", documentation),
                             metadata_receipts)
            receipt_path = (ROOT / metadata_receipts[0]).resolve()
            self.assertTrue(receipt_path.is_relative_to(ROOT))
            receipt = json.loads(receipt_path.read_bytes())
            manifest = json.loads((ROOT / "plugin.json").read_bytes())
            self.assertEqual(receipt["version"], manifest["version"])
            self.assertEqual(documented_panels, [receipt["baseline_panel"]["path"]])
            self.assertIn("captures are historical for " + receipt["version"], documentation)
            self.assertIn("no new model runs or native acceptance", documentation)
            # Exercise the real gate, including all three strict profile suites
            # and the execution panel against the isolated exact baseline.
            result = check_metadata_release.check_release(ROOT, receipt)
            self.assertEqual(result["outcome"], "passed")
            self.assertEqual(result["version"], manifest["version"])
            self.assertEqual(result["baseline_version"], receipt["baseline_version"])
            return
        self.assertTrue(commands, "release CI must declare its current regression suites")
        fixtures = set()
        for command in commands:
            arguments = shlex.split(command)
            self.assertTrue({"--require-current", "--require-complete", "--require-pass"} <= set(arguments))
            first_option = next(index for index, value in enumerate(arguments) if value.startswith("--"))
            records = [path for token in arguments[:first_option] for path in expand_record_paths(token)]
            self.assertGreaterEqual(len(records), 3)
            fixture = arguments[arguments.index("--fixtures") + 1]
            fixtures.add(fixture)
            for relative in [fixture, *records]:
                with self.subTest(reference=relative):
                    path = (ROOT / relative).resolve()
                    self.assertTrue(path.is_relative_to(ROOT))
                    self.assertTrue(path.is_file(), f"missing workflow evidence: {relative}")
        self.assertEqual(fixtures, {"tests/cases.json", "tests/changes-markdown-cases.json",
                                    "tests/fragment-calibration-cases.json"})
        self.assertEqual(len(workflow_panels), 1)
        self.assertEqual(documented_panels, workflow_panels)
        self.assertTrue((ROOT / workflow_panels[0]).is_file())

    # Value: protects=published runner instructions remain represented by exact frozen inputs;
    # fails_when=a runner is edited without retaining matching snapshots for its complete suites;
    # why_new=record validation checks frozen hashes without comparing current runner files;
    # seam=none; no_claim=actual generator independence or installed native host acceptance.
    def test_cli_runner_bytes_are_represented_by_complete_frozen_suites(self) -> None:
        snapshots = [json.loads(path.read_bytes()) for path in (ROOT / "tests/trials").glob("*-snapshot.json")]
        for relative in ("tests/audit-fixes-runner.txt", "tests/verified-execution-runner.txt"):
            data = (ROOT / relative).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            matches = [snapshot for snapshot in snapshots
                       if snapshot.get("runner_context", {}).get("sha256") == digest]
            with self.subTest(runner=relative):
                self.assertTrue(matches, "freeze changed runner inputs before publishing them")
                self.assertEqual({snapshot["fixture_source"] for snapshot in matches},
                                 {"tests/cases.json", "tests/changes-markdown-cases.json",
                                  "tests/fragment-calibration-cases.json"})
                for snapshot in matches:
                    self.assertEqual(snapshot["runner_context"]["text"].encode("utf-8"), data)


if __name__ == "__main__":
    unittest.main()
