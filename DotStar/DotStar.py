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
__version__ = "0.1"

# CONSTANTS
PACKAGE_INFO_FILE = "Package.yml"

PACKAGE_FILE = "Package.py"
PACKAGE_FILE_WIN = "Package.Win.bat"
PACKAGE_FILE_WIN_INSTALL = "Package.Win.Install.bat"
PACKAGE_FILE_WIN_UNINSTALL = "Package.Win.Uninstall.bat"
PACKAGE_FILE_WIN_RUN = "Package.Win.Run.bat"
PACKAGE_FILE_WIN_COMPILE = "Package.Win.Compile.bat"
PACKAGE_FILE_LINUX = "Package.Linux.sh"
PACKAGE_FILE_LINUX_INSTALL = "Package.Linux.Install.sh"
PACKAGE_FILE_LINUX_UNINSTALL = "Package.Linux.Uninstall.sh"
PACKAGE_FILE_LINUX_RUN = "Package.Linux.Run.sh"
PACKAGE_FILE_LINUX_COMPILE = "Package.Linux.Compile.sh"

SETTINGS_FILE = "DotStarSettings.star"
FILE_CACHE_DIRECTORY = "Packages"
INSTALLED_FILES_DIRECTORY = "Installed"
REPO_DIRECTORY = "Repositories"

CURRENT_PLATFORM = sys.platform
CURRENT_VERSION = StrictVersion(__version__)
ACTIONS = [
    'r',    # Run the package
    'i',    # Install the package
    'I',    # Reinstall the package
    'u',    # Uninstall the package
    '0'     # Let the user decide
]
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

def save_settings():
    """
    Save the settings into the Settings file.
    """
    global settings
    try:
        settings_file = SETTINGS_FILE
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
        # Check if the file is installed
        logging.info("Searching installed files for " + path)
        available_files = search_installed_files(path)
        if len(available_files) > 1:
            pass
        if len(available_files) == 1:
            if not(is_locked(path) and (action == 'i' or action == 'u')):
                if action == 'i':
                    # The package should be reinstalled
                    action = 'I'
                local_file_path = os.path.join(FILE_CACHE_DIRECTORY, INSTALLED_FILES_DIRECTORY,
                                               path + ".star")
            else:
                logging.error(path + " is locked. To manipulate this file, unlock it first.")
                return
        else:
            # If the file is not installed, try to get file from repository
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
    elif local_file_path.endswith("Package.yml"):
        compile_file(local_file_path)
    #elif local_file_path.endswith("Run.star"):
    #    open_local_file(local_file_path, action='r')
    # Normal DotStar files
    else:
        open_local_file(local_file_path, action=action)

    # Clean up if necessary
    if local_file_path.endswith("Temp.star"):
        shutil.rmtree(os.path.dirname(local_file_path))

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
        package_file_win = os.path.join(temp_dir, PACKAGE_FILE_WIN)
        package_file_win_install = os.path.join(temp_dir, PACKAGE_FILE_WIN_INSTALL)
        package_file_win_uninstall = os.path.join(temp_dir, PACKAGE_FILE_WIN_UNINSTALL)
        package_file_win_run = os.path.join(temp_dir, PACKAGE_FILE_WIN_RUN)
        package_file_win_compile = os.path.join(temp_dir, PACKAGE_FILE_WIN_COMPILE)
        package_file_linux = os.path.join(temp_dir, PACKAGE_FILE_LINUX)
        package_file_linux_install = os.path.join(temp_dir, PACKAGE_FILE_LINUX_INSTALL)
        package_file_linux_uninstall = os.path.join(temp_dir, PACKAGE_FILE_LINUX_UNINSTALL)
        package_file_linux_run = os.path.join(temp_dir, PACKAGE_FILE_LINUX_RUN)
        package_file_linux_compile = os.path.join(temp_dir, PACKAGE_FILE_LINUX_COMPILE)
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
                        open_local_file(dependency["File"], action='i')

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
                if action == 'r':
                    # Run the app
                    if user_consent("Run the File? (y/n): "):
                        # Select appropiate script, depending on platform
                        if get_current_platform() == "Win32" or get_current_platform() == "Win64":
                            if os.path.exists(package_file_win_run):
                                subprocess.call([package_file_win_run], cwd=temp_dir)
                            elif os.path.exists(package_file_win):
                                pass
                            elif os.path.exists(package_file):
                                os.system("python " + package_file + " run")
                        elif get_current_platform() == "Linux":
                            if os.path.exists(package_file_linux_run):
                                subprocess.call([package_file_linux_run], cwd=temp_dir)
                            elif os.path.exists(package_file_linux):
                                pass
                            elif os.path.exists(package_file):
                                os.system("python " + package_file + " run")
                elif action == 'i':
                    # Install the app
                    # Copy the package to the installation directory
                    installation_dir = os.path.join(FILE_CACHE_DIRECTORY, INSTALLED_FILES_DIRECTORY)
                    new_file_name = info["Name"] + ".star"
                    if not os.path.exists(installation_dir):
                        os.makedirs(installation_dir)
                    installed_file_path = shutil.copy(file_path, installation_dir)
                    os.rename(installed_file_path, os.path.join(installation_dir, new_file_name))

                    # Additional installation steps
                    # Select appropiate script, depending on platform
                    if get_current_platform() == "Win32" or get_current_platform() == "Win64":
                        if os.path.exists(package_file_win_install):
                            if user_consent("Run additional installation steps? (y/n): "):
                                subprocess.call([package_file_win_install], cwd=temp_dir)
                        elif os.path.exists(package_file_win):
                            pass
                        elif os.path.exists(package_file):
                            if user_consent("Run additional installation steps? (y/n): "):
                                os.system("python " + package_file + " install")
                    elif get_current_platform() == "Linux":
                        if os.path.exists(package_file_linux_install):
                            if user_consent("Run additional installation steps? (y/n): "):
                                subprocess.call([package_file_linux_install], cwd=temp_dir)
                        elif os.path.exists(package_file_linux):
                            pass
                        elif os.path.exists(package_file):
                            if user_consent("Run installation steps? (y/n): "):
                                os.system("python " + package_file + " install")

                    logging.info("Installation successful")
                elif action == 'u':
                    # Additional uninstallation steps
                    # Select appropiate script, depending on platform
                    if get_current_platform() == "Win32" or get_current_platform() == "Win64":
                        if os.path.exists(package_file_win_uninstall):
                            if user_consent("Run additional uninstallation steps? (y/n): "):
                                subprocess.call([package_file_win_uninstall], cwd=temp_dir)
                        elif os.path.exists(package_file_win):
                            pass
                        elif os.path.exists(package_file):
                            if user_consent("Run additional uninstallation steps? (y/n): "):
                                os.system("python " + package_file + " uninstall")
                    elif get_current_platform() == "Linux":
                        if os.path.exists(package_file_linux_uninstall):
                            if user_consent("Run additional uninstallation steps? (y/n): "):
                                subprocess.call([package_file_linux_uninstall], cwd=temp_dir)
                        elif os.path.exists(package_file_linux):
                            pass
                        elif os.path.exists(package_file):
                            if user_consent("Run uninstallation steps? (y/n): "):
                                os.system("python " + package_file + " uninstall")

                    # Delete the file
                    os.remove(file_path)
                    logging.info("Removed file " + file_path)
                else:
                    # If no action is specified, let the user decide
                    print(info["Friendly Name"])
                    print("Version " + info["Version"])
                    print(info["Description"])
                    print("Possible actions: ")

            #elif "Document Information" in data:
            #    # Type: Document package
            #    info = data["Document Information"]
            #    resources = info["Resources"]
            #    for resource in resources:
            #        pass
            #elif "Folder Information" in data:
            #    # Type: Folder package
            #    pass
            else:
                # Empty file
                logging.warning("This file is an empty file.")
        except FileNotFoundError as err:
            raise err
        except yaml.YAMLError:
            logging.critical("Error decoding YAML")

        # If necessary, clean up the temporary directory
        shutil.rmtree(temp_dir)
        logging.debug("Removed temporary directory " + temp_dir)
    except zipfile.BadZipFile:
        logging.critical("Bad zip file!")
    except FileNotFoundError:
        logging.critical("File doesn't exist! " + str(err))

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
        output_file = os.path.join(os.getcwd(), other_data["Application Information"]["Name"] + ".star")

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

        # Run the python script for additional compilation steps
        script_file = os.path.join(temp_dir, PACKAGE_FILE)
        if user_consent("Run compilation script? (y/n): "):
            if sys.version_info < (3, 5):
                subprocess.call([sys.executable, script_file, "compile"], cwd=temp_dir)
            else:
                subprocess.run([sys.executable, script_file, "compile"], cwd=temp_dir)

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
        logging.critical(url + " is not a respository URL.")
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
    installation_dir = os.path.join(FILE_CACHE_DIRECTORY, INSTALLED_FILES_DIRECTORY)
    if not os.path.exists(installation_dir):
        os.makedirs(installation_dir)
        return []
    onlyfiles = [f for f in os.listdir(installation_dir) if os.path.isfile(os.path.join(installation_dir, f))]
    return onlyfiles

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
    file_name_with_extension = file_name + ".star"
    return list(filter(lambda item: item == file_name_with_extension, all_installed_files))

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
                print("No files installed yet.")
            else:
                print("Following files are installed: ")
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
                action_to_perform = 'r'
            elif result.install:
                action_to_perform = 'i'
            elif result.uninstall:
                action_to_perform = 'u'
            open_file(input_file, action=action_to_perform)

    # Finished, now clean up
    logging.shutdown()
