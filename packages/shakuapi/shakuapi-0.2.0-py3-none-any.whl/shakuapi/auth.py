import requests
import time

class AuthAPI:
    def __init__(self, base_url, client_id, client_secret):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret

    def get_access_token(self, username, password):
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password
        }
        response = requests.post(f"{self.base_url}/oauth/token", json=data)
        result = response.json()
        result["created_at"] = time.time()
        return result

    def refresh_token(self, refresh_token):
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(f"{self.base_url}/oauth/token", json=data)
        result = response.json()
        result["created_at"] = time.time()
        return result

    def revoke_token(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        requests.get(f"{self.base_url}/api/v1/auth/revoke", headers=headers)
