"""utils: utility functions to help with processing"""

import tkinter as tk

from PIL import Image, ImageChops, ImageTk


def are_images_same(img1: Image.Image, img2: Image.Image):
    """Check if two PIL Images are the same"""
    if img1.size != img2.size or img1.mode != img2.mode:
        return False
    diff = ImageChops.difference(img1, img2)
    return not (diff.getbbox())


def is_valid_image(img: Image.Image) -> bool:
    """Check if PIL Image is valid"""
    try:
        img.load()
        return True
    except (OSError, SyntaxError):
        return False


def display_photo(photo_file: Image.Image) -> None:
    """Display photo in a tkinter window which closes on any key"""
    root = tk.Tk()
    tk_img = ImageTk.PhotoImage(photo_file)
    label = tk.Label(root, image=tk_img)
    label.pack()

    root.bind("<Key>", lambda event: root.destroy())

    root.focus_force()
    root.mainloop()


class InvalidPathError(Exception):
    """Raises if path is invalid"""

    def __init__(self, path):
        self.path = path
        self.message = f"{path} does not exist !"
        super().__init__(self.message)


class InvalidImgError(Exception):
    """Raises if image is invalid"""

    def __init__(self):
        self.message = "Image is invalid !"
        super().__init__(self.message)


class ScoreError(Exception):
    """Raises if score is invalid"""

    def __init__(self, score):
        self.score = score
        self.message = f"{score} is an invalid score !"
        super().__init__(self.message)


class NoNameError(Exception):
    """Raises if fox doesn't have a name"""

    def __init__(self):
        self.message = "This fox doesn't have a name ! Add a name to this fox first."
        super().__init__(self.message)


class MetadataError(Exception):
    """Raises if metadata does not exist"""

    def __init__(self):
        self.message = "Metadata does not exist yet ! Add metadata to this fox first."
        super().__init__(self.message)
