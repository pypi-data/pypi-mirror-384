
# Copyright (C) Integrate.ai, Inc. All rights reserved.

"""
Module containing miscellaneous typer utilities.
"""

from functools import wraps
from pathlib import Path
from rich import print as rprint
from typing import Callable, Any, Dict
import typer
import os
import re
import subprocess


def toggle_prompt_wrapper(option_func: Callable, disable_prompts: str) -> Callable:
    """Decorates a function to remove prompt as a kwarg if disable_prompts is 'true'.

    Args:
        option_func (Callable): function to wrap.
        disable_promtps (str): whether to disable prompts or not ('true' if prompts should be disabled).

    Returns:
        decorated function (Callable): either same function as option_func or same function with prompt kwarg removed.
    """

    @wraps(option_func)
    def wrapper_func(*args, **kwargs):
        updated_kwargs = kwargs.copy()
        if disable_prompts == "true":
            updated_kwargs = kwargs.copy()
            updated_kwargs.pop("prompt")
            return option_func(*args, **updated_kwargs)
        else:
            return option_func(*args, **updated_kwargs)

    return wrapper_func


# wrapper around typer.Option to enable prompting to be condition on IAI_DISABLE_PROMPTS env variable
TogglePromptOption = toggle_prompt_wrapper(typer.Option, disable_prompts=os.environ.get("IAI_DISABLE_PROMPTS", ""))


def cast_path_to_dict(path: Path) -> Dict[str, str]:
    return {
        "parent_path": str(path.parent),
        "parent_dir": str(path.parts[-2]) or "",
        "full_path": str(path),
    }


def path_param_callback(path: str) -> Dict[str, Any]:
    # Expect URLs to be properly formed (s3://).
    # Otherwise they will be treated like local path.
    if path.lower().startswith("s3://"):
        return {
            "s3": True,
            "url": path,
        }
    else:
        if path.lower().startswith("~"):
            p = Path(path).expanduser()
        else:
            p = Path(path).resolve()
        validate_posix_path(p)
        return cast_path_to_dict(p)


def validate_posix_path(path: Path) -> None:
    if not (path.is_file() or path.is_dir()):
        raise typer.BadParameter(f"file or directory {str(path)} does not exist.")
    if not os.access(str(path), os.R_OK):
        raise typer.BadParameter(f"file or directory {str(path)} is not readable.")


def show_package_version(package):
    show_version_command = f"pip show {package}"
    rprint(f"Getting current version for {package}.")

    pipe = subprocess.Popen(show_version_command, stdout=subprocess.PIPE, shell=True)
    out, err = pipe.communicate()
    if pipe.returncode != 0:
        rprint("Failed to get version.")
        raise typer.Exit(code=1)
    out_string = out.decode("utf-8")
    for line in out_string.splitlines():
        if re.search("Version", line):
            rprint(line)
            break
