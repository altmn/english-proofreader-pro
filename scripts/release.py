#!/usr/bin/env python3
"""Validate and reproducibly package the English Proofreader Pro plugin."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "english-proofreader-pro"
EXPECTED_SKILL = "skills/proofread/SKILL.md"
EXPECTED_SKILL_FILES = (EXPECTED_SKILL, "skills/proofread/agents/openai.yaml")
EXPECTED_ICON = "assets/icon.webp"
MAX_SKILL_CHARS = 8000
MAX_METADATA_URL_CHARS = 2048
MAX_INTERFACE_URL_CHARS = 1024
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
PLACEHOLDER = re.compile(
    r"\b(?:TODO|FIXME|TBD|XXX|CHANGEME|PLACEHOLDER)\b|"
    r"\[(?:INSERT|ADD|REPLACE|TODO|TBD)[^\]]*\]|"
    r"<(?:your[-_ ]|insert[-_ ])[^>]+>",
    re.IGNORECASE,
)
IGNORED_PACKAGE_METADATA = {".ds_store"}
ROOT_URL_FIELDS = {"homepage", "repository"}
AUTHOR_URL_FIELDS = {"url"}
INTERFACE_URL_FIELDS = {"websiteURL", "supportURL", "privacyPolicyURL"}


class ReleaseError(Exception):
    """A user-correctable validation or packaging failure."""


def fail(message: str) -> None:
    raise ReleaseError(message)


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"cannot read {label} as UTF-8: {exc}")


def check_placeholders(text: str, label: str) -> None:
    match = PLACEHOLDER.search(text)
    if match:
        fail(f"unfinished placeholder in {label}: {match.group(0)!r}")


def validate_https_url(value: Any, label: str, max_chars: int = MAX_METADATA_URL_CHARS) -> None:
    if not isinstance(value, str) or not value or len(value) > max_chars:
        fail(f"{label} must be a non-empty HTTPS URL of at most {max_chars} characters")
    if any(character.isspace() or ord(character) < 0x20 for character in value) or "\\" in value:
        fail(f"{label} must not contain whitespace, control characters, or backslashes")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        # Accessing .port also detects malformed ports and bracketed hosts.
        parsed.port
    except ValueError:
        fail(f"{label} must be a valid absolute HTTPS URL")
    if parsed.scheme.lower() != "https" or not parsed.netloc or not hostname:
        fail(f"{label} must be a valid absolute HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        fail(f"{label} must not contain URL credentials")


def safe_relative_path(raw: str, label: str) -> str:
    if not raw or "\\" in raw or raw.startswith("/"):
        fail(f"unsafe {label} path: {raw!r}")
    path = PurePosixPath(raw)
    if any(part in ("", ".", "..") for part in path.parts) or path.as_posix() != raw:
        fail(f"unsafe {label} path: {raw!r}")
    return raw


def require_regular_file(relative: str) -> Path:
    safe_relative_path(relative, "runtime")
    path = ROOT.joinpath(*PurePosixPath(relative).parts)
    try:
        parent = ROOT
        for part in PurePosixPath(relative).parts[:-1]:
            parent = parent / part
            if parent.is_symlink():
                fail(f"runtime path contains a symlinked directory: {relative}")
        if path.is_symlink():
            fail(f"required runtime file may not be a symlink: {relative}")
        if not path.is_file():
            fail(f"required runtime file is missing or not a regular file: {relative}")
    except OSError as exc:
        fail(f"cannot inspect {relative}: {exc}")
    return path


def parse_webp_dimensions(data: bytes) -> tuple[int, int] | None:
    """Read dimensions from common WebP bitstreams without external libraries."""
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    offset = 12
    while offset + 8 <= len(data):
        kind = data[offset : offset + 4]
        size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        chunk = data[offset + 8 : offset + 8 + size]
        if len(chunk) != size:
            return None
        if kind == b"VP8X" and size >= 10:
            return (1 + int.from_bytes(chunk[4:7], "little"), 1 + int.from_bytes(chunk[7:10], "little"))
        if kind == b"VP8 " and size >= 10 and chunk[3:6] == b"\x9d\x01\x2a":
            return (int.from_bytes(chunk[6:8], "little") & 0x3FFF, int.from_bytes(chunk[8:10], "little") & 0x3FFF)
        if kind == b"VP8L" and size >= 5 and chunk[0] == 0x2F:
            bits = int.from_bytes(chunk[1:5], "little")
            return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
        offset += 8 + size + (size & 1)
    return None


def validate_manifest() -> dict[str, Any]:
    manifest_path = require_regular_file("plugin.json")
    try:
        manifest = json.loads(read_text(manifest_path, "plugin.json"))
    except json.JSONDecodeError as exc:
        fail(f"plugin.json is not valid JSON: {exc}")
    if not isinstance(manifest, dict):
        fail("plugin.json must contain a JSON object")

    # Validate the subset of the Agent Plugin manifest used by this portable
    # skill-only package, including its OpenAI interface extension.
    required = {"$schema", "name", "version", "description", "author", "license", "keywords", "extensions"}
    missing = sorted(required - manifest.keys())
    if missing:
        fail(f"plugin.json is missing required field(s): {', '.join(missing)}")
    allowed = required | ROOT_URL_FIELDS
    extra = sorted(manifest.keys() - allowed)
    if extra:
        fail(f"unsupported plugin.json field(s): {', '.join(extra)}")
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        fail("plugin.json $schema must identify the Agent Plugin 1.0 schema")

    checks = (("name", PLUGIN_NAME, 64), ("license", "MIT", 32))
    for key, expected, max_length in checks:
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > max_length:
            fail(f"plugin.json {key} must be a non-empty string of at most {max_length} characters")
        if value != expected:
            fail(f"plugin.json {key} must be {expected!r}")
    author = manifest.get("author")
    if not isinstance(author, dict) or not {"name"}.issubset(author) or set(author) - ({"name"} | AUTHOR_URL_FIELDS) or author.get("name") != "Alex Allen":
        fail("plugin.json author.name must be 'Alex Allen'")
    for key in sorted(ROOT_URL_FIELDS):
        if key in manifest:
            validate_https_url(manifest[key], f"plugin.json {key}")
    for key in sorted(AUTHOR_URL_FIELDS):
        if key in author:
            validate_https_url(author[key], f"plugin.json author.{key}")
    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        fail("plugin.json version must be valid semantic versioning")
    prerelease = version.split("+", 1)[0].partition("-")[2]
    if any(identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0") for identifier in prerelease.split(".")):
        fail("plugin.json version must follow semantic versioning (numeric prerelease identifiers may not have leading zeroes)")
    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 300:
        fail("plugin.json description must be non-empty and at most 300 characters")

    keywords = manifest.get("keywords")
    if not isinstance(keywords, list) or not keywords or any(not isinstance(word, str) or not word.strip() or len(word) > 64 for word in keywords):
        fail("plugin.json keywords must be a non-empty list of short strings")
    extensions = manifest.get("extensions")
    if not isinstance(extensions, dict) or set(extensions) != {"com.openai"}:
        fail("plugin.json extensions must contain only com.openai")
    openai = extensions.get("com.openai")
    if not isinstance(openai, dict) or set(openai) != {"interface", "publication"}:
        fail("plugin.json com.openai extension must contain interface and publication")
    interface = openai.get("interface")
    required_interface_fields = {"displayName", "shortDescription", "longDescription", "developerName", "category", "capabilities", "defaultPrompt", "composerIcon", "logo"}
    allowed_interface_fields = required_interface_fields | INTERFACE_URL_FIELDS
    if not isinstance(interface, dict) or not required_interface_fields.issubset(interface) or set(interface) - allowed_interface_fields:
        fail("plugin.json com.openai.interface does not match the supported portable interface schema")
    string_limits = {"displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80, "category": 64}
    for key, maximum in string_limits.items():
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            fail(f"plugin.json interface.{key} must be non-empty and at most {maximum} characters")
    for key in sorted(INTERFACE_URL_FIELDS):
        if key in interface:
            validate_https_url(interface[key], f"plugin.json interface.{key}", MAX_INTERFACE_URL_CHARS)
    if interface["developerName"] != "Alex Allen":
        fail("plugin.json interface.developerName must be 'Alex Allen'")
    if interface["category"] != "Productivity":
        fail("plugin.json interface.category must be 'Productivity'")
    if interface.get("composerIcon") != "./assets/icon.webp" or interface.get("logo") != "./assets/icon.webp":
        fail("plugin.json composerIcon and logo must both reference ./assets/icon.webp")
    for key in ("composerIcon", "logo"):
        safe_relative_path(interface[key][2:], f"interface.{key}")
    capabilities = interface.get("capabilities")
    prompts = interface.get("defaultPrompt")
    if not isinstance(capabilities, list) or not capabilities or len(capabilities) > 20 or any(not isinstance(value, str) or not value.strip() or len(value) > 120 for value in capabilities):
        fail("plugin.json interface.capabilities must contain 1–20 non-empty strings of at most 120 characters")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or any(not isinstance(value, str) or not value.strip() or len(value) > 128 for value in prompts):
        fail("plugin.json interface.defaultPrompt must contain 1–3 non-empty strings of at most 128 characters")
    if len(set(prompts)) != len(prompts):
        fail("plugin.json interface.defaultPrompt entries must be unique")
    publication = openai.get("publication")
    if not isinstance(publication, dict) or set(publication) != {"release_notes"} or not isinstance(publication.get("release_notes"), str) or not publication["release_notes"].strip() or len(publication["release_notes"]) > 500:
        fail("plugin.json publication.release_notes must be a non-empty string of at most 500 characters")
    icon_path = require_regular_file(EXPECTED_ICON)
    dimensions = parse_webp_dimensions(icon_path.read_bytes())
    if dimensions != (1024, 1024):
        fail(f"{EXPECTED_ICON} must be a valid 1024x1024 WebP (detected {dimensions})")

    manifest_text = read_text(manifest_path, "plugin.json")
    check_placeholders(manifest_text, "plugin.json")
    return manifest


def validate_skill() -> list[Path]:
    skill_path = require_regular_file(EXPECTED_SKILL)
    text = read_text(skill_path, EXPECTED_SKILL)
    if len(text) >= MAX_SKILL_CHARS:
        fail(f"{EXPECTED_SKILL} must be under {MAX_SKILL_CHARS} Unicode characters (currently {len(text)})")
    lines = text.splitlines()
    if len(lines) < 5 or lines[0].strip() != "---":
        fail(f"{EXPECTED_SKILL} must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        fail(f"{EXPECTED_SKILL} frontmatter is not closed")
    frontmatter = lines[1:end]
    fields: dict[str, str] = {}
    for line in frontmatter:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if not match:
            fail(f"unsupported YAML frontmatter line in {EXPECTED_SKILL}: {line!r}")
        key, raw_value = match.groups()
        if key in fields:
            fail(f"duplicate {key} key in {EXPECTED_SKILL} frontmatter")
        raw_value = raw_value.strip()
        if raw_value[:1] in {"'", '"'}:
            quote = raw_value[0]
            if len(raw_value) < 2 or raw_value[-1] != quote or quote in raw_value[1:-1]:
                fail(f"unsupported quoted scalar in {EXPECTED_SKILL} frontmatter: {raw_value!r}")
            value = raw_value[1:-1]
        else:
            if raw_value[-1:] in {"'", '"'}:
                fail(f"unmatched quote in {EXPECTED_SKILL} frontmatter: {raw_value!r}")
            value = raw_value
        fields[key] = value
    if set(fields) != {"name", "description"}:
        fail(f"{EXPECTED_SKILL} frontmatter must contain exactly name and description")
    for field in ("name", "description"):
        if not fields.get(field):
            fail(f"{EXPECTED_SKILL} frontmatter requires a non-empty {field}")
    if fields["name"] != "proofread":
        fail(f"{EXPECTED_SKILL} frontmatter name must be 'proofread'")
    if len(fields["name"]) > 64 or len(fields["description"]) > 1024:
        fail(f"{EXPECTED_SKILL} frontmatter name/description exceeds supported metadata limits")
    check_placeholders(text, EXPECTED_SKILL)
    if re.search(r"(?:^|\s)(?:\.\./|/|[A-Za-z]:\\)", text):
        fail(f"{EXPECTED_SKILL} contains a potentially unsafe absolute or parent-relative path")

    skills_root = ROOT / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        fail("skills must be a regular directory")
    allowed_files = set(EXPECTED_SKILL_FILES)
    files: list[Path] = []
    for path in sorted(skills_root.rglob("*")):
        if path.is_symlink():
            fail(f"skill package may not contain symlinks: {path.relative_to(ROOT)}")
        if path.is_file():
            relative = path.relative_to(ROOT).as_posix()
            if path.name.lower() in IGNORED_PACKAGE_METADATA:
                continue
            if relative not in allowed_files:
                fail(f"unexpected skill package file is not in the release allowlist: {relative}")
            content = read_text(path, relative)
            check_placeholders(content, relative)
            files.append(path)
    expected_paths = [require_regular_file(relative) for relative in EXPECTED_SKILL_FILES]
    if set(files) != set(expected_paths):
        missing_files = sorted(allowed_files - {path.relative_to(ROOT).as_posix() for path in files})
        fail(f"required skill package file(s) missing: {', '.join(missing_files)}")
    return expected_paths


def validate() -> list[Path]:
    validate_manifest()
    skill_files = validate_skill()
    package = [require_regular_file("plugin.json"), *skill_files,
               require_regular_file(EXPECTED_ICON), require_regular_file("LICENSE"),
               require_regular_file("PRIVACY.md")]
    # All packaged material is text except the explicitly checked icon.
    for path in package:
        if path.suffix.lower() not in {".webp"}:
            relative = path.relative_to(ROOT).as_posix()
            text = read_text(path, relative)
            check_placeholders(text, relative)
    return sorted(set(package), key=lambda p: p.relative_to(ROOT).as_posix())


def build() -> Path:
    files = validate()
    manifest = validate_manifest()
    output = Path("dist") / f"{PLUGIN_NAME}-{manifest['version']}.zip"
    output_path = ROOT / output
    if output_path.parent.is_symlink() or (output_path.parent.exists() and not output_path.parent.is_dir()):
        fail("dist must be a regular directory before building the release archive")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.is_symlink() or (output_path.exists() and not output_path.is_file()):
        fail(f"release output is not a regular file: {output.as_posix()}")
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    try:
        with zipfile.ZipFile(output_path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                fail(f"built ZIP failed CRC validation at {bad_member}")
            actual = archive.namelist()
            expected = [path.relative_to(ROOT).as_posix() for path in files]
            if actual != expected:
                fail("built ZIP contents differ from the release allowlist")
    except (OSError, zipfile.BadZipFile) as exc:
        fail(f"built ZIP could not be verified: {exc}")
    stage_local_plugin(files, manifest)
    return output_path


def stage_local_plugin(files: list[Path], manifest: dict[str, Any]) -> Path:
    """Stage the runtime package plus a legacy Codex manifest for local testing."""
    stage_root = ROOT / "dist" / "local-plugin"
    dist_root = stage_root.parent
    if dist_root.is_symlink() or not dist_root.is_dir():
        fail("dist must be a regular directory before staging the local plugin")
    if stage_root.is_symlink() or (stage_root.exists() and not stage_root.is_dir()):
        fail("dist/local-plugin must be a regular directory")

    canonical_paths = {path.relative_to(ROOT).as_posix() for path in files}
    compatibility_path = ".codex-plugin/plugin.json"
    expected_files = canonical_paths | {compatibility_path}
    expected_dirs = {
        parent.as_posix()
        for name in expected_files
        for parent in PurePosixPath(name).parents
        if parent.as_posix() != "."
    }

    # Never clear the staging directory: fail closed if it contains anything
    # outside this script's explicit output set, preserving user data.
    if stage_root.exists():
        for path in stage_root.rglob("*"):
            relative = path.relative_to(stage_root).as_posix()
            if path.is_symlink():
                fail(f"staging output contains a symlink; refusing to overwrite: dist/local-plugin/{relative}")
            if path.is_dir() and relative not in expected_dirs:
                fail(f"staging output contains an unexpected directory: dist/local-plugin/{relative}")
            if path.is_file() and relative not in expected_files:
                fail(f"staging output contains an unexpected file: dist/local-plugin/{relative}")

    # The compatibility manifest mirrors the canonical root identity and
    # translates the portable OpenAI extension to the legacy overlay shape.
    openai_extension = manifest["extensions"]["com.openai"]
    legacy_manifest = {
        "name": manifest["name"],
        "version": manifest["version"],
        "description": manifest["description"],
        "author": manifest["author"],
        "license": manifest["license"],
        "keywords": manifest["keywords"],
        "skills": "./skills/",
        "interface": openai_extension["interface"],
        "extensions": {"com.openai": {"publication": openai_extension["publication"]}},
    }
    for key in sorted(ROOT_URL_FIELDS):
        if key in manifest:
            legacy_manifest[key] = manifest[key]

    stage_root.mkdir(parents=True, exist_ok=True)
    for source in files:
        relative = source.relative_to(ROOT)
        destination = stage_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink() or (destination.exists() and not destination.is_file()):
            fail(f"staging target is not a regular file: dist/local-plugin/{relative.as_posix()}")
        shutil.copyfile(source, destination)

    compatibility_manifest = stage_root / compatibility_path
    compatibility_manifest.parent.mkdir(parents=True, exist_ok=True)
    if compatibility_manifest.is_symlink() or (compatibility_manifest.exists() and not compatibility_manifest.is_file()):
        fail("staging target is not a regular file: dist/local-plugin/.codex-plugin/plugin.json")
    compatibility_manifest.write_text(
        json.dumps(legacy_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return stage_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build"))
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            files = validate()
            print(f"Validation passed: {len(files)} runtime files are ready for release.")
        else:
            path = build()
            print(f"Built and verified {path.relative_to(ROOT)} and staged dist/local-plugin")
    except (ReleaseError, OSError, UnicodeError) as exc:
        print(f"release: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
