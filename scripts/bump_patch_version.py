import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / '__version__.py'


def replace(path, old, new):
    content = path.read_text(encoding='utf-8')
    if old not in content:
        raise RuntimeError(f'Expected {old!r} in {path.name}')
    path.write_text(content.replace(old, new), encoding='utf-8')


def main():
    content = VERSION_FILE.read_text(encoding='utf-8')
    match = re.search(r"^VERSION = 'v(\d+)\.(\d+)\.(\d+)'$", content, re.MULTILINE)
    if not match:
        raise RuntimeError('Could not read the current application version')

    major, minor, patch = map(int, match.groups())
    old = f'{major}.{minor}.{patch}'
    new = f'{major}.{minor}.{patch + 1}'

    replace(VERSION_FILE, f"VERSION = 'v{old}'", f"VERSION = 'v{new}'")
    replace(VERSION_FILE, f"PATCH = 'UVR_v{old}_Windows_11'", f"PATCH = 'UVR_v{new}_Windows_11'")
    replace(ROOT / 'UVR-Windows.iss', f'#define AppVersion "{old}"', f'#define AppVersion "{new}"')
    replace(ROOT / 'UVR-Windows.iss', f'OutputBaseFilename=UVR_v{old}_setup', f'OutputBaseFilename=UVR_v{new}_setup')
    replace(ROOT / 'tests' / 'test_core_compat.py', f"self.assertEqual(VERSION, 'v{old}')", f"self.assertEqual(VERSION, 'v{new}')")

    build_doc = ROOT / 'WINDOWS_BUILD.md'
    replace(build_doc, f'UVR_v{old}_setup', f'UVR_v{new}_setup')
    print(new)


if __name__ == '__main__':
    main()
