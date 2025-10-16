"""
Shell script generator for fakenode.
Generates customizable shell scripts that wrap the fakenode server.
"""

import argparse
import os
import sys
import stat


def generate_shell_script(show_version, python_path, create_files=False):
    """Generate a shell script that wraps fakenode with customizable settings.

    Args:
        show_version: The version string to hardcode in the script
        python_path: The path to the Python binary to use
        create_files: Whether to enable file creation (default: False)

    Returns:
        The shell script as a string
    """
    create_files_value = "true" if create_files else "false"

    script = f"""#!/bin/bash
#
# fakenode shell script
# This script can be customized for each node by editing the variables below.

# Version to report (can be edited manually)
SHOW_VERSION="{show_version}"

# Python binary to use (can be edited manually)
PYTHON_PATH="{python_path}"

# Enable file creation - set to "true" to pass --create-files to fakenode (can be edited manually)
CREATE_FILES={create_files_value}

# Build command line arguments
ARGS=("--show-version" "$SHOW_VERSION")

# Add --create-files if enabled
if [ "$CREATE_FILES" = "true" ]; then
    ARGS+=("--create-files")
fi

# Add all passed arguments
ARGS+=("$@")

# Launch fakenode with the configured version and pass through all arguments
"$PYTHON_PATH" -m fakenode.server "${{ARGS[@]}}"
"""
    return script


def main():
    """Main entry point for the fakeshell CLI."""
    parser = argparse.ArgumentParser(
        description='Generate shell scripts for fakenode deployment'
    )

    parser.add_argument(
        '--show-version',
        type=str,
        required=True,
        help='Version number to hardcode in the script'
    )

    parser.add_argument(
        '--python',
        type=str,
        default='python3',
        help='Path to Python binary (default: python3)'
    )

    parser.add_argument(
        '--create-files',
        action='store_true',
        help='Enable file creation in the generated script (default: false)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: stdout). Will set executable bit on Unix systems.'
    )

    args = parser.parse_args()

    # Generate the shell script
    script = generate_shell_script(args.show_version, args.python, args.create_files)

    # Output to stdout or file
    if args.output:
        try:
            # Create the file
            with open(args.output, 'w') as f:
                f.write(script)

            # Set executable bit on Unix systems
            if os.name != 'nt':  # Not Windows
                current_permissions = os.stat(args.output).st_mode
                os.chmod(args.output, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            print(f"Shell script created: {args.output}")

        except Exception as e:
            print(f"Error: Could not create file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Output to stdout
        print(script, end='')


if __name__ == '__main__':
    main()
