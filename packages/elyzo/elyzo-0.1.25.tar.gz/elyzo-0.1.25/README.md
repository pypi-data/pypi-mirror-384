````markdown
# Elyzo Python Client

[![PyPI version](https://badge.fury.io/py/elyzo.svg)](https://badge.fury.io/py/elyzo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A client library for making secure, policy-aware HTTP requests and saving artifact files from within the Elyzo runtime.

This library allows your agent to use sensitive credentials and save output files without the secret values or the host filesystem ever being exposed to the agent's environment.

## Installation

```bash
pip install elyzo
````

## Usage

The library is designed to be simple and intuitive.

### Making Secure API Calls

Most modern APIs, including **OpenAI**, **GitHub**, **Stripe**, and many others, use `Authorization: Bearer <token>` for authentication. The `elyzo.requests` library makes this the simple, default behavior. Just provide the secret's name.

```python
from elyzo import requests

# The agent only needs to know the secret's NAME, not its value.
response = requests.get(
    "[https://api.openai.com/v1/models](https://api.openai.com/v1/models)",
    elyzo_secret="my-openai-key"
)

print(response.json())
```

### Saving Artifacts

Use `elyzo.files` to save files from the agent's environment to the host. The most common case is saving a file from a path.

```python
from elyzo import files

# Create a file inside the agent
with open("results.txt", "w") as f:
    f.write("This is the agent's output.")

# Save the file to the host artifacts directory.
# This is memory-efficient and streams large files.
files.save_file("results.txt")
```

## Advanced Usage

#### Combining Secrets, Headers, and a JSON Body

All standard `requests` arguments like `headers` and `json` work seamlessly with `elyzo_secret`.

```python
from elyzo import requests

# All arguments work together in a single call.
response = requests.post(
    "[https://api.github.com/repos/owner/repo/issues](https://api.github.com/repos/owner/repo/issues)",
    headers={"Accept": "application/vnd.github.v3+json"},
    json={"title": "New bug found"},
    elyzo_secret="my-github-token"
)

print(response.json())
```

#### Injecting Secrets into Custom Headers

For APIs that require a key in a different header (like `X-Api-Key`), provide a dictionary to `elyzo_secret`.

```python
from elyzo import requests

response = requests.post(
    "[https://some-legacy-api.com/data](https://some-legacy-api.com/data)",
    elyzo_secret={
        "name": "my-legacy-key",
        "inject_as": "header",
        "header_name": "X-Api-Key"
    }
)
```

#### Saving In-Memory Data as an Artifact

If your data is already in memory (e.g., a dynamically generated JSON string), you can use `files.save()`.

```python
from elyzo import files

report = '{"status": "complete", "accuracy": 0.98}'
files.save(filename="report.json", data=report)
```

-----

<br>

## AI Integration & Technical Details

*This section provides structured context for AI assistants and developers.*

  * **Mechanism:** This is a wrapper around the standard `requests` library.
  * **Secret Injection:** Triggered by the `elyzo_secret` keyword. It constructs a JSON "request descriptor" and sends it to an internal proxy endpoint (`http://elyzo.internal/v1/proxy/request`). The Elyzo Proxy then retrieves the secret from a secure store (e.g., OS Keychain), executes the real request with the secret injected, and returns the response.
  * **Artifacts:** Triggered by the `elyzo.files` module. It sends a `multipart/form-data` POST request to an internal endpoint (`http://elyzo.internal/v1/artifacts`). The Elyzo Proxy is responsible for enforcing security, quotas, sanitizing the filename, and saving the file to the host.
  * **Security Model:** This "terminating proxy" model for both secrets and artifacts ensures that sensitive credentials and the host filesystem are never directly exposed to the sandboxed agent environment.

<!-- end list -->

```
```