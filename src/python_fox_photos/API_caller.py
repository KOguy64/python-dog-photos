API_URL = "https://randomfox.ca/floof/"
API_JSON_KEY = "image"

import tkinter as tk
from io import BytesIO

import requests as r
from PIL import Image, ImageTk


def get_photo_url(api_url=API_URL, api_json_key=API_JSON_KEY) -> str:
    """Call set API_URL to get photo metadata"""
    response = r.get(api_url)
    response.raise_for_status()
    return response.json()[api_json_key]


def get_photo_file(
    photo_url: str,
) -> Image.Image:
    """Call photo url to get photo file"""

    response = r.get(photo_url)
    img = Image.open(BytesIO(response.content))
    return img


def get_new_photo(api_url=API_URL, api_json_key=API_JSON_KEY) -> Image.Image:
    """Get a new photo from the API"""
    photo_url = get_photo_url(api_url, api_json_key)
    photo_file = get_photo_file(photo_url)
    return photo_file


def display_photo(photo_file: Image.Image) -> None:
    """Display photo in a tkinter window which closes on any key"""
    root = tk.Tk()
    tk_img = ImageTk.PhotoImage(photo_file)
    label = tk.Label(root, image=tk_img)
    label.pack()

    root.bind("<Key>", lambda event: root.destroy())

    root.focus_force()
    root.mainloop()


if __name__ == "__main__":
    new_photo = get_new_photo()
    display_photo(new_photo)
