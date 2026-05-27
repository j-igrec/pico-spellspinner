#!/usr/bin/env python3
"""
tools/deploy.py

Deploy app and pico-ui-kit files to a Raspberry Pi Pico over USB.

Requirements:
    pip install mpremote

Usage:
    python3 tools/deploy.py
"""

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, '..')
_KIT  = os.path.join(_ROOT, 'pico-ui-kit')

# (local path, remote path)
_FILES = [
    (os.path.join(_ROOT, 'main.py'),                        ':main.py'),
    (os.path.join(_ROOT, 'config.py'),                      ':config.py'),
    (os.path.join(_ROOT, 'mode.cfg'),                       ':mode.cfg'),
    (os.path.join(_ROOT, 'data', '__init__.py'),            ':data/__init__.py'),
    (os.path.join(_ROOT, 'data', 'spells.py'),              ':data/spells.py'),
    (os.path.join(_ROOT, 'data', 'spells.jsonl'),           ':data/spells.jsonl'),
    (os.path.join(_ROOT, 'screens', '__init__.py'),         ':screens/__init__.py'),
    (os.path.join(_ROOT, 'screens', 'router.py'),           ':screens/router.py'),
    (os.path.join(_ROOT, 'screens', 'transitions.py'),      ':screens/transitions.py'),
    (os.path.join(_ROOT, 'screens', 'start.py'),            ':screens/start.py'),
    (os.path.join(_ROOT, 'screens', 'spell_card.py'),       ':screens/spell_card.py'),
    (os.path.join(_ROOT, 'screens', 'details.py'),          ':screens/details.py'),
    (os.path.join(_ROOT, 'lib', 'st7789.py'),               ':lib/st7789.py'),
    (os.path.join(_ROOT, 'lib', 'mpu6050.py'),              ':lib/mpu6050.py'),
    (os.path.join(_ROOT, 'lib', 'school_icons.py'),         ':lib/school_icons.py'),
    (os.path.join(_KIT,  'tokens', '__init__.py'),          ':tokens/__init__.py'),
    (os.path.join(_KIT,  'tokens', 'primitive.py'),         ':tokens/primitive.py'),
    (os.path.join(_KIT,  'tokens', 'semantic.py'),          ':tokens/semantic.py'),
    (os.path.join(_KIT,  'tokens', 'semantic_light.py'),    ':tokens/semantic_light.py'),
    (os.path.join(_KIT,  'tokens', 'semantic_dark.py'),     ':tokens/semantic_dark.py'),
    (os.path.join(_KIT,  'tokens', 'colormode.py'),         ':tokens/colormode.py'),
    (os.path.join(_KIT,  'tokens', 'viewport.py'),          ':tokens/viewport.py'),
    (os.path.join(_KIT,  'drawing', '__init__.py'),         ':drawing/__init__.py'),
    (os.path.join(_KIT,  'drawing', 'rect.py'),             ':drawing/rect.py'),
    (os.path.join(_KIT,  'drawing', 'text.py'),             ':drawing/text.py'),
    (os.path.join(_KIT,  'drawing', 'line.py'),             ':drawing/line.py'),
    (os.path.join(_KIT,  'drawing', 'icon.py'),             ':drawing/icon.py'),
    (os.path.join(_KIT,  'components', '__init__.py'),      ':components/__init__.py'),
    (os.path.join(_KIT,  'components', 'badge.py'),         ':components/badge.py'),
    (os.path.join(_KIT,  'components', 'button.py'),        ':components/button.py'),
    (os.path.join(_KIT,  'components', 'status_dot.py'),    ':components/status_dot.py'),
    (os.path.join(_KIT,  'icons', '__init__.py'),           ':icons/__init__.py'),
    (os.path.join(_KIT,  'icons', 'option_a.py'),           ':icons/option_a.py'),
    (os.path.join(_KIT,  'icons', 'option_b.py'),           ':icons/option_b.py'),
    (os.path.join(_KIT,  'icons', 'sparkles.py'),           ':icons/sparkles.py'),
    (os.path.join(_KIT,  'fonts', '__init__.py'),           ':fonts/__init__.py'),
    (os.path.join(_KIT,  'fonts', 'monor8.py'),             ':fonts/monor8.py'),
    (os.path.join(_KIT,  'fonts', 'monob8.py'),             ':fonts/monob8.py'),
    (os.path.join(_KIT,  'fonts', 'monor16.py'),            ':fonts/monor16.py'),
    (os.path.join(_KIT,  'fonts', 'monob16.py'),            ':fonts/monob16.py'),
]

_DIRS = ['data', 'screens', 'lib', 'tokens', 'drawing', 'components', 'icons', 'fonts']


def _mp(*args):
    result = subprocess.run(['mpremote'] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        # Return stderr for the caller to decide whether to treat as fatal.
        return result.stderr.strip()
    return None


def _mkdir(remote_dir):
    """Create a directory on the Pico; silently ignore if it already exists."""
    code = (
        "import os\n"
        "try:\n"
        f"    os.mkdir('{remote_dir}')\n"
        "except OSError:\n"
        "    pass\n"
    )
    _mp('exec', code)


def deploy():
    print('Creating directories...')
    for d in _DIRS:
        _mkdir(d)

    print('Copying files...')
    missing = []
    for src, dst in _FILES:
        rel = os.path.relpath(src, _ROOT)
        if not os.path.exists(src):
            print(f'  SKIP (not found): {rel}')
            missing.append(rel)
            continue
        err = _mp('cp', src, dst)
        if err:
            print(f'  ERROR copying {rel}: {err}')
            sys.exit(1)
        print(f'  {rel}  →  {dst}')

    if missing:
        print(f'\nWarning: {len(missing)} file(s) skipped — run the build scripts first:')
        print('  python3 tools/build_spells.py')
        print('  python3 tools/build_icons.py')

    print('\nDone. Hard-reset the Pico to run the new code:')
    print('  mpremote reset')


if __name__ == '__main__':
    deploy()
