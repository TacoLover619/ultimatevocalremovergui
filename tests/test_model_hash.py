import hashlib

from gui_data.model_hash import hash_model_file


def md5(data):
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def test_small_model_hashes_entire_file(tmp_path):
    model = tmp_path / 'small.onnx'
    content = b'small model data'
    model.write_bytes(content)

    assert hash_model_file(model, tail_bytes=100) == md5(content)


def test_large_model_hashes_only_compatible_tail(tmp_path):
    model = tmp_path / 'large.onnx'
    content = b'prefix that must be skipped' + b'expected-tail'
    model.write_bytes(content)

    assert hash_model_file(model, tail_bytes=13) == md5(b'expected-tail')
