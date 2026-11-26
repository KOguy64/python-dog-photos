"""api_caller: handles calling the api, getting photos, and saving a cache"""

import json
from io import BytesIO
from pathlib import Path

import requests as r
from PIL import Image

OFFLINE_DIR = Path(__file__).parent / "offline"
OFFLINE_REPLY = OFFLINE_DIR / "reply.json"
OFFLINE_PHOTO = OFFLINE_DIR / "fox.jpg"


def get_photo_url(api_url, api_json_key) -> str:
    """Call set API_URL to get photo metadata"""
    response = r.get(api_url, timeout=10)
    response.raise_for_status()
    return response.json()[api_json_key]


def get_photo_file(
    photo_url: str,
) -> Image.Image:
    """Call photo url to get photo file"""

    response = r.get(photo_url, timeout=10)
    img = Image.open(BytesIO(response.content))
    return img


def save_offline_copy(api_url, api_json_key) -> None:
    """Save one API reply and its photo into the package for offline use"""
    response = r.get(api_url, timeout=10)
    response.raise_for_status()
    reply = response.json()
    OFFLINE_DIR.mkdir(exist_ok=True)
    OFFLINE_REPLY.write_text(json.dumps(reply, indent=2))
    get_photo_file(reply[api_json_key]).save(OFFLINE_PHOTO, format="JPEG")


if __name__ == "__main__":
    if OFFLINE_REPLY.exists() and OFFLINE_PHOTO.exists():
        print(f"Offline copy already exists in {OFFLINE_DIR}, leaving it alone")
    else:
        save_offline_copy("https://randomfox.ca/floof/", "image")
        print(f"Saved offline copy to {OFFLINE_DIR}")
