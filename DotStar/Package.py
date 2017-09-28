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

def install_package():
    """
    This function contains all necessary information for
    installing the package
    """
    print("Installing DotStar...")

def run_package():
    """
    Run DotStar
    """
    print("Running DotStar...")

def compile_package():
    """
    Compile DotStar
    """
    print("Compiling DotStar...")
    os.system("pyinstaller DotStar/DotStar.py")
    os.system("%PYTHON%\\Scripts\\pyinstaller.exe DotStar\\DotStar.py")
    print("Creating Windows binaries")
    os.system("%PYTHON%\\python.exe -m py2exe.build_exe DotStar\\DotStar.py")
    print("Creating Linux binaries")
    print("Creating macOS binaries")
    print("Creating installers")
    print("Finished compiling DotStar")

action = sys.argv[1]
if action == "install":
    install_package()
elif action == "run":
    run_package()
elif action == "compile":
    compile_package()
