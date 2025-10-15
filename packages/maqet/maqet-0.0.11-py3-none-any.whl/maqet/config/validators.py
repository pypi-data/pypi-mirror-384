"""
Schema Configuration Validators.

This module implements a decorator-based schema validation system for YAML configs.
Functions decorated with @config_validator automatically validate and normalize
configuration values during the parsing phase.

Key Features:
- Type coercion and value normalization (e.g., bytes to "4G")
- Cross-field validation (e.g., display/VGA compatibility)
- Extensible via @config_validator decorator
- Forward-compatible (unknown keys preserved)

Separation of Concerns:
- config.validators: Schema validation + value normalization (THIS MODULE)
- validation.ConfigValidator: Runtime health checks + pre-start validation

Use this module for:
- Validating config structure and types
- Normalizing values (e.g., converting bytes to "4G", splitting comma-separated tags)
- Cross-field validation (e.g., display/VGA compatibility)

For runtime health checks, see maqet.validation.ConfigValidator module.

Example:
    @config_validator('memory')
    def validate_memory(value: Any) -> str:
        # Validation logic here
        return normalized_value

    @config_validator('cpu', required=True)
    def validate_cpu_count(value: Any) -> int:
        # Validation logic here
        return normalized_value
"""

import os
import re
import warnings
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

# Global registry for config validators
_VALIDATOR_REGISTRY: Dict[str, "ConfigValidator"] = {}

T = TypeVar("T")


class ConfigValidationError(Exception):
    """Configuration validation error."""


class ConfigValidator:
    """Metadata for a configuration validator."""

    def __init__(
        self,
        key: str,
        func: Callable[[Any], Any],
        required: bool = False,
        description: Optional[str] = None,
    ):
        """Initialize a configuration validator.

        Args:
            key: Configuration key this validator handles
            func: Validation function to apply
            required: Whether this key is required in config
            description: Description of the validator
        """
        self.key = key
        self.func = func
        self.required = required
        self.description = description or func.__doc__

    def validate(self, value: Any) -> Any:
        """Run validation on a value."""
        try:
            return self.func(value)
        except Exception as e:
            raise ConfigValidationError(
                f"Validation failed for '{self.key}': {e}"
            )


def config_validator(
    key: str, required: bool = False, description: Optional[str] = None
) -> Callable[[Callable[[Any], T]], Callable[[Any], T]]:
    """
    Register a config validation function.

    Args:
        key: Configuration key this validator handles
        required: Whether this key is required in config
        description: Description of the validator

    Returns:
        Decorated function
    """

    def decorator(func: Callable[[Any], T]) -> Callable[[Any], T]:
        validator = ConfigValidator(key, func, required, description)
        _VALIDATOR_REGISTRY[key] = validator

        @wraps(func)
        def wrapper(value: Any) -> T:
            return validator.validate(value)

        return wrapper

    return decorator


def get_validators() -> Dict[str, ConfigValidator]:
    """Get all registered validators."""
    return _VALIDATOR_REGISTRY.copy()


def get_required_keys() -> Set[str]:
    """Get all required configuration keys."""
    return {
        key
        for key, validator in _VALIDATOR_REGISTRY.items()
        if validator.required
    }


def validate_config_data(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration data using registered validators.

    Args:
        config_data: Configuration dictionary

    Returns:
        Validated and normalized configuration

    Raises:
        ConfigValidationError: If validation fails
    """
    if not isinstance(config_data, dict):
        raise ConfigValidationError("Configuration must be a dictionary")

    validated_config = {}
    required_keys = get_required_keys()

    # Check for missing required keys
    missing_required = required_keys - set(config_data.keys())
    if missing_required:
        raise ConfigValidationError(
            f"Missing required configuration keys: {', '.join(missing_required)}"
        )

    # Check for API commands in config (configs should not contain API commands)
    # Use hardcoded list of known API commands for reliability in tests
    KNOWN_API_COMMANDS = {
        "add", "start", "stop", "rm", "ls", "status", "info", "inspect",
        "qmp", "snapshot", "config", "apply", "dump", "history", "import"
    }

    # Also try to get commands from registry if available
    try:
        from ..api.registry import API_REGISTRY
        registry_commands = set(API_REGISTRY.get_all_cli_commands().keys())
        # Combine hardcoded list with registry (handles both test and production cases)
        api_commands = KNOWN_API_COMMANDS | registry_commands
    except Exception:
        # If registry access fails, use hardcoded list only
        api_commands = KNOWN_API_COMMANDS

    config_keys = set(config_data.keys())
    api_commands_in_config = config_keys & api_commands
    if api_commands_in_config:
        raise ConfigValidationError(
            f"Configuration cannot contain API commands: {', '.join(sorted(api_commands_in_config))}. "
            f"Use CLI or Python API to execute commands."
        )

    # Validate each key that has a validator
    for key, value in config_data.items():
        if key in _VALIDATOR_REGISTRY:
            # Key has a validator, run validation
            validator = _VALIDATOR_REGISTRY[key]
            try:
                validated_config[key] = validator.validate(value)
            except ConfigValidationError:
                raise
            except Exception as e:
                raise ConfigValidationError(
                    f"Validation failed for '{key}': {e}"
                )
        else:
            # No validator for this key, include as-is
            # This allows forward compatibility with new config keys
            validated_config[key] = value

    # Run cross-field validation checks
    validate_display_vga_compatibility(validated_config)

    return validated_config


# Built-in validators for common configuration keys


@config_validator("binary", required=False)
def validate_binary(value: Any) -> str:
    """
    Validate QEMU binary path exists and is executable.

    Note: Binary is not strictly required because machine.py provides a default
    (/usr/bin/qemu-system-x86_64). However, if specified, it must be valid.
    """
    from pathlib import Path

    if not isinstance(value, str):
        raise ValueError("Binary path must be a string")
    if not value.strip():
        raise ValueError("Binary path cannot be empty")

    binary_path = Path(value.strip())

    # Check if file exists
    if not binary_path.exists():
        raise ValueError(
            f"QEMU binary not found: {value}. "
            f"Install QEMU or provide correct binary path."
        )

    # Check if it's a file (not a directory)
    if not binary_path.is_file():
        raise ValueError(f"QEMU binary path is not a file: {value}")

    # Check if executable
    if not os.access(binary_path, os.X_OK):
        raise ValueError(
            f"QEMU binary is not executable: {value}. "
            f"Run: chmod +x {value}"
        )

    return value.strip()


@config_validator("memory")
def validate_memory(value: Any) -> str:
    """Validate memory specification (e.g., '4G', '2048M')."""
    if isinstance(value, int):
        # Convert bytes to megabytes
        return f"{value // (1024 * 1024)}M"

    if not isinstance(value, str):
        raise ValueError("Memory must be a string or integer")

    memory = value.strip()

    # Check for valid memory format
    if re.match(r"^\d+[MGT]$", memory):
        return memory
    elif memory.isdigit():
        # Assume bytes, convert to megabytes
        return f"{int(memory) // (1024 * 1024)}M"
    else:
        raise ValueError(
            "Memory must be in format like '4G', '2048M', or bytes as integer"
        )


@config_validator("cpu")
def validate_cpu(value: Any) -> int:
    """Validate CPU count and warn if exceeds system CPUs."""
    try:
        cpu_count = int(value)
        if cpu_count < 1:
            raise ValueError("CPU count must be at least 1")
        if cpu_count > 64:
            raise ValueError("CPU count cannot exceed 64")

        # Warn if CPU count exceeds available system CPUs
        try:
            system_cpus = os.cpu_count() or 1
            if cpu_count > system_cpus:
                warnings.warn(
                    f"VM configured with {cpu_count} CPUs but system only has "
                    f"{system_cpus} CPUs. This may impact performance. "
                    f"Consider reducing CPU count to {system_cpus} or less.",
                    UserWarning
                )
        except Exception:
            # Can't determine system CPU count - skip warning
            pass

        return cpu_count
    except (ValueError, TypeError):
        raise ValueError("CPU count must be a positive integer")


@config_validator("display")
def validate_display(value: Any) -> str:
    """Validate display setting."""
    if not isinstance(value, str):
        raise ValueError("Display must be a string")

    valid_displays = {"none", "gtk", "sdl", "vnc", "curses", "spice", "cocoa"}

    # Also accept format like "gtk,gl=on" or "vnc=:1"
    display_type = value.split(",")[0].split("=")[0]

    if display_type not in valid_displays:
        warnings.warn(
            f"Display type '{display_type}' may not be supported by QEMU. "
            f"Common types: {', '.join(sorted(valid_displays))}",
            UserWarning
        )

    return value


@config_validator("storage")
def validate_storage(value: Any) -> List[Dict[str, Any]]:
    """Validate storage devices configuration."""
    if not isinstance(value, list):
        raise ValueError("Storage must be a list of device configurations")

    validated_storage = []
    seen_names = set()

    for i, device in enumerate(value):
        if not isinstance(device, dict):
            raise ValueError(f"Storage device {i} must be a dictionary")

        # Auto-generate name if not provided (for backward compatibility)
        validated_device = device.copy()
        if "name" not in validated_device:
            # Generate name from index: hdd0, hdd1, hdd2, etc.
            validated_device["name"] = f"hdd{i}"

        device_name = validated_device["name"]
        if device_name in seen_names:
            raise ValueError(f"Duplicate storage device name: {device_name}")
        seen_names.add(device_name)

        # Validate device type
        device_type = validated_device.get("type", "qcow2")
        valid_types = {"qcow2", "raw", "vmdk", "vdi", "vhd", "virtfs"}
        if device_type not in valid_types:
            raise ValueError(
                f"Storage device {i} type must be one of {valid_types}"
            )

        validated_device["type"] = device_type
        validated_storage.append(validated_device)

    return validated_storage


@config_validator("network")
def validate_network(value: Any) -> List[Dict[str, Any]]:
    """Validate network configuration."""
    if not isinstance(value, list):
        raise ValueError("Network must be a list of network configurations")

    # Basic validation - can be expanded
    return value


@config_validator("arguments")
def validate_arguments(value: Any) -> List[Dict[str, Any]]:
    """Validate structured QEMU arguments."""
    if not isinstance(value, list):
        raise ValueError("Arguments must be a list of argument dictionaries")

    return value


@config_validator("plain_arguments")
def validate_plain_arguments(value: Any) -> List[str]:
    """Validate plain QEMU arguments."""
    if isinstance(value, str):
        # Split string into list
        return value.split()
    elif isinstance(value, list):
        # Validate all items are strings
        for i, arg in enumerate(value):
            if not isinstance(arg, str):
                raise ValueError(f"Plain argument {i} must be a string")
        return value
    else:
        raise ValueError("Plain arguments must be a string or list of strings")


@config_validator("parameters")
def validate_parameters(value: Any) -> Dict[str, Any]:
    """Validate user-defined parameters."""
    if not isinstance(value, dict):
        raise ValueError("Parameters must be a dictionary")

    return value


@config_validator("description")
def validate_description(value: Any) -> str:
    """Validate VM description."""
    if not isinstance(value, str):
        raise ValueError("Description must be a string")

    return value.strip()


@config_validator("tags")
def validate_tags(value: Any) -> List[str]:
    """Validate VM tags."""
    if isinstance(value, str):
        # Split comma-separated tags
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    elif isinstance(value, list):
        # Validate all items are strings
        tags = []
        for tag in value:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
            tags.append(tag.strip())
        return tags
    else:
        raise ValueError("Tags must be a string or list of strings")


@config_validator("vga")
def validate_vga(value: Any) -> str:
    """Validate VGA device type."""
    if not isinstance(value, str):
        raise ValueError("VGA device type must be a string")

    valid_vga = {
        "std",
        "cirrus",
        "vmware",
        "qxl",
        "virtio",
        "virtio-gpu-pci",
        "none",
    }

    if value not in valid_vga:
        warnings.warn(
            f"VGA device type '{value}' may not be supported by QEMU. "
            f"Common types: {', '.join(sorted(valid_vga))}",
            UserWarning
        )

    return value


@config_validator("network")
def validate_network_config(value: Any) -> Dict[str, Any]:
    """Validate network configuration."""
    if isinstance(value, dict):
        # Check network mode
        mode = value.get("mode", "user")
        valid_modes = {"user", "tap", "bridge", "none"}
        if mode not in valid_modes:
            warnings.warn(
                f"Network mode '{mode}' may not be supported. "
                f"Common modes: {', '.join(sorted(valid_modes))}",
                UserWarning
            )

        # Validate MAC address format if provided
        if "mac" in value:
            mac = value["mac"]
            if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac):
                raise ValueError(
                    f"Invalid MAC address format: '{mac}'. "
                    f"Use format like '52:54:00:12:34:56'"
                )

        # Warn about tap mode requiring privileges
        if mode == "tap":
            warnings.warn(
                "Network mode 'tap' typically requires root privileges or "
                "proper permissions on /dev/net/tun. Ensure you have the necessary access.",
                UserWarning
            )

        return value
    elif isinstance(value, list):
        # List of network configurations - validate each
        validated = []
        for net_config in value:
            validated.append(validate_network_config(net_config))
        return validated
    else:
        raise ValueError("Network must be a dictionary or list of dictionaries")


def validate_display_vga_compatibility(config_data: Dict[str, Any]) -> None:
    """
    Validate display/VGA compatibility.

    Warns about potentially inefficient configurations like headless display
    with graphical VGA device.

    Args:
        config_data: Full configuration dictionary

    Note: This is called by validate_config_data() after individual validators.
    """
    display = config_data.get("display", "")
    vga = config_data.get("vga", "")

    if (
        display == "none"
        and vga
        and vga not in {"none", "virtio", "virtio-gpu-pci"}
    ):
        warnings.warn(
            f"Display is 'none' but VGA is '{vga}'. Consider using vga=none "
            f"for headless VMs to reduce resource usage.",
            UserWarning
        )
