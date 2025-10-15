import time
from .auth import AuthAPI
from .services import ServicesAPI

class ShakuClient:
    def __init__(self, client_id, client_secret, base_url="https://api.shaku.tech"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.auth = AuthAPI(base_url, client_id, client_secret)
        self.services = ServicesAPI(base_url)
        self.token_info = None

    def login(self, username, password):
        self.token_info = self.auth.get_access_token(username, password)

    def refresh(self):
        if self.token_info and "refresh_token" in self.token_info:
            self.token_info = self.auth.refresh_token(self.token_info["refresh_token"])

    def revoke(self):
        if self.token_info and "access_token" in self.token_info:
            self.auth.revoke_token(self.token_info["access_token"])
            self.token_info = None

    def _check_token(self):
        if not self.token_info:
            raise Exception("Please login first.")
        if time.time() > self.token_info["created_at"] + self.token_info["expires_in"]:
            self.refresh()

    def size_measurement(self, present_height, img_full_view_body, img_side_view_body):
        self._check_token()
        return self.services.size_measurement(
            token=self.token_info["access_token"],
            present_height=present_height,
            img_full_view_body=img_full_view_body,
            img_side_view_body=img_side_view_body
        )

    def clothes_recognition(self, image_path):
        self._check_token()
        return self.services.clothes_recognition(
            token=self.token_info["access_token"],
            image_path=image_path
        )

    def garment_measurement(self, image_path):
        self._check_token()
        return self.services.garment_measurement(
            token=self.token_info["access_token"],
            image_path=image_path
        )

