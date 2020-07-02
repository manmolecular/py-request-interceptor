#!/usr/bin/env python3

from src.interceptor import Interceptor
from requests import get


class InterceptValues:
    TARGET_HOST = "YOUR_REDIRECT_HOST"
    TARGET_PORT = 443


def example_connect():
    """
    Check intercepted connect
    :return: response body
    """
    response = get(url="https://www.google.com/")
    print(response.text)


if __name__ == "__main__":
    interceptor = Interceptor()
    interceptor.sniff_request(listener_url="http://requestbin.net/r/YOUR_REQUEST_BIN")
    example_connect()
