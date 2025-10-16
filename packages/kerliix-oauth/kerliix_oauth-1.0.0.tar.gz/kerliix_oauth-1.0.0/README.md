# Kerliix OAuth Python SDK

> Official Kerliix OAuth 2.0 SDK for Python

[![PyPI version](https://img.shields.io/pypi/v/kerliix-oauth.svg)](https://pypi.org/project/kerliix-oauth/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

**Kerliix OAuth Python SDK** provides a simple and secure way to integrate Kerliix authentication into your Python applications. It handles the full OAuth 2.0 flow including:

* Generating authorization URLs
* Exchanging authorization codes for tokens
* Token caching and auto-refresh
* Fetching user profile data
* Revoking tokens

---

## Installation

```bash
pip install kerliix-oauth
```

---

## Quick Start

```python
from kerliix_oauth import KerliixOAuth

client = KerliixOAuth(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="http://localhost:5175/callback",
    base_url="http://localhost:4000"
)

# Step 1: Generate auth URL
print("Login at:", client.get_auth_url())

# Step 2: Exchange code for tokens
# code = input("Enter code from redirect URL: ")
# tokens = client.exchange_code_for_token(code)
# print("Tokens:", tokens)

# Step 3: Fetch user info
# user = client.get_user_info(tokens.access_token)
# print("User:", user)
```

---

## Configuration Options

| Option          | Required | Description                                        |
| --------------- | -------- | -------------------------------------------------- |
| `client_id`     | ✅        | Your app’s client ID from Kerliix developer portal |
| `client_secret` | ⚙️       | Required for server-side (authorization code flow) |
| `redirect_uri`  | ✅        | The callback URI registered in your app            |
| `base_url`      | ✅        | Your Kerliix OAuth server URL                      |

---

## OAuth Flow

1. **User clicks login** → Redirect to Kerliix via `get_auth_url()`
2. **Kerliix authenticates** → Redirects back with `?code=XYZ`
3. **Your app exchanges code** → `exchange_code_for_token(code)`
4. **Use token** → Access user data via `get_user_info()`
5. **Optional** → Automatically refresh expired tokens using `refresh_token_if_needed()`

---

## API Reference

### `KerliixOAuth` Class

```python
client = KerliixOAuth(client_id, client_secret, redirect_uri, base_url)
```

### `get_auth_url(scopes=None, state="")`

Generates an OAuth authorization URL.

### `exchange_code_for_token(code)`

Exchanges an authorization code for access and refresh tokens.

### `refresh_token_if_needed()`

Refreshes the access token if it is expired or near expiry.

### `get_user_info(access_token=None)`

Fetches user profile data. Uses cached token if access_token is not provided.

### `revoke_token(token)`

Revokes an access or refresh token and clears cache.

---

## Token Caching

* Tokens are cached in memory with automatic refresh 30 seconds before expiry.
* Works seamlessly for long-running Python applications.

---

## License

MIT © Kerliix Corporation
