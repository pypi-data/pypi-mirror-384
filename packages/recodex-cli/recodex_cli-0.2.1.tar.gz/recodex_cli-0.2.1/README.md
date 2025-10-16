# ReCodEx CLI Client

A command-line interface for the [ReCodEx](https://github.com/ReCodEx) system. This tool allows users to interact with ReCodEx from their terminal, streamlining workflows and enabling scripting possibilities. The aim is not to create a terminal-based replacement for web application, but rather an intermediate layer for bash scripts or other automation tools.

This tool is built on top of the [recodex-pylib](https://github.com/ReCodEx/pylib) Python library, which provides a wrapper for ReCodEx API generated from OpenAPI (swagger) specification.


## Key Features

* **Authentication:** Securely log in to your ReCodEx account. The CLI will securely store your access token for future sessions. The session is shared with the `recodex-pylib` library, so you can use it in conjunction with your Python scripts.
* **Execute Requests:** Send API requests and view responses from the command line.
* **Interactive Mode:** You can use the interactive mode to browse and use existing endpoints.
* **Plugins:** Use existing plugins or write your own to streamline your work.


## Installation

The recommended way to install the ReCodEx CLI is via `pip`. Python 3.11 is recommended, but other versions may also work:

```bash
pip install recodex-cli
```

Note that this also installs the `recodex-pylib` library as a dependency.


### Installation from source code

For developers or those who prefer to install directly from the source code into local venv, follow these steps:

```bash
./bin/init.sh
source ./venv/bin/activate
```

Or you can install it globally (not recommended):

```bash
pip install -r requirements.txt
pip install -e .
```


## Getting Started

The CLI is invoked via either
```bash
python3 -m recodex_cli <command> [options]
```
or using the deployed script wrapper
```bash
recodex <command> [options]
```

Let us review basic operations:

- **Login:** You can login with your credentials or an API token.

    ```bash
    # login with credentials
    recodex login --username test@test.tld --password test --api-url http://your.recodex.domain/api
    
    # login with an API token (can be generated in webapp in user settings)
    recodex login --api-url http://your.recodex.domain/api --token eyJ...

    # login via an interactive prompt
    recodex login --prompt-credentials
    recodex login --prompt-token

    # logout
    recodex logout
    ```
    Let us note that the JWT token (either provided or obtained after credentials verification) is stored in a configuration file in your home directory (usually `~/.local/share/recodex/context.yaml`).

- **Explore Commands:** You can view the full list of available commands and options by running:

    ```bash
    recodex --help
    ```

## Usage

### Call Command

The client defines the `call` command, which can be used to call any endpoint.

- **Interactive Mode:** By calling the command without any arguments, an interactive query will start that will prompt you for what endpoint you want to call and its parameters.


    ```bash
    recodex call
    ```

- **Calling an Endpoint:** To call an endpoint, add an argument in the `presenter.action` format, followed by any request parameters.

    ```bash
    # use QUERY parameters in <name=value> format
    recodex call groups.default --query search=Demo

    # beware that some parameters must be encoded in JSON (the quotes must be backslashed so the bash won't remove them)
    recodex call users.default --filters={\"search\":\"Kloda\"}

    # you can pass a JSON or YAML file as a request body
    recodex call registration.create_invitation --body-path invite.yaml

    # PATH parameters are used in order of declaration (the first one is usually the ID)
    recodex call groups.set_organizational 10000000-2000-4000-8000-160000000000 --body '{"value":true}'
    ```

- **Help:** To print a detailed description on how to use the command, use:

    ```bash
    recodex call --help
    ```

    You can also view all parameters of a specific command.

    ```bash
    recodex call groups.default --help
    ```

### Plugins

The client can also be extended with plugins that can streamline common request patterns.

- **File Upload:**  Files can be uploaded simply by providing a path. Larger files will automatically be fragmented into chunks.

    ```bash
    recodex file upload test.csv 
    > File sent successfully
    > File ID: 73aac159-b2e2-402b-9e19-096f3ec0ae7c
    ```

- **File Download:** 
    ```bash
    recodex file download 73aac159-b2e2-402b-9e19-096f3ec0ae7c --out-path test.csv
    ```

- **Get Swagger:** This command returns the Swagger document (OpenAPI Specification) currently used by the client.

    ```bash
    recodex info swagger
    ```

## Development

### Code Structure

The main entry point is the `console.py` file located in `src/recodex_cli`.
It registers all plugin files and defines the `call`, `login`, and `logout` commands.

All plugins are stored in the `plugins` folder.

The `call_command` folder contains the implementation of the `call` command, notably input parsing, help message generation, and response formatting.

### Writing Plugins

New plugins can be added to the existing plugin files or new ones.
In case you create a new plugin file, do not forget to register it in `console.py`.

The following skeleton implementation can be used as the basis for new commands:

```python
import typer
# import the DefaultApi class that holds all request functions
from recodex.generated.swagger_client.api.default_api import DefaultApi

from ..utils import client_factory
from ..utils import cmd_utils as cmd_utils

# make a Typer object that will be registered in console.py
app = typer.Typer()


@app.command()
def new_command(
    # define positional arguments
    arg: Annotated[
        str, typer.Argument(help="Command argument")
    ],
    # add options
    verbose: Annotated[
        bool, typer.Option(help="Execution Verbosity")
    ] = False,
):
    # get the client object used to send requests
    client = client_factory.get_client_with_verbosity(verbose)

    # send requests (optionally wrap the requests in a lambda)
    command = lambda: client.send_request_by_callback(DefaultApi.login_presenter_action_default)

    # pass the lambda to this utility function to print shorter
    # error messages unless the verbose flag is set (optional)
    response = cmd_utils.execute_with_verbosity(command, verbose)
    
    print(response)
```
