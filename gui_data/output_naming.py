from datetime import datetime
from pathlib import Path


def clean_output_base(input_path, timestamp=None, batch_index=None):
    """Build a filesystem-safe output base from the original input name."""
    timestamp = timestamp or datetime.now()
    batch_suffix = f'_{batch_index}' if batch_index is not None else ''
    return f'{Path(input_path).stem}_clean_{timestamp:%Y-%m-%d_%H-%M-%S}{batch_suffix}'


def default_output_directory(input_paths):
    if not input_paths:
        return ''
    return str(Path(input_paths[0]).resolve().parent)
