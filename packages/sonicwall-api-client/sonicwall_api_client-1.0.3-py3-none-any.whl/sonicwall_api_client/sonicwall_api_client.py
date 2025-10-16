#!/usr/bin/env python
#
#
# Copyright (c) 2025 Samuel Berset
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import requests
import urllib3
from requests.auth import HTTPDigestAuth

urllib3.disable_warnings()


def get_result(response):
    result = response.json()

    if "status" in result:
        success = result["status"].get("success", False)
        message = result["status"].get("info", [{}])[0].get("message", "Unknown error")
        if message == "TOTP":
            return False, "TOTP required", None
        return success, message, None

    return True, "Success.", result


class SonicWallClient:
    def __init__(self, ip: str, port: int, username: str, password: str, tfa: int | None):
    #def __init__(self, ip, port, username, password, tfa=None):
        """
        Initialize a session with the SonicWall API using HTTP Digest Authentication.

        Args:
            ip (str): The IP address of the SonicWall firewall.
            port (int): The port number of the API.
            username (str): The admin username.
            password (str): The admin password.
            tfa (int, optional): The two-factor authentication (2FA/TFA) code if required. Defaults to None.
        """
        self.api_url = f"https://{ip}:{port}/api/sonicos"
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(username, password)
        self.username = username
        self.password = password
        self.tfa = tfa
        self.session.verify = False
        self.bearer_token = None
        self.header = None


    # --- Login / Logout ---

    def login(self) -> tuple[bool, str, dict | None]:
        """
        Authenticate the session with the SonicWall API.
        """
        if self.tfa:
            url = f"{self.api_url}/tfa"

            payload = {
                "user": self.username,
                "password": self.password,
                "tfa": self.tfa,
                "override": True}
        
        else:
            url = f"{self.api_url}/auth"

            payload = {"override": True}

        response = self.session.post(url, json=payload)
        
        self.bearer_token = response.json()["status"].get("info", [{}])[0].get("bearer_token", None)
        if self.bearer_token:
            self.header = {"Authorization": f"Bearer {self.bearer_token}"}
        
        return get_result(response)

    
    def logout(self) -> tuple[bool, str, dict | None]:
        """
        Logout current sessioin.
        """
        url = f"{self.api_url}/auth"
        response = self.session.delete(url)
        return get_result(response)


    # --- pending configurations ---

    def get_pending_configurations(self) -> tuple[bool, str, dict | None]:
        """
        Check if there are pending (unsaved) configuration changes.
        """
        url = f"{self.api_url}/config/pending"
        response = self.session.get(url)
        return get_result(response)
    

    def commit(self) -> tuple[bool, str, dict | None]:
        """
        Commit all pending configuration changes to make them permanent.
        """
        url = f"{self.api_url}/config/pending"
        response = self.session.post(url, json={})
        return get_result(response)
    

    def delete_pending_configurations(self) -> tuple[bool, str, dict | None]:
        """
        Commit all pending configuration changes to make them permanent.
        """
        url = f"{self.api_url}/config/pending"
        response = self.session.delete(url, json={})
        return get_result(response)
    

    # --- generic request ---

    def request(self, method: str, path: str, payload: dict =None) -> tuple[bool, str, dict | None]:
        """
        Do a generic request.

        Args:
            method (string): get, post, put, patch, delete
            path (string): Ex: "/address-object/ipv4" ...
            payload (dict): net always required
        """
        url = f"{self.api_url}{path}"
        response = None
        method = method.lower()

        if method == "get":
            response = self.session.get(url, json=payload)
        elif method == "post":
            response = self.session.post(url, json=payload)
        elif method == "put":
            response = self.session.put(url, json=payload)
        elif method == "patch":
            response = self.session.patch(url, json=payload)
        elif method == "delete":
            response = self.session.delete(url, json=payload)
        else:
            return False, "Bad method", None
        
        return get_result(response)
