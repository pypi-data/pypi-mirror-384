import logging
import os
import importlib.util
import sys


def install_requirements(requirements_file: str, force: bool = False) -> bool:
    import subprocess

    if not os.path.exists(requirements_file):
        logging.warning(f"No requirements file found: '{requirements_file}'")
        return False

    cmd = [sys.executable,"-m", "pip", "install", "-r", requirements_file]
    if force:
        cmd.insert(4, "--force-reinstall")

    logging.info(f"Installing dependencies from '{requirements_file}'...")

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        logging.info(line.strip())

    return_code = process.wait()
    if return_code != 0:
        logging.error(f"pip install failed with exit code {return_code}")
        raise subprocess.CalledProcessError(return_code, cmd)

    logging.info(f"Dependencies from '{requirements_file}' installed successfully!")
    return True


def install_pyproject_dependencies(pyproject_file: str, force: bool = False) -> bool:
    """
    Install dependencies from pyproject.toml file.
    This will install the project in editable mode which includes all dependencies.
    """
    import subprocess
    import os

    if not os.path.exists(pyproject_file):
        logging.warning(f"No pyproject.toml file found: '{pyproject_file}'")
        return False

    # Get the directory containing pyproject.toml
    project_dir = os.path.dirname(pyproject_file)
    
    # Install the project in editable mode, which will install all dependencies
    cmd = [sys.executable, "-m", "pip", "install", "-e", project_dir]
    if force:
        cmd.insert(4, "--force-reinstall")

    logging.info(f"Installing dependencies from pyproject.toml in '{project_dir}'...")

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        logging.info(line.strip())

    return_code = process.wait()
    if return_code != 0:
        logging.error(f"pip install failed with exit code {return_code}")
        raise subprocess.CalledProcessError(return_code, cmd)

    logging.info(f"Dependencies from pyproject.toml in '{project_dir}' installed successfully!")
    return True


def is_installed(import_name: str) -> bool:
    """
    Check if a module is installed. Use the import name NOT the PyPi package name.
    :param import_name:
    :return:
    """
    data= importlib.util.find_spec(import_name) is not None
    logging.info(f"is_installed : {data} for {import_name}")
    return data

