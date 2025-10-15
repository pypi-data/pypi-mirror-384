
# Copyright (C) Integrate.ai, Inc. All rights reserved.

"""Module containing Typer sdk submodule functionality."""

import typer
from rich import print as rprint
from integrate_ai.utils.rest_client import RestClient
import subprocess
from integrate_ai.utils.error_handling import IntegrateAIException

from integrate_ai.utils.typer_utils import TogglePromptOption, show_package_version

app = typer.Typer(no_args_is_help=True)
package = "integrate-ai-sdk"


@app.command()
def install(
    token: str = TogglePromptOption(
        ...,
        help="The IAI token.",
        prompt="Please provide your IAI token",
        envvar="IAI_TOKEN",
    ),
    version: str = typer.Option("", "--version", "-v", help="The version of the sdk to download."),
):
    """
    Install the integrate_ai sdk package. Defaults to pinned version
    Installing a new sdk will override the existing one.
    Will automatically read from the IAI_TOKEN environment variable if set.
    """
    rest_client = RestClient(token)
    pip_install_command = rest_client.get_pip_install_command(version=version, package=package)["pipInstallCommand"]
    if f"pip install {package}" not in pip_install_command:
        raise IntegrateAIException(f" Not installing the right package {pip_install_command}")

    # pip will output the version number and give an error if the version is not found
    if version == "":
        rprint(f"Trying to install the pinned version of {package}.")
    else:
        rprint(f"Trying to install {package}=={version}.")
    subprocess.run(pip_install_command, check=True, shell=True)


@app.command()
def version():
    """
    The currently installed version of the sdk.
    """
    show_package_version(package)


@app.command()
def uninstall():
    """
    Uninstall the sdk and associated files and artifacts.
    """

    rprint(f"Uninstalling {package}")
    pip_uninstall_command = f"pip uninstall {package}"
    subprocess.run(pip_uninstall_command, check=True, shell=True)


@app.command()
def list(
    token: str = TogglePromptOption(
        ..., help="The IAI token.", prompt="Please provide your IAI token", envvar="IAI_TOKEN"
    ),
):
    """
    List the versions of the sdk available to be installed.
    """
    rest_client = RestClient(token)
    versions = rest_client.get_package_versions(package=package)

    if versions["package_name"] != package:
        raise IntegrateAIException("Not getting the right package. ")

    if len(versions["package_versions"]) == 0:
        rprint("No available version.")
    else:
        for version in versions["package_versions"]:
            rprint(version)


@app.callback()
def main():
    """
    Sub command for managing sdk related operations.
    """
    pass  # pragma: no cover
