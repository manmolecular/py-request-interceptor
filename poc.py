#!/usr/bin/env python3

from src.interceptor import Interceptor
from requests import get
from requests.utils import CaseInsensitiveDict

# Initialize 'Interceptor' here, nothing special
intercept = Interceptor()


class OriginalValues:
    """
    This test-class defines original values
    """

    TARGET_HOST = "https://www.google.com/"
    TARGET_PORT = 443


class InterceptValues:
    """
    This test-class defines override values for 'Intercept' class instance
    """

    TARGET_HOST = "http://evil.com/"
    TARGET_PORT = 443

    # FIXME: Set your own requestbin here (or any available listening endpoint) (required to '.sniff'!)
    LISTENER_ENDPOINT = "http://requestbin.net/r/YOUR_REQUESTBIN_ID"

    # FIXME: Modify this request as you wish (but remember that 'Host:' header should be correct)
    TARGET_DATA = (
        "GET / HTTP/1.1\r\n"
        "Host: www.google.com\r\n"
        "User-Agent: Interceptor\r\n"
        "Accept-Encoding: gzip, deflate\r\n"
        "Accept: */*\r\n"
        "Connection: keep-alive\r\n"
        "\r\n "
    )


@intercept.target(host=InterceptValues.TARGET_HOST, port=InterceptValues.TARGET_PORT)
def example_target_connect() -> CaseInsensitiveDict:
    """
    Redirects original-host.com -> evil-host.com
    :return: response headers
    """
    return get(url=OriginalValues.TARGET_HOST).headers


@intercept.sniff(listener=InterceptValues.LISTENER_ENDPOINT)
@intercept.dump()
@intercept.data(data=InterceptValues.TARGET_DATA)
def example_sniff_connect() -> CaseInsensitiveDict:
    """
    Patch request data (change 'User-Agent' + send copy to the listener endpoint, requestbin for example)
    :return: response headers
    """
    return get(url=OriginalValues.TARGET_HOST).headers


@intercept.dump()
def example_original_connect() -> CaseInsensitiveDict:
    """
    Returns original response headers from original-host.com (to compare with)
    :return: response headers
    """
    return get(url=OriginalValues.TARGET_HOST).headers


if __name__ == "__main__":
    # Shows 'google.com' headers
    print(example_original_connect())

    # Shows 'evil.com' headers
    print(example_target_connect())

    # Shows 'google.com' headers (the same as the first one, but with changed data)
    print(example_sniff_connect())
