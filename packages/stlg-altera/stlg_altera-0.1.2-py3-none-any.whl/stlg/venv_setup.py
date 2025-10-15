#!/usr/intel/bin/python3

import subprocess
import sys
import os
import urllib.request

def create_virtualenv(env_name='venv'):
    """
    Create a Python virtual environment with the specified name.

    Args:
        env_name (str): The name/path of the virtual environment directory.
    """
    subprocess.check_call([sys.executable, "-m", "venv", env_name])

def activate_virtualenv(env_name='venv'):
    """
    Get the path to the Python executable within the virtual environment.

    Args:
        env_name (str): The name/path of the virtual environment directory.

    Returns:
        str: Path to the virtual environment's Python interpreter.
    """
    if os.name == 'nt':
        # Windows path
        return os.path.join(env_name, 'Scripts', 'python.exe')
    else:
        # Unix/Linux path
        return os.path.join(env_name, 'bin', 'python')

def ensure_pip_installed(python_exec):
    """
    Ensure that pip is installed in the specified Python environment.
    If not present, download and install pip using get-pip.py.

    Args:
        python_exec (str): Path to the Python executable.
    """
    try:
        subprocess.check_call([python_exec, "-m", "pip", "--version"], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("pip not found. Installing pip using get-pip.py...")
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = "get-pip.py"
        urllib.request.urlretrieve(get_pip_url, get_pip_path)
        subprocess.check_call([python_exec, get_pip_path], stdout=subprocess.DEVNULL)
        print("pip installed successfully.")

def install_requirements(python_exec, proxy_url='http://proxy-dmz.intel.com:911/'):
    """
    Install pip (if necessary), upgrade pip, and install all required packages
    from requirements.txt using the specified proxy.

    Args:
        python_exec (str): Path to the Python executable.
        proxy_url (str): Proxy URL for internet access.
    """
    ensure_pip_installed(python_exec)
    # Upgrade pip using the specified proxy
    subprocess.check_call([python_exec, "-m", "pip", "install", "--upgrade", "pip", "--proxy", proxy_url], stdout=subprocess.DEVNULL)
    # Install required packages from requirements.txt
    subprocess.check_call([python_exec, "-m", "pip", "install", "-r", "/nfs/site/disks/swuser_work_sgundeti/STLG/requirements.txt", "--proxy", proxy_url], stdout=subprocess.DEVNULL)

def setup_venv(env_name='venv', proxy_url='http://proxy-dmz.intel.com:911/'):
    """
    Create and configure a virtual environment, installing all required dependencies.

    Args:
        env_name (str): Name/path for the virtual environment.
        proxy_url (str): Proxy URL for internet access.

    Returns:
        str: Path to the Python interpreter in the new virtual environment.
    """
    create_virtualenv(env_name)
    python_exec = activate_virtualenv(env_name)
    install_requirements(python_exec, proxy_url)
    return python_exec
