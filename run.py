"""
run.py

PyUpdaterWxDemo can be launched by running "python run.py"
"""
import logging
import os
import sys
import threading
import time
import argparse

from pyupdater.client import Client

import wxupdatedemo
from wxupdatedemo.main import PyUpdaterWxDemoApp
from wxupdatedemo.fileserver import run_file_server
from wxupdatedemo.fileserver import wait_for_file_server_to_start
from wxupdatedemo.fileserver import shut_down_file_server
from wxupdatedemo.utils import get_ephemeral_port

from wxupdatedemo.config import CLIENT_CONFIG
from wxupdatedemo.config import update_py_updater_client_config

logger = logging.getLogger(__name__)
STDERR_HANDLER = logging.StreamHandler(sys.stderr)
STDERR_HANDLER.setFormatter(logging.Formatter(logging.BASIC_FORMAT))


class UpdateStatus(object):
    """Enumerated data type"""

    # pylint: disable=invalid-name
    # pylint: disable=too-few-public-methods
    UNKNOWN = 0
    NO_AVAILABLE_UPDATES = 1
    UPDATE_DOWNLOAD_FAILED = 2
    EXTRACTING_UPDATE_AND_RESTARTING = 3
    UPDATE_AVAILABLE_BUT_APP_NOT_FROZEN = 4
    COULD_NOT_CHECK_FOR_UPDATES = 5


UPDATE_STATUS_STR = [
    "Unknown",
    "No available updates were found.",
    "Update download failed.",
    "Extracting update and restarting.",
    "Update available but application is not frozen.",
    "Couldn't check for updates.",
]


def parse_args(argv):
    """
    Parse command-line args.
    """
    usage = "%(prog)s [options]\n" "\n" "You can also run: python setup.py nosetests"
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument(
        "--debug", help="increase logging verbosity", action="store_true"
    )
    parser.add_argument("--version", action="store_true", help="displays version")
    return parser.parse_args(argv[1:])


def initialize_logging(debug=False):
    """
    Initialize logging.
    """
    logger.addHandler(STDERR_HANDLER)
    if debug or "WXUPDATEDEMO_TESTING" in os.environ:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger.setLevel(level)
    logging.getLogger("wxupdatedemo.fileserver").addHandler(STDERR_HANDLER)
    logging.getLogger("wxupdatedemo.fileserver").setLevel(level)
    logging.getLogger("pyupdater").setLevel(level)
    logging.getLogger("pyupdater").addHandler(STDERR_HANDLER)


def start_file_server(file_server_dir):
    """
    Start file server.
    """
    if not file_server_dir:
        message = "The PYUPDATER_FILESERVER_DIR environment variable is not set."
        if hasattr(sys, "frozen"):
            logger.error(message)
            return None
        else:
            file_server_dir = os.path.join(os.getcwd(), "pyu-data", "deploy")
            message += "\n\tSetting fileServerDir to: %s\n" % file_server_dir
            logger.warning(message)
    file_server_port = get_ephemeral_port()
    thread = threading.Thread(
        target=run_file_server, args=(file_server_dir, file_server_port)
    )
    thread.start()
    wait_for_file_server_to_start(file_server_port)
    return file_server_port


def check_for_updates(file_server_port, debug):
    """
    Check for updates.

    Channel options are stable, beta & alpha
    Patches are only created & applied on the stable channel
    """
    assert CLIENT_CONFIG.PUBLIC_KEY is not None
    client = Client(CLIENT_CONFIG, refresh=True)
    app_update = client.update_check(
        CLIENT_CONFIG.APP_NAME, wxupdatedemo.__version__, channel="stable"
    )
    if app_update:
        if hasattr(sys, "frozen"):
            downloaded = app_update.download()
            if downloaded:
                status = UpdateStatus.EXTRACTING_UPDATE_AND_RESTARTING
                if "WXUPDATEDEMO_TESTING_FROZEN" in os.environ:
                    sys.stderr.write(
                        "Exiting with status: %s\n" % UPDATE_STATUS_STR[status]
                    )
                    shut_down_file_server(file_server_port)
                    sys.exit(0)
                shut_down_file_server(file_server_port)
                if debug:
                    logger.debug("Extracting update and restarting...")
                    time.sleep(10)
                app_update.extract_restart()
            else:
                status = UpdateStatus.UPDATE_DOWNLOAD_FAILED
        else:
            status = UpdateStatus.UPDATE_AVAILABLE_BUT_APP_NOT_FROZEN
    else:
        status = UpdateStatus.NO_AVAILABLE_UPDATES
    return status


def display_version_and_exit():
    """
    Display version and exit.

    In some versions of PyInstaller, sys.exit can result in a
    misleading 'Failed to execute script run' message which
    can be ignored: http://tinyurl.com/hddpnft
    """
    sys.stdout.write("%s\n" % wxupdatedemo.__version__)
    sys.exit(0)


def run(argv, client_config=None):
    """
    The main entry point.
    """
    args = parse_args(argv)
    if args.version:
        display_version_and_exit()
    initialize_logging(args.debug)
    file_server_dir = os.environ.get("PYUPDATER_FILESERVER_DIR")
    file_server_port = start_file_server(file_server_dir)
    if file_server_port:
        update_py_updater_client_config(client_config, file_server_port)
        status = check_for_updates(file_server_port, args.debug)
    else:
        status = UpdateStatus.COULD_NOT_CHECK_FOR_UPDATES
    if "WXUPDATEDEMO_TESTING_FROZEN" in os.environ:
        sys.stderr.write("Exiting with status: %s\n" % UPDATE_STATUS_STR[status])
        shut_down_file_server(file_server_port)
        sys.exit(0)
    main_loop = argv[0] != "RunTester"
    if not "WXUPDATEDEMO_TESTING_FROZEN" in os.environ:
        return PyUpdaterWxDemoApp.Run(
            file_server_port, UPDATE_STATUS_STR[status], main_loop
        )
    else:
        return None


if __name__ == "__main__":
    run(sys.argv)
