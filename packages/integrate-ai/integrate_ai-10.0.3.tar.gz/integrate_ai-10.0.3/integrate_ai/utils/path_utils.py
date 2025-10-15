
# Copyright (C) Integrate.ai, Inc. All rights reserved.

import os


def get_mounted_path(mount_path, path):
    if path.get("s3"):
        # No mount, pass the URL as is
        mounted_path = path["url"]
    else:
        mounted_path = path["full_path"].replace(path["parent_path"], mount_path + path["parent_dir"])
    return mounted_path


def get_volumes(mount_path, path):
    volumes = {}
    if not path.get("s3"):
        volumes[path["parent_path"]] = {
            "bind": mount_path + path["parent_dir"],
            "mode": "ro",
        }
    return volumes


def get_aws_env(path):
    if path.get("s3"):
        return {
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "AWS_SESSION_TOKEN": os.getenv("AWS_SESSION_TOKEN"),
            "AWS_REGION": os.getenv("AWS_REGION"),
        }
    return {}
