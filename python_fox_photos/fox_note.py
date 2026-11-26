"""fox_note: handles a fox's image, note, and
score, also handles loading, saving, and deletinig on disk"""

import json
from pathlib import Path

from PIL import Image

from .utils import (
    InvalidImgError,
    InvalidPathError,
    MetadataError,
    ScoreError,
    are_images_same,
    display_photo,
    is_valid_image,
)


class FoxNote:
    """Stores a fox images and it's notes, scores, and name"""

    def __init__(
        self,
        img: Image.Image,
    ):
        self.img = img
        self._has_metadata: bool = False
        self.name: str | None = None
        self._score: float | None = None
        self._note: str | None = None

    @property
    def img(self) -> Image.Image:
        """Returns a fox's photo"""
        return self._img

    @property
    def has_metadata(self):
        """Returns True if a fox has a score and a note"""
        return self._has_metadata

    @img.setter
    def img(self, img):
        if is_valid_image(img):
            self._img: Image.Image = img
        else:
            raise InvalidImgError

    @property
    def note(self) -> str | None:
        """Returns a fox's note (if it has it, else raises MetadataError)"""
        if self.has_metadata:
            return self._note
        else:
            raise MetadataError

    def add_metadata(self, note: str, score: float) -> None:
        """Add a note and a score to a fox"""
        self._note = note
        self.score = score
        self._has_metadata = True

    def get_metadata(self) -> dict:
        """Get a foxs notes and score"""
        return {"note": self.note, "score": self.score}

    @property
    def score(self) -> float | None:
        """Returns a fox's score (if it has it, else raises MetadataError)"""
        if self.has_metadata:
            return self._score

    @score.setter
    def score(self, score: float):
        if score >= 0 and score <= 10:
            self._score = score
        else:
            raise ScoreError(score)

    def display(self):
        """Display a fox's image"""
        display_photo(self.img)

    def __eq__(self, foxnote) -> bool:
        """Check if two foxs are equal by comparing all attributes"""
        if self.has_metadata != foxnote.has_metadata:
            return False

        if self.has_metadata and (
            self.note != foxnote.note or self.score != foxnote.score
        ):
            return False
        if self.name and foxnote.name and (self.name != foxnote.name):
            return False
        return are_images_same(self.img, foxnote.img)


def save_foxnote(foxnote: FoxNote, path: Path):
    """Save a fox its notes and score to system"""
    if foxnote.has_metadata:
        # If foxnote has metadata (saves as a dir), assure that dir exists
        if not path.exists():
            path.mkdir()

        # Save metadata
        metadata_path = path / Path("metadata.json")
        with open(metadata_path, "w") as metadata_file:
            json.dump(foxnote.get_metadata(), metadata_file)

        # Save image
        img_path = path / Path("image.jpg")
        foxnote.img.save(img_path, format="JPEG")

    else:
        img_path = path.with_suffix(".jpg")
        foxnote.img.save(img_path, format="JPEG")


def del_foxnote(path: Path, has_metadata: bool):
    """Delete a fox and its notes and scoresfrom the system"""
    if has_metadata and not path.exists():
        return

    if has_metadata:
        img_path = path / Path("image.jpg")
    else:
        img_path = path.with_suffix(".jpg")

    img_path.unlink(missing_ok=True)

    if has_metadata:
        metadata_path = path / Path("metadata.json")
        metadata_path.unlink(missing_ok=True)
        path.rmdir()


def load_foxnote(path: Path, name: str, has_metadata: bool):
    """Load a fox and its notes and scores from the system"""
    if has_metadata:
        img_path = path / Path("image.jpg")
    else:
        img_path = path.with_suffix(".jpg")

    if not img_path.exists():
        raise InvalidPathError(path)

    img = Image.open(img_path)
    foxnote = FoxNote(img)
    foxnote.name = name

    if has_metadata:
        metadata_path = path / Path("metadata.json")
        if not metadata_path.exists():
            raise InvalidPathError(path)
        with open(metadata_path, "r") as metadata_file:
            metadata_dict = json.load(metadata_file)
        note, score = metadata_dict["note"], metadata_dict["score"]

        foxnote.add_metadata(note, score)

    return foxnote
