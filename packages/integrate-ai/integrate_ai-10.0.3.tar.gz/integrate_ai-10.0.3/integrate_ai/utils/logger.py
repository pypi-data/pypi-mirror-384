
# Copyright (C) Integrate.ai, Inc. All rights reserved.

from pathlib import Path
import os

user_root_dir = Path.home()
logs_folder = os.path.join(user_root_dir, "iai", "logs")


def get_log_paths(client_name: str, session: str):
    """Folder paths for logs can be used when given a client name and session id

    Args:
        client_name (str): name of the client
        session (str): session id

    Returns:
        session_log_path (str): path to the session folder
        full_log_path (str): full path to the client log file
    """
    session_log_path = os.path.join(logs_folder, session)
    full_log_path = os.path.join(session_log_path, f"{client_name}.log")

    return session_log_path, full_log_path
