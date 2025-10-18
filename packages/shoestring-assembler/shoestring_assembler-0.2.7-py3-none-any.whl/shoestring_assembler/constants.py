import os
from pathlib import Path

class Constants:
    SHOESTRING_SHARE = Path(os.getenv("HOME"))/".local/share/shoestring/"
    INSTALLED_SOLUTIONS_LIST = SHOESTRING_SHARE / "installed.json"
    CONSOLE_LOG = SHOESTRING_SHARE / "console_log.html"
    DOCKER_NETWORK_NAME = "internal"

    META_FILE_NAME = "meta.toml"
    DOCKER_ALIAS_SUFFIX = ".docker.local"

    # TODO
    DEFAULT_GIT_HOST = ""
    DEFAULT_GIT_REPO = ""
