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
ACTIONS = [
    'r',    # Run the package
    'i',    # Install the package
    'u',    # Uninstall the package
    'v',    # Verify the package
    '0'     # Let the user decide
]
DEFAULT_SETTINGS = {
    "Repositories":
    [
        "https://raw.githubusercontent.com/joachimschmidt557/DotStarRepo/master/Master.json"
    ],
    "Security":
    {
        "Allow non-local sources": True,
        "Allow unsigned files": True,
        "Allow un-checksumed files": True,
        "Allow downloading non-.star files": True,
        "Always allow running scripts": False
    },
    "Logging":
    {
        "Level": "debug"
    },
    "Locked files":
    []
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

def open_file(path, action='0'):
    """
    Does whats necessary to process the file and
    afterwards opens it
    """
    logging.info("Processing file " + path)
    # Retrieve the file
    local_file_path = ""
    if os.path.isfile(path):
        local_file_path = path
    elif is_url(path):
        local_file_path = download_file(path, get_temporary_directory())
    elif not path.endswith(".star"):
        # Get file from repository
        logging.info("Searching repositories for " + path)
        available_files = search_repos_for_files(path)
        if len(available_files) < 1:
            logging.error("No package found in the repositories")
            return
        if len(available_files) > 1:
            pass
        else:
            local_file_path = download_file(available_files[0]["URL"], get_temporary_directory())

    # Special file names
    if local_file_path.endswith("DotStarSettings.star"):
        load_settings(local_file_path)
        save_settings()
    elif local_file_path.endswith("Compile.star"):
        compile_file(local_file_path)
    elif local_file_path.endswith("Run.star"):
        open_local_file(local_file_path, action='r')
    # Normal DotStar files
    else:
        open_local_file(local_file_path, action=action)

def open_local_file(file_path, action='0'):
    """
    Opens a .star file which is on the local hard-drive
    of the computer
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
                        open_local_file(dependency["File"], action='i')

                # Check the type
                if "Application Information" in data:
                    # Type: Application package
                    info = data["Application Information"]
                    #resources = info["Resources"]
                    #commands = info["Commands"]

                    # Check our specified action
                    if action == 'r':
                        # Run the app
                        if user_consent("Run the File? (y/n): "):
                            os.system("python " + package_file + " run")
                    elif action == 'i':
                        # Install the app
                        # Copy the package to the installation directory
                        installation_dir = os.path.join(FILE_CACHE_DIRECTORY, INSTALLED_FILES_DIRECTORY)
                        os.makedirs(installation_dir)
                        shutil.copy(file_path, installation_dir)

                        # Additional installation steps
                        if user_consent("Run the python script for additional installation steps? (y/n): "):
                            os.system("python " + package_file + " install")
                        logging.info("Installation successful")
                    elif action == 'u':
                        # Additional uninstallation steps
                        if user_consent("Run the python script for additional uninstalltion steps? (y/n): "):
                            os.system("python " + package_file + " uninstall")

                        # Delete the file
                        os.remove(file_path)
                        logging.info("Removed file")
                    else:
                        # If no action is specified, let the user decide
                        print(info["Friendly Name"])
                        print("Version " + info["Version"])
                        print(info["Description"])
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

def open_local_file_partially(file_path, file_name=PACKAGE_INFO_FILE):
    """
    Opens a local file and only extracts the given
    file name from the archive
    """
    try:
        # Extract file to temporary directory
        temp_dir = get_temporary_directory()
        logging.debug("Extracting file to temporary directory " + temp_dir)
    except zipfile.BadZipfile:
        pass

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

def download_file(url, folder_path, file_name="Temp.star"):
    """
    Downloads a .star file and returns the file path
    of the downloaded file
    """
    logging.info("Downloading " + url)
    file_path = os.path.join(folder_path, file_name)
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
    repo_id = 0
    for repository in settings["Repositories"]:
        # Download file
        download_file(repository, REPO_DIRECTORY, file_name="Repo" + str(repo_id) + ".star")
        repo_id += 1
    logging.info("Repositories refreshed successfully")

def clear_local_repo():
    """
    Clears the whole local repo
    """
    if not os.path.exists(REPO_DIRECTORY):
        os.makedirs(REPO_DIRECTORY)
        logging.info("Local repository is already empty")
        return
    shutil.rmtree(REPO_DIRECTORY)
    os.makedirs(REPO_DIRECTORY)
    logging.info("Local repository cleared")

def list_all_repos():
    """
    Lists all repositories
    """
    return settings["Repositories"]

def add_repo(url):
    """
    Adds a repository to the repo list
    """
    if not is_url(url):
        logging.critical(url + " is not a respository URL.")
        return
    settings["Repositories"].append(url)
    logging.info("Repository " + url + " added to the list!")

def remove_repo(id_number):
    """
    Removes a repository at the given id
    """
    try:
        del (settings["Repositories"])[int(id_number)]
        logging.info("Repository with id " + str(id_number) + " removed")
    except IndexError:
        logging.error("Repository with id " + str(id_number) + " doesn't exist")

def search_repos_for_files(file_name):
    """
    Searches the repos in the given settings for
    the specified file (without .star)
    """
    global_repo_data = list_all_repo_files()
    return list(filter(lambda item: item["Name"] == file_name, global_repo_data))

def list_all_repo_files():
    """
    Returns all files inside the repos
    """
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
    Returns a list with filenames (absoulte path) of
    installed files
    """
    installation_dir = os.path.join(FILE_CACHE_DIRECTORY, INSTALLED_FILES_DIRECTORY)
    if not os.path.exists(installation_dir):
        os.makedirs(installation_dir)
        logging.info("No files installed yet.")
        return []
    onlyfiles = [f for f in os.listdir(installation_dir) if os.path.isfile(os.path.join(installation_dir, f))]
    return onlyfiles

def list_outdated_files():
    """
    Lists all outdated, installed files
    """

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
    parser.add_argument("-n", "--unlock", action="store_true", help="Unlock the installed file")

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
    yes_to_all = settings["Security"]["Always allow running scripts"]
    if result.yestoall:
        yes_to_all = True

    # Go though input files
    for input_file in result.files:
        # Commands
        if input_file == "refresh":
            refresh_local_repo()
        elif input_file == "clear":
            clear_local_repo()
        elif input_file == "listall":
            print("Following files are available: ")
            for item in list_all_repo_files():
                print(" - " + item["Name"])
        elif input_file == "listinstalled":
            print("Following files are installed: ")
            for item in list_installed_files():
                print(item)
        elif input_file == "listrepos":
            print("Following repositories are setted: ")
            for item in list_all_repos():
                print(item)
        # Repository manipulation commands
        elif result.search:
            pass
        elif result.lock:
            pass
        elif result.add_repo:
            add_repo(input_file)
            save_settings()
        elif result.remove_repo:
            remove_repo(input_file)
            save_settings()
        else:
            # Normal file
            action = '0'
            if result.verify:
                action = 'v'
            elif result.run:
                action = 'r'
            elif result.install:
                action = 'i'
            elif result.uninstall:
                action = 'u'
            open_file(input_file, action=action)

    # Finished, now clean up
    logging.shutdown()
