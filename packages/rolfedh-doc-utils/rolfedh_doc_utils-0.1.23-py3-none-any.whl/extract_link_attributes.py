#!/usr/bin/env python3
"""
Extract link and xref macros containing attributes into attribute definitions.

This tool finds all link: and xref: macros whose URLs contain attributes,
creates attribute definitions for them, and replaces the macros with
attribute references.
"""

import argparse
import sys
from doc_utils.extract_link_attributes import extract_link_attributes
from doc_utils.version_check import check_version_on_startup
from doc_utils.version import __version__


def main():
    # Check for updates (non-blocking, won't interfere with tool operation)
    check_version_on_startup()
    """Main entry point for the extract-link-attributes CLI tool."""
    parser = argparse.ArgumentParser(
        description='Extract link and xref macros containing attributes into attribute definitions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with auto-discovery
  extract-link-attributes

  # Specify attribute file
  extract-link-attributes --attributes-file common-attributes.adoc

  # Non-interactive mode (uses most common link text)
  extract-link-attributes --non-interactive

  # Dry run to preview changes
  extract-link-attributes --dry-run

  # Scan specific directories
  extract-link-attributes --scan-dir modules --scan-dir assemblies
        """
    )

    parser.add_argument(
        '--attributes-file',
        help='Path to the attributes file to update (auto-discovered if not specified)'
    )

    parser.add_argument(
        '--scan-dir',
        action='append',
        help='Directory to scan for .adoc files (can be used multiple times, default: current directory)'
    )

    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Non-interactive mode: automatically use most common link text for variations'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--validate-links',
        action='store_true',
        help='Validate URLs in link-* attributes before extraction'
    )

    parser.add_argument(
        '--fail-on-broken',
        action='store_true',
        help='Exit extraction if broken links are found in attributes (requires --validate-links)'
    )

    parser.add_argument(
        '--macro-type',
        choices=['link', 'xref', 'both'],
        default='both',
        help='Type of macros to process: link, xref, or both (default: both)'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    try:
        success = extract_link_attributes(
            attributes_file=args.attributes_file,
            scan_dirs=args.scan_dir,
            interactive=not args.non_interactive,
            dry_run=args.dry_run,
            validate_links=args.validate_links,
            fail_on_broken=args.fail_on_broken,
            macro_type=args.macro_type
        )

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()