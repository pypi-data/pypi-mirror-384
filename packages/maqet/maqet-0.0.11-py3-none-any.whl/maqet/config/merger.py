"""
Configuration Merger

Handles deep-merging of multiple configuration files.
Provides utilities for loading and merging YAML configuration files
with deep merge support for complex nested structures.
"""

from pathlib import Path
from typing import Any, Dict, List, Union

import yaml


class ConfigError(Exception):
    """Configuration parsing errors"""


class ConfigMerger:
    """
    Handles deep-merging of multiple configuration files.

    Provides utilities for loading and merging YAML configuration files
    with deep merge support for complex nested structures.
    """

    @staticmethod
    def _merge_arguments_list(
        base_args: List[Any], override_args: List[Any]
    ) -> List[Any]:
        """
        Merge two arguments lists with override behavior.

        For arguments like [{foo: 0}, {bar: 10}] and [{bar: 20}, {baz: 30}],
        later configs override earlier ones by key, producing:
        [{foo: 0}, {bar: 20}, {baz: 30}]

        Args:
            base_args: Base arguments list
            override_args: Override arguments list

        Returns:
            Merged arguments list with overrides applied
        """
        # Track arguments by their keys (for dict items)
        # Use dict to maintain insertion order (Python 3.7+)
        merged = {}

        # Process base arguments first
        for arg in base_args:
            if isinstance(arg, dict):
                # For dict items, use the key as identifier
                for key in arg.keys():
                    merged[key] = arg
            else:
                # For non-dict items (strings), use the item itself as key
                merged[str(arg)] = arg

        # Process override arguments (later configs win)
        for arg in override_args:
            if isinstance(arg, dict):
                # Override or add dict items by key
                for key in arg.keys():
                    merged[key] = arg
            else:
                # Override or add non-dict items
                merged[str(arg)] = arg

        # Convert back to list, preserving order
        return list(merged.values())

    @staticmethod
    def deep_merge(
        base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Deep-merged configuration dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                result[key] = ConfigMerger.deep_merge(result[key], value)
            elif (
                key in result
                and isinstance(result[key], list)
                and isinstance(value, list)
            ):
                # Special handling for 'arguments' list: merge dict items by key
                if key == "arguments":
                    result[key] = ConfigMerger._merge_arguments_list(
                        result[key], value
                    )
                else:
                    # For other lists (storage, etc.), concatenate
                    # This allows adding storage devices, network interfaces, etc.
                    result[key] = result[key] + value
            else:
                # Override scalar values and non-dict types
                result[key] = value

        return result

    @staticmethod
    def _resolve_relative_paths(
        config_data: Dict[str, Any], config_dir: Path
    ) -> Dict[str, Any]:
        """
        Resolve relative file paths in config to absolute paths.

        Layer 3 of automatic path resolution: resolve paths relative to config file location.
        This makes configs portable and allows relative paths like ./live.iso to work.

        Args:
            config_data: Configuration dictionary
            config_dir: Directory containing the config file

        Returns:
            Configuration with resolved absolute paths
        """
        # Resolve storage device file paths
        if "storage" in config_data and isinstance(
            config_data["storage"], list
        ):
            for storage_item in config_data["storage"]:
                if isinstance(storage_item, dict) and "file" in storage_item:
                    file_path = storage_item["file"]
                    if not Path(file_path).is_absolute():
                        # Resolve relative to config file directory
                        storage_item["file"] = str(
                            (config_dir / file_path).resolve()
                        )

                # Resolve VirtFS path entries
                if isinstance(storage_item, dict) and "path" in storage_item:
                    path_value = storage_item["path"]
                    if not Path(path_value).is_absolute():
                        storage_item["path"] = str(
                            (config_dir / path_value).resolve()
                        )

        # Resolve file paths in arguments (drive file=./path,...)
        if "arguments" in config_data and isinstance(
            config_data["arguments"], list
        ):
            for arg_item in config_data["arguments"]:
                if isinstance(arg_item, dict):
                    for key, value in arg_item.items():
                        if isinstance(value, str) and "file=" in value:
                            # Parse drive argument: file=./live.iso,media=cdrom
                            parts = value.split(",")
                            for i, part in enumerate(parts):
                                if part.startswith("file="):
                                    file_path = part[
                                        5:
                                    ]  # Remove 'file=' prefix
                                    if not Path(file_path).is_absolute():
                                        abs_path = str(
                                            (config_dir / file_path).resolve()
                                        )
                                        parts[i] = f"file={abs_path}"
                            arg_item[key] = ",".join(parts)

        return config_data

    @staticmethod
    def load_and_merge_files(
        config_files: Union[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Load and merge multiple configuration files.

        Args:
            config_files: Single config file path or list of config file paths

        Returns:
            Merged configuration data

        Raises:
            ConfigError: If any config file cannot be loaded or parsed
        """
        if isinstance(config_files, str):
            config_files = [config_files]

        if not config_files:
            return {}

        merged_config = {}

        for config_file in config_files:
            config_path = Path(config_file)
            if not config_path.exists():
                raise ConfigError(
                    f"Configuration file not found: {config_file}"
                )

            try:
                with open(config_path) as f:
                    config_data = yaml.safe_load(f) or {}

                if not isinstance(config_data, dict):
                    raise ConfigError(
                        f"Configuration in {config_file} must be a "
                        f"YAML dictionary"
                    )

                # Layer 3: Resolve relative paths in config relative to config file location
                config_dir = config_path.parent.resolve()
                config_data = ConfigMerger._resolve_relative_paths(
                    config_data, config_dir
                )

                # Deep merge with previous configs
                merged_config = ConfigMerger.deep_merge(
                    merged_config, config_data
                )

            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML in {config_file}: {e}")
            except Exception as e:
                raise ConfigError(
                    f"Error loading configuration from {config_file}: {e}"
                )

        return merged_config
