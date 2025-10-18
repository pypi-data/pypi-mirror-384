"""Type stubs for cheap_settings."""

from typing import Any, Optional, Type, TypeVar

_T = TypeVar("_T", bound="CheapSettings")

class CheapSettings:
    """Base class for settings with environment variable support.

    Subclass this and define your settings as typed class attributes.
    Environment variables override defaults, with automatic type conversion.
    """

    @classmethod
    def set_config_from_command_line(
        cls: Type[_T],
        arg_parser: Optional[Any] = None,
        args: Optional[list[str]] = None,
    ) -> Any:
        """Parse command line arguments and set configuration values.

        Args:
            arg_parser: Optional ArgumentParser instance
            args: Optional list of arguments (defaults to sys.argv)

        Returns:
            Namespace object from argparse
        """
        ...

    @classmethod
    def to_static(cls: Type[_T]) -> Type[Any]:
        """Create a static snapshot of current settings.

        Returns a regular Python class with all settings resolved to current values.
        The returned class has no dynamic behavior.
        """
        ...

    def __getattribute__(self, name: str) -> Any: ...
    def __reduce__(self) -> tuple[Any, ...]: ...
    def __getstate__(self) -> dict[str, Any]: ...
    def __setstate__(self, state: dict[str, Any]) -> None: ...

__all__ = ["CheapSettings"]
