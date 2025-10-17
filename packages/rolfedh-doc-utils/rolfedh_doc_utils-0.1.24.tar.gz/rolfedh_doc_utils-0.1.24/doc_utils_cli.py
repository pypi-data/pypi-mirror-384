#!/usr/bin/env python3
"""
doc-utils - CLI tools for AsciiDoc documentation projects

Main entry point that provides a hub for all doc-utils tools.
"""

import argparse
import sys
from doc_utils.version import __version__
from doc_utils.version_check import check_version_on_startup


# Tool definitions with descriptions
TOOLS = [
    {
        'name': 'validate-links',
        'description': 'Validates all links in documentation with URL transposition',
        'example': 'validate-links --transpose "https://prod--https://preview"'
    },
    {
        'name': 'extract-link-attributes',
        'description': 'Extracts link/xref macros with attributes into reusable definitions',
        'example': 'extract-link-attributes --dry-run'
    },
    {
        'name': 'replace-link-attributes',
        'description': 'Resolves Vale LinkAttribute issues by replacing attributes in link URLs',
        'example': 'replace-link-attributes --dry-run'
    },
    {
        'name': 'format-asciidoc-spacing',
        'description': 'Standardizes spacing after headings and around includes',
        'example': 'format-asciidoc-spacing --dry-run modules/'
    },
    {
        'name': 'check-scannability',
        'description': 'Analyzes document readability by checking sentence/paragraph length',
        'example': 'check-scannability --max-sentence-length 5'
    },
    {
        'name': 'archive-unused-files',
        'description': 'Finds and optionally archives unreferenced AsciiDoc files',
        'example': 'archive-unused-files  # preview\narchive-unused-files --archive  # execute'
    },
    {
        'name': 'archive-unused-images',
        'description': 'Finds and optionally archives unreferenced image files',
        'example': 'archive-unused-images  # preview\narchive-unused-images --archive  # execute'
    },
    {
        'name': 'find-unused-attributes',
        'description': 'Identifies unused attribute definitions in AsciiDoc files',
        'example': 'find-unused-attributes  # auto-discovers attributes files'
    },
    {
        'name': 'convert-callouts-to-deflist',
        'description': 'Converts callout-style annotations to definition list format',
        'example': 'convert-callouts-to-deflist --dry-run modules/'
    },
]


def print_tools_list():
    """Print a formatted list of all available tools."""
    print("\n🛠️  Available Tools:\n")

    for tool in TOOLS:
        # Print tool name and description
        experimental = " [EXPERIMENTAL]" if "[EXPERIMENTAL]" in tool['description'] else ""
        desc = tool['description'].replace(" [EXPERIMENTAL]", "")
        print(f"  {tool['name']}{experimental}")
        print(f"    {desc}")
        print()


def print_help():
    """Print comprehensive help information."""
    print(f"doc-utils v{__version__}")
    print("\nCLI tools for maintaining clean, consistent AsciiDoc documentation repositories.")

    print_tools_list()

    print("📚 Usage:")
    print("  doc-utils --version          Show version information")
    print("  doc-utils --list             List all available tools")
    print("  doc-utils --help             Show this help message")
    print("  <tool-name> --help           Show help for a specific tool")
    print()
    print("📖 Documentation:")
    print("  https://rolfedh.github.io/doc-utils/")
    print()
    print("💡 Examples:")
    print("  find-unused-attributes")
    print("  check-scannability --max-sentence-length 5")
    print("  format-asciidoc-spacing --dry-run modules/")
    print()
    print("⚠️  Safety First:")
    print("  Always work in a git branch and review changes with 'git diff'")
    print()


def main():
    """Main entry point for doc-utils command."""
    # Check for updates (non-blocking)
    check_version_on_startup()

    parser = argparse.ArgumentParser(
        description='doc-utils - CLI tools for AsciiDoc documentation projects',
        add_help=False  # We'll handle help ourselves
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'doc-utils {__version__}'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available tools'
    )

    parser.add_argument(
        '--help', '-h',
        action='store_true',
        help='Show this help message'
    )

    # Parse known args to allow for future expansion
    args, remaining = parser.parse_known_args()

    # Handle flags
    if args.list:
        print_tools_list()
        return 0

    if args.help or len(sys.argv) == 1:
        print_help()
        return 0

    # If we get here with remaining args, show help
    if remaining:
        print(f"doc-utils: unknown command or option: {' '.join(remaining)}")
        print("\nRun 'doc-utils --help' for usage information.")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
