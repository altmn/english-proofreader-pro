"""Keep retained GFM render evidence bound to literal generated responses."""

from __future__ import annotations

import hashlib
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from scripts import evaluate


ROOT = Path(__file__).resolve().parent.parent


class RenderedText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.strong_depth = 0
        self.pre_depth = 0
        self.bold_spans: list[str] = []
        self.code_blocks: list[str] = []
        self.interpreted_quote_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "pre":
            self.pre_depth += 1
            self.code_blocks.append("")
        if tag == "strong" and not self.pre_depth:
            if not self.strong_depth:
                self.bold_spans.append("")
            self.strong_depth += 1
        if self.strong_depth and tag in {"em", "code", "del", "s"}:
            self.interpreted_quote_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "strong" and not self.pre_depth:
            self.strong_depth -= 1
        if tag == "pre":
            self.pre_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.pre_depth:
            self.code_blocks[-1] += data
        if self.strong_depth:
            self.bold_spans[-1] += data


class RenderEvidenceTests(unittest.TestCase):
    def test_gfm_evidence_matches_bound_responses_and_literal_bold_quotations(self) -> None:
        for proof_name, record_prefix, capture_date in (
            ("review-markdown-render-2026-11-16.json", "review-markdown-sol", "2026-11-16"),
            ("host-behavior-markdown-render-2026-11-16.json", "host-behavior-markdown-sol", "2026-11-16"),
            ("host-facts-markdown-render-2026-11-16.json", "host-facts-markdown-sol", "2026-11-16"),
            ("audit-fixes-markdown-render-2026-11-25.json", "audit-fixes-markdown-sol", "2026-11-25"),
        ):
            with self.subTest(proof=proof_name):
                self.check_render_evidence(proof_name, record_prefix, capture_date)

    def check_render_evidence(self, proof_name: str, record_prefix: str, capture_date: str) -> None:
        proof = evaluate.load_json(ROOT / "tests/trials" / proof_name, "render evidence")
        self.assertEqual(proof["kind"], "markdown-render-verification")
        seen: set[tuple[str, str]] = set()
        expected: set[tuple[str, str]] = set()
        records = {}
        snapshots = {}
        for number in (1, 2, 3):
            relative = f"tests/trials/{record_prefix}-{number}-{capture_date}.json"
            evaluate.validate_record(ROOT / relative)
            records[relative] = evaluate.load_json(ROOT / relative, "bound record")
            snapshots[relative] = evaluate.load_json(ROOT / records[relative]["snapshot_file"], "bound snapshot")
            expected.update((relative, case["id"]) for case in snapshots[relative]["cases"])
        for observation in proof["observations"]:
            identity = observation["source_record"], observation["case_id"]
            with self.subTest(record=identity[0], case=identity[1]):
                self.assertNotIn(identity, seen)
                seen.add(identity)
                self.assertIn(identity, expected)
                record = records[identity[0]]
                snapshot = snapshots[identity[0]]
                case = next(case for case in record["cases"] if case["id"] == identity[1])
                source_case = next(case for case in snapshot["cases"] if case["id"] == identity[1])
                self.assertEqual(observation["response_sha256"], evaluate.sha256(case["response"]))
                html = observation["rendered_html"]
                self.assertEqual(observation["rendered_html_sha256"], hashlib.sha256(html.encode("utf-8")).hexdigest())
                fenced = re.match(r"\A(`{3,})text\n(.*?)\n\1(?:\n|\Z)", case["response"], re.DOTALL)
                self.assertIsNotNone(fenced)
                assert fenced is not None
                result = fenced[2]
                longest = max((len(run) for run in re.findall(r"`+", result)), default=0)
                self.assertGreater(len(fenced[1]), longest)
                source = source_case["input"].split("Source:\n", 1)[1]
                parsed = RenderedText()
                parsed.feed(html)
                parsed.close()
                self.assertEqual(parsed.bold_spans, ['"' + source + '"', '"' + result + '"'])
                self.assertEqual(parsed.code_blocks, [result + "\n"])
                self.assertEqual(parsed.interpreted_quote_tags, [])
                self.assertEqual((parsed.strong_depth, parsed.pre_depth), (0, 0))
        self.assertTrue(seen)
        self.assertEqual(seen, expected)


if __name__ == "__main__":
    unittest.main()
