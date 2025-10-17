#!/usr/bin/env python3
"""
format-asciidoc-spacing - Format AsciiDoc spacing.

Ensures blank lines after headings and around include directives.
"""

import argparse
import sys
from pathlib import Path

from doc_utils.format_asciidoc_spacing import process_file, find_adoc_files
from doc_utils.version_check import check_version_on_startup
from doc_utils.version import __version__


from doc_utils.spinner import Spinner
# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC) -> None:
    """Print message with color"""
    print(f"{color}{message}{Colors.NC}")


def main():
    # Check for updates (non-blocking, won't interfere with tool operation)
    check_version_on_startup()
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Format AsciiDoc files to ensure proper spacing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Format AsciiDoc files to ensure proper spacing:
- Blank line after headings (=, ==, ===, etc.)
- Blank lines around include:: directives

Examples:
  %(prog)s                                    # Process all .adoc files in current directory
  %(prog)s modules/                          # Process all .adoc files in modules/
  %(prog)s assemblies/my-guide.adoc          # Process single file
  %(prog)s --dry-run modules/               # Preview changes without modifying
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
        help='Show detailed output'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()

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
    adoc_files = find_adoc_files(target_path)

    if not adoc_files:
        if target_path.is_file():
            print_colored(f"Warning: {target_path} is not an AsciiDoc file (.adoc)", Colors.YELLOW)
        print(f"Processed 0 AsciiDoc file(s)")
        print("AsciiDoc spacing formatting complete!")
        return

    # Process each file
    files_processed = 0
    files_modified = 0

    for file_path in adoc_files:
        try:
            changes_made, messages = process_file(file_path, args.dry_run, args.verbose)

            # Print verbose messages
            if args.verbose:
                for msg in messages:
                    print(msg)

            if changes_made:
                files_modified += 1
                if args.dry_run:
                    print_colored(f"Would modify: {file_path}", Colors.YELLOW)
                else:
                    print_colored(f"Modified: {file_path}", Colors.GREEN)
            elif args.verbose:
                print(f"  No changes needed for: {file_path}")

            files_processed += 1

        except KeyboardInterrupt:
            print_colored("\nOperation cancelled by user", Colors.YELLOW)
            sys.exit(1)
        except IOError as e:
            print_colored(f"{e}", Colors.RED)
        except Exception as e:
            print_colored(f"Unexpected error processing {file_path}: {e}", Colors.RED)

    print(f"Processed {files_processed} AsciiDoc file(s)")
    if args.dry_run and files_modified > 0:
        print(f"Would modify {files_modified} file(s)")
    elif files_modified > 0:
        print(f"Modified {files_modified} file(s)")
    print("AsciiDoc spacing formatting complete!")


if __name__ == "__main__":
    main()