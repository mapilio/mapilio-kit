import os
import subprocess
import sys
from pathlib import Path

def get_installed_package_path(package_name):
    result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"Package {package_name} not found")
    for line in result.stdout.splitlines():
        if line.startswith('Location:'):
            return line.split(' ', 1)[1]
    raise ValueError(f"Location not found for package {package_name}")

def create_spec_file():
    requirements_file = 'requirements.txt'
    spec_file = 'flask_app.spec'

    datas = []
    hiddenimports = []

    with open(requirements_file) as f:
        packages = [line.split('==')[0].strip() for line in f if line.strip() and not line.startswith('#')]

    for package in packages:
        try:
            package_path = get_installed_package_path(package)
            datas.append((package_path, package))
            hiddenimports.append(package)
        except ValueError as e:
            print(f"Warning: {e}")

    with open(spec_file, 'w') as f:
        f.write(f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['flask_app.py'],
    pathex=['.'],
    binaries=[],
    datas={datas},
    hiddenimports={hiddenimports},
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MapilioKit-Flask',
    debug=False,
    strip=False,
    upx=True,
    console=True,
)

app = BUNDLE(exe, name='kit-gui.app', icon=None, bundle_identifier=None)
""")

if __name__ == "__main__":
    create_spec_file()
