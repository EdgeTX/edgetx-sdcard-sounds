from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

import release


@pytest.fixture(autouse=True)
def isolated_release_dir(tmp_path, monkeypatch):
    release_dir = tmp_path / "release"
    sounds_dir = tmp_path / "SOUNDS"
    release_dir.mkdir()
    monkeypatch.setattr(release, "RELEASE_DIR", release_dir)
    monkeypatch.setattr(release, "SOUNDS_DIR", sounds_dir)
    return release_dir


def make_variant(release_dir: Path, variant: str, filename: str = "dummy.wav") -> None:
    variant_root = release_dir / "SOUNDS" / variant
    variant_root.mkdir(parents=True, exist_ok=True)
    (variant_root / filename).write_bytes(b"fake-audio")


def test_move_and_trim_truncates_long_variant_name(isolated_release_dir):
    make_variant(isolated_release_dir, "en_gb-glados")

    release.move_variant_directories()
    release.trim_variant_directories()

    expected = isolated_release_dir / "en_gb-glados" / "SOUNDS" / "en" / "dummy.wav"
    assert expected.is_file()


def test_move_and_trim_leaves_already_short_variant_name(isolated_release_dir):
    make_variant(isolated_release_dir, "es")

    release.move_variant_directories()
    release.trim_variant_directories()

    expected = isolated_release_dir / "es" / "SOUNDS" / "es" / "dummy.wav"
    assert expected.is_file()


def test_trim_variant_directories_raises_if_language_folder_missing(isolated_release_dir):
    # Simulate the historical regression: the per-variant language folder was
    # collapsed away during the move step, so trim has nothing to rename.
    broken_root = isolated_release_dir / "en_gb-glados" / "SOUNDS"
    broken_root.mkdir(parents=True)
    (broken_root / "dummy.wav").write_bytes(b"fake-audio")

    with pytest.raises(FileNotFoundError):
        release.trim_variant_directories()


def test_create_release_archives_builds_expected_layout(isolated_release_dir):
    lang_dir = isolated_release_dir / "en_gb-glados" / "SOUNDS" / "en"
    lang_dir.mkdir(parents=True)
    (lang_dir / "dummy.wav").write_bytes(b"fake-audio")

    archive_count = release.create_release_archives("test")

    assert archive_count == 1
    archive_path = isolated_release_dir / "edgetx-sdcard-sounds-en_gb-glados-test.zip"
    assert archive_path.is_file()
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == ["SOUNDS/en/dummy.wav"]


def test_create_release_archives_raises_if_sounds_missing(isolated_release_dir):
    (isolated_release_dir / "en_gb-glados").mkdir()

    with pytest.raises(FileNotFoundError):
        release.create_release_archives("test")
