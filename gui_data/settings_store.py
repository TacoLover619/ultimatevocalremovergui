import copy
import os
import pickle
import tempfile
from pathlib import Path


RECOVERABLE_LOAD_ERRORS = (
    EOFError,
    FileNotFoundError,
    OSError,
    ValueError,
    pickle.UnpicklingError,
)


def save_settings(path, data):
    """Atomically save settings so interruption cannot corrupt the live file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=f'{destination.name}.',
        suffix='.tmp',
        dir=destination.parent,
    )
    try:
        with os.fdopen(descriptor, 'wb') as settings_file:
            pickle.dump(data, settings_file, protocol=pickle.HIGHEST_PROTOCOL)
            settings_file.flush()
            os.fsync(settings_file.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.remove(temporary_path)
        except FileNotFoundError:
            pass
        raise


def load_settings(path, defaults):
    """Load settings and recover from missing or damaged cache files."""
    try:
        with open(path, 'rb') as settings_file:
            return pickle.load(settings_file)
    except RECOVERABLE_LOAD_ERRORS:
        recovered = copy.deepcopy(defaults)
        save_settings(path, recovered)
        return recovered
