import json
import yaml
import click
import typing
from collections.abc import Callable
from recodex.helpers.utils import parse_endpoint_function


def parse_endpoint_or_throw(endpoint: str | Callable) -> tuple[str, str]:
    """Parses an endpoint representation into a presenter and action.

    Args:
        endpoint (str | Callable): Either a string in <presenter.action> for or a generated endpoint function.

    Raises:
        Exception: Thrown when the endpoint could not be parsed.

    Returns:
        tuple[str]: Returns a (presenter, action) string pair.
    """

    if isinstance(endpoint, Callable):
        return parse_endpoint_function(endpoint)

    if endpoint.count(".") != 1:
        raise Exception("The endpoint needs to be in <presenter.action> format.")

    presenter, action = endpoint.split(".")
    return presenter, action


def parse_json(json_string) -> dict:
    try:
        return json.loads(json_string)
    except:
        raise Exception("The JSON string is corrupted.")


def parse_input_body_file(path: str) -> dict:
    """Parses a file as JSON or YAML.

    Args:
        path (str): The path to the file.

    Raises:
        Exception: Thrown when the file could not be found or parsed.

    Returns:
        dict: Returns a dictionary with the parsed file.
    """

    try:
        with open(path, "r") as handle:
            json_or_yaml_string = handle.read()
    except:
        raise Exception("Could not open request body file.")

    return parse_input_body(json_or_yaml_string)


def parse_input_body(json_or_yaml_string: str) -> dict:
    """Parses a string as JSON or YAML.

    Args:
        json_or_yaml_string (str): A string in JSON or YAML format.

    Raises:
        Exception: Thrown when the string could not be parsed.

    Returns:
        dict: Returns a dictionary with the parsed string.
    """

    try:
        return json.loads(json_or_yaml_string)
    except:
        pass

    try:
        return yaml.safe_load(json_or_yaml_string)
    except:
        raise Exception("The request body in neither a valid JSON or YAML.")


def execute_with_verbosity(command: Callable[[], typing.Any], verbose: bool):
    """Executes a callback with a specified error verbosity.

    Args:
        command (Callable[[], typing.Any]): The callback to be executed.
        verbose (bool): In case of an error, whether a long error message should be displayed.

    Raises:
        e: Throws the original exception if verbose.
        click.ClickException: Throws a short exception if not verbose.

    Returns:
        _type_: Returns the return value of the callback.
    """

    try:
        return command()
    except Exception as e:
        if verbose:
            raise e
        else:
            raise click.ClickException(str(e))


def get_param_info_text_tokens(param: dict) -> dict:
    """Parses a request parameter schema.

    Args:
        param (dict): A dictionary representing the parameter.

    Returns:
        dict: A dictionary containing the python_name, type, desc, opt keys describing the parameter.
    """

    # get info
    name = param["python_name"]
    desc = param["description"]
    type = param["schema"]["type"]
    if param["schema"]["nullable"]:
        type += "|null"
    required = param["required"]

    tokens = {
        "python_name": name,
        "type": f"[{type}]",
    }
    if not required:
        tokens["opt"] = "[OPT]"
    tokens["desc"] = desc

    return tokens
