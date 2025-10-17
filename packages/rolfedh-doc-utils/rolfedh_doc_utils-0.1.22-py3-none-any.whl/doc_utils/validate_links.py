#!/usr/bin/env python3
"""
Validate links in AsciiDoc documentation, checking for broken URLs and missing references.
"""

import os
import re
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
import urllib.request
import urllib.error
import socket
from datetime import datetime, timedelta


class LinkValidator:
    """Validates links in AsciiDoc documentation."""

    def __init__(self,
                 timeout: int = 10,
                 retry: int = 3,
                 parallel: int = 10,
                 cache_duration: int = 3600,
                 transpositions: List[Tuple[str, str]] = None):
        """
        Initialize the link validator.

        Args:
            timeout: Timeout in seconds for each URL check
            retry: Number of retries for failed URLs
            parallel: Number of parallel URL checks
            cache_duration: Cache duration in seconds
            transpositions: List of (from_url, to_url) tuples for URL replacement
        """
        self.timeout = timeout
        self.retry = retry
        self.parallel = parallel
        self.cache_duration = cache_duration
        self.transpositions = transpositions or []
        self.cache = {}
        self.cache_file = Path.home() / '.cache' / 'doc-utils' / 'link-validation.json'
        self._load_cache()

    def _load_cache(self):
        """Load cached validation results."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # Check cache expiry
                    now = datetime.now().timestamp()
                    self.cache = {
                        url: result for url, result in cached_data.items()
                        if now - result.get('timestamp', 0) < self.cache_duration
                    }
            except (json.JSONDecodeError, IOError):
                self.cache = {}

    def _save_cache(self):
        """Save validation results to cache."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def transpose_url(self, url: str) -> str:
        """
        Apply transposition rules to URL.

        Args:
            url: Original URL

        Returns:
            Transposed URL if rules match, otherwise original URL
        """
        for from_pattern, to_pattern in self.transpositions:
            if url.startswith(from_pattern):
                return url.replace(from_pattern, to_pattern, 1)
        return url

    def extract_links(self, file_path: str, attributes: Dict[str, str] = None) -> List[Dict]:
        """
        Extract all links from an AsciiDoc file.

        Args:
            file_path: Path to the AsciiDoc file
            attributes: Dictionary of attribute definitions

        Returns:
            List of link dictionaries with url, text, type, line_number
        """
        links = []
        attributes = attributes or {}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Find link: macros
                link_matches = re.finditer(r'link:([^[\]]+)\[([^\]]*)\]', line)
                for match in link_matches:
                    url = match.group(1)
                    text = match.group(2)
                    # Resolve attributes in URL
                    resolved_url = self._resolve_attributes(url, attributes)
                    links.append({
                        'url': resolved_url,
                        'original_url': url,
                        'text': text,
                        'type': 'external',
                        'file': file_path,
                        'line': line_num
                    })

                # Find xref: macros
                xref_matches = re.finditer(r'xref:([^[\]]+)\[([^\]]*)\]', line)
                for match in xref_matches:
                    target = match.group(1)
                    text = match.group(2)
                    # Resolve attributes in target
                    resolved_target = self._resolve_attributes(target, attributes)
                    links.append({
                        'url': resolved_target,
                        'original_url': target,
                        'text': text,
                        'type': 'internal',
                        'file': file_path,
                        'line': line_num
                    })

                # Find image:: directives
                image_matches = re.finditer(r'image::([^[\]]+)\[', line)
                for match in image_matches:
                    path = match.group(1)
                    resolved_path = self._resolve_attributes(path, attributes)
                    links.append({
                        'url': resolved_path,
                        'original_url': path,
                        'text': 'image',
                        'type': 'image',
                        'file': file_path,
                        'line': line_num
                    })

        return links

    def _resolve_attributes(self, text: str, attributes: Dict[str, str]) -> str:
        """Resolve attributes in text."""
        resolved = text
        max_iterations = 10

        for _ in range(max_iterations):
            # Find all attribute references
            refs = re.findall(r'\{([^}]+)\}', resolved)
            if not refs:
                break

            changes_made = False
            for ref in refs:
                if ref in attributes:
                    resolved = resolved.replace(f'{{{ref}}}', attributes[ref])
                    changes_made = True

            if not changes_made:
                break

        return resolved

    def validate_url(self, url: str, original_url: str = None, use_cache: bool = True) -> Dict:
        """
        Validate a single URL.

        Args:
            url: URL to validate
            original_url: Original URL before transposition
            use_cache: Whether to use cached results

        Returns:
            Dictionary with validation results
        """
        # Check cache first
        cache_key = f"{url}:{original_url}" if original_url else url
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now().timestamp() - cached['timestamp'] < self.cache_duration:
                return cached

        result = {
            'url': url,
            'original_url': original_url or url,
            'status': None,
            'error': None,
            'redirect': None,
            'timestamp': datetime.now().timestamp()
        }

        # Apply transposition if needed
        check_url = self.transpose_url(url)
        if check_url != url:
            result['transposed_url'] = check_url

        # Validate the URL
        for attempt in range(self.retry):
            try:
                req = urllib.request.Request(
                    check_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (doc-utils link validator)',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    }
                )

                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result['status'] = response.status
                    # Check for redirect
                    if response.url != check_url:
                        result['redirect'] = response.url
                    break

            except urllib.error.HTTPError as e:
                result['status'] = e.code
                result['error'] = str(e)
                if e.code not in [500, 502, 503, 504]:  # Don't retry client errors
                    break

            except urllib.error.URLError as e:
                result['error'] = str(e.reason)

            except socket.timeout:
                result['error'] = 'Timeout'

            except Exception as e:
                result['error'] = str(e)

            # Wait before retry
            if attempt < self.retry - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        # Cache the result
        self.cache[cache_key] = result

        return result

    def validate_internal_reference(self, ref: str, base_dir: str) -> Dict:
        """
        Validate an internal reference (xref).

        Args:
            ref: Reference path
            base_dir: Base directory for relative paths

        Returns:
            Dictionary with validation results
        """
        result = {
            'url': ref,
            'type': 'internal',
            'status': None,
            'error': None
        }

        # Handle anchor references
        if ref.startswith('#'):
            # TODO: Check if anchor exists in current file
            result['status'] = 'anchor'
            return result

        # Parse file and anchor
        parts = ref.split('#', 1)
        file_ref = parts[0]
        anchor = parts[1] if len(parts) > 1 else None

        # Resolve file path
        if os.path.isabs(file_ref):
            file_path = file_ref
        else:
            file_path = os.path.normpath(os.path.join(base_dir, file_ref))

        # Check if file exists
        if os.path.exists(file_path):
            result['status'] = 'ok'
            # TODO: If anchor provided, check if it exists in the file
        else:
            result['status'] = 'missing'
            result['error'] = f"File not found: {file_path}"

        return result

    def validate_image(self, path: str, base_dir: str) -> Dict:
        """
        Validate an image path.

        Args:
            path: Image path
            base_dir: Base directory for relative paths

        Returns:
            Dictionary with validation results
        """
        result = {
            'url': path,
            'type': 'image',
            'status': None,
            'error': None
        }

        # Check if it's a URL
        if path.startswith(('http://', 'https://')):
            return self.validate_url(path)

        # Resolve file path
        if os.path.isabs(path):
            file_path = path
        else:
            file_path = os.path.normpath(os.path.join(base_dir, path))

        # Check if file exists
        if os.path.exists(file_path):
            result['status'] = 'ok'
        else:
            result['status'] = 'missing'
            result['error'] = f"Image not found: {file_path}"

        return result

    def validate_links_in_file(self, file_path: str, attributes: Dict[str, str] = None) -> List[Dict]:
        """
        Validate all links in a single file.

        Args:
            file_path: Path to the AsciiDoc file
            attributes: Dictionary of attribute definitions

        Returns:
            List of validation results
        """
        links = self.extract_links(file_path, attributes)
        results = []
        base_dir = os.path.dirname(file_path)

        # Group links by type for efficient processing
        external_links = [l for l in links if l['type'] == 'external']
        internal_links = [l for l in links if l['type'] == 'internal']
        image_links = [l for l in links if l['type'] == 'image']

        # Validate external links in parallel
        if external_links:
            with ThreadPoolExecutor(max_workers=self.parallel) as executor:
                futures = {
                    executor.submit(self.validate_url, link['url'], link['original_url']): link
                    for link in external_links
                }

                for future in as_completed(futures):
                    link = futures[future]
                    try:
                        result = future.result()
                        result.update(link)
                        results.append(result)
                    except Exception as e:
                        result = link.copy()
                        result['error'] = str(e)
                        results.append(result)

        # Validate internal references
        for link in internal_links:
            result = self.validate_internal_reference(link['url'], base_dir)
            result.update(link)
            results.append(result)

        # Validate image paths
        for link in image_links:
            result = self.validate_image(link['url'], base_dir)
            result.update(link)
            results.append(result)

        return results

    def validate_all(self, scan_dirs: List[str] = None,
                    attributes_file: str = None,
                    exclude_domains: List[str] = None) -> Dict:
        """
        Validate all links in documentation.

        Args:
            scan_dirs: Directories to scan
            attributes_file: Path to attributes file
            exclude_domains: Domains to skip

        Returns:
            Dictionary with all validation results
        """
        if scan_dirs is None:
            scan_dirs = ['.']

        exclude_domains = exclude_domains or []

        # Load attributes
        attributes = {}
        if attributes_file and os.path.exists(attributes_file):
            attributes = self._load_attributes(attributes_file)

        # Collect all .adoc files
        adoc_files = []
        for scan_dir in scan_dirs:
            for root, _, files in os.walk(scan_dir):
                # Skip hidden directories
                if '/.' in root:
                    continue
                for file in files:
                    if file.endswith('.adoc'):
                        adoc_files.append(os.path.join(root, file))

        # Validate links in all files
        all_results = {
            'files': {},
            'summary': {
                'total': 0,
                'valid': 0,
                'broken': 0,
                'warnings': 0,
                'skipped': 0
            },
            'broken_links': [],
            'warnings': [],
            'transpositions': [
                {'from': t[0], 'to': t[1]} for t in self.transpositions
            ]
        }

        for file_path in adoc_files:
            results = self.validate_links_in_file(file_path, attributes)

            # Filter out excluded domains
            filtered_results = []
            for result in results:
                url = result.get('url', '')
                parsed = urlparse(url)
                if parsed.netloc in exclude_domains:
                    result['status'] = 'skipped'
                    result['reason'] = 'Domain excluded'
                filtered_results.append(result)

            all_results['files'][file_path] = filtered_results

            # Update summary
            for result in filtered_results:
                all_results['summary']['total'] += 1

                if result.get('status') == 'skipped':
                    all_results['summary']['skipped'] += 1
                elif result.get('status') in ['ok', 200, 'anchor']:
                    all_results['summary']['valid'] += 1
                elif result.get('status') in [301, 302, 303, 307, 308]:
                    all_results['summary']['warnings'] += 1
                    all_results['warnings'].append(result)
                elif result.get('error') or result.get('status') in ['missing', 404]:
                    all_results['summary']['broken'] += 1
                    all_results['broken_links'].append(result)
                else:
                    # Treat other status codes as broken
                    all_results['summary']['broken'] += 1
                    all_results['broken_links'].append(result)

        # Save cache
        self._save_cache()

        return all_results

    def _load_attributes(self, attributes_file: str) -> Dict[str, str]:
        """Load attributes from file."""
        attributes = {}

        with open(attributes_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Match attribute definitions
                match = re.match(r'^:([^:]+):\s*(.*)$', line)
                if match:
                    attr_name = match.group(1).strip()
                    attr_value = match.group(2).strip()
                    attributes[attr_name] = attr_value

        return attributes


def parse_transpositions(transpose_args: List[str]) -> List[Tuple[str, str]]:
    """
    Parse transposition arguments.

    Args:
        transpose_args: List of transposition strings in format "from--to"

    Returns:
        List of (from_url, to_url) tuples
    """
    transpositions = []

    for arg in transpose_args or []:
        parts = arg.split('--')
        if len(parts) == 2:
            from_url = parts[0].strip()
            to_url = parts[1].strip()
            transpositions.append((from_url, to_url))
        else:
            print(f"Warning: Invalid transposition format: {arg}")
            print("Expected format: from_url--to_url")

    return transpositions


def format_results(results: Dict, verbose: bool = False) -> str:
    """
    Format validation results for display.

    Args:
        results: Validation results dictionary
        verbose: Whether to show verbose output

    Returns:
        Formatted string for display
    """
    output = []

    # Show transpositions if any
    if results.get('transpositions'):
        output.append("URL Transposition Rules:")
        for trans in results['transpositions']:
            output.append(f"  {trans['from']} → {trans['to']}")
        output.append("")

    # Summary
    summary = results['summary']
    output.append("SUMMARY:")
    output.append(f"✓ Valid: {summary['valid']} links")
    if summary['broken'] > 0:
        output.append(f"✗ Broken: {summary['broken']} links")
    if summary['warnings'] > 0:
        output.append(f"⚠ Warnings: {summary['warnings']} redirects")
    if summary['skipped'] > 0:
        output.append(f"⊘ Skipped: {summary['skipped']} links (excluded domains)")
    output.append("")

    # Broken links
    if results['broken_links']:
        output.append("BROKEN LINKS:")
        for i, link in enumerate(results['broken_links'], 1):
            output.append(f"\n{i}. {link['file']}:{link['line']}")
            if link.get('original_url') and link.get('original_url') != link.get('url'):
                output.append(f"   Original: {link['original_url']}")
                output.append(f"   Resolved: {link['url']}")
            else:
                output.append(f"   URL: {link['url']}")

            if link.get('transposed_url'):
                output.append(f"   Checked: {link['transposed_url']}")

            if link.get('status'):
                output.append(f"   Status: {link['status']}")
            if link.get('error'):
                output.append(f"   Error: {link['error']}")
        output.append("")

    # Warnings (redirects)
    if results['warnings'] and verbose:
        output.append("WARNINGS (Redirects):")
        for i, link in enumerate(results['warnings'], 1):
            output.append(f"\n{i}. {link['file']}:{link['line']}")
            output.append(f"   URL: {link['url']}")
            if link.get('redirect'):
                output.append(f"   Redirects to: {link['redirect']}")
        output.append("")

    return '\n'.join(output)