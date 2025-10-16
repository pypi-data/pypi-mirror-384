import requests
import base64
import time
from urllib.parse import urlencode
from typing import List, Optional
from .cache import TokenCache
from .types import TokenResponse, UserInfo

class KerliixOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, base_url: str):
        if not all([client_id, redirect_uri, base_url]):
            raise ValueError("client_id, redirect_uri, and base_url are required")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url.rstrip('/')
        self.cache = TokenCache()

    def get_auth_url(self, scopes: Optional[List[str]] = None, state: str = "") -> str:
        scopes = scopes or ["openid", "profile", "email"]
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state
        }
        return f"{self.base_url}/oauth/authorize?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> TokenResponse:
        url = f"{self.base_url}/oauth/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        resp = requests.post(
            url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            },
            headers={"Authorization": f"Basic {auth_header}"}
        )
        if not resp.ok:
            raise Exception(f"Token exchange failed: {resp.status_code} {resp.text}")
        data = resp.json()
        token = TokenResponse(**data)
        self.cache.set(token)
        return token

    def refresh_token_if_needed(self) -> Optional[TokenResponse]:
        cached = self.cache.get()
        if cached:
            return cached
        last = self.cache.token
        if not last or not last.refresh_token:
            return None
        url = f"{self.base_url}/oauth/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        resp = requests.post(
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": last.refresh_token
            },
            headers={"Authorization": f"Basic {auth_header}"}
        )
        if not resp.ok:
            raise Exception(f"Failed to refresh token: {resp.status_code} {resp.text}")
        data = resp.json()
        token = TokenResponse(**data)
        self.cache.set(token)
        return token

    def get_user_info(self, access_token: Optional[str] = None) -> UserInfo:
        token = access_token or (self.refresh_token_if_needed().access_token if self.refresh_token_if_needed() else None)
        if not token:
            raise Exception("Missing access token")
        url = f"{self.base_url}/oauth/userinfo"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        if not resp.ok:
            raise Exception(f"Failed to fetch user info: {resp.status_code} {resp.text}")
        data = resp.json()
        return UserInfo(**data)

    def revoke_token(self, token: str) -> bool:
        url = f"{self.base_url}/oauth/revoke"
        resp = requests.post(url, json={"token": token})
        if resp.ok:
            self.cache.clear()
        return resp.ok
