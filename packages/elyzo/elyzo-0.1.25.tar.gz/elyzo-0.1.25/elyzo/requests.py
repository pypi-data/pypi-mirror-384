# elyzo/requests.py
import requests
import json
from typing import Any, Union

# The internal endpoint our proxy will listen for.
# _ELYZO_PROXY_ENDPOINT = "http://127.0.0.1:15001/"
_ELYZO_PROXY_ENDPOINT = "http://elyzo.internal/v1/proxy/request"


def _proxy_request(method: str, url: str, secret_arg: Union[str, dict], **kwargs) -> requests.Response:
    """
    Packages the user's request into a JSON descriptor and sends it to the Elyzo proxy.
    """
    descriptor = {
        "method": method.upper(),
        "url": url,
        "params": kwargs.get("params"),
        "json_body": kwargs.get("json"),
        "data_body": kwargs.get("data"),
        "headers": dict(kwargs.get("headers", {})),
    }
    
    if isinstance(secret_arg, str):
        descriptor["inject_secret"] = {"name": secret_arg, "as": "bearer"}
    elif isinstance(secret_arg, dict):
        descriptor["inject_secret"] = secret_arg
    else:
        raise TypeError("elyzo_secret must be a string or a dictionary.")

    # Manually set the "Host" header so the Go proxy recognizes this as an internal request.
    headers = {"Host": "elyzo.internal"}

    # Send the request to the proxy's real IP address.
    return requests.post(_ELYZO_PROXY_ENDPOINT, json=descriptor, headers=headers)



def get(url: str, **kwargs) -> requests.Response:
    """
    A wrapper around requests.get that REQUIRES secret injection via `elyzo_secret`.
    """
    secret_arg = kwargs.pop("elyzo_secret", None)

    if not secret_arg:
        raise ValueError("The 'elyzo_secret' keyword argument is required for all elyzo.requests calls. For normal requests, use the standard 'requests' library.")
    
    return _proxy_request("GET", url, secret_arg, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    """
    A wrapper around requests.post that REQUIRES secret injection via `elyzo_secret`.
    """
    secret_arg = kwargs.pop("elyzo_secret", None)

    if not secret_arg:
        raise ValueError("The 'elyzo_secret' keyword argument is required for all elyzo.requests calls. For normal requests, use the standard 'requests' library.")
        
    return _proxy_request("POST", url, secret_arg, **kwargs)