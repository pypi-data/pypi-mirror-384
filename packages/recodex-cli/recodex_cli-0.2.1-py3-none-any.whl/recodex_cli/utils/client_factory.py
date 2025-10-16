import typer
from recodex import client_factory
from recodex.client import Client

from .cmd_utils import execute_with_verbosity
from .login_info import LoginInfo


def login(login_info: LoginInfo, verbose=False):
    """Determines and executes the best login approach based on the provided information.

    Args:
        login_info (LoginInfo): Login information obtained from the user.
        verbose (bool, optional): Execution verbosity. Defaults to False.

    Raises:
        Exception: Thrown when important input values were missing, or the login process failed
    """

    # if the api_url was not provided, load it from the session file as a secondary source
    # the api_url may still be None afterwards if it was missing from the session file for some reason
    user_context = client_factory.load_session()
    if user_context is not None and login_info.api_url is None:
        print("Reusing API URL from session file.")
        login_info.api_url = user_context.api_url

    # prompt the API URL and API token and overwrite any existing session file
    if login_info.use_token_prompt:
        if login_info.api_url is None:
            login_info.api_url = typer.prompt("API URL")
        if login_info.api_token is None:
            login_info.api_token = typer.prompt("API Token")
        client_factory.create_session_from_token(login_info.api_url, login_info.api_token, verbose)
        return

    # prompt the API URL, username, and password and overwrite any existing session file
    if login_info.use_credentials_prompt:
        if login_info.api_url is None:
            login_info.api_url = typer.prompt("API URL")
        if login_info.username is None:
            login_info.username = typer.prompt("Username")
        if login_info.password is None:
            login_info.password = typer.prompt("Password", hide_input=True)
        client_factory.create_session_from_credentials(
            login_info.api_url,
            login_info.username,
            login_info.password,
            verbose
        )
        return

    # make sure an API URL was provided
    if login_info.api_url is None:
        raise Exception("Please provide the URL of the host.")

    # login with provided token
    if login_info.api_token is not None:
        client_factory.create_session_from_token(login_info.api_url, login_info.api_token, verbose)
        return

    # either a token or username and password needs to be provided
    if login_info.username is None or login_info.password is None:
        raise Exception("Please provide an API token or a username and password.")

    # login with credentials
    client_factory.create_session_from_credentials(
        login_info.api_url,
        login_info.username,
        login_info.password,
        verbose
    )


def logout(verbose=False):
    """Removes the local user context file, effectively logging the user out.

    Args:
        verbose (bool, optional): Execution verbosity. Defaults to False.
    """

    client_factory.remove_session()


def get_client_with_verbosity(verbose: bool) -> Client:
    """Creates a client object from the local user context file.

    Args:
        verbose (bool): Whether to truncate error messages.

    Returns:
        Client: Returns a client object.
    """

    return execute_with_verbosity(client_factory.get_client_from_session, verbose)


def load_session_with_verbosity(verbose: bool):
    """Loads the local user context file.

    Args:
        verbose (bool): Whether to truncate error messages.

    Returns:
        UserSession | None: Returns a user session object or None if no session file exists.
    """

    session = client_factory.load_session()
    if session is None:
        typer.echo("No session found.")
        if verbose:
            typer.echo(f"Session file path: {client_factory.session_path}")
        return None

    if session.is_token_expired():
        typer.echo("Session token has expired.")
        if verbose:
            typer.echo(f"Token expired at {session.get_token_expiration_time()}.")
            typer.echo(f"Expired API URL: {session.api_url}")
            typer.echo(f"Expired user ID: {session.get_user_id()}")

        return None

    return session


def refresh_session():
    """Refresh the session token even if it is not close to expiration."""
    client_factory.refresh_session()
