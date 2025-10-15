# file: elyzo/files.py
import requests
import os
from typing import Union

# For testing outside a container, we point directly to the proxy's real address.
# In a real container environment, this would be http://elyzo.internal/v1/artifacts
# _ELYZO_ARTIFACT_ENDPOINT = "http://127.0.0.1:15001/v1/artifacts"
_ELYZO_ARTIFACT_ENDPOINT = "http://elyzo.internal/v1/artifacts"

def save(filename: str, data: Union[bytes, str]):
    """
    Saves in-memory data (as bytes or a string) to the Elyzo artifacts store.
    
    :param filename: The name the file should be saved as.
    :param data: The content of the file.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    # `multipart/form-data` is the standard for file uploads.
    files = {
        # The key 'file_data' must match what the Go proxy expects.
        'file_data': (filename, data, 'application/octet-stream')
    }
    form_data = {
        'filename': filename
    }
    
    # Manually set the "Host" header so the proxy's routing logic works.
    headers = {"Host": "elyzo.internal"}

    try:
        response = requests.post(_ELYZO_ARTIFACT_ENDPOINT, data=form_data, files=files, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error saving artifact '{filename}': {e}")
        return None

def save_file(filepath: str):
    """
    Saves a file from a local path to the Elyzo artifacts store.
    This method streams the file from disk and is memory-efficient for large files.

    :param filepath: The path to the file to save.
    """
    # Extract the base filename from the path.
    filename = os.path.basename(filepath)

    try:
        # Open the file in binary read mode. The `with` statement ensures it's closed.
        with open(filepath, "rb") as f:
            # The requests library will automatically stream from the file object `f`.
            files = {
                'file_data': (filename, f, 'application/octet-stream')
            }
            form_data = {
                'filename': filename
            }
            
            headers = {"Host": "elyzo.internal"}

            response = requests.post(_ELYZO_ARTIFACT_ENDPOINT, data=form_data, files=files, headers=headers)
            response.raise_for_status()
            return response
    except FileNotFoundError:
        print(f"Error: File not found at path '{filepath}'")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error saving artifact from path '{filepath}': {e}")
        return None