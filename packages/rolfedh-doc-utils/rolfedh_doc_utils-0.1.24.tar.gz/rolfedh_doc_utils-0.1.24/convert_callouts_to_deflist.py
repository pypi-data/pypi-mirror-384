#!/usr/bin/env python3
"""
convert-callouts-to-deflist - Convert AsciiDoc callouts to definition list format

Converts code blocks with callout-style annotations (<1>, <2>, etc.) to cleaner
definition list format with "where:" prefix.

This tool automatically scans all .adoc files in the current directory (recursively)
by default, or you can specify a specific file or directory.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC) -> None:
    """Print message with color"""
    print(f"{color}{message}{Colors.NC}")


@dataclass
class Callout:
    """Represents a callout with its number and explanation text."""
    number: int
    lines: List[str]  # List of lines to preserve formatting
    is_optional: bool = False


@dataclass
class CalloutGroup:
    """Represents one or more callouts that share the same code line."""
    code_line: str  # The actual code line (without callouts)
    callout_numbers: List[int]  # List of callout numbers on this line


@dataclass
class CodeBlock:
    """Represents a code block with its content and metadata."""
    start_line: int
    end_line: int
    delimiter: str
    content: List[str]
    language: Optional[str] = None


class CalloutConverter:
    """Converts callout-style documentation to definition list format."""

    # Pattern for code block start: [source,language] or [source] with optional attributes
    # Matches: [source], [source,java], [source,java,subs="..."], [source,java,options="..."], etc.
    CODE_BLOCK_START = re.compile(r'^\[source(?:,\s*(\w+))?(?:[,\s]+[^\]]+)?\]')

    # Pattern for callout number in code block (can appear multiple times per line)
    CALLOUT_IN_CODE = re.compile(r'<(\d+)>')

    # Pattern for callout explanation line: <1> Explanation text
    CALLOUT_EXPLANATION = re.compile(r'^<(\d+)>\s+(.+)$')

    # Pattern to detect user-replaceable values in angle brackets
    # Excludes heredoc syntax (<<) and comparison operators
    USER_VALUE_PATTERN = re.compile(r'(?<!<)<([a-zA-Z][^>]*)>')

    def __init__(self, dry_run: bool = False, verbose: bool = False, output_format: str = 'deflist'):
        self.dry_run = dry_run
        self.verbose = verbose
        self.output_format = output_format  # 'deflist' or 'bullets'
        self.changes_made = 0
        self.warnings = []  # Collect warnings for summary

    def log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[INFO] {message}")

    def find_code_blocks(self, lines: List[str]) -> List[CodeBlock]:
        """Find all code blocks in the document."""
        blocks = []
        i = 0

        while i < len(lines):
            # Check for [source] prefix first
            match = self.CODE_BLOCK_START.match(lines[i])
            if match:
                language = match.group(1)
                start = i
                i += 1

                # Find the delimiter line (---- or ....)
                if i < len(lines) and lines[i].strip() in ['----', '....']:
                    delimiter = lines[i].strip()
                    i += 1
                    content_start = i

                    # Find the closing delimiter
                    while i < len(lines):
                        if lines[i].strip() == delimiter:
                            content = lines[content_start:i]
                            blocks.append(CodeBlock(
                                start_line=start,
                                end_line=i,
                                delimiter=delimiter,
                                content=content,
                                language=language
                            ))
                            break
                        i += 1
            # Check for plain delimited blocks without [source] prefix
            elif lines[i].strip() in ['----', '....']:
                delimiter = lines[i].strip()
                start = i
                i += 1
                content_start = i

                # Find the closing delimiter
                while i < len(lines):
                    if lines[i].strip() == delimiter:
                        content = lines[content_start:i]
                        # Only add if block contains callouts
                        if any(self.CALLOUT_IN_CODE.search(line) for line in content):
                            blocks.append(CodeBlock(
                                start_line=start,
                                end_line=i,
                                delimiter=delimiter,
                                content=content,
                                language=None
                            ))
                        break
                    i += 1
            i += 1

        return blocks

    def extract_callouts_from_code(self, content: List[str]) -> List[CalloutGroup]:
        """
        Extract callout numbers from code block content.
        Returns list of CalloutGroups, where each group contains:
        - The code line (with user-replaceable value if found, or full line)
        - List of callout numbers on that line

        Multiple callouts on the same line are grouped together to be merged
        in the definition list.
        """
        groups = []

        for line in content:
            # Look for all callout numbers on this line
            callout_matches = list(self.CALLOUT_IN_CODE.finditer(line))
            if callout_matches:
                # Remove all callouts from the line to get the actual code
                line_without_callouts = self.CALLOUT_IN_CODE.sub('', line).strip()

                # Find all angle-bracket enclosed values
                user_values = self.USER_VALUE_PATTERN.findall(line_without_callouts)

                # Determine what to use as the code line term
                if user_values:
                    # Use the rightmost (closest to the callout) user value
                    code_line = user_values[-1]
                else:
                    # No angle-bracket value found - use the actual code line
                    code_line = line_without_callouts

                # Collect all callout numbers on this line
                callout_nums = [int(m.group(1)) for m in callout_matches]

                groups.append(CalloutGroup(
                    code_line=code_line,
                    callout_numbers=callout_nums
                ))

        return groups

    def extract_callout_explanations(self, lines: List[str], start_line: int) -> Tuple[Dict[int, Callout], int]:
        """
        Extract callout explanations following a code block.
        Returns dict of callouts and the line number where explanations end.
        """
        explanations = {}
        i = start_line + 1  # Start after the closing delimiter

        # Skip blank lines and continuation markers (+)
        while i < len(lines) and (not lines[i].strip() or lines[i].strip() == '+'):
            i += 1

        # Collect consecutive callout explanation lines
        while i < len(lines):
            match = self.CALLOUT_EXPLANATION.match(lines[i])
            if match:
                num = int(match.group(1))
                first_line = match.group(2).strip()
                explanation_lines = [first_line]
                i += 1

                # Collect continuation lines (lines that don't start with a new callout)
                # Continue until we hit a blank line, a new callout, or certain patterns
                while i < len(lines):
                    line = lines[i]
                    # Stop if we hit a blank line, new callout, or list start marker
                    if not line.strip() or self.CALLOUT_EXPLANATION.match(line) or line.startswith('[start='):
                        break
                    # Add continuation line preserving original formatting
                    explanation_lines.append(line)
                    i += 1

                # Check if marked as optional (only in first line)
                is_optional = False
                if first_line.lower().startswith('optional.') or first_line.lower().startswith('optional:'):
                    is_optional = True
                    # Remove "Optional." or "Optional:" from first line
                    explanation_lines[0] = first_line[9:].strip()
                elif '(Optional)' in first_line or '(optional)' in first_line:
                    is_optional = True
                    explanation_lines[0] = re.sub(r'\s*\(optional\)\s*', ' ', first_line, flags=re.IGNORECASE).strip()

                explanations[num] = Callout(num, explanation_lines, is_optional)
            else:
                break

        return explanations, i - 1

    def validate_callouts(self, callout_groups: List[CalloutGroup], explanations: Dict[int, Callout],
                         input_file: Path = None, block_start: int = None, block_end: int = None) -> bool:
        """
        Validate that callout numbers in code match explanation numbers.
        Returns True if valid, False otherwise.
        """
        # Extract all callout numbers from groups
        code_nums = set()
        for group in callout_groups:
            code_nums.update(group.callout_numbers)

        explanation_nums = set(explanations.keys())

        if code_nums != explanation_nums:
            # Format warning message with file and line numbers
            if input_file and block_start is not None and block_end is not None:
                # Line numbers are 1-indexed for display
                line_range = f"{block_start + 1}-{block_end + 1}"
                warning_msg = (
                    f"WARNING: {input_file.name} lines {line_range}: Callout mismatch: "
                    f"code has {sorted(code_nums)}, explanations have {sorted(explanation_nums)}"
                )
                print_colored(warning_msg, Colors.YELLOW)
                # Store warning for summary
                self.warnings.append(warning_msg)
            else:
                self.log(f"Callout mismatch: code has {code_nums}, explanations have {explanation_nums}")
            return False

        return True

    def remove_callouts_from_code(self, content: List[str]) -> List[str]:
        """Remove callout numbers from code block content (handles multiple callouts per line)."""
        cleaned = []
        for line in content:
            # Remove all callout numbers and trailing whitespace
            cleaned.append(self.CALLOUT_IN_CODE.sub('', line).rstrip())
        return cleaned

    def create_definition_list(self, callout_groups: List[CalloutGroup], explanations: Dict[int, Callout]) -> List[str]:
        """
        Create definition list from callout groups and explanations.

        For callouts with user-replaceable values in angle brackets, uses those.
        For callouts without values, uses the actual code line as the term.

        When multiple callouts share the same code line (same group), their
        explanations are merged using AsciiDoc list continuation (+).
        """
        lines = ['\nwhere:']

        # Process each group (which may contain one or more callouts)
        for group in callout_groups:
            code_line = group.code_line
            callout_nums = group.callout_numbers

            # Check if this is a user-replaceable value (contains angle brackets but not heredoc)
            # User values are single words/phrases in angle brackets like <my-value>
            user_values = self.USER_VALUE_PATTERN.findall(code_line)

            if user_values and len(user_values) == 1 and len(code_line) < 100:
                # This looks like a user-replaceable value placeholder
                # Format the value (ensure it has angle brackets)
                user_value = user_values[0]
                if not user_value.startswith('<'):
                    user_value = f'<{user_value}>'
                if not user_value.endswith('>'):
                    user_value = f'{user_value}>'
                term = f'`{user_value}`'
            else:
                # This is a code line - use it as-is in backticks
                term = f'`{code_line}`'

            # Add blank line before each term
            lines.append('')
            lines.append(f'{term}::')

            # Add explanations for all callouts in this group
            for idx, callout_num in enumerate(callout_nums):
                explanation = explanations[callout_num]

                # If this is not the first explanation in the group, add continuation marker
                if idx > 0:
                    lines.append('+')

                # Add explanation lines, prepending "Optional. " to first line if needed
                for line_idx, line in enumerate(explanation.lines):
                    if line_idx == 0 and explanation.is_optional:
                        lines.append(f'Optional. {line}')
                    else:
                        lines.append(line)

        return lines

    def create_bulleted_list(self, callout_groups: List[CalloutGroup], explanations: Dict[int, Callout]) -> List[str]:
        """
        Create bulleted list from callout groups and explanations.

        Follows Red Hat style guide format:
        - Each bullet starts with `*` followed by backticked code element
        - Colon separates element from explanation
        - Blank line between each bullet point

        For callouts with user-replaceable values in angle brackets, uses those.
        For callouts without values, uses the actual code line as the term.

        When multiple callouts share the same code line (same group), their
        explanations are merged with line breaks.
        """
        lines = ['']  # Start with blank line before list

        # Process each group (which may contain one or more callouts)
        for group in callout_groups:
            code_line = group.code_line
            callout_nums = group.callout_numbers

            # Check if this is a user-replaceable value (contains angle brackets but not heredoc)
            # User values are single words/phrases in angle brackets like <my-value>
            user_values = self.USER_VALUE_PATTERN.findall(code_line)

            if user_values and len(user_values) == 1 and len(code_line) < 100:
                # This looks like a user-replaceable value placeholder
                # Format the value (ensure it has angle brackets)
                user_value = user_values[0]
                if not user_value.startswith('<'):
                    user_value = f'<{user_value}>'
                if not user_value.endswith('>'):
                    user_value = f'{user_value}>'
                term = f'`{user_value}`'
            else:
                # This is a code line - use it as-is in backticks
                term = f'`{code_line}`'

            # Collect all explanations for this group
            all_explanation_lines = []
            for idx, callout_num in enumerate(callout_nums):
                explanation = explanations[callout_num]

                # Add explanation lines, prepending "Optional. " to first line if needed
                for line_idx, line in enumerate(explanation.lines):
                    if line_idx == 0 and explanation.is_optional:
                        all_explanation_lines.append(f'Optional. {line}')
                    else:
                        all_explanation_lines.append(line)

                # If there are more callouts in this group, add a line break
                if idx < len(callout_nums) - 1:
                    all_explanation_lines.append('')

            # Format as bullet point: * `term`: explanation
            # First line uses the bullet marker
            lines.append(f'*   {term}: {all_explanation_lines[0]}')

            # Continuation lines (if any) are indented to align with first line
            for continuation_line in all_explanation_lines[1:]:
                if continuation_line:  # Skip empty lines for now
                    lines.append(f'    {continuation_line}')
                else:
                    lines.append('')

            # Add blank line after each bullet point
            lines.append('')

        return lines

    def convert_file(self, input_file: Path) -> Tuple[int, bool]:
        """
        Convert callouts in a file to definition list format.
        Returns tuple of (number of conversions, whether file was modified).
        """
        # Read input file
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f]
        except Exception as e:
            print_colored(f"Error reading {input_file}: {e}", Colors.RED)
            return 0, False

        self.log(f"Processing {input_file} ({len(lines)} lines)")

        # Find all code blocks
        blocks = self.find_code_blocks(lines)
        self.log(f"Found {len(blocks)} code blocks")

        if not blocks:
            return 0, False

        # Process blocks in reverse order to maintain line numbers
        new_lines = lines.copy()
        conversions = 0

        for block in reversed(blocks):
            # Extract callouts from code (returns list of CalloutGroups)
            callout_groups = self.extract_callouts_from_code(block.content)

            if not callout_groups:
                self.log(f"No callouts in block at line {block.start_line + 1}")
                continue

            # Extract all callout numbers for logging
            all_callout_nums = []
            for group in callout_groups:
                all_callout_nums.extend(group.callout_numbers)

            self.log(f"Block at line {block.start_line + 1} has callouts: {all_callout_nums}")

            # Extract explanations
            explanations, explanation_end = self.extract_callout_explanations(new_lines, block.end_line)

            if not explanations:
                self.log(f"No explanations found after block at line {block.start_line + 1}")
                continue

            # Validate callouts match
            if not self.validate_callouts(callout_groups, explanations, input_file, block.start_line, block.end_line):
                continue

            self.log(f"Converting block at line {block.start_line + 1}")

            # Remove callouts from code
            cleaned_content = self.remove_callouts_from_code(block.content)

            # Create output list (definition list or bulleted list based on format option)
            if self.output_format == 'bullets':
                output_list = self.create_bulleted_list(callout_groups, explanations)
            else:  # default to 'deflist'
                output_list = self.create_definition_list(callout_groups, explanations)

            # Replace in document
            # 1. Update code block content
            # Check if block has [source] prefix by checking if start_line contains [source]
            has_source_prefix = self.CODE_BLOCK_START.match(new_lines[block.start_line])
            if has_source_prefix:
                content_start = block.start_line + 2  # After [source] and ----
            else:
                content_start = block.start_line + 1  # After ---- only
            content_end = block.end_line

            # 2. Remove old callout explanations
            explanation_start = block.end_line + 1
            while explanation_start < len(new_lines) and not new_lines[explanation_start].strip():
                explanation_start += 1

            # Build the new section
            new_section = (
                new_lines[:content_start] +
                cleaned_content +
                [new_lines[content_end]] +  # Keep closing delimiter
                output_list +
                new_lines[explanation_end + 1:]
            )

            new_lines = new_section
            conversions += 1
            self.changes_made += 1

        # Write output
        if conversions > 0 and not self.dry_run:
            try:
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines) + '\n')
                self.log(f"Wrote {input_file}")
            except Exception as e:
                print_colored(f"Error writing {input_file}: {e}", Colors.RED)
                return 0, False

        return conversions, conversions > 0


def find_adoc_files(path: Path, exclude_dirs: List[str] = None, exclude_files: List[str] = None) -> List[Path]:
    """
    Find all .adoc files in the given path.

    Args:
        path: Path to search (file or directory)
        exclude_dirs: List of directory patterns to exclude
        exclude_files: List of file patterns to exclude

    Returns:
        List of Path objects for .adoc files
    """
    adoc_files = []
    exclude_dirs = exclude_dirs or []
    exclude_files = exclude_files or []

    # Always exclude .vale directory by default (Vale linter fixtures)
    if '.vale' not in exclude_dirs:
        exclude_dirs.append('.vale')

    if path.is_file():
        if path.suffix == '.adoc':
            # Check if file should be excluded
            if not any(excl in str(path) for excl in exclude_files):
                adoc_files.append(path)
    elif path.is_dir():
        # Recursively find all .adoc files
        for adoc_file in path.rglob('*.adoc'):
            # Check if in excluded directory
            if any(excl in str(adoc_file) for excl in exclude_dirs):
                continue
            # Check if file should be excluded
            if any(excl in str(adoc_file) for excl in exclude_files):
                continue
            adoc_files.append(adoc_file)

    return sorted(adoc_files)


def load_exclusion_list(exclusion_file: Path) -> Tuple[List[str], List[str]]:
    """
    Load exclusion list from file.
    Returns tuple of (excluded_dirs, excluded_files).
    """
    excluded_dirs = []
    excluded_files = []

    try:
        with open(exclusion_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # If it ends with /, it's a directory
                if line.endswith('/'):
                    excluded_dirs.append(line.rstrip('/'))
                else:
                    # Could be file or directory - check if it has extension
                    if '.' in Path(line).name:
                        excluded_files.append(line)
                    else:
                        excluded_dirs.append(line)
    except Exception as e:
        print_colored(f"Warning: Could not read exclusion file {exclusion_file}: {e}", Colors.YELLOW)

    return excluded_dirs, excluded_files


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert AsciiDoc callouts to definition list format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Convert AsciiDoc callout-style documentation to definition list format.

This script identifies code blocks with callout numbers (<1>, <2>, etc.) and their
corresponding explanation lines, then converts them to a cleaner definition list format
with "where:" prefix.

Examples:
  %(prog)s                                    # Process all .adoc files in current directory
  %(prog)s modules/                          # Process all .adoc files in modules/
  %(prog)s assemblies/my-guide.adoc          # Process single file
  %(prog)s --dry-run modules/               # Preview changes without modifying
  %(prog)s --exclude-dir .vale modules/     # Exclude .vale directory

Example transformation:
  FROM:
    [source,yaml]
    ----
    name: <my-secret> <1>
    key: <my-key> <2>
    ----
    <1> Secret name
    <2> Key value

  TO:
    [source,yaml]
    ----
    name: <my-secret>
    key: <my-key>
    ----

    where:

    `<my-secret>`::
    Secret name

    `<my-key>`::
    Key value
        """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='File or directory to process (default: current directory)'
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['deflist', 'bullets'],
        default='deflist',
        help='Output format: "deflist" for definition list with "where:" (default), "bullets" for bulleted list'
    )
    parser.add_argument(
        '--exclude-dir',
        action='append',
        dest='exclude_dirs',
        default=[],
        help='Directory to exclude (can be used multiple times)'
    )
    parser.add_argument(
        '--exclude-file',
        action='append',
        dest='exclude_files',
        default=[],
        help='File to exclude (can be used multiple times)'
    )
    parser.add_argument(
        '--exclude-list',
        type=Path,
        help='Path to file containing directories/files to exclude, one per line'
    )

    args = parser.parse_args()

    # Load exclusion list if provided
    if args.exclude_list:
        if args.exclude_list.exists():
            excluded_dirs, excluded_files = load_exclusion_list(args.exclude_list)
            args.exclude_dirs.extend(excluded_dirs)
            args.exclude_files.extend(excluded_files)
        else:
            print_colored(f"Warning: Exclusion list file not found: {args.exclude_list}", Colors.YELLOW)

    # Convert path to Path object
    target_path = Path(args.path)

    # Check if path exists
    if not target_path.exists():
        print_colored(f"Error: Path does not exist: {target_path}", Colors.RED)
        sys.exit(1)

    # Display dry-run mode message
    if args.dry_run:
        print_colored("DRY RUN MODE - No files will be modified", Colors.YELLOW)

    # Find all AsciiDoc files
    adoc_files = find_adoc_files(target_path, args.exclude_dirs, args.exclude_files)

    if not adoc_files:
        if target_path.is_file():
            print_colored(f"Warning: {target_path} is not an AsciiDoc file (.adoc)", Colors.YELLOW)
        else:
            print(f"No AsciiDoc files found in {target_path}")
        print("Processed 0 AsciiDoc file(s)")
        return

    print(f"Found {len(adoc_files)} AsciiDoc file(s) to process")

    # Create converter
    converter = CalloutConverter(dry_run=args.dry_run, verbose=args.verbose, output_format=args.format)

    # Process each file
    files_processed = 0
    files_modified = 0
    total_conversions = 0

    for file_path in adoc_files:
        try:
            conversions, modified = converter.convert_file(file_path)

            if modified:
                files_modified += 1
                total_conversions += conversions
                if args.dry_run:
                    print_colored(f"Would modify: {file_path} ({conversions} code block(s))", Colors.YELLOW)
                else:
                    print_colored(f"Modified: {file_path} ({conversions} code block(s))", Colors.GREEN)
            elif args.verbose:
                print(f"  No callouts found in: {file_path}")

            files_processed += 1

        except KeyboardInterrupt:
            print_colored("\nOperation cancelled by user", Colors.YELLOW)
            sys.exit(1)
        except Exception as e:
            print_colored(f"Unexpected error processing {file_path}: {e}", Colors.RED)
            if args.verbose:
                import traceback
                traceback.print_exc()

    # Summary
    print(f"\nProcessed {files_processed} AsciiDoc file(s)")
    if args.dry_run and files_modified > 0:
        print(f"Would modify {files_modified} file(s) with {total_conversions} code block conversion(s)")
    elif files_modified > 0:
        print_colored(f"Modified {files_modified} file(s) with {total_conversions} code block conversion(s)", Colors.GREEN)
    else:
        print("No files with callouts to convert")

    # Display warning summary if any warnings were collected
    if converter.warnings:
        print_colored(f"\n⚠️  {len(converter.warnings)} Warning(s):", Colors.YELLOW)
        for warning in converter.warnings:
            print_colored(f"  {warning}", Colors.YELLOW)
        print()

    if args.dry_run and files_modified > 0:
        print_colored("DRY RUN - No files were modified", Colors.YELLOW)

    return 0 if files_processed >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
