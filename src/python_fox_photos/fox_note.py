from pathlib import Path

from PIL import Image

from .utils import InvalidPathError


class FoxNote:
    def __init__(
        self,
        path: Path,
        img: Image.Image,
        name: str,
        score: int = 5,
        note: str | None = None,
    ):
        self.path = path
        self.img = img
        self.name: str = name
        self.score: int = score
        self.note: str | None = note

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path) -> None:
        path = Path(path)
        if not path.exists():
            raise InvalidPathError(path)
        self._path: Path = path

    @property
    def img(self) -> Image.Image:
        return self._img

    @img.setter
    def img(self, img):
        if is_valid_image(img):
            self._img: Image.Image = img
