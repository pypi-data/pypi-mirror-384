from recodex.client_components.client_response import ClientResponse

from .command_state import CommandState


def print_response(response: ClientResponse, state: CommandState):
    """Prints a response object to stdout or a file.

    Args:
        response (ClientResponse): The response object.
        state (CommandState): The command state specifying how to print.

    Raises:
        NotImplementedError: Thrown when an unexpected output format is specified.
    """

    # get response string
    if state.output_format == "json":
        out_string = response.get_json_string(state.output_minimized)
    elif state.output_format == "yaml":
        out_string = response.get_yaml_string(state.output_minimized)
    elif state.output_format == "raw":
        out_string = response.get_data_binary() if state.output_path else response.get_data_str()
    else:
        raise NotImplementedError(f"Unknown output format '{state.output_format}'. Please use 'yaml' or 'json'.")

    # print to console or file
    if state.output_path is None:
        if state.output_extra_newline:
            print(out_string)
        else:
            print(out_string, end="")
    else:
        with open(state.output_path, "wb") as handle:
            if state.output_format == "raw":
                handle.write(out_string)
            else:
                handle.write(out_string.encode('utf-8'))
