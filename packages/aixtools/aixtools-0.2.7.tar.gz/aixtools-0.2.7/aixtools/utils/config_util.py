"""
Utility functions for configuration management and environment variables.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import find_dotenv


def get_project_root() -> Path:
    """
    Return the directory where the main script lives.
    Falls back to the current working directory if run interactively.
    """
    main_mod = sys.modules.get("__main__")
    main_file = getattr(main_mod, "__file__", None)
    if main_file:
        return Path(main_file).resolve().parent

    # no __file__ (e.g. interactive shell); assume cwd is the project root
    return Path.cwd()


def all_parents(path: Path):
    """Yield all parent directories of a given path."""
    while path.parent != path:
        yield path
        path = path.parent


def find_env_file(env_search_dirs: list[Path]):
    """Find the first .env file in the given list of paths and their parents."""
    env_file = find_dotenv()
    logging.warning("Looking for '.env' file in default directory")
    if env_file:
        return env_file
    # Find all parents of the paths
    for search_dir in env_search_dirs:
        # '.env' file in this directory?
        logging.warning("Looking for '.env' file at '%s'", search_dir)
        env_file = find_dotenv(str(search_dir / ".env"))
        if env_file:
            return env_file
        # Try all parents of this dir
        for parent_dir in all_parents(search_dir):
            logging.warning("Looking for '.env' file at '%s'", parent_dir)
            env_file = find_dotenv(str(parent_dir / ".env"))
            if env_file:
                return env_file
    return None


def get_variable_env(name: str, allow_empty=True, default=None) -> str | None:
    """Retrieve environment variable with optional validation and default value."""
    val = os.environ.get(name, default)
    if not allow_empty and ((val is None) or (val == "")):
        raise ValueError(f"Environment variable {name} is not set")
    return val


def set_variable_env(name: str, val: str) -> str:
    """Set environment variable and validate it's not None."""
    os.environ[name] = val
    if val is None:
        raise ValueError(f"Environment variable {name} is set to None")
    return val
