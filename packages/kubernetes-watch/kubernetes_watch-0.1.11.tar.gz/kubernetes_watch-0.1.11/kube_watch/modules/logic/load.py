import os
from prefect import get_run_logger
logger = get_run_logger()

def load_secrets_to_env(data):
    for key, value in data.items():
        if key in os.environ:
            del os.environ[key]
        os.environ[key] = value
        # logger.info(f"ENV VAR: {key} loaded")

def load_env_from_file(filepath):
    with open(filepath, "r") as f:
        for line in f:
            # Remove whitespace and ignore comments
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                # Remove the environment variable if it already exists
                if key in os.environ:
                    del os.environ[key]
                # Set the new value
                os.environ[key] = value
