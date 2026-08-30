import json

from gui_data import update_checker


def test_version_comparison():
    assert update_checker.update_available('v6.0.0', 'v6.0.1')
    assert update_checker.update_available('v6.0.9', 'v6.1.0')
    assert not update_checker.update_available('v6.0.0', 'v6.0.0')
    assert not update_checker.update_available('v6.1.0', 'v6.0.9')


def test_latest_release_uses_project_repository(monkeypatch):
    payload = json.dumps({
        'tag_name': 'v6.1.0',
        'html_url': 'https://github.com/TacoLover619/ultimatevocalremovergui/releases/tag/v6.1.0',
    }).encode()
    requested = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, *args):
            return payload

    def urlopen(request, timeout):
        requested['url'] = request.full_url
        requested['timeout'] = timeout
        return Response()

    monkeypatch.setattr(update_checker.urllib.request, 'urlopen', urlopen)
    release = update_checker.get_latest_release()

    assert requested['url'] == update_checker.RELEASES_API
    assert requested['timeout'] == 10
    assert release['version'] == 'v6.1.0'
