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

# INFO
__version__ = "0.1"

# CONSTANTS
PACKAGE_INFO_FILE = "Package.json"

# VARIABLES


def print_help():
    """
    Prints some help information to the console screen
    """
    print("DotStar version " + __version__)


def open_file(file_path):
    """
    Opens a .star file
    """
    try:
        # Extract file to temporary directory
        temp_dir = get_temporary_directory()
        decompress_file(file_path, temp_dir)

        # Process file
        package_info_file = os.path.join(temp_dir, PACKAGE_INFO_FILE)

        # If necessary, clean up the temporary directory
        
    except zipfile.BadZipFile:
        logging.critical("Bad zip file!")
    except FileNotFoundError:
        logging.critical("File doesn't exist!")


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
            print_help()
        else:
            open_file(argument)
