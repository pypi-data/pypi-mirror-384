
# Copyright (C) Integrate.ai, Inc. All rights reserved.

"""Module containing main CLI entrypoint. Performs any preprocessing required before handing off to Typer."""

import os
import sys


def interactive_mode_check():
    """Check if --no-prompt given as kwarg and set env variable accordingly."""
    if "--no-prompt" in sys.argv:
        os.environ["IAI_DISABLE_PROMPTS"] = "true"
        sys.argv.remove("--no-prompt")
    else:
        os.environ["IAI_DISABLE_PROMPTS"] = ""


def main():
    """Run any pre-Typer checks before starting Typer app."""
    interactive_mode_check()
    from integrate_ai.main import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()  # pragma: no cover
