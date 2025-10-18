import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Union, get_args, get_origin

from .command_line import _bool_str_to_bool, parse_command_line_arguments

# Python 3.10+ has types.UnionType for the | syntax
if sys.version_info >= (3, 10):
    from types import UnionType
else:
    UnionType = None  # noqa


def _reconstruct_settings_instance(module_name, class_name):
    """Helper function to reconstruct a CheapSettings instance when unpickling."""
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls()


def _reconstruct_settings_class(module_name, class_name, _config_data, _annotations):
    """Helper function to reconstruct a CheapSettings class when unpickling."""
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _parse_json(value: str, expected_type: type, setting_name: str):
    """Parse a JSON string, raising a helpful error on failure."""
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError as e:
        # Provide specific guidance based on the error and value
        error_str = str(e)
        if "Expecting property name" in error_str or (
            "Expecting value" in error_str and "'" in value
        ):
            # Likely single quotes or unquoted strings
            example = (
                '{"key": "value"}' if expected_type is dict else '["item1", "item2"]'
            )
            hint = f"Use double quotes for strings in JSON. Example: {example}"
        elif "Expecting value" in error_str and not value.strip():
            hint = "Empty values are not valid JSON. Use '[]' for empty list or '{}' for empty dict"
        elif "Extra data" in error_str:
            hint = "Multiple JSON values found. Wrap them in an array: [value1, value2]"
        else:
            # Show what they provided vs what's expected
            example = (
                '["item1", "item2"]' if expected_type is list else '{"key": "value"}'
            )
            hint = f"Expected format: {example}"

        raise ValueError(
            f"Invalid JSON in {setting_name.upper()} environment variable.\n"
            f"  Your value: {value!r}\n"
            f"  JSON error: {e}\n"
            f"  Hint: {hint}"
        ) from e

    if not isinstance(parsed_value, expected_type):
        # Provide specific examples for type mismatches
        if expected_type is list and isinstance(parsed_value, dict):
            hint = f"To use a dict, change the type annotation to 'dict'. For a list, use: {json.dumps([parsed_value])}"
        elif expected_type is dict and isinstance(parsed_value, list):
            hint = f"To use a list, change the type annotation to 'list'. For a dict, try: {json.dumps(dict(enumerate(parsed_value)))}"
        else:
            type_examples: Dict[type, Any] = {
                list: '["value1", "value2"]',
                dict: '{"key": "value"}',
            }
            hint = (
                f"Use {type_examples.get(expected_type, expected_type.__name__)} format"
            )

        raise ValueError(
            f"JSON type mismatch in {setting_name.upper()} environment variable.\n"
            f"  Expected: {expected_type.__name__}\n"
            f"  Got: {type(parsed_value).__name__}\n"
            f"  Your value: {json.dumps(parsed_value)}\n"
            f"  Hint: {hint}"
        )
    return parsed_value


def _convert_value_to_type(value: Any, to_type: type, name: str) -> Any:
    """Convert a string value from environment to the specified type.

    Handles basic types (int, float, bool, str, list, dict) as well as
    Union/Optional types. For Optional types, the string "none" (case-insensitive)
    is converted to None. Lists and dicts are parsed from JSON strings.

    Args:
        value: The value to convert (usually a string from os.environ)
        to_type: The type annotation to convert to
        name: The name of the setting (for error messages)

    Returns:
        Any: The converted value in the appropriate type

    Raises:
        ValueError: If the value cannot be converted to the specified type
    """
    if value is None:
        return None

    # Handle the case where value is already the correct type
    if not isinstance(value, str):
        return value

    # Handle Union/Optional types (including Python 3.10+ union syntax)
    origin = get_origin(to_type)
    if origin is Union or (UnionType and isinstance(to_type, UnionType)):
        args = get_args(to_type)

        # Special handling for "none" string in Optional types
        if type(None) in args and value.lower() == "none":
            return None

        # Try each type in the union until one works
        for arg in args:
            if arg is type(None):  # Skip None type
                continue
            try:
                return _convert_value_to_type(value, arg, name)
            except (ValueError, TypeError):
                # When JSON parsing fails in a Union, we silently try the next type
                continue
        # If none worked, raise error
        raise ValueError(f"Could not convert '{value}' to any of {args}")

    # Handle generic types like list[str], dict[str, int]
    if origin is not None:
        if origin is list:
            return _parse_json(value, list, name)
        elif origin is dict:
            return _parse_json(value, dict, name)

    # Handle basic types
    # Check bool before int since bool is a subclass of int
    if to_type is bool:
        return _bool_str_to_bool(value)
    elif to_type is int:
        return int(value)
    elif to_type is float:
        return float(value)
    elif to_type is str:
        return value
    elif to_type is list:
        return _parse_json(value, list, name)
    elif to_type is dict:
        return _parse_json(value, dict, name)
    elif to_type is Path:
        return Path(value)

    # If we get here, we don't know how to handle this type
    return value


class _UninitializedSetting:
    def __repr__(self):
        return "UninitializedSetting"


_UNINITIALIZED = _UninitializedSetting()


# TODO: Implement __delattr__
# TODO: ¿¿¿¿¿¿¿ POSSIBLY: Refactor the metaclass to use __init_subclass__ and descriptors for maintainability. ???????
class MetaCheapSettings(type):
    """Metaclass that implements the settings behavior for CheapSettings.

    This metaclass intercepts attribute access to check environment variables
    and performs automatic type conversion based on type hints. Each settings
    class gets its own ConfigInstance to store the default values and annotations.
    """

    class ConfigInstance:
        """Internal storage for settings values and type annotations."""

    # TODO: See https://docs.python.org/3/howto/annotations.html#annotations-howto
    def __new__(mcs, name, bases, dct):
        """Create a new settings class with its own config instance.

        Moves class attributes (settings definitions) from the class dict
        to a ConfigInstance, preserving inheritance of settings from parent classes.
        Type annotations are collected from the class and its parents.
        """
        # Preserve the original module for pickle compatibility
        original_module = dct.get("__module__")

        config_instance = mcs.ConfigInstance()

        # Collect annotations from parent classes
        annotations = {}
        for base in reversed(bases):  # Start from the most base class
            try:
                # Use object.__getattribute__ to avoid calling our custom __getattribute__
                parent_config = object.__getattribute__(base, "__config_instance")
                if hasattr(parent_config, "__annotations__"):
                    annotations.update(parent_config.__annotations__)
                # Also copy parent attributes (skip internal ones)
                for attr in dir(parent_config):
                    if (
                        not attr.startswith("__")
                        and hasattr(parent_config, attr)
                        and not callable(getattr(parent_config, attr))
                    ):
                        setattr(config_instance, attr, getattr(parent_config, attr))
            except AttributeError:
                # Base class doesn't have __config_instance, skip it
                continue

        # Add current class annotations (override parent ones)
        current_annotations = dct.pop("__annotations__", {})
        annotations.update(current_annotations)
        config_instance.__annotations__ = annotations

        # Create a list of keys to avoid modifying dict during iteration
        # TODO: Fix non-dunder attribute handling - Currently we remove ALL non-dunder
        # attributes from the class dict, which breaks if users add methods, properties,
        # static methods, or other descriptors to their settings classes. We should only
        # move attributes that represent actual settings (those with type annotations or
        # simple values), but preserve methods, properties, etc. This requires:
        # 1. Distinguishing between settings attributes and other class members
        # 2. Updating __getattribute__ to handle both settings and regular class attributes
        # 3. Testing with classes that have methods, properties, class methods, static methods
        keys_to_move = []
        for key, value in dct.items():
            # A setting is a class attribute that is not a dunder, not a callable,
            # and not a descriptor like property, static method, or class method.
            if (
                not key.startswith("__")
                and not callable(value)
                and not isinstance(value, (property, staticmethod, classmethod))
            ):
                keys_to_move.append(key)

        for key in keys_to_move:
            setattr(config_instance, key, dct.pop(key))

        # Handle annotations without defaults (settings without initializers)
        for annotation_key, annotation_value in current_annotations.items():
            if not hasattr(config_instance, annotation_key):
                if type(None) in get_args(annotation_value):
                    value = None
                else:
                    value = _UNINITIALIZED
                setattr(config_instance, annotation_key, value)

        # Set the flag after all inheritance copying is done
        # Use the mangled name to prevent user settings from conflicting
        # TODO: Consider revisiting this name mangling approach - alternatives include
        # unique prefixes, nested objects, or __slots__ on ConfigInstance
        object.__setattr__(
            config_instance, "_MetaCheapSettings__raise_on_uninitialized_setting", False
        )

        dct["__config_instance"] = config_instance

        # Create the class
        cls = super().__new__(mcs, name, bases, dct)

        # Restore the original __module__ for pickle compatibility
        # The metaclass machinery might have changed it, but we need to keep
        # the original module where the class was actually defined
        if original_module:
            cls.__module__ = original_module

        return cls

    def __dir__(cls):
        """Provide a directory of settings, methods, and other attributes."""
        # Start with the default directory, which includes methods, etc.
        dir_set = set(super().__dir__())

        # Add all defined settings from the class and its parents
        mro = type.__getattribute__(cls, "__mro__")
        for klass in mro:
            if not hasattr(klass, "__config_instance"):
                continue

            try:
                config_instance = object.__getattribute__(klass, "__config_instance")
            except AttributeError:
                continue

            # Add attributes with initializers
            for attr in config_instance.__dict__:
                if not attr.startswith("__"):
                    dir_set.add(attr)

            # Add attributes with annotations (might not have initializers)
            if hasattr(config_instance, "__annotations__"):
                for attr in config_instance.__annotations__:
                    dir_set.add(attr)

        return sorted(list(dir_set))

    @staticmethod
    def _get_cli_config_instance(klass):
        """Return the command line argument config instance, if present, or `None` if it is not."""
        try:
            return object.__getattribute__(klass, "__cli_config_instance")
        except AttributeError:
            return None

    def __getattribute__(cls, attribute):
        """Get attribute value, checking environment variables first.

        For settings attributes, this checks if an environment variable with the
        uppercase attribute name exists. If found, converts the value using
        the type annotation and returns it. Otherwise, returns the default value.
        Supports inheritance by checking parent classes in the MRO.
        """
        # Special attributes that should use default behavior
        if attribute in ("__config_instance", "__mro__", "__class__", "__dict__"):
            return type.__getattribute__(cls, attribute)

        # Check each class in the MRO for the attribute
        mro = type.__getattribute__(cls, "__mro__")

        # First, check for the attribute in any command line config instance in the MRO
        for klass in mro:
            cli_config_instance = MetaCheapSettings._get_cli_config_instance(klass)
            if cli_config_instance and hasattr(cli_config_instance, attribute):
                return getattr(cli_config_instance, attribute)

        # If not found in CLI configs, check environment variables and default values
        for klass in mro:
            if not hasattr(klass, "__config_instance"):
                continue

            try:
                config_instance = object.__getattribute__(klass, "__config_instance")
            except AttributeError:
                continue

            if (
                hasattr(config_instance, attribute)
                or attribute in config_instance.__annotations__
            ):
                env_attr = os.environ.get(attribute.upper())
                if env_attr is not None:
                    # Check if we have annotations for this attribute
                    if (
                        hasattr(config_instance, "__annotations__")
                        and attribute in config_instance.__annotations__
                    ):
                        return _convert_value_to_type(
                            env_attr,
                            config_instance.__annotations__[attribute],
                            attribute,
                        )
                    else:
                        # No type annotation, try to infer from default value
                        if hasattr(config_instance, attribute):
                            default_value = getattr(config_instance, attribute)
                            inferred_type = type(default_value)
                            # Special case: Path instances have concrete types like PosixPath,
                            # but we want to treat them as Path for conversion
                            if isinstance(default_value, Path):
                                inferred_type = Path
                            return _convert_value_to_type(
                                env_attr, inferred_type, attribute
                            )
                        # No annotation and no default, return as string
                        return env_attr
                if hasattr(config_instance, attribute):
                    attr_value = getattr(config_instance, attribute)
                    if attr_value is _UNINITIALIZED:
                        if config_instance._MetaCheapSettings__raise_on_uninitialized_setting:  # noqa
                            raise AttributeError(f"{attribute} is not initialized")
                        else:
                            attr_value = None
                    return attr_value

        # If not found in any config instance, use default behavior
        return type.__getattribute__(cls, attribute)

    def __setattr__(cls, attribute, value):
        """Set attribute value."""
        if attribute == "__config_instance":
            object.__setattr__(cls, attribute, value)
        else:
            config_instance = object.__getattribute__(cls, "__config_instance")
            setattr(config_instance, attribute, value)

    def __reduce__(cls):
        """Enable pickling of the class itself."""
        # For pickling, we need to return a way to reconstruct this class
        # Since the class is defined in user code, we return the class directly
        # if it can be imported from its module
        try:
            # Try to import the class from its module
            module = importlib.import_module(cls.__module__)
            if hasattr(module, cls.__name__):
                # Class can be imported normally
                return getattr, (module, cls.__name__)
        except (ImportError, AttributeError):
            pass

        # If we can't import it normally, we need to reconstruct it
        config_instance = object.__getattribute__(cls, "__config_instance")
        config_data = {}
        annotations = {}

        if hasattr(config_instance, "__annotations__"):
            annotations = config_instance.__annotations__.copy()

        for attr in dir(config_instance):
            if not attr.startswith("__"):
                config_data[attr] = getattr(config_instance, attr)

        return (
            _reconstruct_settings_class,
            (cls.__module__, cls.__name__, config_data, annotations),
        )


class CheapSettings(metaclass=MetaCheapSettings):
    """Base class for simple, environment-variable-driven configuration.

    Subclass this and define your settings as typed class attributes:

        class MySettings(CheapSettings):
            host: str = "localhost"
            port: int = 8080
            debug: bool = False

    Environment variables will override the defaults:
        HOST=example.com PORT=3000 DEBUG=true python myapp.py

    Supports all basic Python types plus Optional and Union types (or Path
    types). Complex types (list, dict) are parsed from JSON strings.
    """

    def __getattribute__(self, name):
        """Allow instances to access class-level settings."""
        # First try regular instance attribute access
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            # Fall back to class-level attribute access
            # This allows instances to access settings defined at the class level
            return getattr(type(self), name)

    def __reduce__(self):
        """Enable pickling by returning class and state information."""
        # Try to return the class directly if it can be imported
        try:
            module = importlib.import_module(self.__class__.__module__)
            if hasattr(module, self.__class__.__name__):
                cls = getattr(module, self.__class__.__name__)
                return cls, (), self.__getstate__()
        except (ImportError, AttributeError):
            pass

        # Fallback to reconstruction
        return (
            _reconstruct_settings_instance,
            (self.__class__.__module__, self.__class__.__name__),
            self.__getstate__(),
        )

    def __getstate__(self):
        """Get the state for pickling - returns a dict of all settings."""
        # For CheapSettings, we don't actually have instance state
        # All settings are class-level, so we just return an empty dict
        return {}

    def __setstate__(self, state):
        """Restore state when unpickling."""
        # Nothing to restore for CheapSettings instances
        # All settings are accessed from the class level
        pass

    @classmethod
    def to_static(cls) -> object:
        """Create a static snapshot of current settings as a regular class.
        The returned class is a regular Python class without any dynamic behavior.

        Returns:
             object: a new class with all settings resolved to their current values.

        This is useful for:
        - Performance-critical code where attribute access overhead matters
        - Situations where you want to freeze settings at a point in time
        - Working around edge cases with the dynamic metaclass behavior

        Example:
            >>> class MySettings(CheapSettings):
            ...     host: str = "localhost"
            ...     port: int = 8080
            >>> StaticSettings = MySettings.to_static()
            >>> StaticSettings.host  # Just a regular class attribute
            'localhost'
        """
        # Collect all settings and their current resolved values
        attrs = {}

        # Get all settings from the class (including inherited ones)
        for name in dir(cls):
            # Skip private attributes and methods
            if name.startswith("_"):
                continue

            # Get the attribute value
            try:
                value = getattr(cls, name)
            except AttributeError:
                continue

            # Skip methods and other callables
            if callable(value):
                continue

            # Add the resolved value to our static class
            attrs[name] = value

        # Create a new regular class with the resolved values
        static_class = type(f"Static{cls.__name__}", (), attrs)

        # Copy the module for better repr and debugging
        static_class.__module__ = cls.__module__

        return static_class

    @classmethod
    def from_env(cls) -> object:
        """Create a static snapshot with only values from environment variables.

        Returns a regular Python class containing only the settings that are
        explicitly set in environment variables, ignoring all defaults.

        Returns:
            object: A new class with only environment-sourced settings.

        This is useful for:
        - Debugging which settings are coming from the environment
        - Creating minimal configuration objects
        - Validating environment-only deployments

        Example:
            >>> os.environ['HOST'] = 'example.com'
            >>> EnvOnly = MySettings.from_env()
            >>> EnvOnly.host  # 'example.com'
            >>> hasattr(EnvOnly, 'port')  # False (not in env)
        """
        attrs = {}
        config_instance = object.__getattribute__(cls, "__config_instance")
        annotations = getattr(config_instance, "__annotations__", {})

        # Only include attributes that have environment variables set
        for name, type_hint in annotations.items():
            env_name = name.upper()
            if env_name in os.environ:
                # Use the same logic as __getattribute__ to get the converted value
                try:
                    value = getattr(cls, name)
                    attrs[name] = value
                except (AttributeError, ValueError):
                    # Skip if we can't get or convert the value
                    pass

        # Create a simple class with just the env values
        env_class = type(f"{cls.__name__}FromEnv", (), attrs)
        return env_class

    @classmethod
    def set_raise_on_uninitialized(cls, value: bool = True):
        """Set whether to raise an error when accessing uninitialized settings.

        Args:
            value: If True, accessing uninitialized settings raises AttributeError.
                   If False, accessing uninitialized settings returns None (default).

        Example:
            >>> class MySettings(CheapSettings):
            ...     required_setting: str  # No default
            >>> MySettings.set_raise_on_uninitialized(True)
            >>> MySettings.required_setting  # Raises AttributeError
        """
        config_instance = object.__getattribute__(cls, "__config_instance")
        object.__setattr__(
            config_instance, "_MetaCheapSettings__raise_on_uninitialized_setting", value
        )

    @classmethod
    def set_config_from_command_line(cls, arg_parser=None, args=None):
        """Creates command line arguments (as flags) that correspond to the settings, & parses them, setting the
        config values based on them. Settings overridden by command line arguments take precedence over any
        default variables, & over environment variables. Currently, settings of `dict` & `list` types are ignored,
        & no command line arguments are added for them. It can optionally take an instance of argparse.ArgumentParser
        that can be used to pre-configure your own command line arguments. The optional `args` parameter allows
        passing specific arguments for testing (if None, uses sys.argv). Returns the parsed arguments (an
        instance of argparse.Namespace). Can raise various exceptions."""

        # Create a second config instance specifically for command line arguments. This adds a new class attribute
        # called `__cli_config_instance`, & adds any command line arguments that correspond to the attributes of
        # `__config_instance`. It also copies any type annotations for the copied attributes.
        try:
            config_instance = object.__getattribute__(cls, "__config_instance")
        except AttributeError:
            raise AttributeError("Config instance has not been set.")

        if config_instance is None:
            raise AttributeError("Config instance has not been set.")

        cli_config_instance = MetaCheapSettings.ConfigInstance()
        parsed_args = parse_command_line_arguments(
            config_instance, cli_config_instance, arg_parser, args
        )
        # Use type.__setattr__ to set attribute on the class
        type.__setattr__(cls, "__cli_config_instance", cli_config_instance)

        return parsed_args
