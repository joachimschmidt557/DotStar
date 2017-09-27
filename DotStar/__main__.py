"""
This small script stars the main script
"""

import argparse
import logging

import DotStar
__version__ = DotStar.__version__

from DotStar import load_settings
from DotStar import save_settings
from DotStar import open_file
from DotStar import refresh_local_repo
from DotStar import list_all_repo_files
from DotStar import compile_file

settings = None

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
        # Commands
        logging.info("Processing file " + input_file)
        if input_file == "refresh":
            refresh_local_repo()
        elif input_file == "listall":
            print("Following files are available: ")
            for item in list_all_repo_files():
                print(" - " + item["Name"])
        elif input_file == "listinstalled":
            print("Following files are installed: ")
            for item in list_all_repo_files():
                print(" - " + item["Name"])
        else:
            # Normal file
            open_file(input_file)

    # Finished, now clean up
    logging.shutdown()
