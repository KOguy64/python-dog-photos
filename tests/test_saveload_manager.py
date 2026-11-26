from pathlib import Path

import pytest
from PIL import Image

from python_fox_photos.fox_note import FoxNote
from python_fox_photos.saveload_manager import ListDir, load_listdir, save_listdir
from python_fox_photos.utils import UnsafePathError

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


# Path injection


UNSAFE_PATHS = [
    pytest.param("..", id="parent"),
    pytest.param("../foxy", id="parent-file"),
    pytest.param("../../foxy", id="grandparent-file"),
    pytest.param("a/../../foxy", id="sneaky-parent"),
    pytest.param("a/b/../../../foxy", id="deep-sneaky-parent"),
    pytest.param("", id="empty"),
    pytest.param(".", id="main-dir-itself"),
    pytest.param("a/..", id="back-to-main-dir"),
    pytest.param("/tmp/foxy", id="absolute"),
]


@pytest.mark.parametrize("path", UNSAFE_PATHS)
def test_resolve_path_rejects_escaping_paths(tmp_path, path):
    listdir = ListDir(tmp_path / "main", {})
    with pytest.raises(UnsafePathError):
        listdir.resolve_path(Path(path))


@pytest.mark.parametrize("path", ["foxy", "a/foxy", "a/../foxy", "./foxy"])
def test_resolve_path_accepts_paths_inside_main_dir(tmp_path, path):
    listdir = ListDir(tmp_path / "main", {})
    resolved = listdir.resolve_path(Path(path))
    assert resolved.is_relative_to((tmp_path / "main").resolve())


def test_resolve_path_rejects_symlink_out_of_main_dir(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    listdir = ListDir(tmp_path / "main", {})
    (tmp_path / "main" / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(UnsafePathError):
        listdir.resolve_path(Path("link/foxy"))


def test_resolve_path_rejects_prefix_sibling(tmp_path):
    # "main_evil" starts with "main" but is not inside it
    listdir = ListDir(tmp_path / "main", {})
    with pytest.raises(UnsafePathError):
        listdir.resolve_path(Path("../main_evil/foxy"))
