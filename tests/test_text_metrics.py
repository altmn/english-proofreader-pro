"""Exercise the packaged helper through inert data and its real CLI."""

from __future__ import annotations

import hashlib
import json
import runpy
import string
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "skills/proofreader-pro/scripts/text_metrics.py"
HELPER = runpy.run_path(str(SCRIPT))
measure = HELPER["measure"]


class TextMetricsTests(unittest.TestCase):
    def cli(self, raw: bytes, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), *arguments],
                              input=raw, capture_output=True, timeout=10, check=False)

    def test_cli_stdin_and_file_bind_exact_utf8_bytes(self) -> None:
        raw = json.dumps({"text": "One two three", "candidate": "One two", "level": "less_wordy"},
                         indent=2).encode()
        stdin = self.cli(raw)
        self.assertEqual(stdin.returncode, 0, stdin.stderr)
        result = json.loads(stdin.stdout)
        self.assertEqual(result["request_bytes_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["metrics"]["words"], 3)
        self.assertEqual(result["comparison"]["candidate_words"], 2)
        self.assertTrue(result["comparison"]["within_budget"])
        self.assertFalse(result["comparison"]["meaning_verified"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request with spaces.json"
            path.write_bytes(raw)
            from_file = self.cli(b"not the request", "--input", str(path))
        self.assertEqual(from_file.returncode, 0, from_file.stderr)
        self.assertEqual(json.loads(from_file.stdout), result)

    def test_unicode_units_preserve_combining_marks_and_emoji(self) -> None:
        text = "ZÅ λ\u0301🧪"
        result = measure({"text": text})
        self.assertEqual(result["metrics"]["code_points"], 6)
        self.assertEqual(result["metrics"]["letters"], 3)
        self.assertEqual(result["text_sha256"], hashlib.sha256(text.encode()).hexdigest())
        normalized = measure({"text": "ZÅ λ́🧪"})
        self.assertEqual(result["input_sha256"], normalized["input_sha256"])
        self.assertNotEqual(measure({"text": "é"})["text_sha256"],
                            measure({"text": "e\u0301"})["text_sha256"])
        self.assertEqual(measure({"text": "a", "needle": "a"})["input_sha256"],
                         measure({"needle": "a", "text": "a"})["input_sha256"])

    def test_source_commands_and_python_are_inert_cli_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "must not exist"
            text = f"$(touch '{marker}')\n__import__('pathlib').Path({str(marker)!r}).touch()"
            raw = json.dumps({"text": text, "needle": "touch"}).encode()
            process = self.cli(raw)
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result["metrics"]["literal_occurrences"], 2)
            self.assertEqual(result["text_sha256"], hashlib.sha256(text.encode()).hexdigest())
            self.assertFalse(marker.exists())

    def test_occurrences_are_case_sensitive_and_overlap_is_explicit(self) -> None:
        self.assertEqual(measure({"text": "aAa", "needle": "a"})["metrics"]["literal_occurrences"], 2)
        self.assertEqual(measure({"text": "aaaa", "needle": "aa"})["metrics"]["literal_occurrences"], 2)
        self.assertEqual(measure({"text": "aaaa", "needle": "aa", "overlapping": True})
                         ["metrics"]["literal_occurrences"], 3)

    def test_word_convention_excludes_fences_and_standalone_markup(self) -> None:
        text = "```python\nhello world\n```\n** # - > 1. +\nlast"
        self.assertEqual(measure({"text": text})["metrics"]["words"], 3)

    def test_half_up_budgets_and_ranges(self) -> None:
        text = "one two three four five"
        expected = {"trim_the_fat": (5, 5), "less_wordy": (4, 4),
                    "more_concise": (3, 3), "more_succinct": (2, 3)}
        for level, (minimum, maximum) in expected.items():
            with self.subTest(level=level):
                budget = measure({"text": text, "level": level})["budget"]
                self.assertEqual((budget["min_words"], budget["max_words"]), (minimum, maximum))
        self.assertEqual(measure({"text": text, "remaining_percent": 50})["budget"]["min_words"], 3)
        self.assertEqual(measure({"text": text, "remaining_percent": [40, 60]})["budget"]["max_words"], 3)
        self.assertEqual(measure({"text": text, "budget_words": [7, 9]})["budget"]["min_words"], 7)
        self.assertEqual(measure({"text": text, "remaining_percent": 33.3})["budget"]["min_words"], 2)

    def test_comparison_rejects_overcompression_and_longer_candidate(self) -> None:
        request = {"text": "one two three four five", "candidate": "one two", "level": "less_wordy"}
        result = measure(request)
        self.assertFalse(result["comparison"]["within_budget"])
        self.assertEqual(result["comparison"]["reduction_fraction"], {"numerator": 3, "denominator": 5})
        self.assertEqual(result["comparison"]["reduction"], 0.6)
        request["candidate"] = "one two three four"
        self.assertTrue(measure(request)["comparison"]["within_budget"])
        request["candidate"] = "one two three four five six"
        self.assertLess(measure(request)["comparison"]["reduction"], 0)
        self.assertIsNone(measure({"text": "a", "candidate": "b"})["comparison"]["within_budget"])

    def test_empty_input_never_divides_by_zero(self) -> None:
        result = measure({"text": "", "candidate": "", "level": "less_wordy"})
        self.assertEqual(result["metrics"]["words"], 0)
        self.assertIsNone(result["comparison"]["reduction"])
        self.assertIsNone(result["comparison"]["reduction_fraction"])
        self.assertTrue(result["comparison"]["within_budget"])
        result = measure({"text": "", "candidate": "a", "level": "less_wordy"})
        self.assertFalse(result["comparison"]["within_budget"])

    def test_literal_block_preserves_nested_fences_and_trailing_newlines(self) -> None:
        for text in ("", "\n", "\r", "\r\n", "line", "line\n", "line\r",
                     "line\r\n", "line\n\n", "First.\n\nSecond.\r\n",
                     "````markdown\n```text\nexample\n```\n````"):
            with self.subTest(text=text):
                result = measure({"text": "old", "candidate": text, "include_presentation": True})
                presentation = result["presentation"]
                marker = "`" * result["candidate_metrics"]["fence_length"]
                block = presentation["literal_block"]
                self.assertTrue(presentation["separator_newline_added"])
                prefix, suffix = marker + "text\n", "\n" + marker
                self.assertTrue(block.startswith(prefix))
                self.assertTrue(block.endswith(suffix))
                payload = block[len(prefix):-len(suffix)]
                self.assertEqual(payload.encode("utf-8"), text.encode("utf-8"))

    def test_cli_literal_block_always_has_an_independent_wrapper_lf(self) -> None:
        for text, expected in (("", "```text\n\n```"),
                               ("x\n", "```text\nx\n\n```"),
                               ("x\r", "```text\nx\r\n```"),
                               ("x\r\n", "```text\nx\r\n\n```")):
            with self.subTest(payload=repr(text)):
                process = self.cli(json.dumps({"text": text, "include_presentation": True}).encode())
                self.assertEqual(process.returncode, 0, process.stderr)
                result = json.loads(process.stdout)
                self.assertEqual(result["presentation"]["literal_block"], expected)
                self.assertEqual(result["text_sha256"], hashlib.sha256(text.encode()).hexdigest())

    def test_full_quote_escapes_each_original_punctuation_once(self) -> None:
        text = "Full span " + string.punctuation + " stays literal."
        presentation = measure({"text": text, "candidate": text.upper(), "include_presentation": True})["presentation"]
        for name, original in (("before_quote", text), ("after_quote", text.upper())):
            quoted = presentation[name]
            self.assertTrue(quoted.startswith('**"') and quoted.endswith('"**'))
            escaped = quoted[3:-3]
            restored, index = [], 0
            while index < len(escaped):
                if escaped[index] == "\\":
                    index += 1
                    self.assertIn(escaped[index], string.punctuation)
                restored.append(escaped[index])
                index += 1
            self.assertEqual("".join(restored), original)
        self.assertFalse(presentation["edits_verified"])

    def test_multiblock_quote_is_not_falsely_claimed_as_full_bold(self) -> None:
        for text in ("First.\n\nSecond.", "First.\r\n\r\nSecond.", "First.\r\rSecond."):
            result = measure({"text": text, "include_presentation": True})
            self.assertIsNone(result["presentation"]["before_quote"])
            self.assertIn("paragraph", result["presentation"]["quote_limit"])
        self.assertIsNotNone(measure({"text": "One\r\nparagraph.", "include_presentation": True})
                             ["presentation"]["before_quote"])

    def test_api_rejects_unsupported_and_malformed_requests(self) -> None:
        invalid = [[], {}, {"text": None}, {"text": "a", "needle": ""},
                   {"text": "a", "overlapping": False}, {"text": "a", "level": "unknown"},
                   {"text": "a", "include_presentation": 1}, {"text": "a", "extra": "ignored?"},
                   {"text": "a", "remaining_percent": float("nan")},
                   {"text": "a", "remaining_percent": float("inf")},
                   {"text": "a", "remaining_percent": [90, 70]},
                   {"text": "a", "remaining_percent": True},
                   {"text": "a", "remaining_percent": 101},
                   {"text": "a", "budget_words": 1.5},
                   {"text": "a", "level": "less_wordy", "budget_words": 1},
                   {"text": "\ud800"}]
        for request in invalid:
            with self.subTest(request=repr(request)):
                with self.assertRaises(ValueError):
                    measure(request)

    def test_cli_rejects_duplicate_nonfinite_and_invalid_json(self) -> None:
        invalid = [b'{"text":"a","text":"b"}', b'{"text":"a","remaining_percent":1e999}',
                   b'{"text":"a","remaining_percent":NaN}', b'{"text":"a",}', b"[]", b"\xff"]
        for raw in invalid:
            with self.subTest(raw=raw):
                process = self.cli(raw)
                self.assertEqual(process.returncode, 2, process.stderr)
                self.assertEqual(json.loads(process.stdout)["status"], "error")

    def test_input_and_output_limits_fail_without_partial_success(self) -> None:
        limit = HELPER["MAX_INPUT_BYTES"]
        with self.assertRaises(ValueError):
            measure({"text": "x" * (limit + 1)})
        process = self.cli(b" " * (limit + 1))
        self.assertEqual(process.returncode, 2)
        self.assertEqual(json.loads(process.stdout)["status"], "error")
        with self.assertRaises(ValueError):
            measure({"text": "`" * 800_000, "include_presentation": True})

    def test_cli_help_and_input_file_errors(self) -> None:
        help_result = self.cli(b"", "--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn(b"--input", help_result.stdout)
        with tempfile.TemporaryDirectory() as directory:
            missing = self.cli(b"", "--input", str(Path(directory) / "missing.json"))
            folder = self.cli(b"", "--input", directory)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(folder.returncode, 2)


if __name__ == "__main__":
    unittest.main()
