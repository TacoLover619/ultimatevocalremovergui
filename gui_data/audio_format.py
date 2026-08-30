from pathlib import Path

from gui_data.constants import FLAC, MP3, WAV


EXTENSION_FORMATS = {
    '.flac': FLAC,
    '.mp3': MP3,
    '.wav': WAV,
    '.wave': WAV,
}


def detect_audio_format(audio_path, info_reader=None):
    """Detect the input codec, with its extension as a safe fallback."""
    if info_reader is None:
        import soundfile

        info_reader = soundfile.info

    try:
        info = info_reader(audio_path)
        codec = ' '.join((
            str(getattr(info, 'format', '')),
            str(getattr(info, 'format_info', '')),
            str(getattr(info, 'subtype', '')),
            str(getattr(info, 'subtype_info', '')),
        )).upper()
        if 'FLAC' in codec:
            return FLAC
        if 'MPEG' in codec or 'MP3' in codec or 'LAYER III' in codec:
            return MP3
        if 'WAV' in codec or 'WAVE' in codec:
            return WAV
    except (OSError, RuntimeError, ValueError):
        pass

    return EXTENSION_FORMATS.get(Path(audio_path).suffix.lower(), WAV)


def detect_common_audio_format(audio_paths, info_reader=None):
    detected = {
        detect_audio_format(audio_path, info_reader=info_reader)
        for audio_path in audio_paths
    }
    return detected.pop() if len(detected) == 1 else WAV
