from __future__ import annotations

import json
from pathlib import Path

import pytest

import build_checks

HEADER = "StringID,Col1,Translation,Col3,PATH,FILENAME"


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "voices").mkdir()
    (tmp_path / "SOUNDS").mkdir()
    return tmp_path


def write_csv(cwd: Path, name: str, rows: list[str], trailing_newline: bool = True) -> Path:
    path = cwd / "voices" / name
    content = "\n".join([HEADER, *rows])
    if trailing_newline:
        content += "\n"
    path.write_text(content)
    return path


def write_wav(cwd: Path, relative_path: str, size: int = 4) -> Path:
    path = cwd / "SOUNDS" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00" * size)
    return path


def test_check_duplicate_filenames_in_csv_detects_duplicate(isolated_cwd):
    write_csv(
        isolated_cwd,
        "en-US.csv",
        ["1,c1,Text one,c3,,dupe.wav", "2,c1,Text two,c3,,dupe.wav"],
    )
    assert build_checks.checkDuplicateFilenamesInCSV() == 1


def test_check_duplicate_filenames_in_csv_passes_when_unique(isolated_cwd):
    write_csv(
        isolated_cwd,
        "en-US.csv",
        ["1,c1,Text one,c3,,one.wav", "2,c1,Text two,c3,,two.wav"],
    )
    assert build_checks.checkDuplicateFilenamesInCSV() == 0


def test_check_files_in_sounds_not_in_csv_flags_unreferenced_file(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text one,c3,,referenced.wav"])
    write_wav(isolated_cwd, "en/referenced.wav")
    write_wav(isolated_cwd, "en/orphan.wav")

    assert build_checks.checkFilesInSoundsNotInCSV() == 1


def test_check_files_in_sounds_not_in_csv_respects_skip_marker(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", [])
    write_wav(isolated_cwd, "en/orphan.wav")
    (isolated_cwd / "SOUNDS" / "en" / build_checks.SKIP_SOUNDS_NOT_IN_CSV).touch()

    assert build_checks.checkFilesInSoundsNotInCSV() == 0


def test_check_csv_referenced_files_exist_in_sounds_errors_when_translation_present(isolated_cwd):
    # "xx" is not a real voice_generation_config output dir, so the check falls
    # back to the CSV filename's first two letters ("xx") as the language dir.
    write_csv(isolated_cwd, "xx-XX.csv", ["1,c1,Some translation,c3,,missing.wav"])

    assert build_checks.checkCSVReferencedFilesExistInSounds() == 1


def test_check_csv_referenced_files_exist_in_sounds_warns_only_when_translation_blank(isolated_cwd):
    write_csv(isolated_cwd, "xx-XX.csv", ["1,c1,,c3,,missing.wav"])

    assert build_checks.checkCSVReferencedFilesExistInSounds() == 0


def test_check_csv_referenced_files_exist_in_sounds_passes_when_file_present(isolated_cwd):
    write_csv(isolated_cwd, "xx-XX.csv", ["1,c1,Some translation,c3,,present.wav"])
    write_wav(isolated_cwd, "xx/present.wav")

    assert build_checks.checkCSVReferencedFilesExistInSounds() == 0


def test_get_csv_output_dirs_from_generate_script_consolidates_scripts_dir(monkeypatch):
    fake_azure_job = type("Job", (), {})()
    fake_azure_job.csv_path = Path("./voices/xx-XX.csv")
    fake_azure_job.langdir = "xx/SCRIPTS"

    build_checks.getCSVOutputDirsFromGenerateScript.cache_clear()
    monkeypatch.setattr(build_checks, "AZURE_VOICE_JOBS", (fake_azure_job,))
    monkeypatch.setattr(build_checks, "GLADOS_VOICE_JOBS", ())
    try:
        result = build_checks.getCSVOutputDirsFromGenerateScript()
        assert result == {"xx-XX.csv": {"xx"}}
    finally:
        build_checks.getCSVOutputDirsFromGenerateScript.cache_clear()


def test_check_csv_column_count_flags_empty_csv(isolated_cwd):
    (isolated_cwd / "voices" / "en-US.csv").write_text("")

    assert build_checks.checkCSVcolumnCount() == 1


def test_check_csv_column_count_flags_ragged_row(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3,,file.wav,extra"])

    assert build_checks.checkCSVcolumnCount() == 1


def test_check_csv_column_count_passes_for_well_formed_csv(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3,,file.wav"])

    assert build_checks.checkCSVcolumnCount() == 0


def test_check_filename_lengths_in_csv_flags_long_filename(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3,,waytoolongfilename.wav"])

    assert build_checks.checkFilenameLengthsInCSV() == 1


def test_check_filename_lengths_in_csv_skips_scripts_csv(isolated_cwd):
    write_csv(isolated_cwd, "en-US_scripts.csv", ["1,c1,Text,c3,,waytoolongfilename.wav"])

    assert build_checks.checkFilenameLengthsInCSV() == 0


def test_check_filename_lengths_flags_long_filename_and_skips_scripts_dir(isolated_cwd):
    write_wav(isolated_cwd, "en/waytoolongfilename.wav")
    write_wav(isolated_cwd, "en/SCRIPTS/BETAFLIGHT/waytoolongfilename.wav")

    assert build_checks.checkFilenameLengths() == 1


def test_check_no_zero_byte_files_flags_empty_wav(isolated_cwd):
    write_wav(isolated_cwd, "en/empty.wav", size=0)

    assert build_checks.checkNoZeroByteFiles() == 1


def test_check_no_zero_byte_files_passes_for_non_empty_wav(isolated_cwd):
    write_wav(isolated_cwd, "en/nonempty.wav", size=10)

    assert build_checks.checkNoZeroByteFiles() == 0


def test_validate_sounds_json_missing_file(isolated_cwd):
    assert build_checks.validateSoundsJson() == 1


def test_validate_sounds_json_invalid_json(isolated_cwd):
    (isolated_cwd / "sounds.json").write_text("{not valid json")

    assert build_checks.validateSoundsJson() == 1


def test_validate_sounds_json_valid(isolated_cwd):
    (isolated_cwd / "sounds.json").write_text(json.dumps({"ok": True}))

    assert build_checks.validateSoundsJson() == 0


def test_check_for_duplicate_string_id_detects_duplicate(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text one,c3,,one.wav", "1,c1,Text two,c3,,two.wav"])

    assert build_checks.checkForDuplicateStringID() == 1


def test_check_csv_newline_flags_missing_trailing_newline(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3,,file.wav"], trailing_newline=False)

    assert build_checks.checkCSVNewline() == 1


def test_check_csv_newline_passes_with_trailing_newline(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3,,file.wav"], trailing_newline=True)

    assert build_checks.checkCSVNewline() == 0


def test_check_csv_formatting_flags_quote_in_field(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ['1,c1,Text,c3,,fi"le.wav'])

    assert build_checks.checkCSVFormatting() == 1


def test_check_csv_formatting_flags_whitespace_in_field(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3, path,file.wav"])

    assert build_checks.checkCSVFormatting() == 1


def test_check_csv_formatting_passes_for_clean_fields(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3,,file.wav"])

    assert build_checks.checkCSVFormatting() == 0


def test_check_sequential_string_ids_flags_gap_as_error(isolated_cwd):
    write_csv(isolated_cwd, "en-US.csv", ["1,c1,Text,c3,,one.wav", "3,c1,Text,c3,,two.wav"])

    assert build_checks.checkSequentialStringIDs() == 1


def test_check_sequential_string_ids_warns_without_failing_for_warning_only_files(isolated_cwd):
    write_csv(isolated_cwd, "fr-FR.csv", ["1,c1,Text,c3,,one.wav", "3,c1,Text,c3,,two.wav"])

    assert build_checks.checkSequentialStringIDs() == 0


def test_check_sequential_string_ids_ignores_scripts_csv(isolated_cwd):
    write_csv(isolated_cwd, "en-US_scripts.csv", ["1,c1,Text,c3,,one.wav", "5,c1,Text,c3,,two.wav"])

    assert build_checks.checkSequentialStringIDs() == 0
