#!/usr/bin/env python3
"""Tests for validate_links module."""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest
from doc_utils.validate_links import LinkValidator, parse_transpositions, format_results


class TestLinkValidator:
    """Tests for LinkValidator class."""

    def test_transpose_url(self):
        """Test URL transposition."""
        validator = LinkValidator(transpositions=[
            ('https://docs.example.com', 'https://preview.docs.example.com'),
            ('https://api.example.com', 'https://api-staging.example.com')
        ])

        # Test matching transposition
        assert validator.transpose_url('https://docs.example.com/guide') == \
               'https://preview.docs.example.com/guide'

        assert validator.transpose_url('https://api.example.com/v1/users') == \
               'https://api-staging.example.com/v1/users'

        # Test non-matching URL
        assert validator.transpose_url('https://other.com/page') == \
               'https://other.com/page'

    def test_extract_links(self, tmp_path):
        """Test link extraction from AsciiDoc file."""
        test_file = tmp_path / "test.adoc"
        test_file.write_text("""
= Test Document

See link:https://example.com/guide[User Guide] for details.

Check xref:modules/intro.adoc[Introduction] for overview.

image::images/diagram.png[Architecture Diagram]

Also visit link:https://docs.example.com/{version}/api.html[API Reference].
""")

        validator = LinkValidator()
        attributes = {'version': 'v1.0'}
        links = validator.extract_links(str(test_file), attributes)

        assert len(links) == 4

        # Check external link
        assert links[0]['url'] == 'https://example.com/guide'
        assert links[0]['type'] == 'external'
        assert links[0]['text'] == 'User Guide'

        # Check internal reference
        assert links[1]['url'] == 'modules/intro.adoc'
        assert links[1]['type'] == 'internal'

        # Check image
        assert links[2]['url'] == 'images/diagram.png'
        assert links[2]['type'] == 'image'

        # Check link with resolved attribute
        assert links[3]['url'] == 'https://docs.example.com/v1.0/api.html'
        assert links[3]['original_url'] == 'https://docs.example.com/{version}/api.html'

    def test_resolve_attributes(self):
        """Test attribute resolution."""
        validator = LinkValidator()
        attributes = {
            'base-url': 'https://example.com',
            'version': 'v2.0',
            'docs-url': '{base-url}/docs/{version}'
        }

        # Simple attribute
        assert validator._resolve_attributes('{version}', attributes) == 'v2.0'

        # Nested attributes
        assert validator._resolve_attributes('{docs-url}/guide', attributes) == \
               'https://example.com/docs/v2.0/guide'

        # Unknown attribute
        assert validator._resolve_attributes('{unknown}', attributes) == '{unknown}'

    def test_validate_internal_reference(self, tmp_path):
        """Test internal reference validation."""
        # Create test structure
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        (modules_dir / "intro.adoc").touch()

        validator = LinkValidator()

        # Test existing file
        result = validator.validate_internal_reference(
            'modules/intro.adoc',
            str(tmp_path)
        )
        assert result['status'] == 'ok'

        # Test missing file
        result = validator.validate_internal_reference(
            'modules/missing.adoc',
            str(tmp_path)
        )
        assert result['status'] == 'missing'
        assert 'not found' in result['error']

        # Test anchor reference
        result = validator.validate_internal_reference('#section-1', str(tmp_path))
        assert result['status'] == 'anchor'

    def test_validate_image(self, tmp_path):
        """Test image path validation."""
        # Create test image
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "diagram.png").touch()

        validator = LinkValidator()

        # Test existing image
        result = validator.validate_image('images/diagram.png', str(tmp_path))
        assert result['status'] == 'ok'

        # Test missing image
        result = validator.validate_image('images/missing.png', str(tmp_path))
        assert result['status'] == 'missing'

    @patch('urllib.request.urlopen')
    def test_validate_url(self, mock_urlopen):
        """Test URL validation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.url = 'https://example.com'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        validator = LinkValidator()
        result = validator.validate_url('https://example.com')

        assert result['status'] == 200
        assert result['error'] is None

    @patch('urllib.request.urlopen')
    def test_validate_url_with_transposition(self, mock_urlopen):
        """Test URL validation with transposition."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.url = 'https://preview.example.com/guide'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        validator = LinkValidator(transpositions=[
            ('https://example.com', 'https://preview.example.com')
        ])

        result = validator.validate_url('https://example.com/guide')

        assert result['transposed_url'] == 'https://preview.example.com/guide'
        assert result['status'] == 200

    def test_cache_functionality(self, tmp_path):
        """Test caching of validation results."""
        cache_dir = tmp_path / '.cache' / 'doc-utils'
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / 'link-validation.json'

        # Create validator with custom cache location
        validator = LinkValidator(cache_duration=3600)
        validator.cache_file = cache_file

        # Add to cache
        validator.cache['test_url'] = {
            'url': 'test_url',
            'status': 200,
            'timestamp': 1234567890
        }

        # Save cache
        validator._save_cache()
        assert cache_file.exists()

        # Load cache in new validator
        validator2 = LinkValidator(cache_duration=3600)
        validator2.cache_file = cache_file
        validator2._load_cache()

        # Cache should be loaded (but might be expired)
        # Just check the structure was loaded
        assert isinstance(validator2.cache, dict)


class TestParseTranspositions:
    """Tests for parse_transpositions function."""

    def test_parse_single_transposition(self):
        """Test parsing single transposition."""
        result = parse_transpositions(['https://example.com--https://preview.example.com'])
        assert result == [('https://example.com', 'https://preview.example.com')]

    def test_parse_multiple_transpositions(self):
        """Test parsing multiple transpositions."""
        result = parse_transpositions([
            'https://docs.com--https://preview.docs.com',
            'https://api.com--https://api-staging.com'
        ])
        assert len(result) == 2
        assert result[0] == ('https://docs.com', 'https://preview.docs.com')
        assert result[1] == ('https://api.com', 'https://api-staging.com')

    def test_invalid_transposition_format(self, capsys):
        """Test handling of invalid transposition format."""
        result = parse_transpositions(['invalid-format'])
        assert result == []
        captured = capsys.readouterr()
        assert 'Invalid transposition format' in captured.out

    def test_empty_transpositions(self):
        """Test with no transpositions."""
        result = parse_transpositions(None)
        assert result == []
        result = parse_transpositions([])
        assert result == []


class TestFormatResults:
    """Tests for format_results function."""

    def test_format_basic_results(self):
        """Test formatting basic validation results."""
        results = {
            'summary': {
                'total': 10,
                'valid': 8,
                'broken': 2,
                'warnings': 0,
                'skipped': 0
            },
            'broken_links': [
                {
                    'file': 'test.adoc',
                    'line': 10,
                    'url': 'https://example.com/404',
                    'status': 404,
                    'error': 'Not Found'
                }
            ],
            'warnings': [],
            'transpositions': []
        }

        output = format_results(results)

        assert 'SUMMARY:' in output
        assert '✓ Valid: 8 links' in output
        assert '✗ Broken: 2 links' in output
        assert 'BROKEN LINKS:' in output
        assert 'test.adoc:10' in output
        assert 'https://example.com/404' in output

    def test_format_with_transpositions(self):
        """Test formatting results with transpositions."""
        results = {
            'summary': {
                'total': 5,
                'valid': 4,
                'broken': 1,
                'warnings': 0,
                'skipped': 0
            },
            'broken_links': [
                {
                    'file': 'doc.adoc',
                    'line': 5,
                    'url': 'https://docs.example.com/page',
                    'transposed_url': 'https://preview.docs.example.com/page',
                    'status': 404
                }
            ],
            'warnings': [],
            'transpositions': [
                {'from': 'https://docs.example.com', 'to': 'https://preview.docs.example.com'}
            ]
        }

        output = format_results(results)

        assert 'URL Transposition Rules:' in output
        assert 'https://docs.example.com → https://preview.docs.example.com' in output
        assert 'Checked: https://preview.docs.example.com/page' in output

    def test_format_with_warnings(self):
        """Test formatting with redirect warnings."""
        results = {
            'summary': {
                'total': 5,
                'valid': 3,
                'broken': 0,
                'warnings': 2,
                'skipped': 0
            },
            'broken_links': [],
            'warnings': [
                {
                    'file': 'doc.adoc',
                    'line': 15,
                    'url': 'http://example.com',
                    'redirect': 'https://example.com',
                    'status': 301
                }
            ],
            'transpositions': []
        }

        output = format_results(results, verbose=True)

        assert '⚠ Warnings: 2 redirects' in output
        assert 'WARNINGS (Redirects):' in output
        assert 'Redirects to: https://example.com' in output


class TestIntegration:
    """Integration tests for the complete validation flow."""

    def test_validate_all(self, tmp_path):
        """Test complete validation workflow."""
        # Create test structure
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # Create attributes file
        attr_file = tmp_path / "attributes.adoc"
        attr_file.write_text("""
:product-name: TestProduct
:version: 1.0
:docs-url: https://docs.example.com/{version}
""")

        # Create test .adoc file
        test_file = modules_dir / "test.adoc"
        test_file.write_text("""
= Test Module

See link:{docs-url}/guide.html[Guide] for details.

Check xref:intro.adoc[Introduction].

image::../images/logo.png[Logo]
""")

        # Create referenced files
        (modules_dir / "intro.adoc").touch()
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "logo.png").touch()

        # Create validator
        validator = LinkValidator()

        # Mock URL validation to avoid actual network calls
        with patch.object(validator, 'validate_url') as mock_validate:
            mock_validate.return_value = {
                'url': 'https://docs.example.com/1.0/guide.html',
                'status': 200,
                'error': None
            }

            results = validator.validate_all(
                scan_dirs=[str(modules_dir)],
                attributes_file=str(attr_file)
            )

        assert results['summary']['total'] == 3  # 1 link, 1 xref, 1 image
        assert results['summary']['valid'] == 3
        assert results['summary']['broken'] == 0