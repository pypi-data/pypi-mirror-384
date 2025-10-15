
# Copyright (C) Integrate.ai, Inc. All rights reserved.

"""Module containing top-level Typer app functionality."""

import subprocess  # noqa: F401 - needed for unittest patch
import typer
import integrate_ai.sdk as sdk
import integrate_ai.client as client
import integrate_ai.server as server
import integrate_ai.onprem_node as onprem_node
from integrate_ai.utils.typer_utils import show_package_version


app = typer.Typer(no_args_is_help=True)

app.add_typer(sdk.app, name="sdk")
app.add_typer(client.app, name="client")
app.add_typer(server.app, name="server")
app.add_typer(onprem_node.app, name="onprem_node")

package = "integrate-ai"


@app.callback()
def docs(
    no_prompt: bool = typer.Option(False, "--no-prompt", help="Disable prompts. Confirmations will default to `Y`.")
):
    """
    The CLI interface to manage integrate.ai operations.

    Your IAI token will be required in many commmands. For convenience, you can set this in the `IAI_TOKEN` environment variable to avoid repeated prompts.
    """


@app.command()
def version():
    """
    The currently installed version of the cli.
    """
    show_package_version(package)


def main():

    app()


if __name__ == "__main__":
    main()  # pragma: no cover
