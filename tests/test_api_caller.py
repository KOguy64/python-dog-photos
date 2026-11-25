from pathlib import Path

import pytest
from PIL import Image, ImageChops

from python_fox_photos.API_caller import get_new_photo, get_photo_file, get_photo_url

PHOTO_PAGE_PREFIX = "https://randomfox.ca/images"

BAD_API = "https://gobbledygook.com"
BAD_KEY = "amongus"

TEST_PHOTO_DIR = Path("tests/test_photos")
TEST_PHOTO_TUPLE = [
    ("https://randomfox.ca/images/97.jpg", "test_1.jpg"),
    ("https://randomfox.ca/images/37.jpg", "test_2.jpg"),
    ("https://randomfox.ca/images/1.jpg", "test_3.jpg"),
    ("https://randomfox.ca/images/17.jpg", "test_4.jpg"),
    ("https://randomfox.ca/images/34.jpg", "test_5.jpg"),
]


def test_get_photo_calls_correct_page():
    assert PHOTO_PAGE_PREFIX in get_photo_url()


@pytest.mark.parametrize("photo_url, test_photo_file", TEST_PHOTO_TUPLE)
def test_photo_url_gets_correct_imgs(photo_url, test_photo_file):
    test_photo_path = TEST_PHOTO_DIR / Path(test_photo_file)
    print(photo_url, test_photo_path)
    image = get_photo_file(photo_url)
    test_photo = Image.open(test_photo_path)
    diff = ImageChops.difference(image, test_photo)
    assert not diff.getbbox()


def test_bad_API_raises_error():
    with pytest.raises(Exception):
        get_new_photo(api_url=BAD_API)


def test_bad_key_raises_error():
    with pytest.raises(KeyError):
        get_new_photo(api_json_key=BAD_KEY)
