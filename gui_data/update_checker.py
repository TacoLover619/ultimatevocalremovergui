import json
import re
import urllib.request


RELEASES_API = (
    'https://api.github.com/repos/'
    'TacoLover619/ultimatevocalremovergui/releases/latest'
)


def version_key(value):
    """Return a comparable numeric key for tags such as v6.0.1."""
    match = re.search(r'\d+(?:\.\d+)*', value or '')
    if not match:
        raise ValueError(f'Invalid release version: {value!r}')
    return tuple(int(part) for part in match.group().split('.'))


def get_latest_release(timeout=10):
    request = urllib.request.Request(
        RELEASES_API,
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'Ultimate-Vocal-Remover',
            'X-GitHub-Api-Version': '2022-11-28',
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        release = json.load(response)

    tag = release.get('tag_name')
    page_url = release.get('html_url')
    if not tag or not page_url:
        raise ValueError('GitHub release is missing its version or download page')

    return {'version': tag, 'url': page_url}


def update_available(current_version, latest_version):
    return version_key(latest_version) > version_key(current_version)
