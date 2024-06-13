import os
import subprocess
import sys
from pathlib import Path

def install_exiftool():
    if sys.platform == 'linux':
        subprocess.run(['sudo', 'apt', 'install', '-y', 'exiftool'], check=True)
    elif sys.platform == 'darwin':
        subprocess.run(['brew', 'install', 'exiftool'], check=True)
    elif sys.platform == 'win32':
        subprocess.run(['powershell', '-Command',
                        'Set-ExecutionPolicy Bypass -Scope Process -Force; '
                        '[System.Net.ServicePointManager]::SecurityProtocol = '
                        '[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
                        'iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\'))'],
                       check=True)
        subprocess.run(['choco', 'install', 'exiftool', '-y'], check=True)
    else:
        raise ValueError("Unsupported platform")


def get_exiftool_path():
    try:
        if sys.platform == 'linux' or sys.platform == 'darwin':
            # Unix-based systems (Linux, macOS)
            result = subprocess.run(['which', 'exiftool'], capture_output=True, text=True)
        elif sys.platform == 'win32':
            # Windows
            result = subprocess.run(['where', 'exiftool'], capture_output=True, text=True)
        else:
            raise ValueError("Unsupported operating system")

        if result.returncode != 0:
            raise ValueError("ExifTool not found")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error finding ExifTool: {e}")

def get_installed_package_path(package_name):
    result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name], capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"Package {package_name} not found")

    location = None
    for line in result.stdout.splitlines():
        if line.startswith('Location:'):
            location = line.split(' ', 1)[1].strip()
            break

    if not location:
        raise ValueError(f"Location not found for package {package_name}")

    package_folder_name = package_name.split('-')[0]
    package_path = Path(location) / package_folder_name
    if package_path.exists():
        return package_path

    package_folder_name = package_name.replace('-', '_')
    package_path = Path(location) / package_folder_name
    if package_path.exists():
        return package_path

    package_path_with_py = package_path.with_suffix('.py')
    if package_path_with_py.exists():
        return package_path_with_py

    if package_name == 'attrs':
        alt_package_name = 'attr'
        alt_package_path = Path(location) / alt_package_name
        if alt_package_path.exists():
            return alt_package_path

    raise ValueError(f"Package path not found for {package_name}")

def create_spec_file():
    requirements_file = 'requirements.txt'
    spec_file = 'flask_app.spec'

    current_directory = os.getcwd()
    datas = [('templates', 'templates'), ('static', 'static'), ({current_directory}, 'mapilio_kit')]
    hiddenimports = ['configparser']

    # ExifTool'u kur ve yolunu bul
    install_exiftool()
    try:
        exiftool_path = get_exiftool_path()
        datas.append((exiftool_path, 'exiftool'))
    except ValueError as e:
        print(f"Warning: {e}")

    with open(requirements_file) as f:
        packages = [line.split('==')[0].strip() for line in f if line.strip() and not line.startswith('#')]
        print(packages)

    for package in packages:
        try:
            if package == 'ExifRead':
                package = 'exifread'
            package_path = get_installed_package_path(package)

            package_folder_name = package.replace('-', '_')
            hiddenimports.append(package_folder_name)

            if package_folder_name == package:
                package_data_name = package
            else:
                package_data_name = package_path.parts[-1]

            datas.append((str(package_path), package_data_name))

        except ValueError as e:
            print(f"Warning: {e}")
    print(datas)
    with open(spec_file, 'w') as f:
        f.write(f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

options = [("u", None, "OPTION")]

a = Analysis(
    ['flask_app.py'],
    pathex=[SPECPATH],
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
    options,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MapilioKit-Flask',
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
)

app = BUNDLE(exe, name='kit-gui.app', icon=None, bundle_identifier=None)
""")

if __name__ == "__main__":
    create_spec_file()
