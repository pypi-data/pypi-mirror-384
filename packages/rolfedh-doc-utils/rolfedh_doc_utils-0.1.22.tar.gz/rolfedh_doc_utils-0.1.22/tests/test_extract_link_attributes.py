#!/usr/bin/env python3
"""Tests for extract_link_attributes module."""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from doc_utils.extract_link_attributes import (
    find_attribute_files,
    find_link_macros,
    generate_attribute_name,
    group_macros_by_url,
    select_link_text,
    load_existing_attributes,
    create_attributes,
    prepare_file_updates,
    extract_link_attributes
)


class TestFindAttributeFiles:
    """Tests for find_attribute_files function."""

    def test_find_common_attribute_files(self, tmp_path):
        """Test finding common attribute file patterns."""
        # Create test files
        (tmp_path / "common-attributes.adoc").touch()
        (tmp_path / "attributes.adoc").touch()
        (tmp_path / "custom-attributes.adoc").touch()
        subdir = tmp_path / "modules"
        subdir.mkdir()
        (subdir / "module-attributes.adoc").touch()

        # Find files
        files = find_attribute_files(str(tmp_path))

        assert len(files) == 4
        assert "common-attributes.adoc" in files
        assert "attributes.adoc" in files
        assert "custom-attributes.adoc" in files
        assert "modules/module-attributes.adoc" in files

    def test_no_attribute_files(self, tmp_path):
        """Test when no attribute files exist."""
        files = find_attribute_files(str(tmp_path))
        assert files == []


class TestFindLinkMacros:
    """Tests for find_link_macros function."""

    def test_find_link_with_attributes(self, tmp_path):
        """Test finding link macros with attributes."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

See link:https://example.com/{product-version}/guide.html[User Guide] for details.

Also check xref:{base-url}/intro.html[Introduction].

Regular link without attributes: link:https://example.com/static.html[Static Link]
""")

        macros = find_link_macros(str(test_file))

        assert len(macros) == 2
        # First macro
        assert macros[0][0] == "link:https://example.com/{product-version}/guide.html[User Guide]"
        assert macros[0][1] == "https://example.com/{product-version}/guide.html"
        assert macros[0][2] == "User Guide"
        assert macros[0][3] == 4  # Line number (accounting for empty first line)

        # Second macro
        assert macros[1][0] == "xref:{base-url}/intro.html[Introduction]"
        assert macros[1][1] == "{base-url}/intro.html"
        assert macros[1][2] == "Introduction"
        assert macros[1][3] == 6  # Line number

    def test_no_macros_with_attributes(self, tmp_path):
        """Test file with no macros containing attributes."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

Regular link: link:https://example.com/guide.html[Guide]
""")

        macros = find_link_macros(str(test_file))
        assert len(macros) == 0

    def test_find_only_link_macros(self, tmp_path):
        """Test finding only link macros when macro_type='link'."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

See link:https://example.com/{version}/guide.html[Guide].
Also check xref:{base-url}/intro.html[Intro].
""")

        macros = find_link_macros(str(test_file), macro_type='link')

        assert len(macros) == 1
        assert macros[0][0] == "link:https://example.com/{version}/guide.html[Guide]"

    def test_find_only_xref_macros(self, tmp_path):
        """Test finding only xref macros when macro_type='xref'."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

See link:https://example.com/{version}/guide.html[Guide].
Also check xref:{base-url}/intro.html[Intro].
""")

        macros = find_link_macros(str(test_file), macro_type='xref')

        assert len(macros) == 1
        assert macros[0][0] == "xref:{base-url}/intro.html[Intro]"


class TestGenerateAttributeName:
    """Tests for generate_attribute_name function."""

    def test_generate_from_url_with_domain(self):
        """Test attribute name generation from URL with domain."""
        url = "https://docs.example.com/{version}/guide.html"
        existing = set()

        name = generate_attribute_name(url, existing, 1)

        assert name.startswith("link-")
        assert "docs-example" in name or "guide" in name

    def test_generate_unique_names(self):
        """Test generating unique names when conflicts exist."""
        url = "https://example.com/guide.html"
        existing = {"link-example-com-guide"}

        name = generate_attribute_name(url, existing, 1)

        assert name != "link-example-com-guide"
        assert name.startswith("link-")

    def test_clean_special_characters(self):
        """Test that special characters are cleaned."""
        url = "https://example.com/path with spaces/{attr}/file.html"
        existing = set()

        name = generate_attribute_name(url, existing, 1)

        # Should not contain spaces or special chars
        assert " " not in name
        assert "/" not in name
        assert "." not in name


class TestGroupMacrosByUrl:
    """Tests for group_macros_by_url function."""

    def test_group_same_urls(self):
        """Test grouping macros with the same URL."""
        macros = [
            ("file1.adoc", "link:url1[Text1]", "url1", "Text1", 1),
            ("file2.adoc", "link:url1[Text2]", "url1", "Text2", 5),
            ("file3.adoc", "link:url2[Text3]", "url2", "Text3", 10),
        ]

        groups = group_macros_by_url(macros)

        assert len(groups) == 2
        assert "url1" in groups
        assert "url2" in groups
        assert len(groups["url1"]) == 2
        assert len(groups["url2"]) == 1


class TestSelectLinkText:
    """Tests for select_link_text function."""

    def test_single_variation(self):
        """Test when there's only one link text variation."""
        variations = [
            ("file1.adoc", "Same Text", "link:url[Same Text]", 1),
            ("file2.adoc", "Same Text", "link:url[Same Text]", 2),
        ]

        result = select_link_text("url", variations, interactive=False)

        assert result == "Same Text"

    def test_non_interactive_most_common(self):
        """Test non-interactive mode selects most common text."""
        variations = [
            ("file1.adoc", "Text A", "link:url[Text A]", 1),
            ("file2.adoc", "Text B", "link:url[Text B]", 2),
            ("file3.adoc", "Text A", "link:url[Text A]", 3),
        ]

        result = select_link_text("url", variations, interactive=False)

        assert result == "Text A"  # Most common


class TestLoadExistingAttributes:
    """Tests for load_existing_attributes function."""

    def test_load_attributes(self, tmp_path):
        """Test loading existing attributes from file."""
        attr_file = tmp_path / "attributes.adoc"
        attr_file.write_text("""
// Common attributes
:product-name: My Product
:version: 1.0
:docs-url: https://docs.example.com
:link-guide: link:https://example.com/guide.html[User Guide]
""")

        attrs = load_existing_attributes(str(attr_file))

        assert len(attrs) == 4
        assert attrs["product-name"] == "My Product"
        assert attrs["version"] == "1.0"
        assert attrs["docs-url"] == "https://docs.example.com"
        assert attrs["link-guide"] == "link:https://example.com/guide.html[User Guide]"

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading from non-existent file."""
        attrs = load_existing_attributes(str(tmp_path / "missing.adoc"))
        assert attrs == {}


class TestCreateAttributes:
    """Tests for create_attributes function."""

    def test_create_new_attributes(self):
        """Test creating new attributes for URLs."""
        url_groups = {
            "https://example.com/{version}/guide.html": [
                ("file1.adoc", "Guide", "link:https://example.com/{version}/guide.html[Guide]", 1)
            ],
            "{base-url}/intro.html": [
                ("file2.adoc", "Intro", "xref:{base-url}/intro.html[Intro]", 2)
            ]
        }
        existing_attrs = {}

        new_attrs, existing_matched = create_attributes(url_groups, existing_attrs, interactive=False)

        assert len(new_attrs) == 2
        assert len(existing_matched) == 0
        # Check that attributes were created
        attr_values = list(new_attrs.values())
        assert any("link:https://example.com/{version}/guide.html[Guide]" in v for v in attr_values)
        assert any("xref:{base-url}/intro.html[Intro]" in v for v in attr_values)

    def test_skip_existing_urls(self, capsys):
        """Test that URLs with existing attributes are skipped."""
        url_groups = {
            "https://example.com/guide.html": [
                ("file1.adoc", "Guide", "link:https://example.com/guide.html[Guide]", 1)
            ]
        }
        existing_attrs = {
            "existing-link": "link:https://example.com/guide.html[Existing Guide]"
        }

        new_attrs, existing_matched = create_attributes(url_groups, existing_attrs, interactive=False)

        assert len(new_attrs) == 0
        assert len(existing_matched) == 1
        assert "existing-link" in existing_matched
        captured = capsys.readouterr()
        assert "already has attribute" in captured.out


class TestPrepareFileUpdates:
    """Tests for prepare_file_updates function."""

    def test_prepare_updates(self):
        """Test preparing file updates."""
        url_groups = {
            "url1": [
                ("file1.adoc", "Text1", "link:url1[Text1]", 1),
                ("file2.adoc", "Text1", "link:url1[Text1]", 2),
            ],
            "url2": [
                ("file1.adoc", "Text2", "link:url2[Text2]", 3),
            ]
        }
        attribute_mapping = {
            "link-1": "link:url1[Text1]",
            "link-2": "link:url2[Text2]"
        }

        updates = prepare_file_updates(url_groups, attribute_mapping)

        assert len(updates) == 2
        assert "file1.adoc" in updates
        assert "file2.adoc" in updates
        assert len(updates["file1.adoc"]) == 2  # Two replacements in file1
        assert len(updates["file2.adoc"]) == 1  # One replacement in file2

        # Check replacement pairs
        file1_updates = updates["file1.adoc"]
        assert ("link:url1[Text1]", "{link-1}") in file1_updates
        assert ("link:url2[Text2]", "{link-2}") in file1_updates


class TestExtractLinkAttributesIntegration:
    """Integration tests for the main extract_link_attributes function."""

    def test_full_extraction_dry_run(self, tmp_path, capsys):
        """Test full extraction process in dry-run mode."""
        # Create test structure
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # Create attribute file
        attr_file = tmp_path / "common-attributes.adoc"
        attr_file.write_text(":existing-attr: value\n")

        # Create test .adoc file with links
        test_file = modules_dir / "test.adoc"
        test_file.write_text("""
= Test Module

See link:https://docs.example.com/{version}/guide.html[Installation Guide] for setup.

Also check link:https://docs.example.com/{version}/guide.html[Setup Guide] for config.

And xref:{base-url}/intro.html[Introduction] for overview.
""")

        # Run extraction in dry-run mode
        os.chdir(tmp_path)
        result = extract_link_attributes(
            attributes_file=str(attr_file),
            scan_dirs=[str(modules_dir)],
            interactive=False,
            dry_run=True
        )

        assert result is True

        # Check output
        captured = capsys.readouterr()
        assert "Found 3 link and xref macros" in captured.out
        assert "Grouped into 2 unique URLs" in captured.out
        assert "[DRY RUN]" in captured.out

        # Verify no files were modified
        assert attr_file.read_text() == ":existing-attr: value\n"

    def test_full_extraction_with_write(self, tmp_path):
        """Test full extraction process with actual file updates."""
        # Create test structure
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # Create attribute file
        attr_file = tmp_path / "common-attributes.adoc"
        attr_file.write_text(":existing-attr: value\n")

        # Create test .adoc file
        test_file = modules_dir / "test.adoc"
        original_content = """
= Test Module

See link:https://example.com/{version}/guide.html[Guide] for info.
"""
        test_file.write_text(original_content)

        # Run extraction
        os.chdir(tmp_path)
        result = extract_link_attributes(
            attributes_file=str(attr_file),
            scan_dirs=[str(modules_dir)],
            interactive=False,
            dry_run=False
        )

        assert result is True

        # Check that attribute file was updated
        attr_content = attr_file.read_text()
        assert ":existing-attr: value" in attr_content
        assert "// Extracted link attributes" in attr_content
        assert "link:https://example.com/{version}/guide.html[Guide]" in attr_content

        # Check that .adoc file was updated
        updated_content = test_file.read_text()
        assert "link:https://example.com/{version}/guide.html[Guide]" not in updated_content
        assert "{link-" in updated_content  # Should have attribute reference