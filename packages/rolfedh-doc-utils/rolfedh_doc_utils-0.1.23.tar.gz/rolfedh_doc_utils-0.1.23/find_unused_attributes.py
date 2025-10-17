"""
Find Unused AsciiDoc Attributes

Scans an attributes file for attribute definitions (e.g., :version: 1.1), then recursively scans all .adoc files in the current directory (ignoring symlinks) for usages of those attributes (e.g., {version}).

If no attributes file is specified, the tool will auto-discover attributes files in the repository and let you choose one interactively.

Any attribute defined but not used in any .adoc file is reported as NOT USED in both the command line output and a timestamped output file.
"""

import argparse
import os
import sys
from datetime import datetime
from doc_utils.unused_attributes import find_unused_attributes, find_attributes_files, select_attributes_file, comment_out_unused_attributes
from doc_utils.spinner import Spinner
from doc_utils.version_check import check_version_on_startup
from doc_utils.version import __version__

def main():
    # Check for updates (non-blocking, won't interfere with tool operation)
    check_version_on_startup()
    parser = argparse.ArgumentParser(description='Find unused AsciiDoc attributes.')
    parser.add_argument(
        'attributes_file',
        nargs='?',  # Make it optional
        help='Path to the attributes file. If not specified, auto-discovers attributes files.'
    )
    parser.add_argument('-o', '--output', action='store_true', help='Write results to a timestamped txt file in your home directory.')
    parser.add_argument('-c', '--comment-out', action='store_true', help='Comment out unused attributes in the attributes file with "// Unused".')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    args = parser.parse_args()

    # Determine which attributes file to use
    if args.attributes_file:
        # User specified a file
        attr_file = args.attributes_file
    else:
        # Auto-discover attributes files
        spinner = Spinner("Searching for attributes files")
        spinner.start()
        attributes_files = find_attributes_files('.')
        spinner.stop()

        if not attributes_files:
            print("No attributes files found in the repository.")
            print("You can specify a file directly: find-unused-attributes <path-to-attributes-file>")
            return 1

        attr_file = select_attributes_file(attributes_files)
        if not attr_file:
            print("No attributes file selected.")
            return 1

    try:
        spinner = Spinner(f"Analyzing attributes in {os.path.basename(attr_file)}")
        spinner.start()
        unused = find_unused_attributes(attr_file, '.')
        spinner.stop(f"Found {len(unused)} unused attributes")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"\nPlease ensure the file '{attr_file}' exists.")
        print("Usage: find-unused-attributes [<path-to-attributes-file>]")
        return 1
    except (ValueError, PermissionError) as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

    lines = [f":{attr}:  NOT USED" for attr in unused]
    output = '\n'.join(lines)

    if output:
        print('Unused attributes:')
        print(output)
    else:
        print('All attributes are used.')

    if args.output and output:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        home_dir = os.path.expanduser('~')
        filename = os.path.join(home_dir, f'unused_attributes_{timestamp}.txt')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('Unused attributes in ' + attr_file + '\n')
            f.write(output + '\n')
        print(f'Results written to: {filename}')

    if args.comment_out and output:
        # Ask for confirmation before modifying the file
        print(f'\nThis will comment out {len(unused)} unused attributes in: {attr_file}')
        response = input('Continue? (y/n): ').strip().lower()
        if response == 'y':
            commented_count = comment_out_unused_attributes(attr_file, unused)
            print(f'Commented out {commented_count} unused attributes in: {attr_file}')
        else:
            print('Operation cancelled.')

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
