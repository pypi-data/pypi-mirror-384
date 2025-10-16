import os
import subprocess
import time
import unittest
from typing import Optional

import requests


class Client:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def get(self, path: str, params: dict = None, headers: dict = None) -> Optional[requests.Response]:
        if headers is None:
            headers = {}

        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=params,
                headers={**headers, "Content-Type": "application/json"},
            )
        except Exception as e:
            print(f"Exception: {str(e)}")
            return None
        return response

    def post(self, path: str, json: dict, headers: dict = None) -> Optional[requests.Response]:
        if headers is None:
            headers = {}

        try:
            response = requests.post(
                f"{self.base_url}{path}",
                json=json,
                headers={**headers, "Content-Type": "application/json"},
            )
            return response
        except Exception as e:
            print(f"Exception: {str(e)}")
            return None

    def patch(self, path: str, json: dict, headers: dict = None) -> Optional[requests.Response]:
        if headers is None:
            headers = {}

        try:
            response = requests.patch(
                f"{self.base_url}{path}",
                json=json,
                headers={**headers, "Content-Type": "application/json"},
            )
            return response
        except Exception as e:
            print(f"Exception: {str(e)}")
            return None

    def put(self, path: str, json: dict, headers: dict = None) -> Optional[requests.Response]:
        if headers is None:
            headers = {}

        try:
            response = requests.put(
                f"{self.base_url}{path}",
                json=json,
                headers={**headers, "Content-Type": "application/json"},
            )
            return response
        except Exception as e:
            print(f"Exception: {str(e)}")
            return None


class TestEndpointAPIIntegration(unittest.TestCase):
    """
    A test case class for integration testing the endpoint API. Start the functions framework as background process and kill it after the tests are done.

    Attributes:
        FILE (str): The name of the current file.
        BASE_URL (str): The base URL for the API endpoint.
        process (subprocess.Popen): The subprocess for running the Functions Framework.
    """

    FILE = __file__
    BASE_URL = "http://localhost:{}".format(os.getenv("PORT", 8005))
    process = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Client(self.BASE_URL)

    @classmethod
    def setUpClass(cls):
        cls.port = os.getenv("PORT", 8005)
        cls.process = subprocess.Popen(
            [
                "functions-framework",
                "--target",
                "main",
                "--source",
                os.path.basename(cls.FILE).replace("_test.py", ".py"),
                "--port",
                str(cls.port),
            ],
            cwd=os.path.dirname(cls.FILE),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        is_success = False
        for _ in range(10):
            try:
                requests.get(cls.BASE_URL)
                is_success = True
                break
            except Exception:
                time.sleep(1)

        if not is_success:
            raise Exception("Could not start Functions Framework process")

    @classmethod
    def tearDownClass(cls):
        if cls.process:
            cls.process.kill()
            cls.process.wait()
            cls.process = None
