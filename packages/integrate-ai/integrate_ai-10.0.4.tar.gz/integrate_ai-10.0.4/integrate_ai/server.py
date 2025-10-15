
# Copyright (C) Integrate.ai, Inc. All rights reserved.

import typer
import os
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
from integrate_ai.utils.docker_client import DockerClient
from integrate_ai.utils.typer_utils import (
    TogglePromptOption,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def pull(
    token: str = TogglePromptOption(
        ...,
        help="The IAI token.",
        prompt="Please provide your IAI token",
        envvar="IAI_TOKEN",
    ),
    version: str = typer.Option("latest", "--version", "-v", help="The version of the docker image to pull."),
):
    """
    Pull the fl-server docker image.\n Docker must be running for this command to work.
    """

    no_prompt = os.environ.get("IAI_DISABLE_PROMPTS")
    delete_response = False

    # start progress bar
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:

        # connect to docker
        p = progress.add_task(description="Connecting to docker...", total=1)
        docker_client = DockerClient(token, image_name="fl-server")
        progress.update(task_id=p, completed=True)

        # check if any existing docker images on system
        p = progress.add_task(description="Searching for existing server images...", total=1)
        current_images = docker_client.get_local_versions(docker_client.get_repo_name())
        progress.update(task_id=p, completed=True)

        # check for latest docker image
        p = progress.add_task(description="Determining latest available server version...", total=1)
        latest_available_version = docker_client.get_latest_available_version()
        progress.update(task_id=p, completed=True)

    version_to_pull = latest_available_version if version == "latest" else version
    if len(current_images) == 0:
        rprint("No existing server version found on system.")
    else:

        # if images exist on system, check the latest version that is installed
        latest_version = docker_client.get_latest_version_of_image(current_images) or "`latest`"

        rprint(
            f"Latest version of docker image found on system is {latest_version}. Most recent version is {latest_available_version}."
        )

        if latest_version == version_to_pull:

            # no point installing if they already have the latest image
            rprint("The requested version of the server image is already on your system. Exiting...")
            raise typer.Exit(0)
        else:
            prompt_msg = f"A newer version {latest_available_version} was found. The current version of the server image will be deleted from your system. Do you want to proceed?"
            # confirm that they are ok with deleting current server images on system
            prompt_msg = "Installing this server image will delete any current version of this image on your system. Do you want to proceed?"
            if no_prompt:
                delete_response = True
            else:
                delete_response = typer.confirm(prompt_msg)

        # delete current server images if they ok'd it
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            if delete_response:
                p = progress.add_task(
                    description="Yes response received. Deleting existing server images...",
                    total=1,
                )
                docker_client.delete_images(current_images)
                progress.update(task_id=p, completed=True)
            elif not delete_response and len(current_images) > 0:
                rprint("`No` response received. Exiting...")
                raise typer.Exit(0)

    # login and pull docker image
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        p = progress.add_task(description="Logging into docker repo...", total=1)
        docker_client.login()
        progress.update(task_id=p, completed=True)
        p = progress.add_task(
            description=f"Pulling docker image {version_to_pull}. This will take a few minutes...",
            total=1,
        )
        pull_result = docker_client.pull(repo=docker_client.get_repo_name(), tag=version_to_pull)
        assert pull_result
        progress.update(task_id=p, completed=True)
        rprint(f"Image {version_to_pull} is now available.")
        raise typer.Exit(0)


@app.command()
def version(
    token: str = TogglePromptOption(
        ...,
        help="Your generated IAI token.",
        prompt="Please provide your IAI token",
        envvar="IAI_TOKEN",
    ),
):
    """
    The currently installed version of the fl-server image.
    """
    docker_client = DockerClient(token=token, image_name="fl-server")
    current_images = docker_client.get_local_versions(docker_client.get_repo_name())
    latest_version = docker_client.get_latest_version_of_image(current_images)
    if len(current_images) == 0:
        rprint("No server image found on system.")
    elif not latest_version:
        rprint("Found version tagged as `latest`.")
    else:
        rprint(latest_version)


@app.command()
def list(
    token: str = TogglePromptOption(
        ...,
        help="The IAI token.",
        prompt="Please provide your IAI token",
        envvar="IAI_TOKEN",
    )
):
    """
    List all available docker server images versions to pull.
    """
    docker_client = DockerClient(token=token, image_name="fl-server")
    versions = docker_client.get_versions()
    rprint("\n".join(versions))


@app.callback()
def main():
    """
    Sub command for managing fl-server related operations.
    """
