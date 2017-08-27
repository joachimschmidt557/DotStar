"""
This main module contains the core of DotStar
"""

# IMPORTS
import sys
import os
import random
import tempfile
import zipfile
import logging
import json
import shutil
import platform
import subprocess
from distutils.version import StrictVersion

# INFO
__version__ = "0.1"

# CONSTANTS
PACKAGE_INFO_FILE = "Package.json"
CURRENT_PLATFORM = sys.platform
CURRENT_VERSION = StrictVersion(__version__)

# VARIABLES


def print_help():
    """
    Prints some help information to the console screen
    """
    print("DotStar version " + __version__)
    print("Command-line arguments: ")
    print("-h\t--help\tShow this help page")
    print("-n\t--no-gui\tStart without a GUI")


def open_file(file_path, run=False):
    """
    Opens a .star file
    """
    try:
        # Extract file to temporary directory
        temp_dir = get_temporary_directory()
        decompress_file(file_path, temp_dir)

        # Process file
        package_info_file = os.path.join(temp_dir, PACKAGE_INFO_FILE)
        try:
            with open(package_info_file) as package_info_json:
                data = json.load(package_info_json)

                # Check the "DotStar Information area"
                version_used_to_compile = StrictVersion(data["DotStar Information"]["Version"])
                if CURRENT_VERSION < version_used_to_compile:
                    pass

                # Check the type
                if "Application Information" in data:
                    info = data["Application Information"]
                    resources = info["Resources"]
                    for resource in resources:
                        if resource == "html":
                            print("hey")
                        if resource == "executable-win32":
                            if CURRENT_PLATFORM == "win32":
                                path_to_exe = os.path.join(temp_dir, resources[resource])
                                subprocess.run(path_to_exe)
                        if resource == "executable-win64":
                            pass
                        if resource == "executable":
                            pass
                elif "Document Information" in data:
                    info = data["Document Information"]
                    resources = info["Resources"]
                    for resource in resources:
                        pass
                else:
                    # Empty file
                    pass
        except FileNotFoundError:
            raise FileNotFoundError
        except json.JSONDecodeError:
            logging.critical("Error decoding JSON")

        # If necessary, clean up the temporary directory
        shutil.rmtree(temp_dir)
    except zipfile.BadZipFile:
        logging.critical("Bad zip file!")
    except FileNotFoundError:
        logging.critical("File doesn't exist!")


def compile_file(file_path):
    """
    Compile the specified .star file with all it's resources into a new .star file
    """
    raise NotImplementedError


def decompress_file(file_path, extract_path):
    """
    Decompresses a .star file to the path specified
    """
    with zipfile.ZipFile(file_path, "r") as z:
        z.extractall(extract_path)

def get_temporary_directory():
    """
    Returns a temporary directory path that is guaranteed to not
    yet exist
    """
    directory = os.path.join(tempfile.gettempdir(),
                             "DotStar",
                             str(random.randint(0, 10000)))
    while os.path.exists(directory):
        directory = os.path.join(tempfile.gettempdir(),
                                 "DotStar",
                                 str(random.randint(0, 10000)))
    return directory

if __name__ == "__main__":
    # Main code goes here
    # Get command-line arguments
    args = sys.argv

    # Remove first argument as this is just the path to this file
    del args[0]

    # Iterate through arguments
    for argument in args:
        if argument == "-h" or argument == "--help":
            # Print help page
            print_help()
        elif argument == "-n" or argument == "--no-gui":
            # Don't use GUI
            pass
        elif argument.endswith("Compile.star"):
            # The following file is a set of compilation instructions
            compile_file(argument)
        elif argument.endswith("Run.star"):
            # The following file is a program which starts directly
            open_file(argument, True)
        else:
            open_file(argument)
