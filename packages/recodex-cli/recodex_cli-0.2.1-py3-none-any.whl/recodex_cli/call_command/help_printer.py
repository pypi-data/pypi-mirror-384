import click
from rich.console import Console
from rich.panel import Panel
from recodex.client_components.endpoint_resolver import EndpointResolver

from ..utils import cmd_utils as cmd_utils


class HelpPrinter:
    """Class handling detailed help messages for the call command endpoints.
    """

    path_panel: Panel | None = None
    query_panel: Panel | None = None
    body_panel: Panel | None = None
    console: Console | None = None

    def __get_param_panel(self, params: list[dict], title) -> Panel:
        rows_tokenized = []
        for param in params:
            rows_tokenized.append(cmd_utils.get_param_info_text_tokens(param))

        rows = ["" for i in range(len(rows_tokenized))]

        self.__add_text_token(rows, rows_tokenized, "python_name", "bright_cyan")
        self.__add_text_token(rows, rows_tokenized, "type", "yellow")
        self.__add_text_token(rows, rows_tokenized, "opt", "magenta")
        self.__add_text_token(rows, rows_tokenized, "desc")

        text = "\n".join(rows)
        return self.__create_panel(text, title)

    def __add_text_token(
            self,
            texts: list[str],
            token_dicts: list[dict[str, str]],
            token_key: str,
            color: str = "white"
    ):
        max_len = 0
        for text in texts:
            if len(text) > max_len:
                max_len = len(text)

        for i in range(len(texts)):
            if token_key not in token_dicts[i]:
                continue
            # append texts with spaces
            texts[i] += " " * (max_len - len(texts[i]))
            # add token
            token = f" {token_dicts[i][token_key]}".replace("[", "\\[")
            # add token color
            token = f"[{color}]{token}[/{color}]"
            texts[i] += token

    def __create_panel(self, text: str, title: str) -> Panel:
        # escape opening brackets

        return Panel(
            text,
            border_style="dim",
            title=title,
            title_align="left",
        )

    def __prepare(self, ctx: click.Context, endpoint: str, verbose: bool):
        self.ctx = ctx
        self.formatter = ctx.make_formatter()

        self.print_detail = endpoint != ""
        if self.print_detail:
            def __init():
                presenter, action = cmd_utils.execute_with_verbosity(
                    lambda: cmd_utils.parse_endpoint_or_throw(endpoint),
                    verbose
                )
                endpoint_resolver = EndpointResolver()
                self.console = Console()
                path_params = endpoint_resolver.get_path_params(presenter, action)
                query_params = endpoint_resolver.get_query_params(presenter, action)

                self.path_panel, self.query_panel, self.body_panel = None, None, None
                if len(path_params) > 0:
                    self.path_panel = self.__get_param_panel(path_params, "Path Parameters Detail")
                if len(query_params) > 0:
                    self.query_panel = self.__get_param_panel(query_params, "Query Parameters Detail")
                if endpoint_resolver.endpoint_has_body(presenter, action):
                    self.body_panel = self.__create_panel("The endpoint expects a JSON body.", "Body Detail")
            cmd_utils.execute_with_verbosity(__init, verbose)

    def print(self, ctx: click.Context, endpoint: str, verbose: bool):
        self.__prepare(ctx, endpoint, verbose)
        self.ctx.command.format_help(self.ctx, self.formatter)

        if self.print_detail:
            if self.console is None:
                raise Exception("The Console was not instantiated properly.")
            if self.path_panel:
                self.console.print(self.path_panel)
            if self.query_panel:
                self.console.print(self.query_panel)
            if self.body_panel:
                self.console.print(self.body_panel)
