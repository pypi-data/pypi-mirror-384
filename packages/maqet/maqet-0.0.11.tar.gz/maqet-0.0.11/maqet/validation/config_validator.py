"""
Runtime Configuration Validator for MAQET.

Performs runtime validation and health checks before starting QEMU instances.
Delegates schema validation to config.validators module to avoid duplication.

This validator focuses on runtime concerns:
- Binary health checks (QEMU binary actually works)
- Tool availability (qemu-img installed)
- System resource validation

For schema/structure validation, see maqet.config.validators module.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict

from ..constants import Timeouts
from ..logger import LOG


class ConfigValidationError(Exception):
    """Configuration validation errors."""


class ConfigValidator:
    """
    Runtime validator for VM configuration.

    This validator performs runtime health checks before starting VMs.
    It delegates schema validation to the config.validators module to
    avoid code duplication.

    Separation of Concerns:
    - config.validators: Schema validation + value normalization
    - validation.ConfigValidator: Runtime health checks + pre-start validation

    Use config.validators for:
    - Validating config structure and types
    - Normalizing values (e.g., bytes to "4G")
    - Cross-field validation

    Use validation.ConfigValidator for:
    - Binary health checks (qemu-system-x86_64 --version works)
    - Tool availability checks (qemu-img installed)
    - Pre-start validation orchestration

    Extracted from Machine class to follow single-responsibility principle.
    """

    def validate_config(self, config_data: Dict[str, Any]) -> None:
        """
        Validate VM configuration data using schema validator.

        Delegates to config.validators.validate_config_data() for schema
        validation, then performs any additional runtime checks if needed.

        Args:
            config_data: VM configuration dictionary

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        # Import schema validator to avoid circular dependency
        from ..config.validators import (
            ConfigValidationError as SchemaValidationError,
        )
        from ..config.validators import validate_config_data

        try:
            # Delegate to schema validator for structure/format validation
            validate_config_data(config_data)
        except SchemaValidationError as e:
            # Re-raise as our own exception type for consistency
            raise ConfigValidationError(str(e))

    def validate_binary_health(self, binary: str) -> None:
        """
        Perform health check on QEMU binary.

        Verifies binary works by running --version command.

        Args:
            binary: Path to QEMU binary

        Raises:
            ConfigValidationError: If binary health check fails
        """
        binary_path = Path(binary)

        if not binary_path.exists():
            raise ConfigValidationError(f"QEMU binary not found: {binary}")

        # Health check: Verify binary works by running --version
        try:
            result = subprocess.run(
                [str(binary_path), '--version'],
                capture_output=True,
                text=True,
                timeout=Timeouts.BINARY_VERSION_CHECK,
            )
            if result.returncode != 0:
                raise ConfigValidationError(
                    f"QEMU binary failed health check: {binary}\n"
                    f"Error: {result.stderr.strip()}"
                )
            LOG.debug(f"QEMU binary health check passed: {binary}")

        except FileNotFoundError:
            raise ConfigValidationError(
                f"QEMU binary not executable: {binary}\n"
                f"Check file permissions and ensure it's a valid binary."
            )
        except subprocess.TimeoutExpired:
            raise ConfigValidationError(
                f"QEMU binary health check timed out: {binary}\n"
                f"Binary may be hung or unresponsive."
            )
        except Exception as e:
            raise ConfigValidationError(
                f"QEMU binary validation failed: {binary}\n"
                f"Error: {e}"
            )

    def validate_qemu_img_available(self) -> None:
        """
        Verify qemu-img tool is available for storage operations.

        Logs warning if qemu-img is not found (storage auto-creation may fail).
        """
        try:
            subprocess.run(
                ["qemu-img", "--version"],
                capture_output=True,
                check=True,
                timeout=Timeouts.BINARY_VERSION_CHECK,
            )
            LOG.debug("qemu-img utility found and working")
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            LOG.warning(
                "qemu-img not found - storage auto-creation may fail. "
                "Install QEMU tools (qemu-utils or qemu-img package)."
            )

    def pre_start_validation(self, config_data: Dict[str, Any]) -> None:
        """
        Perform all pre-start validation checks.

        Combines binary health check and qemu-img availability check.
        Called immediately before starting VM.

        Args:
            config_data: VM configuration dictionary

        Raises:
            ConfigValidationError: If any validation check fails
        """
        # Get binary path (use default if not specified)
        binary = config_data.get("binary", "/usr/bin/qemu-system-x86_64")

        # Perform binary health check
        self.validate_binary_health(binary)

        # Check qemu-img availability (warning only)
        self.validate_qemu_img_available()
