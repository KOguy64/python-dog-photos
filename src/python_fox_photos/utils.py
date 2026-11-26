from PIL import Image


def is_valid_image(img: Image.Image) -> bool:
    try:
        img.load()
        return True
    except (OSError, SyntaxError):
        return False


class InvalidPathError(Exception):

    def __init__(self, path):
        self.path = path
        self.message = f"{path} does not exist !"
        super().__init__(self.message)
