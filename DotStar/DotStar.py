"""
This main module contains the core of DotStar
"""

# IMPORTS
import sys
import os
import random
import tempfile
import zipfile
import zlib
import logging
import json
import shutil
import platform
import subprocess
from distutils.version import StrictVersion
import argparse

# INFO
__version__ = "0.1"

# CONSTANTS
PACKAGE_INFO_FILE = "Package.json"
SETTINGS_FILE = "DotStarSettings.json"

CURRENT_PLATFORM = sys.platform
CURRENT_VERSION = StrictVersion(__version__)
DEFAULT_SETTINGS = {
    "Security":
    {
        "Allow non-local sources": True,
        "Allow unsigned files": True,
        "Allow downloading non-.star files": True
    },
    "Logging":
    {
        "Level": "info"
    }
}

# VARIABLES
settings = None

def load_settings():
    """
    Loads the user-defined settings. If these don't
    exist, loads the default settings.
    """
    global settings
    try:
        settings_file = SETTINGS_FILE
        with open(settings_file) as settings_json:
            settings = json.load(settings_json)
    except:
        logging.info("Using default settings")
        settings = DEFAULT_SETTINGS

def save_settings():
    """
    Save the settings into the Settings JSON file.
    """
    global settings
    try:
        settings_file = SETTINGS_FILE
        with open(settings_file, 'w') as settings_json:
            json.dump(settings, settings_json)
    except:
        logging.error("Couldn't update settings")

def print_help():
    """
    Prints some help information to the console screen
    """
    print("DotStar version " + __version__)
    print("Command-line arguments: ")
    print("-h\t--help\tShow this help page")
    print("-n\t--no-gui\tStart without a GUI")


def open_file(file_path, run=False, install=False):
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
                    # This file was created with a newer version of DotStar
                    # So, this version may be out-of-date
                    pass

                # Check the integrity area
                if "Integrity Information" in data:
                    pass

                # Check the type
                if "Application Information" in data:
                    info = data["Application Information"]
                    resources = info["Resources"]
                    commands = info["Commands"]

                    # Check our specified action
                    if run:
                        # Run the app
                        os.system('python Package.py run')
                    elif install:
                        # Install the app
                        os.system('python Package.py install')
                elif "Document Information" in data:
                    info = data["Document Information"]
                    resources = info["Resources"]
                    for resource in resources:
                        pass
                elif "Folder Information" in data:
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
    try:
        # Create temporary folder to store the files into
        temp_dir = get_temporary_directory()
        output_file = ""

        # Read the file into JSON
        with open(file_path) as compilation_info_json:
            data = json.load(compilation_info_json)

            # Create Package.json
            # Create DotStar information area
            dotstar_information = {
                "Version": str(__version__)
            }


            # Copy the files into the folder

        # Zip the folder
        compress_folder(temp_dir, output_file)

        # Finish
        shutil.rmtree(temp_dir)
    except FileNotFoundError:
        logging.critical("File doesn't exist")
    except json.JSONDecodeError:
        logging.critical("Bad JSON")

def decompress_file(file_path, extract_path):
    """
    Decompresses a .star file to the path specified
    """
    with zipfile.ZipFile(file_path, "r") as z:
        z.extractall(extract_path)

def compress_folder(folder_path, zipfile_path):
    """
    Compress a folder into a .star file
    """
    dir_to_zip_len = len(folder_path.rstrip(os.sep)) + 1
    with zipfile.ZipFile(zipfile_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # Iterate over all files
        for (dirpath, dirnames, filenames) in os.walk(folder_path):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                entry = path[dir_to_zip_len:]
                z.write(path, entry)

def get_temporary_directory(in_folder_path=os.path.join(tempfile.gettempdir(),
                                                        "DotStar")):
    """
    Returns a temporary directory path that is guaranteed to not
    yet exist
    """
    directory = os.path.join(in_folder_path,
                             str(random.randint(0, 10000)))
    while os.path.exists(directory):
        directory = os.path.join(in_folder_path,
                                 str(random.randint(0, 10000)))
    return directory

if __name__ == "__main__":
    # Main code goes here
    # Load settings
    load_settings()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog="DotStar",
                                     description="DotStar application version "+__version__)

    parser.add_argument("-l", "--log-level", choices=["debug", "info", "warning", "error"],
                        default="warning", help="Change the logging level")
    #parser.add_argument("-n", "--no-gui", action="store_true", help="Don't show a GUI")
    parser.add_argument("-v", "--verify", action="store_true", help="Verify the file")
    parser.add_argument("-i", "--install", action="store_true", help="Install the file")
    parser.add_argument("-r", "--run", action="store_true", help="Run the file")
    parser.add_argument("files", nargs='+', help="Input files")

    result = parser.parse_args()

    # Set up logging
    logging_level = settings["Logging"]["Level"]
    logging_level = result.log_level

    if logging_level == "debug":
        logging.basicConfig(level=logging.DEBUG)
    elif logging_level == "info":
        logging.basicConfig(level=logging.INFO)
    elif logging_level == "warning":
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.CRITICAL)

    for input_file in result.files:
        # Special file names
        if input_file.endswith("Compile.star"):
            compile_file(input_file)
        elif input_file.endswith("Run.star"):
            open_file(input_file, run=True)
        else:
            if result.verify:
                #Verify the file
                pass
            elif result.run:
                #Run the file
                open_file(input_file, run=True)
            elif result.install:
                #Install the file
                pass
            else:
                #Open the file
                open_file(input_file)
