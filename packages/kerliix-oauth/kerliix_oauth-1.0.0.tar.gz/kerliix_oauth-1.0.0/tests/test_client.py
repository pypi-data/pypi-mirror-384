import pytest
from kerliix_oauth import KerliixOAuth

CLIENT_ID = "demo-client"
CLIENT_SECRET = "demo-secret"
REDIRECT_URI = "http://localhost:5175/callback"
BASE_URL = "http://localhost:4000"

def test_auth_url():
    client = KerliixOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, BASE_URL)
    url = client.get_auth_url(scopes=["openid", "profile", "email"], state="test123")
    assert "client_id=demo-client" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A5175%2Fcallback" in url
    assert "response_type=code" in url
    print("✅ Authorization URL:", url)
