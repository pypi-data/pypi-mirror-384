#!/usr/bin/env python3
"""
MAQET CLI Entry Point.

Main CLI interface that uses the unified API generation system.
"""

import json
import sys
import traceback
from enum import IntEnum

from .__version__ import __version__
from .maqet import Maqet


class ExitCode(IntEnum):
    """Exit code constants for MAQET CLI."""

    SUCCESS = 0
    ERROR = 1
    INTERRUPTED = 2
    INVALID_CONFIG = 3


def main():
    """Execute the main CLI entry point."""
    # Check for --version flag first (before creating Maqet instance)
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"MAQET version {__version__}")
        return ExitCode.SUCCESS

    # Check for debug mode - this enables full tracebacks on errors
    # Note: --debug is different from -v/--verbose which controls log verbosity
    # --debug affects error reporting, -v affects logging levels
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        sys.argv.remove("--debug")

    # Check for output format
    output_format = "auto"
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]
            sys.argv.pop(idx)  # Remove --format
            sys.argv.pop(idx)  # Remove format value

    try:
        maqet = Maqet()
        result = maqet.cli()

        # Handle CLI output based on format
        _format_output(result, output_format)

        return ExitCode.SUCCESS

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(ExitCode.INTERRUPTED)

    except Exception as e:
        if debug_mode:
            # Print full traceback in debug mode
            print("\n=== Debug Traceback ===", file=sys.stderr)
            traceback.print_exc()
            print("=" * 23, file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
            print("Run with --debug for full traceback", file=sys.stderr)
        sys.exit(ExitCode.ERROR)


def _format_output(result, format_type: str = "auto"):
    """
    Format and print output using FormatterFactory.

    Args:
        result: Result data to format
        format_type: Output format (auto, json, yaml, plain, table)
    """
    if result is None:
        return

    from .formatters import FormatterFactory

    try:
        formatter = FormatterFactory.create(format_type)
        formatter.format(result)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(ExitCode.ERROR)


if __name__ == "__main__":
    main()
