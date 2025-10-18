import subprocess
import os
from typing import List
from prefect import get_run_logger
logger = get_run_logger()

def run_standalone_script(package_name, package_run, package_exec):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # script_path = os.path.join(script_dir, package_name.replace('.', os.sep))
    target_dir = os.path.join(script_dir, os.pardir, os.pardir, *package_name.split('.'))

    full_command = f"{package_run} {os.path.join(target_dir, package_exec)}"

    # Execute the command
    try:
        result = subprocess.run(full_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
        # logger.info(f"Output: {result.stdout}")
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        # All logs should have already been handled above, now just raise an exception
        logger.error("The subprocess encountered an error: %s", e)
        raise Exception("Subprocess failed with exit code {}".format(e.returncode))
    

def run_standalone_script_modified(base_path: str, package_name: str, package_run_cmds: List[str]):
    # Construct the absolute path to the target directory
    target_dir = os.path.join(base_path, *package_name.split('.'))

    commands = [f"cd {target_dir}"] + package_run_cmds
    full_command = " && ".join(commands)

    # full_command = f"cd {target_dir} && {package_run_cmd}"

    # Build the full command to execute
    # full_command = f"{package_run} {os.path.join(target_dir, package_exec)}"

    # print(full_command)

    # Execute the command
    try:
        result = subprocess.run(full_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        logger.error("Command failed with exit code %s", e.returncode)
        logger.error("Output:\n%s", e.stdout)
        logger.error("Errors:\n%s", e.stderr)
        raise Exception(f"Subprocess failed with exit code {e.returncode}. Check logs for more details.")
        # raise Exception(f"Subprocess failed with exit code {e.returncode}")