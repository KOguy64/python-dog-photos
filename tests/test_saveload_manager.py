from pathlib import Path

import pytest
from PIL import Image

from python_fox_photos.fox_note import FoxNote
from python_fox_photos.saveload_manager import ListDir, load_listdir, save_listdir

LISTDIRJSON_PATH = Path("tests/listdir.json")
BAD_LISTDIRJSON_PATH = Path("tests/badlistdir.json")
MAINDIR_PATH = Path("tests/test_saved_photos")


@pytest.fixture()
def good_listdir() -> ListDir:
    return ListDir(MAINDIR_PATH, {"cute fox": {"has_metadata": True, "path": "test_1"}})


def test_loading_listdir_works(good_listdir):
    loaded_listdir = load_listdir(LISTDIRJSON_PATH)
    print(loaded_listdir, good_listdir)
    assert loaded_listdir == good_listdir


def test_listdir_saves_correctly(good_listdir):
    test_dir = Path("test.json")
    test_dir.unlink(missing_ok=True)
    save_listdir(good_listdir, test_dir)
    assert load_listdir(test_dir) == good_listdir
    test_dir.unlink(missing_ok=True)


# Deleting entries


def test_remove_file_removes_entry(good_listdir):
    good_listdir.remove_file("cute fox")
    assert "cute fox" not in good_listdir.saved_files


def test_remove_missing_file_raises(good_listdir):
    with pytest.raises(KeyError):
        good_listdir.remove_file("not a fox")


def test_remove_file_does_not_touch_source_dict():
    saved_files = {"cute fox": {"has_metadata": True, "path": "test_1"}}
    listdir = ListDir(MAINDIR_PATH, saved_files)
    listdir.remove_file("cute fox")
    assert "cute fox" in saved_files


def test_removal_persists_after_save(good_listdir, tmp_path):
    listdir_path = tmp_path / "listdir.json"
    good_listdir.remove_file("cute fox")
    save_listdir(good_listdir, listdir_path)
    assert load_listdir(listdir_path).saved_files == {}


def test_add_then_remove_restores_listdir(good_listdir):
    note = FoxNote(Image.new("RGB", (16, 16), "orange"))
    note.name = "temp fox"
    good_listdir.add_file(note, Path("temp_fox"))
    good_listdir.remove_file("temp fox")
    assert good_listdir == ListDir(
        MAINDIR_PATH, {"cute fox": {"has_metadata": True, "path": "test_1"}}
    )


def test_listdir_creates_missing_main_dir(tmp_path):
    main_dir = tmp_path / "new_dir"
    ListDir(main_dir, {})
    assert main_dir.is_dir()
