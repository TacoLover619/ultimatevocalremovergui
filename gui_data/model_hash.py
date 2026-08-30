import hashlib
from pathlib import Path


MODEL_HASH_BYTES = 10_000 * 1024


def hash_model_file(path, tail_bytes=MODEL_HASH_BYTES):
    """Match UVR's model hash format without reading large models in full."""
    model_path = Path(path)
    file_size = model_path.stat().st_size
    with model_path.open('rb') as model_file:
        model_file.seek(max(0, file_size - tail_bytes))
        return hashlib.md5(model_file.read(), usedforsecurity=False).hexdigest()
