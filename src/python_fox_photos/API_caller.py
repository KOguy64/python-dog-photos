API_URL = "https://randomfox.ca/floof/"
API_JSON_KEY = "image"

from io import BytesIO

import requests as r
from PIL import Image


def get_photo_url():
    response = r.get(API_URL)
    return response.json()[API_JSON_KEY]


def get_photo_file(photo_url: str) -> Image.Image:
    response = r.get(photo_url)
    img = Image.open(BytesIO(response.content))
    return img


def get_new_photo() -> Image.Image:
    photo_url = get_photo_url()
    photo_file = get_photo_file(photo_url)
    return photo_file


if __name__ == "__main__":
    new_photo = get_new_photo()
    new_photo.show()
    input("end?")
