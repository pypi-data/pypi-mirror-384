"""
Format AsciiDoc spacing - ensures blank lines after headings and around include directives.

Core logic for formatting AsciiDoc files with proper spacing.
"""

import re
from pathlib import Path
from typing import List, Tuple


def process_file(file_path: Path, dry_run: bool = False, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Process a single AsciiDoc file to fix spacing issues.

    Args:
        file_path: Path to the file to process
        dry_run: If True, show what would be changed without modifying
        verbose: If True, show detailed output

    Returns:
        Tuple of (changes_made, messages) where messages is a list of verbose output
    """
    messages = []

    if verbose:
        messages.append(f"Processing: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError) as e:
        raise IOError(f"Error reading {file_path}: {e}")

    # Remove trailing newlines from lines for processing
    lines = [line.rstrip('\n\r') for line in lines]

    new_lines = []
    changes_made = False
    in_block = False  # Track if we're inside a block (admonition, listing, etc.)
    in_conditional = False  # Track if we're inside a conditional block
    in_comment_block = False  # Track if we're inside a //// comment block

    for i, current_line in enumerate(lines):
        prev_line = lines[i-1] if i > 0 else ""
        next_line = lines[i+1] if i + 1 < len(lines) else ""

        # Check for conditional start (ifdef:: or ifndef::)
        if re.match(r'^(ifdef::|ifndef::)', current_line):
            in_conditional = True
            # Add blank line before conditional if needed
            # Don't add if previous line is a comment (they form a logical unit)
            if (prev_line and
                not re.match(r'^\s*$', prev_line) and
                not re.match(r'^(ifdef::|ifndef::|endif::)', prev_line) and
                not re.match(r'^//', prev_line)):
                new_lines.append("")
                changes_made = True
                if verbose:
                    messages.append("  Added blank line before conditional block")
            new_lines.append(current_line)

        # Check for conditional end (endif::)
        elif re.match(r'^endif::', current_line):
            new_lines.append(current_line)
            in_conditional = False
            # Add blank line after conditional if needed
            if (next_line and
                not re.match(r'^\s*$', next_line) and
                not re.match(r'^(ifdef::|ifndef::|endif::)', next_line)):
                new_lines.append("")
                changes_made = True
                if verbose:
                    messages.append("  Added blank line after conditional block")

        # Check for comment block delimiters (////)
        elif re.match(r'^////+$', current_line):
            in_comment_block = not in_comment_block  # Toggle comment block state
            new_lines.append(current_line)

            # If we're closing a comment block, add blank line after if needed
            if not in_comment_block:
                if (next_line and
                    not re.match(r'^\s*$', next_line) and
                    not re.match(r'^////+$', next_line)):
                    new_lines.append("")
                    changes_made = True
                    if verbose:
                        messages.append("  Added blank line after comment block")

        # Check for block delimiters (====, ----, ...., ____)
        # These are used for admonitions, listing blocks, literal blocks, etc.
        elif re.match(r'^(====+|----+|\.\.\.\.+|____+)$', current_line):
            in_block = not in_block  # Toggle block state
            new_lines.append(current_line)

        # Check for role blocks ([role="..."])
        # Role blocks don't need special spacing - they're followed directly by content
        elif not in_block and not in_comment_block and re.match(r'^\[role=', current_line):
            new_lines.append(current_line)

        # Check for block titles (.Title)
        elif not in_block and not in_comment_block and re.match(r'^\.[A-Z]', current_line):
            # Add blank line before block title if needed
            if (prev_line and
                not re.match(r'^\s*$', prev_line) and
                not re.match(r'^=+\s+', prev_line) and
                not re.match(r'^\[role=', prev_line)):  # Don't add if previous is heading, empty, or role block
                new_lines.append("")
                changes_made = True
                if verbose:
                    truncated = current_line[:50] + "..." if len(current_line) > 50 else current_line
                    messages.append(f"  Added blank line before block title: {truncated}")
            new_lines.append(current_line)

        # Check if current line is a heading (but not if we're in a block)
        elif not in_block and re.match(r'^=+\s+', current_line):
            new_lines.append(current_line)

            # Check if next line is not empty, not another heading, and not a comment block
            if (next_line and
                not re.match(r'^=+\s+', next_line) and
                not re.match(r'^\s*$', next_line) and
                not re.match(r'^////+$', next_line)):  # Don't add if next is comment block
                new_lines.append("")
                changes_made = True
                if verbose:
                    truncated = current_line[:50] + "..." if len(current_line) > 50 else current_line
                    messages.append(f"  Added blank line after heading: {truncated}")

        # Check if current line is a comment (AsciiDoc comments start with //)
        elif re.match(r'^//', current_line):
            # Skip special handling if we're inside a conditional block
            if in_conditional:
                new_lines.append(current_line)
            else:
                # Check if next line is an include directive
                if next_line and re.match(r'^include::', next_line):
                    # This comment belongs to the include, add blank line before comment if needed
                    # This includes when previous line is an include (to separate include blocks)
                    if (prev_line and
                        not re.match(r'^\s*$', prev_line) and
                        not re.match(r'^//', prev_line) and
                        not re.match(r'^:', prev_line)):
                        new_lines.append("")
                        changes_made = True
                        if verbose:
                            messages.append("  Added blank line before comment above include")
                    new_lines.append(current_line)
                else:
                    # Standalone comment, just add it
                    new_lines.append(current_line)

        # Check if current line is an attribute (starts with :)
        elif re.match(r'^:', current_line):
            # Skip special handling if we're inside a conditional block
            if in_conditional:
                new_lines.append(current_line)
            else:
                # Check if next line is an include directive
                if next_line and re.match(r'^include::', next_line):
                    # This attribute belongs to the include, add blank line before attribute if needed
                    if (prev_line and
                        not re.match(r'^\s*$', prev_line) and
                        not re.match(r'^//', prev_line) and
                        not re.match(r'^:', prev_line)):  # Don't add if previous is comment or attribute
                        new_lines.append("")
                        changes_made = True
                        if verbose:
                            messages.append("  Added blank line before attribute above include")
                    new_lines.append(current_line)
                else:
                    # Standalone attribute, just add it
                    new_lines.append(current_line)

        # Check if current line is an include directive
        elif re.match(r'^include::', current_line):
            # Handle includes inside conditional blocks
            if in_conditional:
                # Add blank line between consecutive includes within conditional blocks
                if prev_line and re.match(r'^include::', prev_line):
                    new_lines.append("")
                    changes_made = True
                    if verbose:
                        messages.append("  Added blank line between includes in conditional block")
                new_lines.append(current_line)
            else:
                # Check if this is an attribute include (contains "attribute" in the path)
                is_attribute_include = 'attribute' in current_line.lower()

                # Check if this appears near the top of the file (within first 10 lines after H1)
                # Find the H1 heading position
                h1_position = -1
                for j in range(min(i, 10)):  # Look back up to 10 lines or to current position
                    if re.match(r'^=\s+', lines[j]):  # H1 heading starts with single =
                        h1_position = j
                        break

                # If this is an attribute include near the H1 heading, don't add surrounding blank lines
                is_near_h1 = h1_position >= 0 and (i - h1_position) <= 2

                # Check if previous line is a comment or attribute (which belongs to this include)
                has_comment_above = prev_line and re.match(r'^//', prev_line)
                has_attribute_above = prev_line and re.match(r'^:', prev_line)

                # If it's an attribute include near H1, only the heading's blank line is needed
                if not (is_attribute_include and is_near_h1):
                    # Don't add blank line if there's a comment or attribute above (it was handled by the comment/attribute logic)
                    if not has_comment_above and not has_attribute_above:
                        # Add blank line before include if previous line is not empty
                        # This includes adding blank lines between consecutive includes
                        if (prev_line and
                            not re.match(r'^\s*$', prev_line)):
                            new_lines.append("")
                            changes_made = True
                            if verbose:
                                truncated = current_line[:50] + "..." if len(current_line) > 50 else current_line
                                messages.append(f"  Added blank line before include: {truncated}")

                new_lines.append(current_line)

                # If it's an attribute include near H1, don't add blank line after
                if not (is_attribute_include and is_near_h1):
                    # Add blank line after include if next line exists and is not empty and not an include
                    if (next_line and
                        not re.match(r'^\s*$', next_line) and
                        not re.match(r'^include::', next_line)):
                        new_lines.append("")
                        changes_made = True
                        if verbose:
                            truncated = current_line[:50] + "..." if len(current_line) > 50 else current_line
                            messages.append(f"  Added blank line after include: {truncated}")

        else:
            new_lines.append(current_line)

    # Apply changes if any were made
    if changes_made:
        # Clean up any consecutive blank lines we may have added
        cleaned_lines = []
        for i, line in enumerate(new_lines):
            # Check if this is a blank line we're about to add
            if line == "":
                # Check if the previous line is also a blank line
                if i > 0 and cleaned_lines and cleaned_lines[-1] == "":
                    # Skip this blank line as we already have one
                    continue
            cleaned_lines.append(line)

        if not dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for line in cleaned_lines:
                        f.write(line + '\n')
            except IOError as e:
                raise IOError(f"Error writing {file_path}: {e}")
    else:
        if verbose:
            messages.append("  No changes needed")

    return changes_made, messages


def find_adoc_files(path: Path) -> List[Path]:
    """Find all .adoc files in the given path"""
    adoc_files = []

    if path.is_file():
        if path.suffix == '.adoc':
            adoc_files.append(path)
    elif path.is_dir():
        adoc_files = list(path.rglob('*.adoc'))

    return adoc_files