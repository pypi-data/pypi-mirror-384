import typer
from typing_extensions import Annotated

from ..utils import client_factory

app = typer.Typer()


@app.command()
def swagger(
    verbose: Annotated[
        bool, typer.Option(help="Execution Verbosity")
    ] = False,
):
    """Prints the swagger document currently used by the application.
    """
    client = client_factory.get_client_with_verbosity(verbose)
    print(client.endpoint_resolver.get_swagger())
