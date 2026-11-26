from pathlib import Path

import pytest
from PIL import Image

from python_fox_photos.fox_note import FoxNote, del_foxnote, load_foxnote, save_foxnote
from python_fox_photos.utils import InvalidPathError, MetadataError, ScoreError

FOXNOTE_WITH_METADATA_PATH = Path("tests/test_saved_photos/test_1")


@pytest.fixture()
def foxnote_with_metadata():
    image = Image.open(FOXNOTE_WITH_METADATA_PATH / Path("image.jpg"))
    foxnote = FoxNote(image)
    foxnote.name = "test_1"
    foxnote.add_metadata("okay this guy is a pretty cute guy", 9)
    return foxnote


FOXNOTE_WITHOUT_METADATA_PATH = Path("tests/test_saved_photos/test_2")


@pytest.fixture()
def foxnote_without_metadata():
    image = Image.open(FOXNOTE_WITHOUT_METADATA_PATH.with_suffix(".jpg"))
    foxnote = FoxNote(image)
    foxnote.name = "test_2"
    return foxnote


def test_load_foxnote_with_metadata_works(foxnote_with_metadata):
    assert (
        load_foxnote(FOXNOTE_WITH_METADATA_PATH, "test_1", has_metadata=True)
        == foxnote_with_metadata
    )


def test_load_foxnote_without_metadata_works(foxnote_without_metadata):
    assert (
        load_foxnote(FOXNOTE_WITHOUT_METADATA_PATH, "test_2", has_metadata=False)
        == foxnote_without_metadata
    )


@pytest.fixture()
def blank_foxnote():
    return FoxNote(Image.new("RGB", (16, 16), "orange"))


# Metadata errors


def test_note_without_metadata_raises(blank_foxnote):
    with pytest.raises(MetadataError):
        print(blank_foxnote.note)


def test_get_metadata_without_metadata_raises(blank_foxnote):
    with pytest.raises(MetadataError):
        blank_foxnote.get_metadata()


def test_add_metadata_makes_metadata_readable(blank_foxnote):
    blank_foxnote.add_metadata("fluffy", 7.5)
    assert blank_foxnote.has_metadata
    assert blank_foxnote.get_metadata() == {"note": "fluffy", "score": 7.5}


@pytest.mark.parametrize("score", [0, 10])
def test_boundary_scores_are_accepted(blank_foxnote, score):
    blank_foxnote.add_metadata("edge case", score)
    assert blank_foxnote.score == score


@pytest.mark.parametrize("score", [-1, -0.1, 10.1, 11])
def test_out_of_range_score_raises(blank_foxnote, score):
    with pytest.raises(ScoreError):
        blank_foxnote.add_metadata("bad score", score)


def test_failed_add_metadata_leaves_no_metadata(blank_foxnote):
    with pytest.raises(ScoreError):
        blank_foxnote.add_metadata("bad score", 11)
    assert not blank_foxnote.has_metadata


def test_load_foxnote_missing_image_raises(tmp_path):
    with pytest.raises(InvalidPathError):
        load_foxnote(tmp_path / "nope", "nope", has_metadata=False)


def test_load_foxnote_missing_metadata_file_raises(tmp_path, blank_foxnote):
    fox_dir = tmp_path / "fox"
    fox_dir.mkdir()
    blank_foxnote.img.save(fox_dir / "image.jpg", format="JPEG")
    with pytest.raises(InvalidPathError):
        load_foxnote(fox_dir, "fox", has_metadata=True)


# Saving and deleting


def test_save_then_load_with_metadata(tmp_path, blank_foxnote):
    blank_foxnote.add_metadata("roundtrip", 5)
    save_foxnote(blank_foxnote, tmp_path / "fox")
    loaded = load_foxnote(tmp_path / "fox", "fox", has_metadata=True)
    assert loaded.get_metadata() == {"note": "roundtrip", "score": 5}
    assert loaded.name == "fox"


def test_save_then_load_without_metadata(tmp_path, blank_foxnote):
    save_foxnote(blank_foxnote, tmp_path / "fox")
    loaded = load_foxnote(tmp_path / "fox", "fox", has_metadata=False)
    assert not loaded.has_metadata
    assert loaded.img.size == blank_foxnote.img.size


def test_del_foxnote_with_metadata_removes_dir(tmp_path, blank_foxnote):
    blank_foxnote.add_metadata("bye", 3)
    save_foxnote(blank_foxnote, tmp_path / "fox")
    del_foxnote(tmp_path / "fox", has_metadata=True)
    assert not (tmp_path / "fox").exists()


def test_del_foxnote_without_metadata_removes_jpg(tmp_path, blank_foxnote):
    save_foxnote(blank_foxnote, tmp_path / "fox")
    del_foxnote(tmp_path / "fox", has_metadata=False)
    assert not (tmp_path / "fox.jpg").exists()


def test_del_foxnote_without_metadata_missing_file_is_ok(tmp_path):
    del_foxnote(tmp_path / "ghost", has_metadata=False)


def test_del_foxnote_with_metadata_missing_dir_is_ok(tmp_path):
    # Session.load_photo relies on this when a saved fox has gone missing
    del_foxnote(tmp_path / "ghost", has_metadata=True)


def test_del_foxnote_leaves_other_foxes_alone(tmp_path, blank_foxnote):
    save_foxnote(blank_foxnote, tmp_path / "keep")
    save_foxnote(blank_foxnote, tmp_path / "remove")
    del_foxnote(tmp_path / "remove", has_metadata=False)
    assert (tmp_path / "keep.jpg").exists()
