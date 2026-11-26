"""Bad input, broken files and lost connections must never end in a traceback"""

import json
import tkinter as tk

import pytest
import requests
from PIL import Image

from python_fox_photos import api_caller, terminal_interface
from python_fox_photos.api_caller import OFFLINE_PHOTO, OFFLINE_REPLY
from python_fox_photos.fox_note import FoxNote
from python_fox_photos.saveload_manager import load_listdir
from python_fox_photos.terminal_interface import Session

API_URL = "https://randomfox.ca/floof/"
FAKE_PHOTO_URL = "https://randomfox.ca/images/1.jpg"
MAIN_DIR = "saved"


class FakeResponse:
    """Stands in for requests.Response"""

    def __init__(self, json_data=None, content=b"", status_error=None, json_error=None):
        self._json_data = json_data
        self.content = content
        self._status_error = status_error
        self._json_error = json_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._json_data


@pytest.fixture(autouse=True)
def no_offline_fox(tmp_path, monkeypatch):
    """Hide the committed offline fox unless a test asks for it"""
    monkeypatch.setattr(terminal_interface, "OFFLINE_REPLY", tmp_path / "none.json")
    monkeypatch.setattr(terminal_interface, "OFFLINE_PHOTO", tmp_path / "none.jpg")


@pytest.fixture()
def fake_requests(monkeypatch):
    """Make requests.get inside api_caller return or raise whatever the test wants"""

    def _fake_requests(api_reply, photo_reply=None):
        def fake_get(url, *args, **kwargs):
            reply = api_reply if url == API_URL else photo_reply
            if isinstance(reply, Exception):
                raise reply
            return reply

        monkeypatch.setattr(api_caller.r, "get", fake_get)

    return _fake_requests


@pytest.fixture()
def answer_always(monkeypatch):
    """Answer every input() prompt with the same text"""

    def _answer_always(answer):
        monkeypatch.setattr("builtins.input", lambda prompt="": answer)

    return _answer_always


@pytest.fixture()
def raise_on_input(monkeypatch):
    """Make every input() prompt raise, like Ctrl+C or Ctrl+D"""

    def _raise_on_input(error):
        def fake_input(prompt=""):
            raise error

        monkeypatch.setattr("builtins.input", fake_input)

    return _raise_on_input


@pytest.fixture()
def session(tmp_path, monkeypatch) -> Session:
    """A session working in an empty temp dir, with no tkinter windows"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(terminal_interface, "display_photo", lambda img: None)
    (tmp_path / MAIN_DIR).mkdir()
    listdir_path = tmp_path / "listdir.json"
    listdir_path.write_text(json.dumps({"main_dir": MAIN_DIR, "saved_files": {}}))
    return Session(str(listdir_path))


@pytest.fixture()
def named_fox(session) -> FoxNote:
    fox = FoxNote(Image.new("RGB", (16, 16), "orange"))
    fox.name = "foxy"
    session._current_foxnote = fox
    return fox


def register_fox(session, name, path, has_metadata):
    session.listdir.saved_files[name] = {"has_metadata": has_metadata, "path": path}
    session.update_metadata()


# API failures


API_FAILURES = [
    pytest.param(requests.ConnectionError("no network"), id="no-network"),
    pytest.param(requests.Timeout("too slow"), id="timeout"),
    pytest.param(
        FakeResponse(status_error=requests.HTTPError("503 Server Error")),
        id="http-error",
    ),
    pytest.param(
        FakeResponse(json_error=requests.JSONDecodeError("Expecting value", "", 0)),
        id="reply-not-json",
    ),
    pytest.param(FakeResponse(json_data={"link": FAKE_PHOTO_URL}), id="missing-key"),
]


@pytest.mark.parametrize("api_reply", API_FAILURES)
def test_get_new_photo_survives_api_failure(session, fake_requests, api_reply):
    fake_requests(api_reply)
    session.get_new_photo()
    assert session._current_foxnote is None


def test_get_new_photo_survives_photo_download_failure(session, fake_requests):
    fake_requests(
        FakeResponse(json_data={"image": FAKE_PHOTO_URL}),
        requests.ConnectionError("dropped"),
    )
    session.get_new_photo()
    assert session._current_foxnote is None


def test_get_new_photo_survives_photo_that_is_not_an_image(session, fake_requests):
    fake_requests(
        FakeResponse(json_data={"image": FAKE_PHOTO_URL}),
        FakeResponse(content=b"<html>Not Found</html>"),
    )
    session.get_new_photo()
    assert session._current_foxnote is None


def test_start_survives_no_network(session, fake_requests, answer_always):
    fake_requests(requests.ConnectionError("no network"))
    answer_always("exit")
    session.start()
    assert session.exit_sig


# Broken listdir.json


@pytest.mark.parametrize(
    "listdir_text",
    [
        pytest.param("{ this is not json", id="not-json"),
        pytest.param("", id="empty-file"),
        pytest.param(json.dumps({"saved_files": {}}), id="missing-main-dir"),
        pytest.param(json.dumps({"main_dir": MAIN_DIR}), id="missing-saved-files"),
        pytest.param(json.dumps(["not", "a", "dict"]), id="wrong-shape"),
    ],
)
def test_session_survives_broken_listdir(tmp_path, monkeypatch, listdir_text):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "listdir.json").write_text(listdir_text)
    session = Session("listdir.json")
    assert session.listdir.saved_files == {}


# Broken saved foxes


def test_load_survives_jpg_that_is_not_an_image(session, tmp_path):
    (tmp_path / MAIN_DIR / "foxy.jpg").write_bytes(b"definitely not a jpeg")
    register_fox(session, "foxy", "foxy", has_metadata=False)
    session.load_photo("foxy")
    assert session._current_foxnote is None


@pytest.mark.parametrize(
    "metadata_text",
    [
        pytest.param("{ this is not json", id="not-json"),
        pytest.param(json.dumps({"note": "no score"}), id="missing-score"),
        pytest.param(json.dumps({"score": 5}), id="missing-note"),
        pytest.param(json.dumps({"note": "too good", "score": 99}), id="bad-score"),
        pytest.param(
            json.dumps({"note": "huh", "score": "high"}), id="score-not-number"
        ),
    ],
)
def test_load_survives_broken_metadata(session, tmp_path, metadata_text):
    fox_dir = tmp_path / MAIN_DIR / "foxy"
    fox_dir.mkdir()
    Image.new("RGB", (16, 16), "orange").save(fox_dir / "image.jpg", format="JPEG")
    (fox_dir / "metadata.json").write_text(metadata_text)
    register_fox(session, "foxy", "foxy", has_metadata=True)
    session.load_photo("foxy")
    assert session._current_foxnote is None


# Saving to a bad place


@pytest.mark.parametrize("has_metadata", [False, True])
def test_save_survives_missing_parent_dir(
    session, named_fox, answer_always, has_metadata
):
    if has_metadata:
        named_fox.add_metadata("cute", 9)
    answer_always("no/such/dir/foxy")
    session.save_photo()


def test_failed_save_does_not_add_entry(session, named_fox, answer_always):
    answer_always("no/such/dir/foxy")
    session.save_photo()
    assert "foxy" not in session.listdir.saved_files
    assert "foxy" not in load_listdir(session.listdir_path).saved_files


def test_save_survives_permission_error(session, named_fox, answer_always, monkeypatch):
    def no_permission(foxnote, path):
        raise PermissionError(f"Permission denied: {path}")

    monkeypatch.setattr(terminal_interface, "save_foxnote", no_permission)
    answer_always("foxy")
    session.save_photo()


def test_session_survives_unwritable_listdir(session, monkeypatch):
    def no_permission(listdir, listdir_path):
        raise PermissionError(f"Permission denied: {listdir_path}")

    monkeypatch.setattr(terminal_interface, "save_listdir", no_permission)
    session.exit()


# Display


def test_display_survives_no_screen(session, named_fox, monkeypatch):
    def no_screen(img):
        raise tk.TclError("no display name and no $DISPLAY environment variable")

    monkeypatch.setattr(terminal_interface, "display_photo", no_screen)
    session.display_photo()


# Ctrl+C and Ctrl+D


@pytest.mark.parametrize("error", [KeyboardInterrupt, EOFError])
def test_start_survives_ctrl_c_and_ctrl_d(session, named_fox, raise_on_input, error):
    session.get_new_photo = lambda: None
    raise_on_input(error)
    try:
        session.start()
    except KeyboardInterrupt:
        # Re-raising would stop the whole pytest run, so fail this test instead
        pytest.fail("KeyboardInterrupt escaped Session.start()")


@pytest.mark.parametrize("error", [KeyboardInterrupt, EOFError])
def test_add_note_survives_ctrl_c_and_ctrl_d(session, named_fox, raise_on_input, error):
    raise_on_input(error)
    try:
        session.process_cmd("addnote")
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt escaped the addnote command")


# Comparing foxes


def test_foxes_with_different_sizes_are_not_equal():
    small = FoxNote(Image.new("RGB", (16, 16), "orange"))
    big = FoxNote(Image.new("RGB", (32, 32), "orange"))
    assert small != big


def test_foxes_with_different_modes_are_not_equal():
    rgb = FoxNote(Image.new("RGB", (16, 16), "orange"))
    grey = FoxNote(Image.new("L", (16, 16), 128))
    assert rgb != grey


# Offline copy


def test_committed_offline_fox_exists():
    assert OFFLINE_REPLY.exists()
    assert OFFLINE_PHOTO.exists()


def test_offline_uses_committed_fox(session, fake_requests, monkeypatch):
    monkeypatch.setattr(terminal_interface, "OFFLINE_REPLY", OFFLINE_REPLY)
    monkeypatch.setattr(terminal_interface, "OFFLINE_PHOTO", OFFLINE_PHOTO)
    fake_requests(requests.ConnectionError("no network"))
    session.get_new_photo()
    assert session._current_foxnote is not None


def test_offline_survives_broken_offline_fox(session, fake_requests, tmp_path):
    (tmp_path / "none.json").write_text("{ this is not json")
    (tmp_path / "none.jpg").write_bytes(b"definitely not a jpeg")
    fake_requests(requests.ConnectionError("no network"))
    session.get_new_photo()
    assert session._current_foxnote is None


def test_new_fox_does_not_change_offline_copy(session, fake_requests, answer_always):
    before = (OFFLINE_REPLY.read_bytes(), OFFLINE_PHOTO.read_bytes())
    fake_requests(
        FakeResponse(json_data={"image": FAKE_PHOTO_URL}),
        FakeResponse(content=OFFLINE_PHOTO.read_bytes()),
    )
    answer_always("n")
    session.get_new_photo()
    assert session._current_foxnote is not None
    assert (OFFLINE_REPLY.read_bytes(), OFFLINE_PHOTO.read_bytes()) == before


# Path injection


ESCAPING_PATHS = [
    pytest.param("../foxy", id="parent"),
    pytest.param("../../foxy", id="grandparent"),
    pytest.param("a/../../foxy", id="sneaky-parent"),
    pytest.param("..", id="parent-dir"),
    pytest.param(".", id="main-dir-itself"),
]


@pytest.mark.parametrize("has_metadata", [False, True])
@pytest.mark.parametrize("path", ESCAPING_PATHS)
def test_save_refuses_path_outside_main_dir(
    session, named_fox, answer_always, tmp_path, path, has_metadata
):
    if has_metadata:
        named_fox.add_metadata("cute", 9)
    before = {p for p in tmp_path.rglob("*") if p.name != "listdir.json"}
    answer_always(path)
    session.save_photo()
    after = {p for p in tmp_path.rglob("*") if p.name != "listdir.json"}
    assert after == before
    assert "foxy" not in session.listdir.saved_files
    assert "foxy" not in load_listdir(session.listdir_path).saved_files


def test_save_refuses_absolute_path(session, named_fox, answer_always, tmp_path):
    target = tmp_path / "outside" / "foxy"
    target.parent.mkdir()
    answer_always(str(target))
    session.save_photo()
    assert not target.with_suffix(".jpg").exists()
    assert "foxy" not in session.listdir.saved_files


def test_save_inside_main_dir_still_works(session, named_fox, answer_always, tmp_path):
    answer_always("a/../foxy")
    session.save_photo()
    assert (tmp_path / MAIN_DIR / "foxy.jpg").exists()
    assert "foxy" in session.listdir.saved_files


@pytest.mark.parametrize("has_metadata", [False, True])
def test_del_does_not_touch_files_outside_main_dir(session, tmp_path, has_metadata):
    victim = tmp_path / "victim"
    if has_metadata:
        victim.mkdir()
        (victim / "image.jpg").write_bytes(b"keep me")
        (victim / "metadata.json").write_text("{}")
    else:
        victim.with_suffix(".jpg").write_bytes(b"keep me")
    register_fox(session, "evil", "../victim", has_metadata)

    session.del_photo("evil")

    if has_metadata:
        assert (victim / "image.jpg").exists()
        assert (victim / "metadata.json").exists()
    else:
        assert victim.with_suffix(".jpg").exists()
    assert "evil" not in session.listdir.saved_files
    assert "evil" not in load_listdir(session.listdir_path).saved_files


def test_load_refuses_entry_outside_main_dir(session, tmp_path):
    outside = tmp_path / "outside"
    Image.new("RGB", (16, 16), "orange").save(outside.with_suffix(".jpg"))
    register_fox(session, "evil", "../outside", False)

    session.load_photo("evil")

    assert session._current_foxnote is None
    assert outside.with_suffix(".jpg").exists()
    assert "evil" not in session.listdir.saved_files
