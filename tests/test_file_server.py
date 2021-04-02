"""
Test ability to run file server
"""
import threading
import tempfile
import unittest
import os

import requests

from wxupdatedemo.fileserver import run_file_server
from wxupdatedemo.fileserver import wait_for_file_server_to_start
from wxupdatedemo.fileserver import shut_down_file_server
from wxupdatedemo.fileserver import LOCALHOST
from wxupdatedemo.utils import get_ephemeral_port


class FileServerTester(unittest.TestCase):
    """
    Test ability to run file server
    """
    def __init__(self, *args, **kwargs):
        super(FileServerTester, self).__init__(*args, **kwargs)
        self.file_server_thread = None
        self.file_server_port = None
        self.test_file_name = "testfile.txt"
        self.test_file_content = "Hello, world!"

    def setUp(self):
        temp_file = tempfile.NamedTemporaryFile()
        self.file_server_dir = temp_file.name
        temp_file.close()
        os.mkdir(self.file_server_dir)
        test_file_path = os.path.join(self.file_server_dir, self.test_file_name)
        with open(test_file_path, 'w') as testFile:
            testFile.write(self.test_file_content)
        os.environ['PYUPDATER_FILESERVER_DIR'] = self.file_server_dir
        os.environ['WXUPDATEDEMO_TESTING'] = 'True'

    def test_file_server(self):
        """
        Test ability to run file server
        """
        self.file_server_port = get_ephemeral_port()
        self.file_server_thread = \
            threading.Thread(target=run_file_server,
                             args=(self.file_server_dir, self.file_server_port))
        self.file_server_thread.start()
        wait_for_file_server_to_start(self.file_server_port)
        url = "http://%s:%s" % (LOCALHOST, self.file_server_port)
        url = "%s/%s" % (url, self.test_file_name)
        response = requests.get(url, timeout=1)
        self.assertEqual(response.text, self.test_file_content)

    def tearDown(self):
        """
        Shut down file server
        """
        shut_down_file_server(self.file_server_port)
        self.file_server_thread.join()
        del os.environ['PYUPDATER_FILESERVER_DIR']
        del os.environ['WXUPDATEDEMO_TESTING']
