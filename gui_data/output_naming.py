from datetime import datetime
from pathlib import Path


def clean_output_base(input_path, timestamp=None):
    """Build a filesystem-safe output base from the original input name."""
    timestamp = timestamp or datetime.now()
    return f'{Path(input_path).stem}_clean_{timestamp:%Y-%m-%d_%H-%M-%S}'


def default_output_directory(input_paths):
    if not input_paths:
        return ''
    return str(Path(input_paths[0]).resolve().parent)
