from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import release


@pytest.fixture(autouse=True)
def isolated_release_dir(tmp_path, monkeypatch):
    release_dir = tmp_path / "release"
    sounds_dir = tmp_path / "SOUNDS"
    release_dir.mkdir()
    monkeypatch.setattr(release, "SCRIPT_DIR", tmp_path)
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


def test_recreate_release_dir_wipes_existing_contents(isolated_release_dir):
    (isolated_release_dir / "stale.txt").write_text("stale")

    release.recreate_release_dir()

    assert isolated_release_dir.is_dir()
    assert list(isolated_release_dir.iterdir()) == []


def test_recreate_release_dir_creates_when_missing(monkeypatch, tmp_path):
    missing_dir = tmp_path / "does-not-exist-yet"
    monkeypatch.setattr(release, "RELEASE_DIR", missing_dir)

    release.recreate_release_dir()

    assert missing_dir.is_dir()


def test_create_release_directories_mirrors_sounds_tree(isolated_release_dir, tmp_path):
    sounds_dir = tmp_path / "SOUNDS"
    (sounds_dir / "en" / "SCRIPTS" / "INAV").mkdir(parents=True)
    (sounds_dir / "es").mkdir()

    release.create_release_directories()

    assert (isolated_release_dir / "SOUNDS" / "en" / "SCRIPTS" / "INAV").is_dir()
    assert (isolated_release_dir / "SOUNDS" / "es").is_dir()


def test_remove_root_sounds_dir_removes_when_empty(isolated_release_dir):
    (isolated_release_dir / "SOUNDS").mkdir()

    release.remove_root_sounds_dir()

    assert not (isolated_release_dir / "SOUNDS").exists()


def test_remove_root_sounds_dir_raises_when_not_empty(isolated_release_dir):
    root_sounds_dir = isolated_release_dir / "SOUNDS"
    root_sounds_dir.mkdir()
    (root_sounds_dir / "stray.wav").write_bytes(b"leftover")

    with pytest.raises(OSError):
        release.remove_root_sounds_dir()


def test_env_flags_uses_default_when_unset(monkeypatch):
    monkeypatch.delenv("RELEASE_TEST_FLAGS", raising=False)

    assert release.env_flags("RELEASE_TEST_FLAGS", "-a -b") == ["-a", "-b"]


def test_env_flags_splits_quoted_env_value(monkeypatch):
    monkeypatch.setenv("RELEASE_TEST_FLAGS", "-af 'a complex filter' -y")

    assert release.env_flags("RELEASE_TEST_FLAGS", "") == ["-af", "a complex filter", "-y"]


def test_run_checked_succeeds_silently_for_zero_exit():
    release.run_checked([sys.executable, "-c", "pass"])


def test_run_checked_raises_called_process_error_for_nonzero_exit():
    with pytest.raises(subprocess.CalledProcessError):
        release.run_checked([sys.executable, "-c", "import sys; sys.exit(3)"])


def test_run_checked_raises_keyboard_interrupt_for_interrupt_exit_code():
    with pytest.raises(KeyboardInterrupt):
        release.run_checked([sys.executable, "-c", "import sys; sys.exit(130)"])
