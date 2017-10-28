"""
The Package.py file contains all necessary information for
handling this package.

This python script will be called by DotStar when the user
decides to install, run or do something with the package.

Possible command-line arguments are:
    - "install"
        - "win.install"
    - "run"
        - "win.run"
    - "open"
    - "compile"
"""

import sys
import os
import shutil

def install_package():
    """
    This function contains all necessary information for
    installing the package
    """
    print("Installing DotStar...")
    dest_dir = ""
    shutil.copytree(os.path.dirname(os.path.abspath(__file__)),
                    dest_dir)

def add_to_windows_path():
    old_path = os.environ['PATH']
    try:
        os.environ['PATH'] = "{}{}{}".format('/my/new/path', os.pathsep, old_path)
    finally:
        os.environ['PATH'] = old_path

def run_package():
    """
    Run DotStar
    """
    print("Running DotStar from the package is not possible.")
    print("Please install DotStar first using dotstar -i dotstar")

action = sys.argv[1]
if action == "install":
    install_package()
elif action == "run":
    run_package()
