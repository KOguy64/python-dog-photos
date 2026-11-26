import json
from pathlib import Path

import pytest
from PIL import Image

from python_fox_photos import terminal_interface
from python_fox_photos.fox_note import FoxNote, load_foxnote, save_foxnote
from python_fox_photos.saveload_manager import load_listdir
from python_fox_photos.terminal_interface import Session

FAKE_PHOTO_URL = "https://randomfox.ca/images/1.jpg"
MAIN_DIR = "saved"


@pytest.fixture()
def set_inputs(monkeypatch):
    """Feed answers to input() in order; fails loudly if input() is called too often"""

    def _set_inputs(*answers):
        answers_iter = iter(answers)

        def fake_input(prompt=""):
            try:
                return next(answers_iter)
            except StopIteration:
                pytest.fail(f"Unexpected input() call: {prompt!r}")

        monkeypatch.setattr("builtins.input", fake_input)

    return _set_inputs


@pytest.fixture()
def displayed(monkeypatch):
    """Replace the tkinter window with a list that records displayed images"""
    shown = []
    monkeypatch.setattr(terminal_interface, "display_photo", shown.append)
    return shown


@pytest.fixture()
def fake_api(monkeypatch):
    """Stop the session from calling the real API"""
    calls = []

    def fake_get_photo_url(api_url, api_json_key):
        calls.append(api_url)
        return FAKE_PHOTO_URL

    monkeypatch.setattr(terminal_interface, "get_photo_url", fake_get_photo_url)
    monkeypatch.setattr(
        terminal_interface,
        "get_photo_file",
        lambda photo_url: Image.new("RGB", (16, 16), "orange"),
    )
    return calls


@pytest.fixture()
def session(tmp_path, monkeypatch, fake_api, displayed) -> Session:
    """A session working in an empty temp dir, with a listdir.json pointing to MAIN_DIR"""
    monkeypatch.chdir(tmp_path)
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


def saved_entries(session):
    return load_listdir(session.listdir_path).saved_files


# Startup


def test_new_session_creates_listdir_and_files_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Session("listdir.json")
    assert (tmp_path / "listdir.json").exists()
    assert (tmp_path / "files").is_dir()


def test_session_loads_existing_listdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / MAIN_DIR).mkdir()
    entry = {"has_metadata": False, "path": "foxy"}
    (tmp_path / "listdir.json").write_text(
        json.dumps({"main_dir": MAIN_DIR, "saved_files": {"foxy": entry}})
    )
    session = Session("listdir.json")
    assert session.listdir.saved_files == {"foxy": entry}


# Command handling


def test_wrong_arg_count_is_rejected(session, capsys):
    assert session.get_list("extra") is None
    assert "only accepts 0 arguments" in capsys.readouterr().out


def test_unknown_command_is_reported(session, capsys):
    session.process_cmd("dance")
    assert "Can't parse 'dance'" in capsys.readouterr().out


def test_process_cmd_passes_args(session, capsys):
    session.process_cmd("help get")
    assert "Here's what get does" in capsys.readouterr().out


def test_help_lists_every_command(session, capsys):
    session.help()
    out = capsys.readouterr().out
    for cmd in session.cmd_map:
        assert cmd in out


def test_help_with_unknown_command_does_not_crash(session):
    session.process_cmd("help dance")


def test_exit_sets_exit_signal_and_saves(session, named_fox):
    session.listdir.add_file(named_fox, Path("foxy"))
    session.exit()
    assert session.exit_sig
    assert "foxy" in saved_entries(session)


# Getting and displaying foxes


def test_get_new_photo_sets_current_fox(session, set_inputs, displayed):
    set_inputs("n")
    session.get_new_photo()
    assert session._current_foxnote is not None
    assert displayed == []


def test_get_new_photo_displays_on_y(session, set_inputs, displayed):
    set_inputs("y")
    session.get_new_photo()
    assert displayed == [session._current_foxnote.img]


def test_current_foxnote_fetches_when_empty(session, set_inputs, fake_api):
    set_inputs("n")
    assert session.current_foxnote is not None
    assert len(fake_api) == 1


# Names and notes


def test_name_sets_name(session, named_fox, set_inputs):
    named_fox.name = None
    set_inputs("vulpes")
    session.name()
    assert named_fox.name == "vulpes"


def test_name_cannot_be_changed(session, named_fox, set_inputs, capsys):
    set_inputs()
    session.name()
    assert named_fox.name == "foxy"
    assert "foxy" in capsys.readouterr().out


def test_add_note_adds_metadata(session, named_fox, set_inputs):
    set_inputs("8.5", "very orange")
    session.add_note()
    assert named_fox.get_metadata() == {"note": "very orange", "score": 8.5}


def test_add_note_retries_on_non_number(session, named_fox, set_inputs):
    set_inputs("lots", "7", "nice")
    session.add_note()
    assert named_fox.score == 7


def test_add_note_retries_on_out_of_range_score(session, named_fox, set_inputs):
    set_inputs("11", "too much", "10", "just right")
    session.add_note()
    assert named_fox.get_metadata() == {"note": "just right", "score": 10}


def test_read_note_without_metadata(session, named_fox, capsys):
    session.read_note()
    assert "Add some notes" in capsys.readouterr().out


def test_edit_note_replaces_metadata(session, named_fox, set_inputs):
    named_fox.add_metadata("old", 2)
    set_inputs("9", "new")
    session.edit_note()
    assert named_fox.get_metadata() == {"note": "new", "score": 9}


# Listing


def test_get_list_empty(session, capsys):
    session.get_list()
    assert "No saved foxes found" in capsys.readouterr().out


def test_get_list_shows_saved_names(session, named_fox, capsys):
    session.listdir.add_file(named_fox, Path("foxy"))
    session.get_list()
    assert "foxy" in capsys.readouterr().out


# Saving


def test_save_adds_entry_to_listdir_json(session, named_fox, set_inputs):
    set_inputs("foxy")
    session.save_photo()
    assert saved_entries(session)["foxy"] == {"has_metadata": False, "path": "foxy"}


def test_save_without_metadata_writes_into_main_dir(
    session, named_fox, set_inputs, tmp_path
):
    set_inputs("foxy")
    session.save_photo()
    assert (tmp_path / MAIN_DIR / "foxy.jpg").exists()


def test_save_with_metadata_writes_into_main_dir(
    session, named_fox, set_inputs, tmp_path
):
    named_fox.add_metadata("cute", 9)
    set_inputs("foxy")
    session.save_photo()
    assert (tmp_path / MAIN_DIR / "foxy" / "image.jpg").exists()
    assert (tmp_path / MAIN_DIR / "foxy" / "metadata.json").exists()


def test_save_asks_for_name_when_unnamed(session, named_fox, set_inputs):
    named_fox.name = None
    set_inputs("vulpes", "vulpes")
    session.save_photo()
    assert "vulpes" in saved_entries(session)


# Loading


def test_save_then_load_round_trip(session, named_fox, set_inputs):
    named_fox.add_metadata("roundtrip", 6)
    set_inputs("foxy")
    session.save_photo()
    session._current_foxnote = None

    session.load_photo("foxy")
    loaded = session._current_foxnote
    assert loaded is not None
    assert loaded.name == "foxy"
    assert loaded.get_metadata() == {"note": "roundtrip", "score": 6}


def test_load_unknown_name(session, capsys):
    session.load_photo("ghost")
    assert "no fox with that name" in capsys.readouterr().out


def test_load_missing_fox_removes_entry(session, named_fox):
    named_fox.add_metadata("gone", 1)
    session.listdir.add_file(named_fox, Path("foxy"))
    session.update_metadata()

    session.load_photo("foxy")
    assert "foxy" not in session.listdir.saved_files
    assert "foxy" not in saved_entries(session)


# Deleting


def test_del_photo_removes_files_and_entry(session, named_fox, tmp_path):
    named_fox.add_metadata("bye", 4)
    save_foxnote(named_fox, tmp_path / MAIN_DIR / "foxy")
    session.listdir.add_file(named_fox, Path("foxy"))
    session.update_metadata()

    session.del_photo("foxy")
    assert not (tmp_path / MAIN_DIR / "foxy").exists()
    assert "foxy" not in saved_entries(session)


def test_del_photo_without_metadata_removes_jpg(session, named_fox, tmp_path):
    save_foxnote(named_fox, tmp_path / MAIN_DIR / "foxy")
    session.listdir.add_file(named_fox, Path("foxy"))

    session.del_photo("foxy")
    assert not (tmp_path / MAIN_DIR / "foxy.jpg").exists()


def test_del_photo_keeps_other_foxes(session, named_fox, tmp_path):
    save_foxnote(named_fox, tmp_path / MAIN_DIR / "foxy")
    session.listdir.add_file(named_fox, Path("foxy"))
    other = FoxNote(Image.new("RGB", (16, 16), "white"))
    other.name = "snowy"
    save_foxnote(other, tmp_path / MAIN_DIR / "snowy")
    session.listdir.add_file(other, Path("snowy"))

    session.del_photo("foxy")
    assert (tmp_path / MAIN_DIR / "snowy.jpg").exists()
    assert load_foxnote(tmp_path / MAIN_DIR / "snowy", "snowy", False).name == "snowy"
    assert "snowy" in session.listdir.saved_files


def test_del_unknown_fox(session, capsys):
    session.del_photo("ghost")
    assert "don't have that fox" in capsys.readouterr().out
