from datetime import datetime

from gui_data.output_naming import clean_output_base, default_output_directory
from gui_data.constants import SELECT_OUTPUT_TEXT


def test_clean_output_base_appends_date_and_time():
    timestamp = datetime(2026, 8, 30, 16, 5, 9)

    assert clean_output_base('C:/Voice Samples/voice.wav', timestamp) == (
        'voice_clean_2026-08-30_16-05-09'
    )


def test_clean_output_base_distinguishes_batch_files():
    timestamp = datetime(2026, 8, 30, 16, 5, 9)

    assert clean_output_base('C:/Voice Samples/voice.wav', timestamp, batch_index=2) == (
        'voice_clean_2026-08-30_16-05-09_2'
    )


def test_default_output_directory_matches_input(tmp_path):
    input_file = tmp_path / 'voice.wav'

    assert default_output_directory([input_file]) == str(tmp_path.resolve())
    assert default_output_directory([]) == ''


def test_output_control_selects_a_folder():
    assert SELECT_OUTPUT_TEXT == 'Select Output Folder'
