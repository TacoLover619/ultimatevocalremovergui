import pickle

from gui_data.settings_store import load_settings, save_settings


def test_settings_round_trip(tmp_path):
    settings_path = tmp_path / 'data.pkl'
    expected = {'volume': 0.75, 'models': ['a', 'b']}

    save_settings(settings_path, expected)

    assert load_settings(settings_path, {}) == expected
    assert not list(tmp_path.glob('*.tmp'))


def test_corrupt_settings_are_recovered(tmp_path):
    settings_path = tmp_path / 'data.pkl'
    settings_path.write_bytes(b'not a pickle')
    defaults = {'gpu': False, 'nested': {'value': 1}}

    recovered = load_settings(settings_path, defaults)
    recovered['nested']['value'] = 2

    assert defaults['nested']['value'] == 1
    with settings_path.open('rb') as settings_file:
        assert pickle.load(settings_file) == defaults


def test_empty_settings_are_recovered(tmp_path):
    settings_path = tmp_path / 'data.pkl'
    settings_path.touch()

    assert load_settings(settings_path, {'ready': True}) == {'ready': True}
