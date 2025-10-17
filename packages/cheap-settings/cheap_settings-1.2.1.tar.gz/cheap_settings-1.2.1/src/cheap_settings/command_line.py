import argparse
import sys
from typing import Optional, Sequence, get_args, get_origin

# TODO: Add dict/list support to command_line.py using the existing JSON parsing logic.


def _convert_to_argument_name(name: str) -> str:
    """Convert an attribute name to an argument name."""
    name = name.lower()
    return name.replace("_", "-")


def _bool_str_to_bool(value: str) -> bool:
    """Convert a string to a boolean value."""
    normalized_value = value.lower()
    if normalized_value in ("true", "1", "yes", "on"):
        return True
    elif normalized_value in ("false", "0", "no", "off"):
        return False
    else:
        raise ValueError(f"{value} is not a valid boolean value")


def _optional_type_converter(inner_type):
    """Create a converter function for Optional types that handles 'none'."""

    def converter(value: str):
        if value.lower() == "none":
            return None
        return inner_type(value)

    return converter


def _get_arg_parser(
    config_instance, parser: Optional[argparse.ArgumentParser] = None
) -> argparse.ArgumentParser:
    """Create an argument parser from the given config instance. Creates an argument
    parser, or uses the supplied parser if present, then iterates through
    the config instance's attributes, converting them to argument names, & adds
    them as arguments to the parser, using the attribute's type annotations
    to determine the argument type. Returns an argument parser instance."""
    if parser is None:
        parser = argparse.ArgumentParser()

    # Get annotations directly from the config instance
    annotations = getattr(config_instance, "__annotations__", {})

    # Reserved argument names that conflict with argparse built-ins
    reserved_args = {"help", "h"}

    # Process both attributes and annotations
    all_names = set(dir(config_instance)) | set(annotations.keys())

    for name in all_names:
        if name.startswith("_"):
            continue

        # TODO: Document this behavior
        # Check for reserved names
        if name.lower() in reserved_args:
            raise ValueError(
                f"Cannot use '{name}' as a setting name because it conflicts with argparse built-in options. "
                f"Reserved names: {', '.join(sorted(reserved_args))}"
            )

        argument_name = _convert_to_argument_name(name)
        argument_type = annotations.get(name)
        argument_default = getattr(config_instance, name, None)
        argument_action = "store"

        if argument_type is None:
            argument_type = type(argument_default) or str

        # Handle Optional/Union types for argparse
        is_optional = False
        origin = get_origin(argument_type)
        if origin is not None:
            # For Optional/Union types, extract the non-None type
            args = get_args(argument_type)
            has_none = type(None) in args
            if has_none:
                is_optional = True
                for arg in args:
                    if arg is not type(None):
                        argument_type = arg
                        break

        if argument_type is bool:
            if is_optional:
                # Optional bools always accept explicit values
                argument_type = _bool_str_to_bool
            elif argument_default is None:
                argument_type = _bool_str_to_bool
            elif argument_default is False:
                argument_action = "store_true"
            elif argument_default is True:  # No, this expression cannot be simplified
                argument_name = "no-" + argument_name
                argument_action = "store_false"
            else:
                argument_type = _bool_str_to_bool
        elif argument_type in (dict, list):
            # TODO: Add support for dict and list types from the command line.
            #  This will likely involve parsing JSON strings.
            continue

        # Wrap the type converter for Optional types to handle "none"
        if is_optional and argument_type is not _bool_str_to_bool:
            argument_type = _optional_type_converter(argument_type)

        argument_name = "--" + argument_name

        # store_true/store_false don't accept type parameter
        if argument_action in ("store_true", "store_false"):
            parser.add_argument(
                argument_name,
                default=argument_default,
                action=argument_action,
                dest=name,
            )
        else:
            parser.add_argument(
                argument_name,
                type=argument_type,
                default=argument_default,
                action=argument_action,
                dest=name,
            )

    return parser


def _incorporate_parsed_arguments(
    args: argparse.Namespace, config_instance, cli_config_instance, provided_args
):
    """Updates the cli_config_instance with only the arguments that were explicitly provided.
    As designed, command line args will always override environment variables."""
    # Get annotations directly from the config instance
    annotations = getattr(config_instance, "__annotations__", {})

    for name, value in vars(args).items():
        if hasattr(config_instance, name) or name in annotations:
            # Check if this argument was actually provided on the command line
            arg_name = "--" + _convert_to_argument_name(name)
            no_arg_name = "--no-" + _convert_to_argument_name(name)

            # Only set if the argument was explicitly provided
            if arg_name in provided_args or no_arg_name in provided_args:
                setattr(cli_config_instance, name, value)


def parse_command_line_arguments(
    config_instance: "MetaCheapSettings.ConfigInstance",  # noqa F821
    cli_config_instance: "MetaCheapSettings.ConfigInstance",  # noqa F821
    parser: Optional[argparse.ArgumentParser] = None,
    args: Optional[Sequence[str]] = None,
) -> argparse.Namespace:
    """Creates an argument parser from the config instance, then
    Parses the command line arguments and returns an argparse.Namespace.

    Args:
        config_instance: The config instance to read settings from
        cli_config_instance: The config instance to store CLI values
        parser: Optional custom ArgumentParser
        args: Optional list of arguments to parse (if None, uses sys.argv)
    Returns:
        argparse.Namespace: The parsed arguments
    """

    parser = _get_arg_parser(config_instance, parser)
    parsed_args = parser.parse_args(args)
    # Pass the actual args that were provided
    provided_args = args if args is not None else sys.argv[1:]
    _incorporate_parsed_arguments(
        parsed_args, config_instance, cli_config_instance, provided_args
    )
    return parsed_args
