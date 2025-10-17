#!/usr/bin/env python3
"""
Validate links in AsciiDoc documentation.

This tool checks all links in AsciiDoc files for validity, including:
- External HTTP/HTTPS links
- Internal cross-references (xref)
- Image paths
"""

import argparse
import sys
import json
from doc_utils.validate_links import LinkValidator, parse_transpositions, format_results
from doc_utils.version_check import check_version_on_startup
from doc_utils.version import __version__
from doc_utils.spinner import Spinner


def main():
    # Check for updates (non-blocking, won't interfere with tool operation)
    check_version_on_startup()
    """Main entry point for the validate-links CLI tool."""
    parser = argparse.ArgumentParser(
        description='Validate links in AsciiDoc documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic validation
  validate-links

  # Validate against preview environment
  validate-links --transpose "https://docs.redhat.com--https://preview.docs.redhat.com"

  # Multiple transpositions
  validate-links \\
    --transpose "https://docs.redhat.com--https://preview.docs.redhat.com" \\
    --transpose "https://access.redhat.com--https://stage.access.redhat.com"

  # With specific options
  validate-links \\
    --transpose "https://docs.example.com--https://preview.example.com" \\
    --attributes-file common-attributes.adoc \\
    --timeout 15 \\
    --retry 3 \\
    --parallel 20 \\
    --exclude-domain localhost \\
    --exclude-domain example.com

  # Export results to JSON
  validate-links --output report.json --format json
        """
    )

    parser.add_argument(
        '--transpose',
        action='append',
        help='Transpose URLs from production to preview/staging (format: from_url--to_url)'
    )

    parser.add_argument(
        '--attributes-file',
        help='Path to the AsciiDoc attributes file'
    )

    parser.add_argument(
        '--scan-dir',
        action='append',
        help='Directory to scan for .adoc files (can be used multiple times, default: current directory)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Timeout in seconds for each URL check (default: 10)'
    )

    parser.add_argument(
        '--retry',
        type=int,
        default=3,
        help='Number of retries for failed URLs (default: 3)'
    )

    parser.add_argument(
        '--parallel',
        type=int,
        default=10,
        help='Number of parallel URL checks (default: 10)'
    )

    parser.add_argument(
        '--cache-duration',
        type=int,
        default=3600,
        help='Cache duration in seconds (default: 3600)'
    )

    parser.add_argument(
        '--exclude-domain',
        action='append',
        dest='exclude_domains',
        help='Domain to exclude from validation (can be used multiple times)'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching of validation results'
    )

    parser.add_argument(
        '--output',
        help='Output file for results'
    )

    parser.add_argument(
        '--format',
        choices=['text', 'json', 'junit'],
        default='text',
        help='Output format (default: text)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output including warnings'
    )

    parser.add_argument(
        '--fail-on-broken',
        action='store_true',
        help='Exit with error code if broken links are found'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    # Parse transpositions
    transpositions = parse_transpositions(args.transpose)

    # Show configuration
    print("Validating links in documentation...")
    if args.attributes_file:
        print(f"Loading attributes from {args.attributes_file}")
    if transpositions:
        print("\nURL Transposition Rules:")
        for from_url, to_url in transpositions:
            print(f"  {from_url} → {to_url}")
        print()

    # Create validator
    validator = LinkValidator(
        timeout=args.timeout,
        retry=args.retry,
        parallel=args.parallel,
        cache_duration=args.cache_duration if not args.no_cache else 0,
        transpositions=transpositions
    )

    try:
        # Run validation
        spinner = Spinner("Validating links")
        spinner.start()
        results = validator.validate_all(
            scan_dirs=args.scan_dir,
            attributes_file=args.attributes_file,
            exclude_domains=args.exclude_domains
        )
        total = results['summary']['total']
        valid = results['summary']['valid']
        spinner.stop(f"Validated {total} links: {valid} valid")

        # Format output
        if args.format == 'json':
            output = json.dumps(results, indent=2)
        elif args.format == 'junit':
            # TODO: Implement JUnit XML format
            output = format_results(results, verbose=args.verbose)
        else:
            output = format_results(results, verbose=args.verbose)

        # Save or print output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Results saved to {args.output}")
            # Still print summary to console
            if args.format != 'text':
                summary = results['summary']
                print(f"\nSummary: {summary['valid']} valid, {summary['broken']} broken, "
                      f"{summary['warnings']} warnings")
        else:
            print(output)

        # Exit code
        if args.fail_on_broken and results['summary']['broken'] > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nValidation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()