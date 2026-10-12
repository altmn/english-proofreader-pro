"""Offline checks for public documentation and synthetic fixture integrity."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
PRIVATE_HOST_LINK = re.compile(
    r"https?://(?:www\.)?chatgpt\.com/(?:c/[0-9a-f-]{20,}|plugins/Plugin_[A-Za-z0-9]+)"
)
MARKDOWN_LINK = re.compile(r"\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)")


class PublicRepositoryTests(unittest.TestCase):
    def test_public_docs_do_not_link_private_host_resources(self) -> None:
        docs = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
        docs += list((ROOT / "tests").glob("*.md"))
        for doc in docs:
            with self.subTest(document=doc.relative_to(ROOT).as_posix()):
                self.assertIsNone(PRIVATE_HOST_LINK.search(doc.read_text(encoding="utf-8")))

    def test_relative_documentation_links_resolve(self) -> None:
        docs = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
        docs += list((ROOT / "tests").glob("*.md"))
        for doc in docs:
            for target in MARKDOWN_LINK.findall(doc.read_text(encoding="utf-8")):
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                with self.subTest(document=doc.name, target=target):
                    destination = (doc.parent / unquote(url.path)).resolve()
                    self.assertTrue(destination.is_relative_to(ROOT))
                    self.assertTrue(destination.is_file(), f"missing link target: {target}")

    def test_behavior_fixtures_have_unique_ids_and_observable_expectations(self) -> None:
        fixture = json.loads((ROOT / "tests/cases.json").read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema_version"], 1)
        self.assertTrue(fixture["shared_output_contract"])
        cases = fixture["cases"]
        self.assertGreater(len(cases), 0)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["input"].strip())
                self.assertTrue(case["expect"]["task"].strip())
                self.assertGreater(len(case["expect"]), 1)


if __name__ == "__main__":
    unittest.main()
