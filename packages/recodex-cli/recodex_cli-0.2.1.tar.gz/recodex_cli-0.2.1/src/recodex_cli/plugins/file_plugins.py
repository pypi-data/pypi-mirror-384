import typer
from typing_extensions import Annotated
import recodex.helpers.file_upload_helper as file_upload_helper
from recodex.generated.swagger_client.api.default_api import DefaultApi

from ..utils import client_factory
from ..utils import cmd_utils as cmd_utils
from ..call_command.command import call
from ..call_command.command_state import CommandState

app = typer.Typer()


@app.command()
def upload(
    filepath: Annotated[
        str, typer.Argument(help="Path to the file to be uploaded")
    ],
    verbose: Annotated[
        bool, typer.Option(help="Execution Verbosity")
    ] = False,
):
    """Uploads the given file to the ReCodEx server in chunks.
    """
    client = client_factory.get_client_with_verbosity(verbose)

    def command():
        return file_upload_helper.upload(client, filepath, verbose)
    file_id = cmd_utils.execute_with_verbosity(command, verbose)

    print("File sent successfully")
    print(f"File ID: {file_id}")


@app.command()
def download(
    id: Annotated[
        str, typer.Argument(help="The ID of the file")
    ],
    out_path: Annotated[
        str | None, typer.Option(
            help="If set, the file will be saved to this path instead of being printed to stdin",
            allow_dash=True
        )
    ] = None,
    verbose: Annotated[
        bool, typer.Option(help="Execution Verbosity")
    ] = False,
):
    """Downloads the specified file from the ReCodEx server.
    """
    client = client_factory.get_client_with_verbosity(verbose)

    state = CommandState(verbose)
    state.output_path = out_path
    state.output_format = "raw"

    # preserve the file content and do not add any extra newline
    state.output_extra_newline = False

    def command():
        call(client, DefaultApi.uploaded_files_presenter_action_download, path_values=[id], state=state)
    cmd_utils.execute_with_verbosity(command, verbose)
