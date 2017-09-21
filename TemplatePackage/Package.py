"""
The Package.py file contains all necessary information for
handling this package.

This python script will be called by DotStar when the user
decides to install, run or do something with the package.

Possible command-line arguments are:
    - "install"
    - "run"
    - "open"
"""

import sys

action = sys.argv[0]
if action == "install":
    install_package()

def install_package():
    """
    This function contains all necessary information for
    installing the package
    """
    pass
