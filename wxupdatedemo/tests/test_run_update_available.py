"""
Test ability to run PyUpdaterWxDemo and confirm that an update is available.

We don't want this test to be dependent on having a
client_config.py (created by pyupdater init), so
we set the WXUPDATEDEMO_TESTING environment variable
before loading the wxupdatedemo.config module or
the run module.
"""
# pylint: disable=bad-continuation
# pylint: disable=line-too-long
import unittest
import os
import sys
import gzip
import json
import shutil
import tempfile

import ed25519
import wx

from wxupdatedemo import __version__

APP_NAME = "PyUpdaterWxDemo"
CURRENT_VERSION = "0.0.1"
UPDATE_VERSION = "0.0.2"
# PyUpdater version format is:
# Major.Minor.Patch.[Alpha|Beta|Stable].ReleaseNumber
# where Alpha=0, Beta=1 and Stable=2
UPDATE_VERSION_PYU_FORMAT = "%s.2.0" % UPDATE_VERSION

VERSIONS = {
    "updates": {
        APP_NAME: {
            UPDATE_VERSION_PYU_FORMAT: {
                "mac": {
                    "file_hash": "bd4bc8824dfd8240d5bdb9e46f21a86af4d6d1cc1486a2a99cc4b9724a79492b",
                    "filename": "%s-mac-%s.tar.gz" % (APP_NAME, UPDATE_VERSION),
                    "file_size": 30253628,
                },
                "win": {
                    "file_hash": "b1399df583bce4ca45665b3960fd918a316d86c997d6c33556eda1cc2b555e59",
                    "filename": "%s-win-%s.zip" % (APP_NAME, UPDATE_VERSION),
                    "file_size": 14132995,
                },
                "nix32": {
                    "file_hash": "bd4bc8824dfd8240d5bdb9e46f21a86af4d6d1cc1486a2a99cc4b9724a79492b",
                    "filename": "%s-nix32-%s.tar.gz" % (APP_NAME, UPDATE_VERSION),
                    "file_size": 30253628,
                },
                "nix64": {
                    "file_hash": "bd4bc8824dfd8240d5bdb9e46f21a86af4d6d1cc1486a2a99cc4b9724a79492b",
                    "filename": "%s-nix64-%s.tar.gz" % (APP_NAME, UPDATE_VERSION),
                    "file_size": 30253628,
                },
            }
        }
    },
    "latest": {
        APP_NAME: {
            "stable": {
                "mac": UPDATE_VERSION_PYU_FORMAT,
                "win": UPDATE_VERSION_PYU_FORMAT,
                "nix32": UPDATE_VERSION_PYU_FORMAT,
                "nix64": UPDATE_VERSION_PYU_FORMAT,
            }
        }
    },
}

# Generated by "pyupdater keys -c":
# These keys are only used for automated testing!
# DO NOT SHARE YOUR PRODUCTION PRIVATE_KEY !!!
PUBLIC_KEY = "12y2oHGB2oroRQJkR73CJNaFeQy776oXsUrqWaAEiZU"
PRIVATE_KEY = "nHgoNwSmXSDNSMqQTtdAEmi/6otajiNYJEXESvAO8dc"

KEYS = {
    "app_public": "MIBCEwFh7AcaxJrHKIgYqAmZ9YX16NXVHLi+EdDmtYc",
    "signature": "1YTDuJauq7qVFUrKPHGMMESllJ4umo6u5r9pEgVmvlxgXi3qGXnKWo2LG94+oosN3KiO8DlxOmyfuwaaQKtFCw",
}


class RunTester(unittest.TestCase):
    """
    Test ability to run PyUpdaterWxDemo and confirm that an update is available.
    """

    def __init__(self, *args, **kwargs):
        super(RunTester, self).__init__(*args, **kwargs)
        self.app = None
        self.file_server_dir = None

    def setUp(self):
        temp_file = tempfile.NamedTemporaryFile()
        self.file_server_dir = temp_file.name
        temp_file.close()
        os.mkdir(self.file_server_dir)
        os.environ["PYUPDATER_FILESERVER_DIR"] = self.file_server_dir
        private_key = ed25519.SigningKey(PRIVATE_KEY.encode("utf-8"), encoding="base64")
        signature = private_key.sign(
            json.dumps(VERSIONS, sort_keys=True).encode("utf-8"),
            encoding="base64",
        ).decode()
        VERSIONS["signature"] = signature
        keys_file_path = os.path.join(self.file_server_dir, "keys.gz")
        with gzip.open(keys_file_path, "wb") as keys_file:
            keys_file.write(json.dumps(KEYS, sort_keys=True).encode("utf-8"))
        versions_file_path = os.path.join(self.file_server_dir, "versions.gz")
        with gzip.open(versions_file_path, "wb") as versions_file:
            versions_file.write(json.dumps(VERSIONS, sort_keys=True).encode("utf-8"))
        os.environ["WXUPDATEDEMO_TESTING"] = "True"
        from wxupdatedemo.config import CLIENT_CONFIG

        self.client_config = CLIENT_CONFIG
        self.client_config.PUBLIC_KEY = PUBLIC_KEY
        self.client_config.APP_NAME = APP_NAME

    def test_run_update_available(self):
        """
        Test ability to run PyUpdaterWxDemo and confirm that an update is available.
        """
        self.assertEqual(__version__, CURRENT_VERSION)
        from run import run

        self.app = run(argv=["RunTester", "--debug"], client_config=self.client_config)
        self.assertEqual(
            self.app.status_bar.GetStatusText(),
            "Update available but application is not frozen.",
        )
        sys.stderr.write("We can only restart a frozen app!\n")

    def tearDown(self):
        """
        Destroy the app
        """
        if self.app:
            self.app.frame.Hide()
            self.app.OnCloseFrame(wx.PyEvent())
            self.app.frame.Destroy()
        del os.environ["PYUPDATER_FILESERVER_DIR"]
        del os.environ["WXUPDATEDEMO_TESTING"]
        shutil.rmtree(self.file_server_dir)
