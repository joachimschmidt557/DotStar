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
import shutil
import struct
import platform
import subprocess
from distutils.version import StrictVersion
import argparse
import re
import requests
import hashlib
import yaml

# INFO
__version__ = "0.1.1"

# CONSTANTS
PACKAGE_INFO_FILE = "Package.yml"

WORKING_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE = os.path.join(WORKING_DIRECTORY, "DotStarSettings.star")
PACKAGES_DIRECTORY = os.path.join(WORKING_DIRECTORY, "Packages")
PACKAGE_CACHE_DIRECTORY = os.path.join(PACKAGES_DIRECTORY, "Cache")
INSTALLED_FILES_DIRECTORY = os.path.join(PACKAGES_DIRECTORY, "Installed")
REPO_DIRECTORY = os.path.join(WORKING_DIRECTORY, "Repositories")

CURRENT_VERSION = StrictVersion(__version__)
DEFAULT_SETTINGS = {
    "Repositories":
    [
        "https://raw.githubusercontent.com/joachimschmidt557/DotStarRepo/master/Master.yml"
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
        with open(settings_file) as settings_yaml:
            settings = yaml.load(settings_yaml)
    except yaml.YAMLError:
        settings = DEFAULT_SETTINGS
    except FileNotFoundError:
        settings = DEFAULT_SETTINGS

def save_settings(settings_file=SETTINGS_FILE):
    """
    Save the settings into the Settings file.
    """
    global settings
    try:
        with open(settings_file, 'w') as settings_yaml:
            yaml.dump(settings, settings_yaml)
    except:
        logging.error("Couldn't update settings")

def get_current_platform():
    """
    Returns the current platform DotStar is
    running on
    """
    bitness = get_current_bitness()
    simple_name = platform.system()
    #version = platform.version()
    if simple_name == "Windows":
        if bitness == 32:
            return "Win32"
        if bitness == 64:
            return "Win64"
    elif simple_name == "Linux":
        return "Linux"
    elif simple_name == "Darwin":
        return "macOS"

def get_current_bitness():
    """
    Returns '32' or '64' according to the OS'
    and python's bitness
    """
    return 8 * struct.calcsize("P")

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

def open_file(input_name, action='0'):
    """
    Does whats necessary to process the file and
    afterwards opens it
    """
    logging.info("Processing file " + input_name)

    # Retrieve the file
    local_file_path = ""
    if os.path.isfile(input_name):
        local_file_path = input_name
    elif is_url(input_name):
        local_file_path = download_file(input_name, get_temporary_directory())
    elif not input_name.endswith(".star"):
        # Check if the file is installed
        logging.info("Searching installed files for " + input_name)
        available_files = search_installed_files(input_name)
        #if len(available_files) > 1:
        #    pass
        if len(available_files) == 1:
            if not (is_locked(input_name) and (action == "Install" or action == "Uninstall")):
                if action == "Install":
                    # The package should be reinstalled
                    action = "Install"
                local_file_path = os.path.join(INSTALLED_FILES_DIRECTORY, input_name)
            else:
                logging.error(input_name + " is locked. To manipulate this file, unlock it first.")
                return
        else:
            # If the file is not installed, try to get file from repository
            logging.info("Searching repositories for " + input_name)
            available_files = search_repos_for_files(input_name)
            if len(available_files) < 1:
                logging.error("No package found in the repositories")
                return
            if len(available_files) > 1:
                pass
            else:
                local_file_path = cache_retrieve_file(available_files[0]["URL"],
                                                      available_files[0]["Name"],
                                                      available_files[0]["Version"])

    # Special file names
    if local_file_path.endswith("DotStarSettings.star"):
        load_settings(local_file_path)
        save_settings()
    elif local_file_path.endswith("Package.yml"):
        compile_file(local_file_path)

    # Normal DotStar files
    else:
        open_local_file_or_folder(local_file_path, action=action)

    # Clean up if necessary
    if local_file_path.endswith("Temp.star"):
        shutil.rmtree(os.path.dirname(local_file_path))

def open_local_file_or_folder(file_or_dir_path, action='0'):
    """
    Opens a .star file which is on the local hard-drive
    of the computer
    """
    try:
        if os.path.isfile(file_or_dir_path):
            # Extract file to temporary directory
            temp_dir = get_temporary_directory()
            logging.debug("Extracting file to temporary directory " + temp_dir)
            decompress_file(file_or_dir_path, temp_dir)
        elif os.path.isdir(file_or_dir_path):
            # Set this folder as our working directory
            temp_dir = file_or_dir_path
        else:
            logging.error("Path is whether file nor folder.")
            return

        # Process file
        package_info_file = os.path.join(temp_dir, PACKAGE_INFO_FILE)
        try:
            with open(package_info_file) as package_info_yaml:
                data = yaml.load(package_info_yaml)

            # Check the "DotStar Information area"
            version_used_to_compile = StrictVersion(data["DotStar Information"]["Version"])
            if CURRENT_VERSION < version_used_to_compile:
                # This file was created with a newer version of DotStar
                # So, this version may be out-of-date
                logging.warning("Your DotStar version may be out-of-date. This file " +
                                "was created using a newer version of DotStar.")

            # Check the integrity area
            if "Integrity Information" in data:
                if not verify_integrity(temp_dir, data["Integrity Information"]):
                    logging.error("Package corrupted.")
                    return

            # Check the dependencies area
            if "Dependency Information" in data:
                for dependency in data["Dependencies"]:
                    logging.debug("This file depends on " + dependency["Name"])
                    # Check if the dependecy is installed
                    if not is_installed(dependency["Name"]):
                        # Install dependency
                        open_local_file_or_folder(dependency["File"], action="Install")

            # Check the type
            if "Application Information" in data:
                # Type: Application package
                info = data["Application Information"]

                # Check the platform area
                if "Supported Platforms" in info:
                    if get_current_platform() not in info["Supported Platforms"]:
                        logging.critical("This app is currently not supported on this platform")
                        return

                # Check our specified action
                if action == "Run":
                    # Run the app
                    # Select appropiate script, depending on platform
                    select_additional_tasks(temp_dir, "Run")

                elif action == "Install":
                    # Install the app
                    # Copy the temp_dir to the installation directory
                    installation_dir = os.path.join(INSTALLED_FILES_DIRECTORY,
                                                    info["Name"])
                    if not os.path.exists(os.path.dirname(installation_dir)):
                        os.makedirs(os.path.dirname(installation_dir))
                    if os.path.exists(installation_dir):
                        shutil.rmtree(installation_dir)
                    shutil.copytree(temp_dir, installation_dir)

                    # Additional installation steps
                    select_additional_tasks(temp_dir, "Install")

                    logging.info("Installation successful")
                elif action == "Uninstall":
                    # Additional uninstallation steps
                    select_additional_tasks(temp_dir, "Uninstall")

                    # Delete the file
                    if os.path.isfile(file_or_dir_path):
                        os.remove(file_or_dir_path)
                        logging.info("Removed file " + file_or_dir_path)
                    else:
                        shutil.rmtree(file_or_dir_path)
                        logging.info("Removed folder " + file_or_dir_path)
                else:
                    # If no action is specified, let the user decide
                    print(info["Friendly Name"])
                    print("Version " + info["Version"])
                    print(info["Description"])
                    print("Possible actions: ")

            else:
                # Empty file
                logging.warning("This file is an empty file.")
        except FileNotFoundError as err:
            raise err
        except yaml.YAMLError:
            logging.critical("Error decoding YAML")

        # If necessary, clean up the temporary directory
        if os.path.isfile(file_or_dir_path):
            shutil.rmtree(temp_dir)
            logging.debug("Removed temporary directory " + temp_dir)
    except zipfile.BadZipFile:
        logging.critical("Bad zip file!")
    except FileNotFoundError:
        logging.critical("File doesn't exist! " + str(err))

#def open_local_file_partially(file_path, file_name=PACKAGE_INFO_FILE):
#    """
#    Opens a local file and only extracts the given
#    file name from the archive
#    """
#    try:
#        # Extract file to temporary directory
#        temp_dir = get_temporary_directory()
#        logging.debug("Extracting file to temporary directory " + temp_dir)
#    except zipfile.BadZipfile:
#        pass

def select_additional_tasks(folder_path, action):
    """
    Selects and runs additional steps
    """
    current_platform = get_current_platform()
    user_consent_message = ("Additional supportive scripts for action '" + action +
                            "' were found. Run? (Y/n):")

    if current_platform.startswith("Win"):
        # The script created specifically for this action
        package_file_specific = os.path.join(folder_path, "Package.Win." + action + ".bat")
        package_file_specific_posh = os.path.join(folder_path, "Package.Win." + action + ".ps1")

        # The script created generally for this platform
        package_file = os.path.join(folder_path, "Package.Win.bat")
        package_file_posh = os.path.join(folder_path, "Package.Win.ps1")

        if os.path.exists(package_file_specific_posh):
            if user_consent(user_consent_message):
                subprocess.call([package_file_specific_posh], cwd=folder_path)
        elif os.path.exists(package_file_specific):
            if user_consent(user_consent_message):
                subprocess.call([package_file_specific], cwd=folder_path)
        elif os.path.exists(package_file):
            pass

    elif current_platform.startswith("Linux"):
        # The script created specifically for this action
        package_file_specific = os.path.join(folder_path, "Package.Linux." + action + ".sh")

        # The script created generally for this platform
        package_file = os.path.join(folder_path, "Package.Linux.bat")

        if os.path.exists(package_file_specific):
            if user_consent(user_consent_message):
                subprocess.call(["bash", package_file_specific], cwd=folder_path)
        elif os.path.exists(package_file):
            pass

    elif current_platform.startswith("macOS"):
        # The script created specifically for this action
        package_file_specific = os.path.join(folder_path, "Package.macOS." + action + ".sh")

        # The script created generally for this platform
        package_file = os.path.join(folder_path, "Package.macOS.sh")

        if os.path.exists(package_file_specific):
            if user_consent(user_consent_message):
                subprocess.call(["bash", package_file_specific], cwd=folder_path)
        elif os.path.exists(package_file):
            pass

def compile_file(file_path):
    """
    Compile the specified file with all it's resources into a new .star file
    """
    logging.info("Attempting to compile " + file_path)
    try:
        # Create temporary folder to store the files into
        temp_dir = get_temporary_directory(create_directory=False)
        output_file = ""

        # Read the file
        with open(file_path) as compilation_info_yaml:
            other_data = yaml.load(compilation_info_yaml)

        # Extract compilation information
        ignored_list = []
        if "Compilation Information" in other_data:
            # Get the list of files/folders to be ignored
            if "Ignore files" in other_data["Compilation Information"]:
                ignored_list = other_data["Compilation Information"]["Ignore files"]

            # Clean up the compilation information area
            other_data.pop("Compilation Information")

        # Copy the necessary files into the folder
        shutil.copytree(os.path.dirname(file_path), temp_dir,
                        ignore=shutil.ignore_patterns(*ignored_list))

        # Get the output file name
        output_file = os.path.join(os.getcwd(),
                                   other_data["Application Information"]["Name"] + ".star")

        # Create Package.yml
        package_yaml_file = os.path.join(temp_dir, PACKAGE_INFO_FILE)

        # Create DotStar information area
        data = {
            "DotStar Information":
            {
                "Version": str(__version__)
            }
        }
        # Append the other data to our DotStar info area
        data.update(other_data)

        # Write to Package.yml
        with open(package_yaml_file, 'w') as package_file:
            yaml.dump(data, package_file)

        # Run additional compilation steps
        select_additional_tasks(temp_dir, "Compile")

        # Zip the folder
        compress_folder(temp_dir, output_file)
        logging.info("Compiled package: " + output_file)

        # Finish and clean up
        shutil.rmtree(temp_dir)
    except FileNotFoundError as err:
        logging.critical("File doesn't exist " + str(err))
    except yaml.YAMLError:
        logging.critical("Error decoding YAML")

def decompress_file(file_path, extract_path):
    """
    Decompresses a .star file to the path specified
    """
    with zipfile.ZipFile(file_path, "r") as z:
        z.extractall(extract_path)

def compress_folder(folder_path, zipfile_path):
    """
    Compress a folder into a file (no adding of .zip extension)
    """
    shutil.make_archive(zipfile_path, "zip", folder_path)

    # If the file already exists, delete it to prevent an error
    if os.path.exists(zipfile_path):
        os.remove(zipfile_path)

    # Remove the .zip part of the file name
    os.rename(zipfile_path + ".zip", zipfile_path)

def cache_retrieve_file(url, file_name, version):
    """
    Checks the cache if the file is already downloaded. If
    not, then download the file and add it to the cache.
    Returns the file path of the local file.
    """
    # Check if the file is already in the cache
    local_file_path = os.path.join(PACKAGE_CACHE_DIRECTORY, file_name, version, file_name)
    if os.path.isfile(local_file_path):
        return local_file_path

    # Download the file into the cache
    download_file(url, os.path.join(PACKAGE_CACHE_DIRECTORY, file_name, version), file_name)
    return local_file_path

def cache_clear_old_versions():
    """
    Clears all old versions of programs in the cache
    """
    #TODO

def cache_clear():
    """
    Clear all cached files
    """
    if not os.path.exists(PACKAGE_CACHE_DIRECTORY):
        os.makedirs(PACKAGE_CACHE_DIRECTORY)
        logging.info("Cache is already empty")
        return
    shutil.rmtree(PACKAGE_CACHE_DIRECTORY)
    os.makedirs(PACKAGE_CACHE_DIRECTORY)
    logging.info("Cache cleared")

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
    if not is_url(url):
        logging.error("URL is not valid.")
        return
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    r = requests.get(url)
    with open(file_path, "wb") as dotstarfile:
        dotstarfile.write(r.content)
    return file_path

def verify_integrity(folder_path, integrity_info):
    """
    Verifies the folder's integrity using the data
    """
    return True

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
    Adds a repository to the repo list. Requires
    save_settings to have any effect.
    """
    if not is_url(url):
        logging.critical(url + " is not a valid URL.")
        return
    settings["Repositories"].append(url)
    logging.info("Repository " + url + " added to the list!")

def remove_repo(id_number):
    """
    Removes a repository at the given id.
    Requires save_settings to have any effect.
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
        with open(os.path.join(REPO_DIRECTORY, filename)) as repo_yaml:
            all_repo_files += yaml.load(repo_yaml)["Packages"]
    return all_repo_files

def list_installed_files():
    """
    Returns a list with filenames (absoulte path) of
    installed files
    """
    #TODO: Better output with details (version)
    installation_dir = INSTALLED_FILES_DIRECTORY
    if not os.path.exists(installation_dir):
        os.makedirs(installation_dir)
        return []
    onlyfolders = [f for f in os.listdir(installation_dir) if os.path.isdir(os.path.join(installation_dir, f))]
    return onlyfolders

def is_installed(file_name):
    """
    Returns whether file_name is installed or not.
    (file_name without ".star")
    """
    if len(search_installed_files(file_name)) == 1:
        return True
    return False

def lock_installed_file(file_name):
    """
    Locks the specified installed file (without .star).
    Requires save_settings to have any effect.
    """
    # Check if the package is really installed
    if not is_installed(file_name):
        logging.error(file_name + " is not installed yet.")
        return

    # Lock the file
    settings["Locked files"].append(file_name)
    logging.info(file_name + " successfully locked.")

def unlock_locked_file(file_name):
    """
    Unlocks the specified locked file (without .star).
    Requires save_settings to have any effect.
    """
    # Check if the package is even locked
    if not is_locked(file_name):
        logging.error(file_name + " is not locked.")
        return

    # Unlock the file
    settings["Locked files"].remove(file_name)
    logging.info(file_name + " successfully unlocked.")

def is_locked(file_name):
    """
    Returns whether file_name is locked or not
    """
    if not is_installed(file_name):
        return False
    if file_name in settings["Locked files"]:
        return True
    return False

def list_outdated_files():
    """
    Lists all outdated, installed files
    """

def search_installed_files(file_name):
    """
    Searches the installed .star files for matching
    files (file_name without ".star")
    """
    all_installed_files = list_installed_files()
    return list(filter(lambda item: item == file_name, all_installed_files))

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
    parser.add_argument("-f", "--find", action="store_true", help="Search all installed files")
    parser.add_argument("-o", "--lock", action="store_true", help="Prevent modifying or removing the installed file")
    parser.add_argument("-n", "--unlock", action="store_true", help="Unlock the installed file")

    # Repository flags
    parser.add_argument("-a", "--add-repo", action="store_true", help="Adds a repository")
    parser.add_argument("-x", "--remove-repo", action="store_true", help="Removes a repository")

    # File-specific flags
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
    if settings["Security"]["Always allow running scripts"] or result.yestoall:
        yes_to_all = True
    else: yes_to_all = False

    # Go though input files
    for input_file in result.files:
        # Commands
        if input_file == "refresh":
            refresh_local_repo()
        elif input_file == "clear":
            clear_local_repo()
        elif input_file == "listall":
            all_available_files = list_all_repo_files()
            if len(all_available_files) < 1:
                print("No files available")
            else:
                print("Following files are available: ")
                for item in all_available_files:
                    print(" - " + item["Name"])
        elif input_file == "listinstalled":
            all_installed_files = list_installed_files()
            if len(all_installed_files) < 1:
                print("No packages installed yet.")
            else:
                print("Following packages are installed: ")
                for item in all_installed_files:
                    print("- " + item)
        elif input_file == "listrepos":
            all_repos = list_all_repos()
            if len(all_repos) < 1:
                print("No repositories setted")
            else:
                print("Following repositories are setted: ")
                for item in all_repos:
                    print(" - " + item)
        # Repository manipulation commands
        elif result.find:
            for item in search_installed_files(input_file):
                print(item)
        elif result.search:
            for item in search_repos_for_files(input_file):
                print(item)
        elif result.lock:
            lock_installed_file(input_file)
            save_settings()
        elif result.unlock:
            unlock_locked_file(input_file)
            save_settings()
        elif result.add_repo:
            add_repo(input_file)
            save_settings()
        elif result.remove_repo:
            remove_repo(input_file)
            save_settings()
        else:
            # Normal file
            action_to_perform = '0'
            if result.run:
                action_to_perform = "Run"
            elif result.install:
                action_to_perform = "Install"
            elif result.uninstall:
                action_to_perform = "Uninstall"
            open_file(input_file, action=action_to_perform)

    # Finished, now clean up
    logging.shutdown()
