"""Offline text measurements; source strings are data, never executable code.

measure(request) accepts the same object as the UTF-8 JSON CLI. Required: text.
Optional: candidate, needle, overlapping, level, remaining_percent, budget_words,
include_presentation. The three budget selectors are mutually exclusive. Custom
budgets accept a point or a two-item inclusive range. Percentages describe words
remaining, not reduction. input_sha256 hashes canonical JSON; the CLI additionally
hashes the exact input bytes. No measurement establishes meaning or edit quality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import string
import sys
from fractions import Fraction
from pathlib import Path


MAX_INPUT_BYTES = 1024 * 1024
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
LEVELS = {
    "trim_the_fat": (90, 95),
    "less_wordy": (70, 70),
    "more_concise": (60, 60),
    "more_succinct": (40, 50),
}
FIELDS = {
    "text", "candidate", "needle", "overlapping", "level",
    "remaining_percent", "budget_words", "include_presentation",
}
FENCE_LINE = re.compile(r"[ \t]*(?:`{3,}[^`]*|~{3,}[^~]*)[ \t]*")
MARKUP_TOKEN = re.compile(r"(?:[`*_~#>+\-]+|[0-9]+[.)])")
PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
CONVENTIONS = {
    "characters": "Unicode code points, including whitespace; no normalization",
    "letters": "Unicode str.isalpha(); combining marks are not letters",
    "words": (
        "Whitespace-separated units; omit whole backtick/tilde fence lines "
        "with optional info text, tokens made only of `*_~#>+-, and numeric "
        "list-marker tokens such as 1. or 1)."
    ),
    "occurrences": "Case-sensitive literal matches; nonoverlapping by default",
    "budgets": "Words remaining; nearest integer with halves upward",
    "reduction": "(source_words-candidate_words)/source_words; null at zero source words",
    "input_sha256": "UTF-8 JSON with sorted keys, no whitespace, and unescaped Unicode",
    "text_sha256": "Exact UTF-8 string bytes; no normalization",
}


def _json_bytes(value: object, limit: int) -> bytes:
    result = bytearray()
    try:
        chunks = json.JSONEncoder(
            ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).iterencode(value)
        for chunk in chunks:
            encoded = chunk.encode("utf-8")
            if len(result) + len(encoded) > limit:
                raise ValueError("JSON exceeds the byte limit")
            result.extend(encoded)
    except (TypeError, UnicodeError, RecursionError) as error:
        raise ValueError("request must contain supported UTF-8 JSON values") from error
    return bytes(result)


def _text(request: dict, key: str, *, required: bool = False) -> str | None:
    if key not in request:
        if required:
            raise ValueError("text is required")
        return None
    value = request[key]
    if type(value) is not str:
        raise ValueError("text, candidate, and needle must be strings when supplied")
    if len(value) > MAX_INPUT_BYTES:
        raise ValueError("text exceeds the input byte limit")
    try:
        if len(value.encode("utf-8")) > MAX_INPUT_BYTES:
            raise ValueError("text exceeds the input byte limit")
    except UnicodeError as error:
        raise ValueError("strings must contain valid Unicode scalar values") from error
    return value


def _range(value: object, *, percent: bool) -> tuple[int | float, int | float]:
    values = value if type(value) is list else [value, value]
    if len(values) != 2:
        raise ValueError("a budget range must have two endpoints")
    ceiling = 100 if percent else MAX_INPUT_BYTES
    for endpoint in values:
        if type(endpoint) not in ((int, float) if percent else (int,)):
            raise ValueError("budget endpoints have unsupported types")
        if not 0 <= endpoint <= ceiling or not math.isfinite(endpoint):
            raise ValueError("budget endpoint is outside the supported range")
    if values[0] > values[1]:
        raise ValueError("budget endpoints must be ordered")
    return values[0], values[1]


def _half_up(words: int, percent: int | float) -> int:
    value = Fraction(str(percent)) * words / 100
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def _metrics(text: str, needle: str | None, overlapping: bool) -> dict:
    words = sum(
        1
        for line in text.splitlines()
        if not FENCE_LINE.fullmatch(line)
        for token in line.split()
        if not MARKUP_TOKEN.fullmatch(token)
    )
    longest = max((len(match.group()) for match in re.finditer(r"`+", text)), default=0)
    occurrences = None
    if needle is not None:
        occurrences = text.count(needle)
        if overlapping:
            occurrences, offset = 0, 0
            while (offset := text.find(needle, offset)) != -1:
                occurrences += 1
                offset += 1
    return {
        "code_points": len(text),
        "letters": sum(character.isalpha() for character in text),
        "words": words,
        "literal_occurrences": occurrences,
        "longest_backtick_run": longest,
        "fence_length": max(3, longest + 1),
    }


def _quote(text: str) -> str | None:
    # Markdown emphasis cannot span separate paragraph blocks. Call per span.
    if PARAGRAPH_BREAK.search(text.replace("\r\n", "\n").replace("\r", "\n")):
        return None
    escaped = "".join("\\" + character if character in string.punctuation else character
                      for character in text)
    return '**"' + escaped + '"**'


def measure(request: dict) -> dict:
    """Return deterministic measurements, or raise ValueError for invalid input."""
    if type(request) is not dict:
        raise ValueError("request must be a JSON object")
    if set(request) - FIELDS:
        raise ValueError("unsupported request field")
    text = _text(request, "text", required=True)
    candidate = _text(request, "candidate")
    needle = _text(request, "needle")
    if needle == "":
        raise ValueError("needle must not be empty")
    for name in ("overlapping", "include_presentation"):
        if name in request and type(request[name]) is not bool:
            raise ValueError("overlapping and include_presentation must be booleans")
    if "overlapping" in request and needle is None:
        raise ValueError("overlapping requires a needle")
    selectors = [name for name in ("level", "remaining_percent", "budget_words")
                 if name in request]
    if len(selectors) > 1:
        raise ValueError("supply only one budget selector")
    endpoints = None
    if "level" in request:
        if type(request["level"]) is not str or request["level"] not in LEVELS:
            raise ValueError("unsupported shortening level")
        endpoints = LEVELS[request["level"]]
    elif "remaining_percent" in request:
        endpoints = _range(request["remaining_percent"], percent=True)
    elif "budget_words" in request:
        endpoints = _range(request["budget_words"], percent=False)
    input_bytes = _json_bytes(request, MAX_INPUT_BYTES)
    overlap = request.get("overlapping", False)
    metrics = _metrics(text, needle, overlap)
    candidate_metrics = None if candidate is None else _metrics(candidate, needle, overlap)
    budget = None
    if endpoints is not None:
        minimum, maximum = endpoints
        if "budget_words" not in request:
            minimum, maximum = (_half_up(metrics["words"], point) for point in endpoints)
        budget = {"min_words": minimum, "max_words": maximum,
                  "kind": "point" if minimum == maximum else "range"}
    comparison = None
    if candidate_metrics is not None:
        original_words, final_words = metrics["words"], candidate_metrics["words"]
        difference = original_words - final_words
        comparison = {
            "source_words": original_words,
            "candidate_words": final_words,
            "reduction": difference / original_words if original_words else None,
            "reduction_fraction": {"numerator": difference, "denominator": original_words}
            if original_words else None,
            "within_budget": None if budget is None else
            budget["min_words"] <= final_words <= budget["max_words"],
            "meaning_verified": False,
        }
    result = {
        "schema_version": 1,
        "status": "ok",
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "candidate_sha256": None if candidate is None else
        hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
        "conventions": dict(CONVENTIONS, overlapping=overlap),
        "metrics": metrics,
        "candidate_metrics": candidate_metrics,
        "budget": budget,
        "comparison": comparison,
    }
    if request.get("include_presentation", False):
        output = text if candidate is None else candidate
        output_metrics = metrics if candidate_metrics is None else candidate_metrics
        marker = "`" * output_metrics["fence_length"]
        result["presentation"] = {
            "literal_block": marker + "text\n" + output + "\n" + marker,
            "separator_newline_added": True,
            "before_quote": _quote(text),
            "after_quote": None if candidate is None else _quote(candidate),
            "quote_limit": "For multi-paragraph Changes, request each full sentence or paragraph separately.",
            "edits_verified": False,
        }
    _json_bytes(result, MAX_OUTPUT_BYTES - 1)
    return result


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _number(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("non-finite JSON number")
    return value


def _constant(_token: str) -> None:
    raise ValueError("non-finite JSON number")


def _read(path: Path | None) -> bytes:
    if path is None:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
            with os.fdopen(descriptor, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError("input file must be a regular file")
                raw = stream.read(MAX_INPUT_BYTES + 1)
        except OSError as error:
            raise ValueError("cannot read the input file") from error
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds the byte limit")
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Read UTF-8 JSON from this file instead of stdin")
    arguments = parser.parse_args()
    try:
        raw = _read(arguments.input)
        try:
            request = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                                 parse_float=_number, parse_constant=_constant)
        except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
            raise ValueError("input must be valid UTF-8 JSON") from error
        result = measure(request)
        result["request_bytes_sha256"] = hashlib.sha256(raw).hexdigest()
        encoded = _json_bytes(result, MAX_OUTPUT_BYTES - 1)
    except (ValueError, OverflowError, RecursionError) as error:
        encoded = _json_bytes({"schema_version": 1, "status": "error", "error": str(error)},
                              MAX_OUTPUT_BYTES - 1)
        sys.stdout.buffer.write(encoded + b"\n")
        return 2
    sys.stdout.buffer.write(encoded + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
