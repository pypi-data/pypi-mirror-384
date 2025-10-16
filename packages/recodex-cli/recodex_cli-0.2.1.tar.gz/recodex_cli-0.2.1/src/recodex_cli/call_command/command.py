import typer
import inquirer
import click
from typing import Any
from collections.abc import Callable
from recodex.client import Client
from recodex.client_components.endpoint_resolver import EndpointResolver

from .response_printer import print_response
from ..utils import cmd_utils as cmd_utils
from .help_printer import HelpPrinter
from .command_state import CommandState


def call_interactive(client: Client, state: CommandState):
    """Starts an interactive call prompt for the user.

    Args:
        client (Client): The client object used.
        state (CommandState, optional): The state detailing extra info for the command execution.
            Defaults to CommandState().
    """

    endpoint_resolver = EndpointResolver()
    presenter, action = prompt_endpoint(endpoint_resolver)
    endpoint = f"{presenter}.{action}"
    path_param_values, query_param_values, body_string = prompt_request_data(endpoint_resolver, presenter, action)
    body = cmd_utils.parse_json(body_string)

    call(client, endpoint, path_param_values, query_param_values, body, state)


def call(
    client: Client,
    endpoint: str | Callable,
    path_values: list[str] = [],
    query_values: list[str] = [],
    body: dict = {},
    state: CommandState = CommandState(),
    files: dict = {}
):
    """Calls a single ReCodEx endpoint.

    Args:
        client (Client): The client object used.
        endpoint (str | Callable): A string name or function of the endpoint.
        path_values (list[str], optional): A list of PATH parameter values in order of definition. Defaults to [].
        query_values (list[str], optional): A list of query parameters in the form of "name=value" strings.
            Defaults to [].
        body (dict, optional): The body of the request. Defaults to {}.
        state (CommandState, optional): The state detailing extra info for the command execution.
            Defaults to CommandState().
        files (dict, optional): A dictionary of files uploaded to ReCodEx. Defaults to {}.
    """

    presenter, action = cmd_utils.parse_endpoint_or_throw(endpoint)

    # parse params
    path_dict = path_list_to_dict(client.endpoint_resolver, presenter, action, path_values)
    query_dict = query_list_to_dict(client.endpoint_resolver, presenter, action, query_values)

    if state.verbose:
        typer.echo("Sending Request...")
    response = client.send_request(presenter, action, body, path_dict, query_dict, files)
    print_response(response, state)


def path_list_to_dict(
    endpoint_resolver: EndpointResolver,
    presenter: str,
    action: str,
    path_values: list[str]
) -> dict[str, str]:
    # get param definitions
    path_params = endpoint_resolver.get_path_params(presenter, action)

    # check if the number of provided params matches the definitions
    if len(path_params) < len(path_values):
        plural_s = "s" if len(path_params) > 1 else ''
        raise Exception(f"Expected {len(path_params)} PATH parameter{plural_s}, but got {len(path_values)}.")
    elif len(path_params) > len(path_values):
        missing_params = []
        for i in range(len(path_values), len(path_params)):
            missing_params.append(path_params[i]["python_name"])
        params_text = ", ".join(missing_params)
        plural_text = "s are" if len(missing_params) > 1 else ' is'
        raise Exception(f"The following PATH parameter{plural_text} missing: {params_text}.")

    # construct param_name->param_value dict
    path_dict = {}
    for i in range(len(path_params)):
        path_dict[path_params[i]["python_name"]] = path_values[i]
    return path_dict


def query_list_to_dict(
    endpoint_resolver: EndpointResolver,
    presenter: str,
    action: str,
    query_values: list[str]
) -> dict[str, Any]:
    query_dict = {}
    for query_value in query_values:
        if query_value.count("=") < 1:
            raise Exception("The query values need to be in <name=value> format.")

        # there can be '=' in the value, so split by the first one
        split_pos = query_value.find("=")
        name = query_value[0: split_pos]
        value = query_value[split_pos + 1:]

        query_param = endpoint_resolver.get_query_param(presenter, action, name)
        if not query_param or name != query_param["python_name"]:
            raise Exception(f"Unknown QUERY parameter: {name}.")

        # handle arrays and objects
        if query_param["schema"]["type"] == "array" or query_param["schema"]["type"] == "object":
            try:
                value = cmd_utils.parse_json(value)
            except:
                raise Exception(f"The QUERY parameter '{name}' is not a valid JSON array or object.")

        query_dict[name] = value
    return query_dict


def prompt_endpoint(endpoint_resolver: EndpointResolver):
    presenter_choices = endpoint_resolver.get_presenters()
    question = [
        inquirer.List(
            'presenter',
            message="What presenter would you like to use?",
            choices=presenter_choices,
        ),
    ]
    presenter = inquirer.prompt(question)['presenter']  # type: ignore

    action_choices = endpoint_resolver.get_actions(presenter)
    question = [
        inquirer.List(
            'action',
            message="What action would you like to use?",
            choices=action_choices,
        ),
    ]
    action = inquirer.prompt(question)['action']  # type: ignore

    return presenter, action


def prompt_request_data(endpoint_resolver: EndpointResolver, presenter: str, action: str):
    path_params = endpoint_resolver.get_path_params(presenter, action)
    path_param_values = prompt_path_values(path_params)

    query_params = endpoint_resolver.get_query_params(presenter, action)
    query_param_values = prompt_query_values(query_params)

    json_string = "{}"
    if endpoint_resolver.endpoint_has_body(presenter, action):
        json_string = typer.prompt("Request Body [JSON]")

    return path_param_values, query_param_values, json_string


# prompt the user for path values, returning a list of retrieved values
def prompt_path_values(params):
    path_values = []
    for param in params:
        prompt_tokens = cmd_utils.get_param_info_text_tokens(param)
        prompt = " ".join(prompt_tokens.values())

        # get prompt value
        value = typer.prompt(prompt)
        path_values.append(value)
    return path_values


# prompt the user for query values, returning a list in <name=value> format
def prompt_query_values(params):
    query_values = []
    for param in params:
        prompt_tokens = cmd_utils.get_param_info_text_tokens(param)
        prompt = " ".join(prompt_tokens.values())
        name = param["python_name"]
        required = param["required"]

        # get prompt value
        if required:
            value = typer.prompt(prompt)
        else:
            value = typer.prompt(prompt, "", show_default=False)

        # do not propagate empty strings
        if value != "":
            # the call function expects query params in <name=value> format
            query_values.append(f"{name}={value}")

    return query_values


def help_callback(ctx: click.Context, _, display_help: bool):
    if not display_help:
        return display_help

    endpoint = ctx.params['endpoint']
    verbose = ctx.params['verbose']

    help_printer = HelpPrinter()
    help_printer.print(ctx, endpoint, verbose)
    return display_help
