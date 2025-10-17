#!/usr/bin/env python3
"""
Extract link and xref macros containing attributes into attribute definitions.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import unicodedata

from .spinner import Spinner
from .validate_links import LinkValidator


def find_attribute_files(base_path: str = '.') -> List[str]:
    """Find potential attribute files in the repository."""
    common_patterns = [
        '**/common-attributes.adoc',
        '**/attributes.adoc',
        '**/*-attributes.adoc',
        '**/attributes-*.adoc',
        '**/common_attributes.adoc',
        '**/_common-attributes.adoc'
    ]

    attribute_files = []
    base = Path(base_path)

    for pattern in common_patterns:
        for file_path in base.glob(pattern):
            if file_path.is_file():
                rel_path = file_path.relative_to(base)
                attribute_files.append(str(rel_path))

    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in attribute_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    return sorted(unique_files)


def select_attribute_file(attribute_files: List[str]) -> str:
    """Let user interactively select an attribute file."""
    if not attribute_files:
        return None

    print("\nMultiple attribute files found. Please select one:")
    for i, file_path in enumerate(attribute_files, 1):
        print(f"  {i}. {file_path}")

    while True:
        try:
            choice = input(f"\nEnter your choice (1-{len(attribute_files)}): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(attribute_files):
                return attribute_files[index]
            else:
                print(f"Please enter a number between 1 and {len(attribute_files)}")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return None


def load_existing_attributes(file_path: str) -> Dict[str, str]:
    """Load existing attributes from file."""
    attributes = {}
    if not os.path.exists(file_path):
        return attributes

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Match attribute definitions
            match = re.match(r'^:([^:]+):\s*(.+)$', line)
            if match:
                attr_name = match.group(1).strip()
                attr_value = match.group(2).strip()
                attributes[attr_name] = attr_value

    return attributes


def find_link_macros(file_path: str, macro_type: str = 'both') -> List[Tuple[str, str, str, int]]:
    """
    Find all link: and xref: macros containing attributes in their URLs.

    Args:
        file_path: Path to the file to scan
        macro_type: Type of macros to find - 'link', 'xref', or 'both' (default: 'both')

    Returns list of tuples: (full_macro, url, link_text, line_number)
    """
    macros = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Pattern to match link: and xref: macros
            # Matches: (link|xref):url[text] where url contains {attribute}
            patterns = []

            if macro_type in ('link', 'both'):
                patterns.append(r'(link:([^[\]]*\{[^}]+\}[^[\]]*)\[([^\]]*)\])')

            if macro_type in ('xref', 'both'):
                patterns.append(r'(xref:([^[\]]*\{[^}]+\}[^[\]]*)\[([^\]]*)\])')

            for pattern in patterns:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    full_macro = match.group(1)
                    url = match.group(2)
                    link_text = match.group(3)
                    macros.append((full_macro, url, link_text, line_num))

    return macros


def generate_attribute_name(url: str, existing_attrs: Set[str], counter: int) -> str:
    """Generate a unique attribute name from URL."""
    # Start with a base name from the URL
    base_name = url

    # Extract domain or path components
    if '://' in url:
        # Remove protocol
        base_name = re.sub(r'^[^:]+://', '', url)

    # Remove attributes from the name generation
    base_name = re.sub(r'\{[^}]+\}', '', base_name)

    # Extract meaningful parts
    if '/' in base_name:
        parts = base_name.split('/')
        # Use domain and last path component
        if len(parts) > 1:
            domain_part = parts[0].replace('.', '-')
            path_part = parts[-1].split('.')[0] if parts[-1] else ''
            if path_part:
                base_name = f"{domain_part}-{path_part}"
            else:
                base_name = domain_part

    # Clean up the name
    base_name = re.sub(r'[^a-zA-Z0-9-]', '-', base_name)
    base_name = re.sub(r'-+', '-', base_name)
    base_name = base_name.strip('-').lower()

    # Limit length
    if len(base_name) > 30:
        base_name = base_name[:30]

    # Make it unique
    attr_name = f"link-{base_name}"
    original_name = attr_name
    suffix = 1

    while attr_name in existing_attrs:
        attr_name = f"{original_name}-{suffix}"
        suffix += 1

    return attr_name


def group_macros_by_url(macros: List[Tuple[str, str, str, str, int]]) -> Dict[str, List[Tuple[str, str, str, int]]]:
    """
    Group macros by URL, collecting all link text variations.

    Returns: Dict[url, List[(file_path, link_text, full_macro, line_number)]]
    """
    url_groups = defaultdict(list)

    for file_path, full_macro, url, link_text, line_num in macros:
        url_groups[url].append((file_path, link_text, full_macro, line_num))

    return url_groups


def select_link_text(url: str, variations: List[Tuple[str, str, str, int]], interactive: bool = True) -> str:
    """
    Select link text for a URL with multiple variations.

    variations: List[(file_path, link_text, full_macro, line_number)]
    """
    # Extract unique link texts
    unique_texts = {}
    for file_path, link_text, _, line_num in variations:
        if link_text not in unique_texts:
            unique_texts[link_text] = []
        unique_texts[link_text].append(f"{file_path}:{line_num}")

    if len(unique_texts) == 1:
        # Only one variation, use it
        return list(unique_texts.keys())[0]

    if not interactive:
        # Use most common (appears in most locations)
        most_common = max(unique_texts.items(), key=lambda x: len(x[1]))
        return most_common[0]

    # Interactive selection
    print(f"\nMultiple link text variations found for URL: {url}")
    print("Please select the preferred text:")

    text_list = list(unique_texts.items())
    for i, (text, locations) in enumerate(text_list, 1):
        print(f"\n  {i}. \"{text}\"")
        print(f"     Used in: {', '.join(locations[:3])}")
        if len(locations) > 3:
            print(f"     ... and {len(locations) - 3} more locations")

    print(f"\n  {len(text_list) + 1}. Enter custom text")

    while True:
        try:
            choice = input(f"\nEnter your choice (1-{len(text_list) + 1}): ").strip()
            index = int(choice) - 1

            if 0 <= index < len(text_list):
                return text_list[index][0]
            elif index == len(text_list):
                custom_text = input("Enter custom link text: ").strip()
                if custom_text:
                    return custom_text
                else:
                    print("Text cannot be empty. Please try again.")
            else:
                print(f"Please enter a number between 1 and {len(text_list) + 1}")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\nUsing most common text variation.")
            most_common = max(unique_texts.items(), key=lambda x: len(x[1]))
            return most_common[0]


def collect_all_macros(scan_dirs: List[str] = None, macro_type: str = 'both', exclude_files: List[str] = None) -> List[Tuple[str, str, str, str, int]]:
    """
    Collect all link/xref macros with attributes from all .adoc files.

    Args:
        scan_dirs: Directories to scan (default: current directory)
        macro_type: Type of macros to find - 'link', 'xref', or 'both' (default: 'both')
        exclude_files: List of file paths to exclude from scanning (typically all attributes files)

    Returns: List[(file_path, full_macro, url, link_text, line_number)]
    """
    if scan_dirs is None:
        scan_dirs = ['.']

    all_macros = []

    # Normalize all exclude file paths
    exclude_paths = set()
    if exclude_files:
        for file in exclude_files:
            if file:  # Check for None or empty string
                exclude_paths.add(os.path.abspath(file))

    for scan_dir in scan_dirs:
        for root, _, files in os.walk(scan_dir):
            # Skip hidden directories and .archive
            if '/.archive' in root or '/.' in root:
                continue

            for file in files:
                if file.endswith('.adoc'):
                    file_path = os.path.join(root, file)
                    # Skip any attributes files to prevent self-referencing
                    if exclude_paths and os.path.abspath(file_path) in exclude_paths:
                        continue
                    macros = find_link_macros(file_path, macro_type)
                    for full_macro, url, link_text, line_num in macros:
                        all_macros.append((file_path, full_macro, url, link_text, line_num))

    return all_macros


def create_attributes(url_groups: Dict[str, List[Tuple[str, str, str, int]]],
                     existing_attrs: Dict[str, str],
                     interactive: bool = True) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Create new attributes for each unique URL and track existing ones.

    Returns: Tuple[new_attributes, existing_matching_attributes]
    """
    new_attributes = {}
    existing_matching_attributes = {}
    existing_attr_names = set(existing_attrs.keys())
    counter = 1

    for url, variations in url_groups.items():
        # Check if this URL already has an attribute
        existing_attr = None
        for attr_name, attr_value in existing_attrs.items():
            if url in attr_value:
                existing_attr = attr_name
                existing_matching_attributes[attr_name] = attr_value
                break

        if existing_attr:
            print(f"URL already has attribute {{{existing_attr}}}: {url}")
            continue

        # Select link text
        link_text = select_link_text(url, variations, interactive)

        # Generate attribute name
        attr_name = generate_attribute_name(url, existing_attr_names | set(new_attributes.keys()), counter)
        counter += 1

        # Determine macro type (link or xref)
        first_macro = variations[0][2]  # full_macro from first variation
        macro_type = 'xref' if first_macro.startswith('xref:') else 'link'

        # Create attribute value
        attr_value = f"{macro_type}:{url}[{link_text}]"
        new_attributes[attr_name] = attr_value

        print(f"Created attribute: :{attr_name}: {attr_value}")

    return new_attributes, existing_matching_attributes


def update_attribute_file(file_path: str, new_attributes: Dict[str, str], dry_run: bool = False):
    """Add new attributes to the attribute file."""
    if not new_attributes:
        print("No new attributes to add.")
        return

    if dry_run:
        print(f"\n[DRY RUN] Would add {len(new_attributes)} attributes to {file_path}:")
        for attr_name, attr_value in new_attributes.items():
            print(f"  :{attr_name}: {attr_value}")
        return

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

    # Append new attributes
    with open(file_path, 'a', encoding='utf-8') as f:
        if os.path.getsize(file_path) > 0:
            f.write('\n')  # Add newline if file not empty
        f.write('// Extracted link attributes\n')
        for attr_name, attr_value in sorted(new_attributes.items()):
            f.write(f":{attr_name}: {attr_value}\n")

    print(f"Added {len(new_attributes)} attributes to {file_path}")


def replace_macros_with_attributes(file_updates: Dict[str, List[Tuple[str, str]]], dry_run: bool = False):
    """
    Replace link/xref macros with their attribute references.

    file_updates: Dict[file_path, List[(old_macro, attribute_ref)]]
    """
    for file_path, replacements in file_updates.items():
        if dry_run:
            print(f"\n[DRY RUN] Would update {file_path}:")
            for old_macro, attr_ref in replacements[:3]:
                print(f"  Replace: {old_macro}")
                print(f"     With: {attr_ref}")
            if len(replacements) > 3:
                print(f"  ... and {len(replacements) - 3} more replacements")
            continue

        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Apply replacements
        for old_macro, attr_ref in replacements:
            content = content.replace(old_macro, attr_ref)

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Updated {file_path}: {len(replacements)} replacements")


def prepare_file_updates(url_groups: Dict[str, List[Tuple[str, str, str, int]]],
                        attribute_mapping: Dict[str, str]) -> Dict[str, List[Tuple[str, str]]]:
    """
    Prepare file updates mapping macros to attribute references.

    Returns: Dict[file_path, List[(old_macro, attribute_ref)]]
    """
    file_updates = defaultdict(list)

    # Create reverse mapping from URL to attribute name
    url_to_attr = {}
    for attr_name, attr_value in attribute_mapping.items():
        # Extract URL from attribute value
        match = re.match(r'(?:link|xref):([^\[]+)\[', attr_value)
        if match:
            url = match.group(1)
            url_to_attr[url] = attr_name

    # Map each macro occurrence to its attribute
    for url, variations in url_groups.items():
        if url in url_to_attr:
            attr_name = url_to_attr[url]
            for file_path, _, full_macro, _ in variations:
                file_updates[file_path].append((full_macro, f"{{{attr_name}}}"))

    return dict(file_updates)


def validate_link_attributes(attributes_file: str, fail_on_broken: bool = False) -> bool:
    """
    Validate URLs in link-* attributes.

    Returns: True if validation passes (no broken links or fail_on_broken is False), False otherwise
    """
    if not os.path.exists(attributes_file):
        return True  # No file to validate yet

    print(f"\nValidating links in {attributes_file}...")
    spinner = Spinner("Validating link attributes")
    spinner.start()

    # Extract link attributes from file
    link_attributes = {}
    with open(attributes_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Match :link-*: URL patterns
            match = re.match(r'^:(link-[a-zA-Z0-9_-]+):\s*(https?://[^\s]+)', line)
            if match:
                attr_name = match.group(1)
                url = match.group(2).strip()
                link_attributes[attr_name] = (url, line_num)

    if not link_attributes:
        spinner.stop("No link attributes to validate")
        return True

    # Validate each URL
    validator = LinkValidator(timeout=10, retry=2, parallel=5)
    broken_links = []

    for attr_name, (url, line_num) in link_attributes.items():
        try:
            is_valid = validator.validate_url(url)
            if not is_valid:
                broken_links.append((attr_name, url, line_num))
        except Exception as e:
            broken_links.append((attr_name, url, line_num))

    # Report results
    total = len(link_attributes)
    broken = len(broken_links)
    valid = total - broken

    spinner.stop(f"Validated {total} link attributes: {valid} valid, {broken} broken")

    if broken_links:
        print("\n⚠️  Broken link attributes found:")
        for attr_name, url, line_num in broken_links:
            print(f"  Line {line_num}: :{attr_name}: {url}")

        if fail_on_broken:
            print("\nStopping extraction due to broken links (--fail-on-broken)")
            return False
        else:
            print("\nContinuing with extraction despite broken links...")

    return True


def extract_link_attributes(attributes_file: str = None,
                           scan_dirs: List[str] = None,
                           interactive: bool = True,
                           dry_run: bool = False,
                           validate_links: bool = False,
                           fail_on_broken: bool = False,
                           macro_type: str = 'both') -> bool:
    """
    Main function to extract link attributes.

    Args:
        attributes_file: Path to attributes file
        scan_dirs: Directories to scan
        interactive: Enable interactive mode
        dry_run: Preview changes without modifying files
        validate_links: Validate URLs before extraction
        fail_on_broken: Exit if broken links found
        macro_type: Type of macros to process - 'link', 'xref', or 'both' (default: 'both')

    Returns: True if successful, False otherwise
    """
    # Find or confirm attributes file
    if not attributes_file:
        found_files = find_attribute_files()

        if not found_files:
            print("No attribute files found.")
            response = input("Create common-attributes.adoc? (y/n): ").strip().lower()
            if response == 'y':
                attributes_file = 'common-attributes.adoc'
            else:
                print("Please specify an attribute file with --attributes-file")
                return False
        elif len(found_files) == 1:
            attributes_file = found_files[0]
            print(f"Using attribute file: {attributes_file}")
        else:
            attributes_file = select_attribute_file(found_files)
            if not attributes_file:
                return False

    # Validate existing link attributes if requested
    if validate_links:
        if not validate_link_attributes(attributes_file, fail_on_broken):
            return False

    # Load existing attributes
    spinner = Spinner("Loading existing attributes")
    spinner.start()
    existing_attrs = load_existing_attributes(attributes_file)
    spinner.stop(f"Loaded {len(existing_attrs)} existing attributes")

    # Find all attributes files to exclude from processing
    all_attribute_files = find_attribute_files()

    # Notify user about excluded files if there are multiple
    if len(all_attribute_files) > 1:
        print(f"Excluding {len(all_attribute_files)} attributes files from processing:")
        for f in all_attribute_files:
            print(f"  - {f}")

    # Collect all macros, excluding ALL attributes files
    macro_desc = {'link': 'link', 'xref': 'xref', 'both': 'link and xref'}[macro_type]
    spinner = Spinner(f"Scanning for {macro_desc} macros with attributes")
    spinner.start()
    all_macros = collect_all_macros(scan_dirs, macro_type, exclude_files=all_attribute_files)
    spinner.stop()

    if not all_macros:
        print(f"No {macro_desc} macros with attributes found.")
        return True

    print(f"Found {len(all_macros)} {macro_desc} macros with attributes")

    # Group by URL
    spinner = Spinner("Grouping macros by URL")
    spinner.start()
    url_groups = group_macros_by_url(all_macros)
    spinner.stop(f"Grouped into {len(url_groups)} unique URLs")

    # Create new attributes and track existing ones
    new_attributes, existing_matching_attributes = create_attributes(url_groups, existing_attrs, interactive)

    if not new_attributes and not existing_matching_attributes:
        print("No new attributes to create and no existing attributes match found URLs.")
        return True

    # Validate new attributes before writing if requested
    if validate_links and not dry_run and new_attributes:
        print("\nValidating new link attributes...")
        spinner = Spinner("Validating new URLs")
        spinner.start()

        validator = LinkValidator(timeout=10, retry=2, parallel=5)
        broken_new = []

        for attr_name, attr_value in new_attributes.items():
            # Extract URL from attribute value (could be link: or xref:)
            url_match = re.search(r'(https?://[^\[]+)', attr_value)
            if url_match:
                url = url_match.group(1).strip()
                try:
                    if not validator.validate_url(url):
                        broken_new.append((attr_name, url))
                except Exception:
                    broken_new.append((attr_name, url))

        spinner.stop(f"Validated {len(new_attributes)} new attributes")

        if broken_new:
            print("\n⚠️  Broken URLs in new attributes:")
            for attr_name, url in broken_new:
                print(f"  :{attr_name}: {url}")

            if fail_on_broken:
                print("\nStopping due to broken URLs in new attributes (--fail-on-broken)")
                return False

    # Update attribute file (only if there are new attributes)
    if new_attributes:
        update_attribute_file(attributes_file, new_attributes, dry_run)

    # Prepare file updates (include both new and existing matching attributes)
    all_attributes = {**existing_attrs, **new_attributes}
    file_updates = prepare_file_updates(url_groups, all_attributes)

    # Replace macros
    if file_updates:
        spinner = Spinner(f"Updating {len(file_updates)} files")
        spinner.start()
        replace_macros_with_attributes(file_updates, dry_run)
        spinner.stop(f"Updated {len(file_updates)} files")

    if dry_run:
        print("\n[DRY RUN] No files were modified. Run without --dry-run to apply changes.")
    else:
        total_processed = len(new_attributes) + len(existing_matching_attributes)
        if new_attributes and existing_matching_attributes:
            print(f"\nSuccessfully processed {total_processed} link attributes:")
            print(f"  - Created {len(new_attributes)} new attributes")
            print(f"  - Replaced macros using {len(existing_matching_attributes)} existing attributes")
        elif new_attributes:
            print(f"\nSuccessfully extracted {len(new_attributes)} link attributes")
        elif existing_matching_attributes:
            print(f"\nSuccessfully replaced macros using {len(existing_matching_attributes)} existing link attributes")

    return True