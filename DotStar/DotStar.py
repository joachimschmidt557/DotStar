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
import re
import requests
import hashlib

# INFO
__version__ = "0.1"

# CONSTANTS
PACKAGE_INFO_FILE = "Package.json"
PACKAGE_FILE = "Package.py"
SETTINGS_FILE = "DotStarSettings.star"
FILE_CACHE_DIRECTORY = "Packages"
INSTALLED_FILES_DIRECTORY = "Installed"
REPO_DIRECTORY = "Repositories"

CURRENT_PLATFORM = sys.platform
CURRENT_VERSION = StrictVersion(__version__)
DEFAULT_SETTINGS = {
    "Repositories":
    [
        "https://raw.githubusercontent.com/joachimschmidt557/DotStarRepo/master/Master.json"
    ],
    "Security":
    {
        "Allow non-local sources": True,
        "Allow unsigned files": True,
        "Allow downloading non-.star files": True
    },
    "Logging":
    {
        "Level": "debug"
    }
}

# VARIABLES
settings = None
yes_to_all = False

def load_settings(settings_file=SETTINGS_FILE):
    """
    Loads the user-defined settings. If these don't
    exist, loads the default settings.
    """
    global settings
    try:
        with open(settings_file) as settings_json:
            settings = json.load(settings_json)
    except:
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

def user_consent(message):
    """
    Returns whether the user agrees to the message
    """
    if yes_to_all:
        return True
    user_input = input(message)
    while not (user_input == '' or
               user_input == 'y' or
               user_input == 'Y' or
               user_input == 'n' or
               user_input == 'N'):
        user_input = input("Please provide a correct option")
    if user_input == '' or user_input == 'y' or user_input == 'Y':
        return True
    return False

def open_file(file_path, run=False, install=False):
    """
    Opens a .star file
    """
    try:
        # Extract file to temporary directory
        temp_dir = get_temporary_directory()
        logging.debug("Extracting file to temporary directory " + temp_dir)
        decompress_file(file_path, temp_dir)

        # Process file
        package_info_file = os.path.join(temp_dir, PACKAGE_INFO_FILE)
        package_file = os.path.join(temp_dir, PACKAGE_FILE)
        try:
            with open(package_info_file) as package_info_json:
                data = json.load(package_info_json)

                # Check the "DotStar Information area"
                version_used_to_compile = StrictVersion(data["DotStar Information"]["Version"])
                if CURRENT_VERSION < version_used_to_compile:
                    # This file was created with a newer version of DotStar
                    # So, this version may be out-of-date
                    logging.warning("""Your DotStar version may be out-of-date. This file
                                    was created using a newer version of DotStar.""")

                # Check the integrity area
                if "Integrity Information" in data:
                    if "Hashes" in data["Integrity Information"]:
                        # Calculate hashes

                        # Compare and abort if necessary
                        pass

                # Check the dependencies area
                if "Dependency Information" in data:
                    for dependency in data["Dependencies"]:
                        logging.debug("This file depends on " + dependency["Name"])
                        # Check if the dependecy is installed

                        # Install dependency
                        open_file(dependency["File"], install=True)

                # Check the type
                if "Application Information" in data:
                    # Type: Application package
                    info = data["Application Information"]
                    #resources = info["Resources"]
                    #commands = info["Commands"]

                    # Check our specified action
                    if run:
                        # Run the app
                        if user_consent("Run the File? (y/n): "):
                            os.system("python " + package_file + " run")
                    elif install:
                        # Install the app
                        # Copy the package to the installation directory
                        installation_dir = os.path.join(FILE_CACHE_DIRECTORY, INSTALLED_FILES_DIRECTORY)
                        os.makedirs(installation_dir)
                        shutil.copy(file_path, installation_dir)

                        # Additional installation steps
                        if user_consent("Run the python script for additional installation steps? (y/n): "):
                            os.system("python " + package_file + " install")
                    else:
                        # If no action is specified, let the user decide
                        print(info["Friendly Name"])
                        print("Version " + info["Version"])
                        print("Possible actions: ")

                elif "Document Information" in data:
                    # Type: Document package
                    info = data["Document Information"]
                    resources = info["Resources"]
                    for resource in resources:
                        pass
                elif "Folder Information" in data:
                    # Type: Folder package
                    pass
                else:
                    # Empty file
                    logging.warning("This file is an empty file.")
        except FileNotFoundError:
            raise FileNotFoundError
        except json.JSONDecodeError:
            logging.critical("Error decoding JSON")

        # If necessary, clean up the temporary directory
        shutil.rmtree(temp_dir)
        logging.debug("Removed temporary directory " + temp_dir)
    except zipfile.BadZipFile:
        logging.critical("Bad zip file!")
    except FileNotFoundError:
        logging.critical("File doesn't exist!")


def compile_file(file_path):
    """
    Compile the specified .star file with all it's resources into a new .star file
    """
    logging.info("Attempting to compile " + file_path)
    try:
        # Create temporary folder to store the files into
        temp_dir = get_temporary_directory(create_directory=False)
        output_file = ""

        # Copy the necessary files into the folder
        shutil.copytree(os.path.dirname(file_path), temp_dir)

        # Read the file into JSON
        with open(file_path) as compilation_info_json:
            other_data = json.load(compilation_info_json)

            # Get the output file name
            output_file = os.path.join(os.getcwd(), other_data["Application Information"]["Name"] + ".star")

            # Create Package.json
            package_json_file = os.path.join(temp_dir, PACKAGE_INFO_FILE)

            # Create DotStar information area
            data = {
                "DotStar Information":
                {
                    "Version": str(__version__)
                }
            }
            # Append the other data to our DotStar info area
            data.update(other_data)

            # Write to Package.json
            with open(package_json_file, 'w') as package_file:
                json.dump(data, package_file)

            # Run the python script for additional compilation steps
            script_file = os.path.join(temp_dir, PACKAGE_FILE)
            if user_consent("Run compilation script? (y/n): "):
                os.system("python " + script_file + " compile")

        # Zip the folder
        compress_folder(temp_dir, output_file)
        logging.info("Compiled package: " + output_file)

        # Finish and clean up
        shutil.rmtree(temp_dir)
    except FileNotFoundError as err:
        logging.critical("File doesn't exist " + str(err))
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

def is_url(path):
    """
    Returns whether path is a URL
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(regex.match(path))

def download_file(url, folder_path):
    """
    Downloads a .star file and returns the file path
    of the downloaded file
    """
    logging.info("Downloading " + url)
    file_path = os.path.join(folder_path, "Temp.star")
    r = requests.get(url)
    with open(file_path, "wb") as dotstarfile:
        dotstarfile.write(r.content)
    return file_path

def refresh_local_repo():
    """
    Downloads all repository data, thus refreshing
    all programs
    """
    if not os.path.exists(REPO_DIRECTORY):
        os.makedirs(REPO_DIRECTORY)
    for repository in settings["Repositories"]:
        # Download file
        download_file(repository, REPO_DIRECTORY)
    logging.info("Repositories refreshed successfully")

def list_all_repos():
    """
    Lists all repos
    """
    return settings["Repositories"]

def add_repo(url):
    """
    Adds a repository to the repo list
    """
    if not is_url(url):
        logging.critical(url + " is not a respository URL.")
    settings["Repositories"] += url
    logging.info("Repository " + url + " added to the list!")

def remove_repo(id_number):
    """
    Removes a repository at the given id
    """

def search_repos_for_files(file_name):
    """
    Searches the repos in the given settings for
    the specified file (without .star)
    """
    global_repo_data = {}
    # Get all files in the repository directory
    for (dirpath, dirnames, filenames) in os.walk(REPO_DIRECTORY):
        for filename in filenames:
            with open(filename) as repo_json:
                global_repo_data.update(json.load(repo_json))
    return filter(lambda item: item["Name"] == file_name, global_repo_data)

def list_all_repo_files():
    """
    Returns all files in the repos
    """
    print("Following packages are available: ")
    all_repo_files = []
    # Check if repository directory exists
    if not os.path.exists(REPO_DIRECTORY):
        return []
    # Get all files in the repository directory
    onlyfiles = [f for f in os.listdir(REPO_DIRECTORY) if os.path.isfile(os.path.join(REPO_DIRECTORY, f))]
    for filename in onlyfiles:
        with open(os.path.join(REPO_DIRECTORY, filename)) as repo_json:
            all_repo_files += json.load(repo_json)["Packages"]
    return all_repo_files

def list_installed_files():
    """
    Lists all installed files
    """
    installation_dir = os.path.join(FILE_CACHE_DIRECTORY, INSTALLED_FILES_DIRECTORY)
    os.makedirs(installation_dir)

def search_installed_files(file_name):
    """
    Searches the installed .star files for matching
    files
    """
    output = []
    raise NotImplementedError

def get_temporary_directory(in_folder_path=os.path.join(tempfile.gettempdir(),
                                                        "DotStar"),
                            create_directory=True):
    """
    Returns a temporary directory path that is guaranteed to not
    yet exist
    """
    directory = os.path.join(in_folder_path,
                             str(random.randint(0, 10000)))
    while os.path.exists(directory):
        directory = os.path.join(in_folder_path,
                                 str(random.randint(0, 10000)))
    if create_directory:
        os.makedirs(directory)
    return directory

if __name__ == "__main__":
    # Main code goes here
    # Load settings
    load_settings()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(prog="DotStar",
                                     description="DotStar application version "+__version__)

    parser.add_argument("-l", "--log-level", choices=["debug", "info", "warning", "error"],
                        default="debug", help="Change the logging level")
    parser.add_argument("-y", "--yestoall", action="store_true", help="Automattically allow all actions")

    # General flags
    parser.add_argument("-s", "--search", action="store_true", help="Search all available files")
    parser.add_argument("-o", "--lock", action="store_true", help="Prevent modifying or removing the installed file")

    # Repository flags
    parser.add_argument("-a", "--add-repo", action="store_true", help="Adds a repository")
    parser.add_argument("-x", "--remove-repo", action="store_true", help="Removes a repository")

    # File-specific flags
    parser.add_argument("-v", "--verify", action="store_true", help="Verify the file")
    parser.add_argument("-i", "--install", action="store_true", help="Install the file")
    parser.add_argument("-u", "--uninstall", action="store_true", help="Uninstall the file")
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

    # Yes to all ?
    yes_to_all = result.yestoall

    # Go though input files
    for input_file in result.files:
        # Special file names
        logging.info("Processing file " + input_file)
        if input_file == "refresh":
            refresh_local_repo()
        elif input_file == "listall":
            for item in list_all_repo_files():
                print(item["Name"])
        elif input_file == "listinstalled":
            for item in list_all_repo_files():
                print(item["Name"])
        elif input_file.endswith("DotStarSettings.star"):
            load_settings(input_file)
            save_settings()
        elif input_file.endswith("Compile.star"):
            compile_file(input_file)
        elif input_file.endswith("Run.star"):
            if is_url(input_file):
                open_file(download_file(input_file, get_temporary_directory()), run=True)
            else:
                open_file(input_file, run=True)
        # Normal DotStar files
        else:
            if result.verify:
                #Verify the file
                pass
            elif result.run:
                #Run the file
                if is_url(input_file):
                    open_file(download_file(input_file, get_temporary_directory()), run=True)
                else:
                    open_file(input_file, run=True)
            elif result.install:
                #Install the file
                if is_url(input_file):
                    open_file(download_file(input_file, get_temporary_directory()), install=True)
                else:
                    open_file(input_file, install=True)
            else:
                #Open the file
                if is_url(input_file):
                    open_file(download_file(input_file, get_temporary_directory()))
                else:
                    open_file(input_file)

    # Finished, now clean up
    logging.shutdown()
