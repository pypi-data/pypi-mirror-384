"""
Replace AsciiDoc attributes within link URLs with their actual values.

This module finds and replaces attribute references (like {attribute-name}) that appear
in the URL portion of AsciiDoc link macros (link: and xref:) with their resolved values
from attributes.adoc. Link text is preserved unchanged.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def find_attributes_files(root_dir: Path) -> List[Path]:
    """Find all attributes.adoc files in the repository."""
    attributes_files = []

    for path in root_dir.rglob('**/attributes.adoc'):
        # Skip hidden directories and common build directories
        parts = path.parts
        if any(part.startswith('.') or part in ['target', 'build', 'node_modules'] for part in parts):
            continue
        attributes_files.append(path)

    return attributes_files


def load_attributes(attributes_file: Path) -> Dict[str, str]:
    """Load attribute definitions from an attributes.adoc file."""
    attributes = {}

    with open(attributes_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Match attribute definitions
            # Format: :attribute-name: value
            match = re.match(r'^:([a-zA-Z0-9_-]+):\s*(.*)$', line)
            if match:
                attr_name = match.group(1)
                attr_value = match.group(2).strip()
                attributes[attr_name] = attr_value

    return attributes


def resolve_nested_attributes(attributes: Dict[str, str], max_iterations: int = 10) -> Dict[str, str]:
    """Resolve nested attribute references within attribute values."""
    for _ in range(max_iterations):
        changes_made = False

        for attr_name, attr_value in attributes.items():
            # Find all attribute references in the value
            refs = re.findall(r'\{([a-zA-Z0-9_-]+)\}', attr_value)

            for ref in refs:
                if ref in attributes:
                    new_value = attr_value.replace(f'{{{ref}}}', attributes[ref])
                    if new_value != attr_value:
                        attributes[attr_name] = new_value
                        changes_made = True
                        attr_value = new_value

        if not changes_made:
            break

    return attributes


def replace_link_attributes_in_file(file_path: Path, attributes: Dict[str, str], dry_run: bool = False, macro_type: str = 'both') -> int:
    """
    Replace attribute references within link macros in a single file.

    Args:
        file_path: Path to the file to process
        attributes: Dictionary of attribute definitions
        dry_run: Preview changes without modifying files
        macro_type: Type of macros to process - 'link', 'xref', or 'both' (default: 'both')

    Returns: Number of replacements made
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    replacement_count = 0

    # Find all link macros containing attributes in the URL portion only
    # Match link: and xref: macros, capturing URL and text separately
    link_patterns = []

    if macro_type in ('link', 'both'):
        # link:url[text] - replace only in URL portion
        link_patterns.append((r'link:([^[\]]*)\[([^\]]*)\]', 'link'))

    if macro_type in ('xref', 'both'):
        # xref:target[text] - replace only in target portion
        link_patterns.append((r'xref:([^[\]]*)\[([^\]]*)\]', 'xref'))

    # Handle empty text cases based on macro type
    if macro_type == 'both':
        link_patterns.append((r'(link|xref):([^[\]]*)\[\]', 'empty_text'))
    elif macro_type == 'link':
        link_patterns.append((r'(link):([^[\]]*)\[\]', 'empty_text'))
    elif macro_type == 'xref':
        link_patterns.append((r'(xref):([^[\]]*)\[\]', 'empty_text'))

    for pattern, link_type in link_patterns:
        matches = list(re.finditer(pattern, content))

        # Process matches in reverse order to maintain string positions
        for match in reversed(matches):
            if link_type == 'empty_text':
                # For links with empty text []
                macro_type = match.group(1)  # 'link' or 'xref'
                url_part = match.group(2)
                text_part = ''

                # Check if URL contains attributes
                if re.search(r'\{[a-zA-Z0-9_-]+\}', url_part):
                    modified_url = url_part

                    # Replace attributes only in URL
                    attr_matches = re.findall(r'\{([a-zA-Z0-9_-]+)\}', url_part)
                    for attr_name in attr_matches:
                        if attr_name in attributes:
                            attr_pattern = re.escape(f'{{{attr_name}}}')
                            modified_url = re.sub(attr_pattern, attributes[attr_name], modified_url)
                            replacement_count += 1

                    if modified_url != url_part:
                        # Reconstruct the link with modified URL
                        modified = f'{macro_type}:{modified_url}[]'
                        start = match.start()
                        end = match.end()
                        content = content[:start] + modified + content[end:]
            else:
                # For links with text
                url_part = match.group(1)
                text_part = match.group(2)

                # Check if URL contains attributes
                if re.search(r'\{[a-zA-Z0-9_-]+\}', url_part):
                    modified_url = url_part

                    # Replace attributes only in URL
                    attr_matches = re.findall(r'\{([a-zA-Z0-9_-]+)\}', url_part)
                    for attr_name in attr_matches:
                        if attr_name in attributes:
                            attr_pattern = re.escape(f'{{{attr_name}}}')
                            modified_url = re.sub(attr_pattern, attributes[attr_name], modified_url)
                            replacement_count += 1

                    if modified_url != url_part:
                        # Reconstruct the link with modified URL but original text
                        if link_type == 'link':
                            modified = f'link:{modified_url}[{text_part}]'
                        else:  # xref
                            modified = f'xref:{modified_url}[{text_part}]'

                        start = match.start()
                        end = match.end()
                        content = content[:start] + modified + content[end:]

    # Write changes if not in dry-run mode
    if content != original_content:
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return replacement_count

    return 0


def find_adoc_files(root_dir: Path, exclude_dirs: Optional[set] = None) -> List[Path]:
    """Find all *.adoc files in the repository."""
    if exclude_dirs is None:
        exclude_dirs = {'.git', 'target', 'build', 'node_modules'}

    adoc_files = []

    for path in root_dir.rglob('*.adoc'):
        # Check if any part of the path is in exclude_dirs
        parts = set(path.parts)
        if not parts.intersection(exclude_dirs):
            adoc_files.append(path)

    return adoc_files