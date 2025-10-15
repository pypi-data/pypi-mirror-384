"""
CLI Generator

Automatically generates argparse CLI commands from @api_method decorated methods.

This module implements the CLI interface generation component of MAQET's unified API system.
It takes method metadata and creates a complete command-line interface with proper argument
parsing, help text, and command routing.

The CLIGenerator converts Python method signatures into argparse subcommands, handling:
- Required and optional parameters
- Type conversion (str, int, bool, list)
- Default values and help text
- Command examples and documentation
- Error handling and validation

Example:
    @api_method(cli_name="start", description="Start VM")
    def start(self, vm_id: str, detach: bool = False):
        pass

    Becomes CLI command:
    $ maqet start myvm --detach
"""

import argparse
import inspect
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union, get_args, get_origin

from ..api import APIMethodMetadata, APIRegistry
from ..logger import configure_file_logging, set_verbosity
from .base_generator import BaseGenerator

LOG = logging.getLogger(__name__)


class CLIGenerator(BaseGenerator):
    """
    Generates CLI commands from @api_method decorated methods.

    This generator creates an argparse-based CLI that automatically
    maps CLI arguments to method parameters and executes the appropriate
    method on the Maqet instance.

    Key Features:
    - Automatic subcommand generation from method metadata
    - Type-aware argument parsing (bool flags, optional args, etc.)
    - Built-in help generation with examples and descriptions
    - Global options support (--verbose, --config-dir, etc.)
    - Proper error handling and user feedback

    Usage:
        generator = CLIGenerator(maqet_instance, API_REGISTRY)
        result = generator.run(sys.argv[1:])

    The generator automatically creates CLI commands like:
    - maqet add config.yaml --name myvm
    - maqet start myvm --detach
    - maqet qmp myvm system_powerdown
    """

    def __init__(self, maqet_instance: Any, registry: APIRegistry):
        """
        Initialize CLI generator.

        Args:
            maqet_instance: Instance of Maqet class
            registry: API registry containing method metadata
        """
        super().__init__(maqet_instance, registry)
        self.parser: Optional[argparse.ArgumentParser] = None

    def generate(self) -> argparse.ArgumentParser:
        """
        Generate argparse CLI from registered methods.

        Returns:
            Configured ArgumentParser
        """
        # Create parent parser with global options for subparsers
        # This allows global options AFTER subcommands (e.g., maqet ls -v)
        self.global_parent = argparse.ArgumentParser(add_help=False)
        self._add_global_options_to_parent()

        # Create main parser with global options at top level
        # This allows global options BEFORE subcommands (e.g., maqet -v ls)
        self.parser = argparse.ArgumentParser(
            prog="maqet",
            description="MAQET - M4x0n's QEMU Tool for VM management",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Add global options directly to main parser (for before subcommand)
        self._add_global_options_to_main()

        # Add subcommands
        subparsers = self.parser.add_subparsers(
            dest="command", help="Available commands", metavar="COMMAND"
        )

        # Group methods by parent (None for top-level, string for nested)
        parent_groups = {}
        for category in self.registry.get_categories():
            methods = self.registry.get_by_category(category)
            for metadata in methods:
                if not metadata.hidden:
                    parent = metadata.parent
                    if parent not in parent_groups:
                        parent_groups[parent] = []
                    parent_groups[parent].append(metadata)

        # Add top-level commands (parent=None)
        if None in parent_groups:
            for metadata in parent_groups[None]:
                self._add_subcommand(subparsers, metadata)

        # Add parent commands with nested subcommands
        for parent, child_methods in parent_groups.items():
            if parent is not None:
                self._add_parent_command(subparsers, parent, child_methods)

        return self.parser

    def run(self, args: Optional[List[str]] = None) -> Any:
        """
        Parse arguments and execute the appropriate method.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])

        Returns:
            Result of method execution
        """
        if self.parser is None:
            self.generate()

        parsed_args = self.parser.parse_args(args)

        # Configure logging based on verbosity flags
        self._configure_logging(parsed_args)

        if not hasattr(parsed_args, "command") or parsed_args.command is None:
            self.parser.print_help()
            sys.exit(1)

        # Determine which command to execute (handle nested subcommands)
        command_name = parsed_args.command

        # Check if this is a nested subcommand
        if hasattr(parsed_args, "subcommand") and parsed_args.subcommand:
            # This is a nested command (e.g., maqet qmp pause)
            metadata = self.registry.get_by_cli_name(parsed_args.subcommand)
            if not metadata:
                print(
                    f"Error: Unknown subcommand '{parsed_args.subcommand}'",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            # This is a top-level command (e.g., maqet start)
            metadata = self.registry.get_by_cli_name(command_name)
            if not metadata:
                print(
                    f"Error: Unknown command '{command_name}'",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Execute method
        try:
            result = self._execute_method(metadata, parsed_args)
            return result
        except Exception as e:
            cmd_display = (
                f"{command_name} {parsed_args.subcommand}"
                if hasattr(parsed_args, "subcommand") and parsed_args.subcommand
                else command_name
            )
            print(
                f"Error executing {cmd_display}: {e}", file=sys.stderr
            )
            sys.exit(1)

    def _add_global_options_to_parent(self) -> None:
        """Add global CLI options to parent parser (for subparsers)."""
        # TODO(architect, 2025-10-10): [REFACTOR] Duplicate code - exact same as _add_global_options_to_main
        # Context: Global options added twice (to main parser and parent parser), exact same code
        # duplicated. Issue #10 in ARCHITECTURAL_REVIEW.md.
        #
        # Recommendation: Extract to common method:
        #   def _add_global_options(self, parser):
        #       parser.add_argument("-v", "--verbose", ...)
        # Then call from both methods.
        #
        # Effort: Small (<1 hour)
        # Priority: Medium
        # See: ARCHITECTURAL_REVIEW.md Issue #10
        self.global_parent.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Increase verbosity (-v, -vv, -vvv)",
        )
        self.global_parent.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Suppress non-error output",
        )
        self.global_parent.add_argument(
            "--config-dir", help="Override config directory path"
        )
        self.global_parent.add_argument(
            "--data-dir", help="Override data directory path"
        )
        self.global_parent.add_argument(
            "--runtime-dir", help="Override runtime directory path"
        )
        self.global_parent.add_argument(
            "--log-file", help="Enable file logging to specified path"
        )

    def _add_global_options_to_main(self) -> None:
        """Add global CLI options to main parser (for before subcommand)."""
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Increase verbosity (-v, -vv, -vvv)",
        )
        self.parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Suppress non-error output",
        )
        self.parser.add_argument(
            "--config-dir", help="Override config directory path"
        )
        self.parser.add_argument(
            "--data-dir", help="Override data directory path"
        )
        self.parser.add_argument(
            "--runtime-dir", help="Override runtime directory path"
        )
        self.parser.add_argument(
            "--log-file", help="Enable file logging to specified path"
        )

    def _configure_logging(self, args: argparse.Namespace) -> None:
        """
        Configure logging based on CLI arguments.

        Args:
            args: Parsed command line arguments
        """
        # Handle verbosity levels
        # Check both verbose and count attribute (for compatibility)
        verbosity = max(
            getattr(args, "verbose", 0) or 0,
            getattr(args, "count", 0) or 0
        )
        quiet = getattr(args, "quiet", False)

        if quiet:
            # Set to ERROR level for quiet mode
            set_verbosity(0)
        else:
            # Set verbosity based on -v flags
            # Verbosity mapping:
            # 0 = INFO (default)
            # 1 (-v) = DEBUG
            # 2+ (-vv, -vvv) = DEBUG
            # Logger expects: 0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG
            if verbosity == 0:
                set_verbosity(2)  # INFO level (default)
            else:
                set_verbosity(3)  # DEBUG level for any -v flag

        # Configure file logging if requested
        # Try both log_file and log-file (argparse converts - to _)
        log_file = getattr(args, "log_file", None) or getattr(args, "log-file", None)
        if log_file:
            from pathlib import Path

            configure_file_logging(Path(log_file))

    def _add_subcommand(
        self,
        subparsers: argparse._SubParsersAction,
        metadata: APIMethodMetadata,
    ) -> None:
        """
        Add a subcommand for a method.

        Args:
            subparsers: Argparse subparsers object
            metadata: Method metadata
        """
        # Create subparser with global parent to inherit global options
        sub = subparsers.add_parser(
            metadata.cli_name,
            help=metadata.description,
            description=metadata.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[self.global_parent],
        )

        # Add aliases if specified
        for alias in metadata.aliases:
            subparsers._name_parser_map[alias] = sub

        # Add method parameters as arguments (excluding **kwargs)
        for param_name, param in metadata.parameters.items():
            if param.kind != inspect.Parameter.VAR_KEYWORD:  # Skip **kwargs
                self._add_parameter_argument(sub, metadata, param_name, param)

        # Special handling for apply command: add common config parameters
        if metadata.cli_name == "apply":
            self._add_apply_config_parameters(sub)

        # Add examples to help if available
        if metadata.examples:
            examples_text = "\nExamples:\n" + "\n".join(
                f"  {example}" for example in metadata.examples
            )
            sub.epilog = examples_text

    def _add_parent_command(
        self,
        subparsers: argparse._SubParsersAction,
        parent_name: str,
        child_methods: List[APIMethodMetadata],
    ) -> None:
        """
        Add a parent command with nested subcommands.

        Args:
            subparsers: Argparse subparsers object
            parent_name: Name of the parent command (e.g., 'qmp')
            child_methods: List of child method metadata
        """
        # Create parent subparser with global parent to inherit global options
        parent_parser = subparsers.add_parser(
            parent_name,
            help=f"{parent_name.upper()} subcommands",
            description=f"{parent_name.upper()} subcommands",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[self.global_parent],
        )

        # Add nested subparsers for child commands
        child_subparsers = parent_parser.add_subparsers(
            dest="subcommand",
            help="Available subcommands",
            metavar="SUBCOMMAND",
        )

        # Add each child method as a nested subcommand
        for metadata in child_methods:
            self._add_subcommand(child_subparsers, metadata)

    def _add_parameter_argument(
        self,
        parser: argparse.ArgumentParser,
        metadata: APIMethodMetadata,
        param_name: str,
        param: inspect.Parameter,
    ) -> None:
        """
        Add an argument for a method parameter.

        Args:
            parser: Argument parser
            metadata: Method metadata for context
            param_name: Parameter name
            param: Parameter metadata
        """
        # Determine argument properties
        is_required = param.default == inspect.Parameter.empty
        arg_name = param_name.replace("_", "-")

        # Check for Union[str, List[str]] type for multiple files support
        is_multiple_files = self._is_multiple_files_param(param)

        # Special handling for vm_id parameters - make them positional for
        # better UX
        is_vm_id_param = param_name == "vm_id"

        # For rm command, vm_id should be optional positional since it has
        # --all alternative
        is_rm_command = metadata.cli_name == "rm"

        # Special handling for VAR_POSITIONAL parameters (*args)
        is_var_positional = param.kind == inspect.Parameter.VAR_POSITIONAL

        if param.annotation == bool:
            # Boolean flags
            if is_required:
                # Required boolean (rare case)
                parser.add_argument(
                    f"--{arg_name}",
                    action="store_true",
                    required=True,
                    help=f"{param_name} (required boolean flag)",
                )
            else:
                # Optional boolean flag
                default_value = (
                    param.default
                    if param.default != inspect.Parameter.empty
                    else False
                )
                parser.add_argument(
                    f"--{arg_name}",
                    action=(
                        "store_true" if not default_value else "store_false"
                    ),
                    default=default_value,
                    help=f"{param_name} (default: {default_value})",
                )
        elif is_multiple_files:
            # Multiple files parameter (Union[str, List[str]])
            if is_required:
                parser.add_argument(
                    param_name,
                    nargs="+",
                    help=f"{param_name} (one or more files)",
                )
            else:
                parser.add_argument(
                    f"--{arg_name}",
                    nargs="*",
                    default=param.default,
                    help=f"{param_name} (one or more files, default: {
                        param.default})",
                )
        elif is_vm_id_param:
            # Special handling for vm_id parameters - make them positional for
            # better UX
            if is_rm_command:
                # For rm command, vm_id is optional positional since --all is
                # alternative
                parser.add_argument(
                    param_name,
                    nargs="?",
                    default=param.default,
                    help=f"{
                        param_name} (VM name or ID, optional when using --all)",
                )
            elif is_required:
                # Regular required vm_id (for start, stop, status, etc.)
                parser.add_argument(
                    param_name, help=f"{param_name} (VM name or ID, required)"
                )
            else:
                # Optional vm_id but still positional
                parser.add_argument(
                    param_name,
                    nargs="?",
                    default=param.default,
                    help=f"{param_name} (VM name or ID, optional)",
                )
        elif is_var_positional:
            # VAR_POSITIONAL parameters (*args) - use nargs='*' for zero or
            # more
            parser.add_argument(
                param_name,
                nargs="*",
                help=f"{param_name} (zero or more values)",
            )
        elif is_required:
            # Required positional argument
            parser.add_argument(param_name, help=f"{param_name} (required)")
        else:
            # Optional argument with default
            parser.add_argument(
                f"--{arg_name}",
                default=param.default,
                help=f"{param_name} (default: {param.default})",
            )

    def _is_multiple_files_param(self, param: inspect.Parameter) -> bool:
        """
        Check if parameter accepts multiple files (Union[str, List[str]]).

        Args:
            param: Parameter to check

        Returns:
            True if parameter accepts multiple files
        """
        if param.annotation == inspect.Parameter.empty:
            return False

        # Check for Union[str, List[str]] or similar patterns
        origin = get_origin(param.annotation)
        if origin is Union:
            args = get_args(param.annotation)
            # Check for Union[str, List[str]] pattern
            has_str = str in args
            has_list_str = any(
                get_origin(arg) is list and get_args(arg) == (str,)
                for arg in args
            )
            return has_str and has_list_str

        return False

    def _execute_method(
        self, metadata: APIMethodMetadata, args: argparse.Namespace
    ) -> Any:
        """
        Execute a method with parsed arguments.

        Args:
            metadata: Method metadata
            args: Parsed command line arguments

        Returns:
            Method execution result
        """
        # Extract method parameters from parsed args
        method_kwargs = {}
        method_args = []

        # Check if method has VAR_POSITIONAL (*args) parameter
        has_var_positional = any(
            param.kind == inspect.Parameter.VAR_POSITIONAL
            for param in metadata.parameters.values()
        )

        # Collect positional parameters that come before VAR_POSITIONAL
        positional_params = []
        for param_name, param in metadata.parameters.items():
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                positional_params.append((param_name, param))
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                break  # Stop when we hit VAR_POSITIONAL

        for param_name, param in metadata.parameters.items():
            # Skip **kwargs parameters
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                continue

            # Convert parameter names (dashes to underscores)
            arg_name = param_name.replace("_", "-")

            # Get value from args
            if hasattr(args, param_name):
                value = getattr(args, param_name)
            elif hasattr(args, arg_name):
                value = getattr(args, arg_name.replace("-", "_"))
            else:
                continue

            if value is not None:
                # Handle VAR_POSITIONAL parameters (*args) specially
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    # For *args parameters, extend the args list
                    if isinstance(value, list):
                        method_args.extend(value)
                    else:
                        method_args.append(value)
                elif (
                    param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                    and has_var_positional
                ):
                    # When method has VAR_POSITIONAL, regular positional params
                    # must go in method_args to avoid "multiple values" error
                    method_args.insert(0, value)
                else:
                    # Everything else goes in kwargs
                    method_kwargs[param_name] = value

        # Special handling for apply command: collect config parameters as
        # kwargs
        if metadata.cli_name == "apply":
            config_params = {}
            for param_name in ["memory", "cpu", "binary", "enable_kvm"]:
                arg_name = param_name.replace("_", "-")
                if hasattr(args, arg_name.replace("-", "_")):
                    value = getattr(args, arg_name.replace("-", "_"))
                    if value is not None:
                        config_params[param_name] = value

            # Add config parameters to method kwargs
            method_kwargs.update(config_params)

        # Resolve config file paths to absolute paths for consistent handling
        if "config" in method_kwargs and method_kwargs["config"] is not None:

            config = method_kwargs["config"]
            if isinstance(config, str):
                # Single config file - resolve to absolute path
                method_kwargs["config"] = os.path.abspath(config)
            elif isinstance(config, list):
                # Multiple config files - resolve each to absolute path
                method_kwargs["config"] = [os.path.abspath(c) for c in config]

        # Execute method directly
        method = getattr(self.maqet_instance, metadata.name)

        # Execute method with both positional and keyword arguments
        return method(*method_args, **method_kwargs)

    def _add_apply_config_parameters(
        self, parser: argparse.ArgumentParser
    ) -> None:
        """
        Add common configuration parameters for the apply command.

        Args:
            parser: Argument parser for the apply subcommand
        """
        # Memory configuration
        parser.add_argument(
            "--memory", type=str, help="VM memory size (e.g., 2G, 4096M)"
        )

        # CPU configuration
        parser.add_argument("--cpu", type=int, help="Number of CPU cores")

        # Binary path
        parser.add_argument("--binary", type=str, help="Path to QEMU binary")

        # KVM enablement
        parser.add_argument(
            "--enable-kvm", action="store_true", help="Enable KVM acceleration"
        )
