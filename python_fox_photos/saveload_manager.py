"""saveload_manager: handles list of foxes, saved as a ListDir into a json file"""

import copy
import json
from pathlib import Path

from python_fox_photos.utils import InvalidPathError, UnsafePathError

from .fox_note import FoxNote

MAIN_DIR_KEY = "main_dir"
SAVED_FILES_KEY = "saved_files"


class ListDir:
    """An object containing the main storage directory and a listing of saved files"""

    def __init__(self, main_dir: Path, saved_files: dict):
        if not main_dir.exists():
            main_dir.mkdir(parents=True, exist_ok=True)
        self.main_dir = main_dir
        self.saved_files = copy.deepcopy(saved_files)

    @property
    def main_dir(self):
        """Return the main directory used for storing foxes"""
        return self._main_dir

    @main_dir.setter
    def main_dir(self, path: Path) -> None:
        if path.exists():
            self._main_dir = str(path)
        else:
            raise InvalidPathError(path)

    def resolve_path(self, path: Path) -> Path:
        """Join path onto main_dir, raising UnsafePathError if it escapes main_dir"""
        main_dir = Path(self.main_dir).resolve()
        full_path = (main_dir / path).resolve()
        if full_path == main_dir or not full_path.is_relative_to(main_dir):
            raise UnsafePathError(path)
        return full_path

    def add_file(self, note: FoxNote, path: Path) -> None:
        """Add a file to the listing"""
        self.saved_files[note.name] = {
            "has_metadata": note.has_metadata,
            "path": str(path),
        }

    def remove_file(self, name):
        """Remove a file from the listing"""
        self.saved_files.pop(name)

    def __eq__(self, listdir) -> bool:
        return (
            self.main_dir == listdir.main_dir
            and self.saved_files == listdir.saved_files
        )

    def __str__(self) -> str:
        return (
            f"ListDir(\nmain_dir: {self.main_dir}\nsaved_files: {self.saved_files}\n)"
        )


def load_listdir(listdir_path: Path) -> ListDir:
    """Load a listing from a json file"""
    with open(listdir_path, "r") as file:
        listdir_json = json.load(file)

    main_dir = Path(listdir_json[MAIN_DIR_KEY])
    saved_files = listdir_json[SAVED_FILES_KEY]
    if isinstance(saved_files, list):
        raise TypeError
    return ListDir(main_dir, saved_files)


def save_listdir(listdir: ListDir, listdir_path: Path):
    """Save a listing to a json file"""
    saved_file_dict = {"main_dir": listdir.main_dir, "saved_files": listdir.saved_files}
    with open(listdir_path, "w") as file:
        json.dump(saved_file_dict, file)
