"""
API Method Decorator.

The @api_method decorator is the core of MAQET's unified API generation system.
It captures method metadata to enable automatic CLI and Python API generation.
"""

import inspect
from functools import wraps
from typing import Callable, List, Optional

from .metadata import APIMethodMetadata
from .registry import API_REGISTRY


def api_method(
    cli_name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general",
    requires_vm: bool = False,
    examples: Optional[List[str]] = None,
    aliases: Optional[List[str]] = None,
    hidden: bool = False,
    parent: Optional[str] = None,
) -> Callable:
    """
    Decorate MAQET API methods to enable unified CLI and Python API generation.

    This decorator captures method metadata that is used by generators to automatically
    create CLI commands and Python API methods from the same source.

    Args:
        cli_name: CLI command name (defaults to method name with underscores as dashes)
        description: Human-readable description (defaults to docstring summary)
        category: Method category for grouping ('vm', 'qmp', 'storage', 'system')
        requires_vm: Whether this method requires a VM to be specified
        examples: List of usage examples
        aliases: Alternative CLI command names
        hidden: Whether to hide from CLI help (for internal methods)
        parent: Parent command name for nested subcommands (e.g., 'qmp')

    Returns:
        Decorated function with metadata attached

    Example:
        @api_method(
            cli_name="start",
            description="Start a virtual machine",
            category="vm",
            requires_vm=True,
            examples=["maqet start myvm", "maqet start myvm --detach"]
        )
        def start(self, vm_id: str, detach: bool = False):
            '''Start a virtual machine.'''
            # Implementation here
    """

    def decorator(func: Callable) -> Callable:
        # Extract description from docstring if not provided
        if description is None:
            doc_description = _extract_description_from_docstring(func.__doc__)
        else:
            doc_description = description

        # Get method signature
        signature = inspect.signature(func)

        # Create metadata
        metadata = APIMethodMetadata(
            name=func.__name__,
            function=func,
            owner_class="",  # Will be set when method is bound to a class
            cli_name=cli_name,
            description=doc_description,
            signature=signature,
            category=category,
            requires_vm=requires_vm,
            examples=examples or [],
            aliases=aliases or [],
            hidden=hidden,
            parent=parent,
        )

        # Store metadata on the function for later registration
        func._api_metadata = metadata

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Copy metadata to wrapper
        wrapper._api_metadata = metadata

        return wrapper

    return decorator


def _extract_description_from_docstring(docstring: Optional[str]) -> str:
    """
    Extract first line of docstring as description.

    Args:
        docstring: Function docstring

    Returns:
        First non-empty line of docstring or default message
    """
    if not docstring:
        return "No description available"

    lines = [line.strip() for line in docstring.strip().split("\n")]
    first_line = next((line for line in lines if line), "")

    return first_line or "No description available"


class AutoRegisterAPI:
    """
    Base class that automatically registers @api_method decorated methods.

    Any class that inherits from this will automatically have its @api_method
    decorated methods registered with the global API registry when the class
    is defined. This eliminates the need for manual register_class_methods() calls.

    Example:
        class Maqet(AutoRegisterAPI):
            @api_method(category="vm")
            def start(self, vm_id: str):
                pass

        # Methods are automatically registered - no manual call needed!
    """

    def __init_subclass__(cls, **kwargs):
        """
        Automatically register decorated methods when a subclass is created.

        This method is called whenever a class inherits from AutoRegisterAPI,
        enabling automatic registration without manual function calls.
        """
        super().__init_subclass__(**kwargs)

        # Register all @api_method decorated methods from this class
        for name, method in inspect.getmembers(
            cls, predicate=inspect.isfunction
        ):
            if hasattr(method, "_api_metadata"):
                metadata: APIMethodMetadata = method._api_metadata
                # Set the owner class now that we know it
                metadata.owner_class = cls.__name__
                # Register with global registry
                API_REGISTRY.register(metadata)


def register_class_methods(cls: type) -> None:
    """
    Register all @api_method decorated methods from a class.

    This function should be called after class definition to register
    all decorated methods with the global API registry.

    NOTE: This function is kept for backward compatibility, but new code
    should inherit from AutoRegisterAPI instead for automatic registration.

    Args:
        cls: Class containing decorated methods

    Example:
        class Maqet:
            @api_method(category="vm")
            def start(self, vm_id: str):
                pass

        register_class_methods(Maqet)

    """
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if hasattr(method, "_api_metadata"):
            metadata: APIMethodMetadata = method._api_metadata
            # Set the owner class now that we know it
            metadata.owner_class = cls.__name__
            # Register with global registry
            API_REGISTRY.register(metadata)
