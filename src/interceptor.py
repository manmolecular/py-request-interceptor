#!/usr/bin/env python3

import http.client
from requests import post
from urllib.parse import urlparse


class Interceptor:
    """
    This class provides simple functions and methods
    to patch some parts of the standard Python3 HTTP library,
    such as http.client (maybe something else in future)

    To read more:
    1. https://docs.python.org/3/library/http.client.html
    2. https://github.com/python/cpython/tree/3.8/Lib/http/client.py
    """
    def __init__(self, client: http.client or None = None):
        """
        Initialize Interceptor class.
        No needed for now.
        """
        self.client = client or http.client

    def sniff_request(self, listener_url: str) -> None:
        """
        Sniff request and re-send it to another endpoint
        :param listener_url: listener URL
        :return: None
        """
        original_send = self.client.HTTPConnection.send

        def send_data(data) -> None:
            """
            Re-send data to another endpoint
            :param data: data to send
            :return: None
            """
            self.client.HTTPConnection.send = original_send
            try:
                post(url=listener_url, data=data)
            except:
                pass
            self.client.HTTPConnection.send = patch

        def patch(_self, data, *args, **kwargs) -> http.client.HTTPConnection.send:
            """
            Patch wrapper for original 'send' function
            :param _self: 'HTTPConnection' object instance
            :param data: any sendable data from original request
            :param args: additional positional arguments
            :param kwargs: additional named arguments
            :return: return 'HTTPConnection.send' with patched data
            """
            send_data(data)
            return original_send(_self, data)

        self.client.HTTPConnection.send = patch

    def patch_data(self, patch_data=None) -> None:
        """
        Patches original 'HTTPConnection.send' function to
        replace old data with the new one
        :param patch_data: any data that can be sent
        :return: None
        """
        original_send = self.client.HTTPConnection.send

        def patch(_self, data, *args, **kwargs) -> http.client.HTTPConnection.send:
            """
            Patch wrapper for original 'send' function
            :param _self: 'HTTPConnection' object instance
            :param data: any sendable data from original request
            :param args: additional positional arguments
            :param kwargs: additional named arguments
            :return: return 'HTTPConnection.send' with patched data
            """
            return original_send(_self, patch_data or data)

        self.client.HTTPConnection.send = patch

    def patch_target(self, patch_host, patch_port) -> None:
        """
        Patches original 'HTTPConnection.send' function to
        provide new target pair: (host, port)
        :param patch_host: new target host
        :param patch_port: new target port
        :return: None
        """
        original_send = self.client.HTTPConnection.send

        def patch_sock(_self, *args, **kwargs) -> http.client.HTTPConnection.connect:
            """
            Patch wrapper for original 'connect' function
            :param _self: 'HTTPConnection' object instance
            :param args: additional positional arguments
            :param kwargs: additional named arguments
            :return: return 'HTTPConnection.connect()' with patched target
            """
            _self.host = urlparse(patch_host).netloc
            _self.port = patch_port
            _self.connect()
            return _self

        def host_replace(host: str, data):
            """
            Replace 'Host: www.example.com' header with right header
            :param host: host to connect
            :param data: raw request
            :return: modified data
            """
            data_str = data.decode("utf-8")
            headers, body = data_str.split("\r\n\r\n")
            headers_split = headers.split("\r\n")
            for index, header in enumerate(headers_split or []):
                if "host:" in header.lower():
                    headers_split[index] = f"Host: {host}"
            headers = "\r\n".join(headers_split)
            data_str = f"{headers}\r\n\r\n{body}"
            return data_str.encode("utf-8")

        def patch_http(_self, data, *args, **kwargs) -> http.client.HTTPConnection.send:
            """
            Patch wrapper for original 'send' function
            :param _self: 'HTTPConnection' object instance
            :param data: any sendable data from original request
            :param args: additional positional arguments
            :param kwargs: additional named arguments
            :return: return 'HTTPConnection.send' with patched data
            """
            connection = patch_sock(_self)
            data = host_replace(connection.host, data)
            return original_send(connection, data)

        self.client.HTTPConnection.send = patch_http
