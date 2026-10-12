"""Credential-free tests for release validation and archive invariants."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlunsplit

from scripts import release


SOURCE_ROOT = Path(__file__).resolve().parent.parent


class ReleaseBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        for relative in ("plugin.json", "LICENSE", "PRIVACY.md", "assets/icon.webp"):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE_ROOT / relative, destination)
        shutil.copytree(SOURCE_ROOT / "skills", self.root / "skills")
        self.root_patch = patch.object(release, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def write_manifest(self, manifest: dict[str, object]) -> None:
        (self.root / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")

    def read_manifest(self) -> dict[str, object]:
        return json.loads((self.root / "plugin.json").read_text(encoding="utf-8"))

    def test_validation_returns_only_runtime_allowlist(self) -> None:
        files = release.validate()
        names = [path.relative_to(self.root).as_posix() for path in files]

        self.assertEqual(
            names,
            [
                "LICENSE",
                "PRIVACY.md",
                "assets/icon.webp",
                "plugin.json",
                "skills/proofread/SKILL.md",
                "skills/proofread/agents/openai.yaml",
            ],
        )
        self.assertFalse(any(name.startswith(("tests/", "docs/", ".codex-plugin/")) for name in names))

    def test_unlisted_skill_file_is_not_packaged(self) -> None:
        extra = self.root / "skills/proofread/private-notes.txt"
        extra.write_text("must not be shipped", encoding="utf-8")

        with self.assertRaisesRegex(release.ReleaseError, "not in the release allowlist"):
            release.validate()

    def test_metadata_https_urls_are_accepted(self) -> None:
        manifest = self.read_manifest()
        manifest["homepage"] = "https://github.com/altmn/english-proofreader-pro"
        manifest["repository"] = "https://github.com/altmn/english-proofreader-pro"
        manifest["author"]["url"] = "https://github.com/altmn"
        interface = manifest["extensions"]["com.openai"]["interface"]
        interface["websiteURL"] = "https://github.com/altmn/english-proofreader-pro"
        interface["supportURL"] = "https://github.com/altmn/english-proofreader-pro/issues"
        interface["privacyPolicyURL"] = "https://github.com/altmn/english-proofreader-pro/blob/master/PRIVACY.md"
        self.write_manifest(manifest)

        self.assertEqual(release.validate_manifest(), manifest)

    def test_local_compatibility_overlay_carries_urls_and_keeps_existing_fields(self) -> None:
        manifest = self.read_manifest()
        manifest["homepage"] = "https://github.com/altmn/english-proofreader-pro"
        manifest["repository"] = "https://github.com/altmn/english-proofreader-pro"
        manifest["author"]["url"] = "https://github.com/altmn"
        interface = manifest["extensions"]["com.openai"]["interface"]
        interface["websiteURL"] = "https://github.com/altmn/english-proofreader-pro"
        interface["supportURL"] = "https://github.com/altmn/english-proofreader-pro/issues"
        interface["privacyPolicyURL"] = "https://github.com/altmn/english-proofreader-pro/blob/master/PRIVACY.md"
        self.write_manifest(manifest)

        release.build()
        overlay = json.loads((self.root / "dist/local-plugin/.codex-plugin/plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(overlay["homepage"], manifest["homepage"])
        self.assertEqual(overlay["repository"], manifest["repository"])
        self.assertEqual(overlay["author"], manifest["author"])
        self.assertEqual(overlay["interface"], interface)
        self.assertEqual(overlay["skills"], "./skills/")
        self.assertEqual(overlay["name"], release.PLUGIN_NAME)
        self.assertIn("extensions", overlay)

    def test_metadata_urls_reject_insecure_malformed_credentials_whitespace_and_overlong_values(self) -> None:
        invalid_values = (
            "http://example.com",
            "https:///missing-host",
            # Synthetic userinfo tests URL rejection without a credential-shaped
            # URL literal that public-repository secret scanners would flag.
            urlunsplit(("https", "example-user:example-password@example.com", "/path", "", "")),
            "https://example.com/with space",
            "https://example.com/" + ("x" * release.MAX_METADATA_URL_CHARS),
        )
        for value in invalid_values:
            with self.subTest(value=value[:60]):
                manifest = self.read_manifest()
                manifest["homepage"] = value
                self.write_manifest(manifest)
                with self.assertRaises(release.ReleaseError):
                    release.validate_manifest()

    def test_interface_url_limit_is_1024_characters(self) -> None:
        value_at_limit = "https://a/" + ("x" * (release.MAX_INTERFACE_URL_CHARS - len("https://a/")))
        release.validate_https_url(value_at_limit, "interface.websiteURL", release.MAX_INTERFACE_URL_CHARS)

        with self.assertRaisesRegex(release.ReleaseError, "at most 1024 characters"):
            release.validate_https_url(value_at_limit + "x", "interface.websiteURL", release.MAX_INTERFACE_URL_CHARS)

    def test_terms_of_service_url_uses_interface_url_limit(self) -> None:
        manifest = self.read_manifest()
        interface = manifest["extensions"]["com.openai"]["interface"]
        interface["termsOfServiceURL"] = "https://a/" + ("x" * (release.MAX_INTERFACE_URL_CHARS - len("https://a/")))
        self.write_manifest(manifest)
        release.validate_manifest()

        interface["termsOfServiceURL"] += "x"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(release.ReleaseError, "interface.termsOfServiceURL.*1024"):
            release.validate_manifest()

    def test_review_commerce_is_false_and_description_is_bounded_text(self) -> None:
        manifest = self.read_manifest()
        openai = manifest["extensions"]["com.openai"]
        openai["review"] = {"commerce": False, "commerce_description": "No paid features or transactions."}
        self.write_manifest(manifest)
        release.validate_manifest()

        openai["review"]["commerce_description"] = "x" * 4000
        self.write_manifest(manifest)
        release.validate_manifest()

        for commerce in (True, "false", 0):
            with self.subTest(commerce=commerce):
                manifest = self.read_manifest()
                manifest["extensions"]["com.openai"]["review"]["commerce"] = commerce
                self.write_manifest(manifest)
                with self.assertRaisesRegex(release.ReleaseError, "commerce must be false"):
                    release.validate_manifest()

        manifest = self.read_manifest()
        manifest["extensions"]["com.openai"]["review"]["commerce"] = False
        manifest["extensions"]["com.openai"]["review"]["commerce_description"] = 12
        self.write_manifest(manifest)
        with self.assertRaisesRegex(release.ReleaseError, "commerce_description must be a string"):
            release.validate_manifest()

        manifest["extensions"]["com.openai"]["review"]["commerce"] = False
        manifest["extensions"]["com.openai"]["review"]["commerce_description"] = "x" * 4001
        self.write_manifest(manifest)
        with self.assertRaisesRegex(release.ReleaseError, "at most 4000 characters"):
            release.validate_manifest()

    def test_review_rejects_unrecognized_or_secret_fields(self) -> None:
        manifest = self.read_manifest()
        manifest["extensions"]["com.openai"]["review"] = {
            "commerce": False,
            "commerce_description": "No paid features.",
            "api_key": "not-a-real-key",
        }

        self.write_manifest(manifest)
        with self.assertRaisesRegex(release.ReleaseError, "review must contain only"):
            release.validate_manifest()

    def test_publication_countries_allow_empty_and_valid_codes_but_reject_bad_lists(self) -> None:
        manifest = self.read_manifest()
        publication = manifest["extensions"]["com.openai"]["publication"]
        publication["countries"] = []
        self.write_manifest(manifest)
        release.validate_manifest()

        publication["countries"] = ["US", "CA"]
        self.write_manifest(manifest)
        release.validate_manifest()

        for countries in (["US", "US"], ["us"], ["USA"], [1], "US"):
            with self.subTest(countries=countries):
                manifest = self.read_manifest()
                manifest["extensions"]["com.openai"]["publication"]["countries"] = countries
                self.write_manifest(manifest)
                with self.assertRaises(release.ReleaseError):
                    release.validate_manifest()

    def test_overlay_preserves_review_and_explicit_empty_countries(self) -> None:
        manifest = self.read_manifest()
        openai = manifest["extensions"]["com.openai"]
        openai["review"] = {"commerce": False, "commerce_description": "No paid features."}
        openai["publication"]["countries"] = []
        self.write_manifest(manifest)

        release.build()
        overlay = json.loads((self.root / "dist/local-plugin/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
        overlay_openai = overlay["extensions"]["com.openai"]

        self.assertEqual(overlay_openai["publication"], openai["publication"])
        self.assertEqual(overlay_openai["publication"]["countries"], [])
        self.assertEqual(overlay_openai["review"], openai["review"])

    def test_semver_rejects_leading_zero_numeric_prerelease_and_accepts_alphanumeric_and_build_metadata(self) -> None:
        manifest = self.read_manifest()
        manifest["version"] = "1.0.0-01"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(release.ReleaseError, "numeric prerelease identifiers"):
            release.validate_manifest()

        manifest["version"] = "1.0.0-alpha.1+build.01"
        self.write_manifest(manifest)
        self.assertEqual(release.validate_manifest()["version"], "1.0.0-alpha.1+build.01")

    def test_author_url_is_allowed_but_other_author_fields_are_rejected(self) -> None:
        manifest = self.read_manifest()
        manifest["author"]["url"] = "https://github.com/altmn"
        self.write_manifest(manifest)
        release.validate_manifest()

        manifest["author"]["email"] = "author@example.com"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(release.ReleaseError, "author.name"):
            release.validate_manifest()

    def test_skill_character_limit_is_exclusive_at_8000(self) -> None:
        skill_path = self.root / release.EXPECTED_SKILL
        header = "---\nname: proofread\ndescription: x\n---\n"
        skill_path.write_text(header + ("a" * (release.MAX_SKILL_CHARS - len(header))), encoding="utf-8")

        with self.assertRaisesRegex(release.ReleaseError, "must be under 8000"):
            release.validate_skill()

    def test_skill_frontmatter_and_absolute_path_failures(self) -> None:
        skill_path = self.root / release.EXPECTED_SKILL
        skill_path.write_text("---\nname: proofread\nname: proofread\ndescription: x\n---\nbody\n", encoding="utf-8")
        with self.assertRaisesRegex(release.ReleaseError, "duplicate name"):
            release.validate_skill()

        skill_path.write_text("---\nname: proofread\ndescription: x\n---\nAvoid /private/data.\n", encoding="utf-8")
        with self.assertRaisesRegex(release.ReleaseError, "unsafe absolute or parent-relative path"):
            release.validate_skill()

    def test_build_is_byte_for_byte_reproducible_and_has_fixed_metadata(self) -> None:
        first_path = release.build()
        first_bytes = first_path.read_bytes()
        second_path = release.build()

        self.assertEqual(first_path, second_path)
        self.assertEqual(first_bytes, second_path.read_bytes())
        with zipfile.ZipFile(second_path) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(
                archive.namelist(),
                [
                    "LICENSE",
                    "PRIVACY.md",
                    "assets/icon.webp",
                    "plugin.json",
                    "skills/proofread/SKILL.md",
                    "skills/proofread/agents/openai.yaml",
                ],
            )
            self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_build_rejects_symlinked_archive_target_without_touching_target(self) -> None:
        dist = self.root / "dist"
        dist.mkdir()
        sentinel = self.root / "keep.bin"
        sentinel.write_bytes(b"do not overwrite")
        archive_target = dist / f"{release.PLUGIN_NAME}-1.0.0.zip"
        archive_target.symlink_to(sentinel)

        with self.assertRaisesRegex(release.ReleaseError, "release output is not a regular file"):
            release.build()

        self.assertEqual(sentinel.read_bytes(), b"do not overwrite")

    def test_build_rejects_symlinked_dist_directory(self) -> None:
        external_dist = self.root / "external-dist"
        external_dist.mkdir()
        self.root.joinpath("dist").symlink_to(external_dist, target_is_directory=True)

        with self.assertRaisesRegex(release.ReleaseError, "dist must be a regular directory"):
            release.build()

        self.assertEqual(list(external_dist.iterdir()), [])

    def test_staging_failure_preserves_unexpected_user_file(self) -> None:
        stage = release.build().parent / "local-plugin"
        unexpected = stage / "user-data.txt"
        unexpected.write_text("preserve me", encoding="utf-8")

        with self.assertRaisesRegex(release.ReleaseError, "unexpected file"):
            release.build()

        self.assertEqual(unexpected.read_text(encoding="utf-8"), "preserve me")

    def test_staging_symlink_cannot_escape_destination_tree(self) -> None:
        stage = release.build().parent / "local-plugin"
        external = self.root / "outside-stage"
        external.mkdir()
        sentinel = external / "sentinel.txt"
        sentinel.write_text("preserve me", encoding="utf-8")
        shutil.rmtree(stage / "skills")
        (stage / "skills").symlink_to(external, target_is_directory=True)

        with self.assertRaisesRegex(release.ReleaseError, "staging output contains a symlink"):
            release.build()

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve me")

    def test_runtime_symlink_is_rejected(self) -> None:
        skill = self.root / "skills/proofread/SKILL.md"
        original = skill.read_bytes()
        target = self.root / "original-skill.md"
        target.write_bytes(original)
        skill.unlink()
        skill.symlink_to(target)

        with self.assertRaisesRegex(release.ReleaseError, "symlink"):
            release.validate()


if __name__ == "__main__":
    unittest.main()
