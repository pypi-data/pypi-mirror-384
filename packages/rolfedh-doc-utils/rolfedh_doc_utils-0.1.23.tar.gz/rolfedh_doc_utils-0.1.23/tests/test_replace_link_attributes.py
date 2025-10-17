#!/usr/bin/env python3
"""Tests for replace_link_attributes module."""

import tempfile
from pathlib import Path
import pytest
from doc_utils.replace_link_attributes import (
    load_attributes,
    resolve_nested_attributes,
    replace_link_attributes_in_file,
)


class TestLoadAttributes:
    """Tests for load_attributes function."""

    def test_load_basic_attributes(self, tmp_path):
        """Test loading basic attribute definitions."""
        attr_file = tmp_path / "attributes.adoc"
        attr_file.write_text("""
// Common attributes
:product-name: My Product
:version: 1.0
:docs-url: https://docs.example.com
""")

        attrs = load_attributes(attr_file)

        assert len(attrs) == 3
        assert attrs["product-name"] == "My Product"
        assert attrs["version"] == "1.0"
        assert attrs["docs-url"] == "https://docs.example.com"


class TestResolveNestedAttributes:
    """Tests for resolve_nested_attributes function."""

    def test_resolve_simple_nesting(self):
        """Test resolving simple nested attributes."""
        attributes = {
            "base-url": "https://example.com",
            "docs-url": "{base-url}/docs",
            "guide-url": "{docs-url}/guide.html"
        }

        resolved = resolve_nested_attributes(attributes)

        assert resolved["base-url"] == "https://example.com"
        assert resolved["docs-url"] == "https://example.com/docs"
        assert resolved["guide-url"] == "https://example.com/docs/guide.html"

    def test_no_nesting(self):
        """Test attributes without nesting."""
        attributes = {
            "url1": "https://example.com",
            "url2": "https://another.com"
        }

        resolved = resolve_nested_attributes(attributes)

        assert resolved == attributes


class TestReplaceLinkAttributesInFile:
    """Tests for replace_link_attributes_in_file function."""

    def test_replace_in_link_macro(self, tmp_path):
        """Test replacing attributes in link: macros."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

See link:{docs-url}/guide.html[User Guide] for details.
""")

        attributes = {"docs-url": "https://docs.example.com"}

        count = replace_link_attributes_in_file(test_file, attributes, dry_run=False)

        assert count == 1
        content = test_file.read_text()
        assert "link:https://docs.example.com/guide.html[User Guide]" in content
        assert "{docs-url}" not in content

    def test_replace_in_xref_macro(self, tmp_path):
        """Test replacing attributes in xref: macros."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

Check xref:{base-path}/intro.adoc[Introduction].
""")

        attributes = {"base-path": "modules"}

        count = replace_link_attributes_in_file(test_file, attributes, dry_run=False)

        assert count == 1
        content = test_file.read_text()
        assert "xref:modules/intro.adoc[Introduction]" in content

    def test_preserve_link_text(self, tmp_path):
        """Test that link text is preserved unchanged."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test

link:{url}/page.html[Custom Link Text]
""")

        attributes = {"url": "https://example.com"}

        replace_link_attributes_in_file(test_file, attributes, dry_run=False)

        content = test_file.read_text()
        assert "[Custom Link Text]" in content

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry-run mode doesn't modify files."""
        test_file = tmp_path / "test.adoc"
        original_content = """
link:{url}/page.html[Link]
"""
        test_file.write_text(original_content)

        attributes = {"url": "https://example.com"}

        replace_link_attributes_in_file(test_file, attributes, dry_run=True)

        # File should be unchanged
        assert test_file.read_text() == original_content

    def test_macro_type_link_only(self, tmp_path):
        """Test processing only link: macros."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

link:{docs-url}/guide.html[Guide]
xref:{base-path}/intro.adoc[Intro]
""")

        attributes = {
            "docs-url": "https://docs.example.com",
            "base-path": "modules"
        }

        count = replace_link_attributes_in_file(test_file, attributes, dry_run=False, macro_type='link')

        assert count == 1
        content = test_file.read_text()
        assert "link:https://docs.example.com/guide.html[Guide]" in content
        assert "xref:{base-path}/intro.adoc[Intro]" in content  # xref unchanged

    def test_macro_type_xref_only(self, tmp_path):
        """Test processing only xref: macros."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

link:{docs-url}/guide.html[Guide]
xref:{base-path}/intro.adoc[Intro]
""")

        attributes = {
            "docs-url": "https://docs.example.com",
            "base-path": "modules"
        }

        count = replace_link_attributes_in_file(test_file, attributes, dry_run=False, macro_type='xref')

        assert count == 1
        content = test_file.read_text()
        assert "link:{docs-url}/guide.html[Guide]" in content  # link unchanged
        assert "xref:modules/intro.adoc[Intro]" in content

    def test_macro_type_both(self, tmp_path):
        """Test processing both link: and xref: macros."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

link:{docs-url}/guide.html[Guide]
xref:{base-path}/intro.adoc[Intro]
""")

        attributes = {
            "docs-url": "https://docs.example.com",
            "base-path": "modules"
        }

        count = replace_link_attributes_in_file(test_file, attributes, dry_run=False, macro_type='both')

        assert count == 2
        content = test_file.read_text()
        assert "link:https://docs.example.com/guide.html[Guide]" in content
        assert "xref:modules/intro.adoc[Intro]" in content

    def test_multiple_attributes_in_url(self, tmp_path):
        """Test replacing multiple attributes in a single URL."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
link:{base-url}/{version}/guide.html[Guide]
""")

        attributes = {
            "base-url": "https://example.com",
            "version": "v2.0"
        }

        count = replace_link_attributes_in_file(test_file, attributes, dry_run=False)

        assert count == 2
        content = test_file.read_text()
        assert "link:https://example.com/v2.0/guide.html[Guide]" in content
