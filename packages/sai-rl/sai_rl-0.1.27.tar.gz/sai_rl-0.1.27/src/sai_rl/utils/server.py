import os


def get_is_server():
    return os.environ.get("SAI_SERVER", "false") == "true"
