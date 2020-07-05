#!/usr/bin/env python3

import http.client
from requests import post
from urllib.parse import urlparse
from typing import Union


class InterceptorBase:
    """
    This class provides simple functions and methods
    to patch some parts of the standard Python3 HTTP library,
    such as http.client (maybe something else in future)

    Work In Progress, PoC stage.

    Can be used to catch API calls from other libraries, intercept it,
    sniff and something else.

    This is the base class, so it is no need to use it directly.
    Please, use the 'Interceptor' class instance or write your own
    required handlers in the 'Interceptor'.

    Thanks.

    To read more:
    1. https://docs.python.org/3/library/http.client.html
    2. https://github.com/python/cpython/tree/3.8/Lib/http/client.py
    """

    def __init__(self, client: http.client or None = None):
        """
        Initialize Interceptor base class.
        Not really required IRL, but helpful for purposes
        like saving of the original 'send' point + client settings
        :param client: client to use to, 'http.client' as default one
        """
        self.client = client or http.client
        self.original_send = self.client.HTTPConnection.send

    def _restore_send(self) -> None:
        """
        Restore original send function call after use
        :return: None
        """
        self.client.HTTPConnection.send = self.original_send

    def _sniff_request(self, listener_url: str) -> None:
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
                if not isinstance(data, bytes):
                    data = data.encode("utf-8")
                post(url=listener_url, data=data)
            except Exception as unexp_send_err:
                # TODO: Do something with this exception in future
                ...
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

    def _patch_data(self, patch_data_body=None) -> None:
        """
        Patches original 'HTTPConnection.send' function to
        replace old data with the new one
        :param patch_data_body: any data that can be sent
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
            encoded_patch_body = None
            if patch_data_body is not None and not isinstance(patch_data_body, bytes):
                encoded_patch_body = patch_data_body.encode("utf-8")
            return original_send(_self, encoded_patch_body or data)

        self.client.HTTPConnection.send = patch

    def _patch_target(self, patch_host, patch_port) -> None:
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
            FIXME: Improve the logic here (it should be better!)
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


class Interceptor(InterceptorBase):
    def __init__(self, client: http.client or None = None):
        """
        Wrap 'InterceptorBase' as decorator or handler functions
        :param client: client to use
        """
        super().__init__(client=client)

    def target(self, host, port) -> callable:
        """
        Wrap function to lead requests to another target
        :param host: host to lead to
        :param port: port to lead to
        :return: wrap function
        """

        def wrap(function):
            def wrapped_function(*args, **kwargs):
                self._patch_target(patch_host=host, patch_port=port)
                function_output = function(*args, **kwargs)
                self._restore_send()
                return function_output

            return wrapped_function

        return wrap

    def data(self, data: Union[str, bytes]) -> callable:
        """
        Replace original data with something new
        :param data: new data
        :return: wrap function
        """

        def wrap(function):
            def wrapped_function(*args, **kwargs):
                self._patch_data(patch_data_body=data)
                function_output = function(*args, **kwargs)
                self._restore_send()
                return function_output

            return wrapped_function

        return wrap

    def sniff(self, listener: str) -> callable:
        """
        Sniff requests
        :param listener: listener endpoint
        :return: wrap function
        """

        def wrap(function):
            def wrapped_function(*args, **kwargs):
                self._sniff_request(listener_url=listener)
                function_output = function(*args, **kwargs)
                self._restore_send()
                return function_output

            return wrapped_function

        return wrap
