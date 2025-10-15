"""
Configuration settings and environment variables for the application.
"""

import logging
import sys
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from aixtools.utils.config_util import find_env_file, get_project_root, get_variable_env
from aixtools.utils.utils import str2bool

# Debug mode
LOG_LEVEL = logging.DEBUG

# Set up some environment variables (there are usually set up by 'config.sh')

# This file's path
FILE_PATH = Path(__file__).resolve()

# This project's root directory (AixTools)
# if installed as a package, it will be `.venv/lib/python3.x/site-packages/aixtools`
PROJECT_DIR = FILE_PATH.parent.parent.parent.resolve()

# Get the main project directory (the one project that is using this package)
PROJECT_ROOT = get_project_root()

# From the environment variables


# Iterate over all parents of FILE_PATH to find .env files
def all_parents(path: Path):
    """Yield all parent directories of a given path."""
    while path.parent != path:
        yield path
        path = path.parent


# Set up environment search path
# Start with the most specific (current directory) and expand outward
env_dirs = [Path.cwd(), PROJECT_ROOT, FILE_PATH.parent]
env_file = find_env_file(env_dirs)

if env_file:
    logging.info("Using .env file at '%s'", env_file)
    # Load the environment variables from the found .env file
    load_dotenv(env_file)
    # Assign project dir based on the .env file
    MAIN_PROJECT_DIR = Path(env_file).parent
    logging.info("Using MAIN_PROJECT_DIR='%s'", MAIN_PROJECT_DIR)
    # Assign variables in '.env' global python environment
    env_vars = dotenv_values(env_file)
    globals().update(env_vars)
else:
    logging.error("No '.env' file found in any of the search paths, or their parents: %s", env_dirs)
    sys.exit(1)

# ---
# Directories
# ---
SCRIPTS_DIR = MAIN_PROJECT_DIR / "scripts"
DATA_DIR = Path(get_variable_env("DATA_DIR") or MAIN_PROJECT_DIR / "data")
DATA_DB_DIR = Path(get_variable_env("DATA_DB_DIR", default=DATA_DIR / "db"))
LOGS_DIR = MAIN_PROJECT_DIR / "logs"

logging.warning("Using         DATA_DIR='%s'", DATA_DIR)

# Vector database
VDB_CHROMA_PATH = DATA_DB_DIR / "chroma.db"
VDB_DEFAULT_SIMILARITY_THRESHOLD = 0.85

# ---
# Variables in '.env' file
# Explicitly load specific variables
# ---

MODEL_TIMEOUT = int(get_variable_env("MODEL_TIMEOUT", default="120"))  # type: ignore

MODEL_FAMILY = get_variable_env("MODEL_FAMILY")

# Azure models
AZURE_MODEL_NAME = get_variable_env("AZURE_MODEL_NAME")
AZURE_OPENAI_ENDPOINT = get_variable_env("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = get_variable_env("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = get_variable_env("AZURE_OPENAI_API_VERSION")

# OpenAI models
OPENAI_API_KEY = get_variable_env("OPENAI_API_KEY")
OPENAI_MODEL_NAME = get_variable_env("OPENAI_MODEL_NAME")

# Ollama models
OLLAMA_URL = get_variable_env("OLLAMA_URL")
OLLAMA_MODEL_NAME = get_variable_env("OLLAMA_MODEL_NAME")

# OpenRouter models
OPENROUTER_API_KEY = get_variable_env("OPENROUTER_API_KEY")
OPENROUTER_API_URL = get_variable_env("OPENROUTER_API_URL", default="https://openrouter.ai/api/v1")
OPENROUTER_MODEL_NAME = get_variable_env("OPENROUTER_MODEL_NAME")

# Embeddings
VDB_EMBEDDINGS_MODEL_FAMILY = get_variable_env("VDB_EMBEDDINGS_MODEL_FAMILY")
OPENAI_VDB_EMBEDDINGS_MODEL_NAME = get_variable_env("OPENAI_VDB_EMBEDDINGS_MODEL_NAME")
AZURE_VDB_EMBEDDINGS_MODEL_NAME = get_variable_env("AZURE_VDB_EMBEDDINGS_MODEL_NAME")
OLLAMA_VDB_EMBEDDINGS_MODEL_NAME = get_variable_env("OLLAMA_VDB_EMBEDDINGS_MODEL_NAME")

# Bedrock models
AWS_ACCESS_KEY_ID = get_variable_env("AWS_ACCESS_KEY_ID", allow_empty=True)
AWS_SECRET_ACCESS_KEY = get_variable_env("AWS_SECRET_ACCESS_KEY", allow_empty=True)
AWS_SESSION_TOKEN = get_variable_env("AWS_SESSION_TOKEN", allow_empty=True)
AWS_REGION = get_variable_env("AWS_REGION", allow_empty=True, default="us-east-1")
AWS_PROFILE = get_variable_env("AWS_PROFILE", allow_empty=True)
BEDROCK_MODEL_NAME = get_variable_env("BEDROCK_MODEL_NAME", allow_empty=True)

# LogFire
LOGFIRE_TOKEN = get_variable_env("LOGFIRE_TOKEN", True, "")
LOGFIRE_TRACES_ENDPOINT = get_variable_env("LOGFIRE_TRACES_ENDPOINT", True, "")

# Google Vertex AI
GOOGLE_GENAI_USE_VERTEXAI = str2bool(get_variable_env("GOOGLE_GENAI_USE_VERTEXAI", True, True))
GOOGLE_CLOUD_PROJECT = get_variable_env("GOOGLE_CLOUD_PROJECT", True)
GOOGLE_CLOUD_LOCATION = get_variable_env("GOOGLE_CLOUD_LOCATION", True)

# vault parameters.
VAULT_ADDRESS = get_variable_env("VAULT_ADDRESS", default="http://localhost:8200")
VAULT_TOKEN = get_variable_env("VAULT_TOKEN", allow_empty=True)
VAULT_ENV = get_variable_env("ENV", allow_empty=True)
VAULT_MOUNT_POINT = get_variable_env("VAULT_MOUNT_POINT", allow_empty=True)
VAULT_PATH_PREFIX = get_variable_env("VAULT_PATH_PREFIX", allow_empty=True)

# OAuth parameters
APP_SECRET_ID = get_variable_env("APP_SECRET_ID")
APP_CLIENT_ID = get_variable_env("APP_CLIENT_ID")

# used for token audience check
APP_API_ID = get_variable_env("APP_API_ID")
APP_TENANT_ID = get_variable_env("APP_TENANT_ID")

# used for token authorization check
APP_AUTHORIZED_GROUPS = get_variable_env("APP_AUTHORIZED_GROUPS", allow_empty=True)
