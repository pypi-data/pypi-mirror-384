# SonicWall API Python Client

A simple Python client for interacting with the SonicWall SonicOS REST API, using HTTP Digest Authentication.

## Features

- Login / logout to the SonicOS API
- Check and manage pending configurations
- Generic requests (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`)
- Persistent session support via `requests.Session()`

## Installation

Install the package from PyPI:

```bash
pip install sonicwall-api-client
```

## Import

```python
from sonicwall_api_client import SonicWallClient
```

## Examples

### Initialize the client

```python
# Initialize the client (with optional TFA code)
client = SonicWallClient(
    ip="192.168.1.1",
    port=443,
    username="admin",
    password="password"
    tfa="123456"  # optional, only if TFA is enabled
)
```
> **Note**  
> The `tfa` argument is optional and should only be provided if the SonicWall firewall is configured with Two-Factor Authentication (TFA/2FA).  
> If TFA is not required, you can omit this argument.


### Connect to the firewall

```python
# Log in
success, message, _ = client.login()
if success:
    print("Login successful.")
else:
    print(f"Login failed: {message}")
```

### Check pending configurations

```python
success, message, data = client.get_pending_configurations()
if success:
    print("Pending configurations:", data)
else:
    print(f"Error: {message}")
```

### Commit configurations

```python
success, message, _ = client.commit()
if success:
    print("Configurations committed successfully.")
else:
    print(f"Commit error: {message}")
```

### Discard pending configurations

```python
success, message, _ = client.delete_pending_configurations()
if success:
    print("Pending changes discarded.")
else:
    print(f"Error: {message}")
```

### Generic request

```python
# Without payload
success, message, data = client.request("get", "/zones")
if success:
    print("Zones list:", data)
else:
    print(f"Request error: {message}")

# With payload
payload = {
    "zones": [
        {
            "name": "LAN_IT",
            "security_type": "public",
            "interface_trust": False,
            "auto_generate_access_rules": {
                "allow_from_to_equal": False,
                "allow_from_higher": False,
                "allow_to_lower": False,
                "deny_from_lower": False
            },
        }
    ]
}

success, message, _ = client.request("post", "/zones", payload)
if success:
    print("Object created successfully.")
else:
    print(f"Creation error: {message}")
```

### Logout

```python
success, message, _ = client.logout()
if success:
    print("Logged out successfully.")
else:
    print(f"Logout error: {message}")
```

## License

MIT