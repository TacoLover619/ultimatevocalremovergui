from types import SimpleNamespace

from gui_data.audio_format import detect_audio_format, detect_common_audio_format
from gui_data.constants import FLAC, MP3, WAV


def codec(format='', format_info='', subtype='', subtype_info=''):
    return SimpleNamespace(
        format=format,
        format_info=format_info,
        subtype=subtype,
        subtype_info=subtype_info,
    )


def test_detects_codec_before_extension():
    assert detect_audio_format(
        'voice.bin',
        info_reader=lambda _: codec(format='FLAC'),
    ) == FLAC
    assert detect_audio_format(
        'voice.bin',
        info_reader=lambda _: codec(subtype_info='MPEG Layer III'),
    ) == MP3
    assert detect_audio_format(
        'voice.bin',
        info_reader=lambda _: codec(format_info='WAV (Microsoft)'),
    ) == WAV


def test_falls_back_to_case_insensitive_extension():
    def failed_probe(_):
        raise RuntimeError('unsupported codec probe')

    assert detect_audio_format('voice.MP3', failed_probe) == MP3
    assert detect_audio_format('voice.FlAc', failed_probe) == FLAC
    assert detect_audio_format('voice.WAVE', failed_probe) == WAV


def test_multiple_matching_inputs_keep_their_format():
    failed_probe = lambda _: (_ for _ in ()).throw(RuntimeError())

    assert detect_common_audio_format(
        ['one.mp3', 'two.MP3'],
        info_reader=failed_probe,
    ) == MP3


def test_mixed_inputs_use_wav_to_avoid_lossy_conversion():
    failed_probe = lambda _: (_ for _ in ()).throw(RuntimeError())

    assert detect_common_audio_format(
        ['one.mp3', 'two.flac'],
        info_reader=failed_probe,
    ) == WAV
