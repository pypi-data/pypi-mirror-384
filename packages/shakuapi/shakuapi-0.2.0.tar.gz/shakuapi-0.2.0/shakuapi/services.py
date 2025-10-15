import requests
import base64

class ServicesAPI:
    def __init__(self, base_url):
        self.base_url = base_url

    def size_measurement(self, token, present_height, img_full_view_body, img_side_view_body):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        def encode_image(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        data = {
            "present_height": present_height,
            "img_full_view_body": encode_image(img_full_view_body),
            "img_side_view_body": encode_image(img_side_view_body)
        }
        r = requests.post(f"{self.base_url}/api/v1/services/sizeMeasurement", json=data, headers=headers)
        return r.json()

    def clothes_recognition(self, token, image_path):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        with open(image_path, "rb") as f:
            image_encoded = base64.b64encode(f.read()).decode("utf-8")

        data = {"image": image_encoded}
        r = requests.post(f"{self.base_url}/api/v1/services/autoTagging", json=data, headers=headers)
        return r.json()

    def garment_measurement(self, token, image_path):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        with open(image_path, "rb") as f:
            image_encoded = base64.b64encode(f.read()).decode("utf-8")

        data = {"Image": image_encoded}
        r = requests.post(f"{self.base_url}/api/v1/services/garmentMeasurement", json=data, headers=headers)
        return r.json()

