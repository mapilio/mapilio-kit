# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
options = [("u", None, "OPTION")]

a = Analysis(
    ['flask_app.py'],
    pathex=[SPECPATH],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('mapilio_kit', 'mapilio_kit'),
        ('testkit-env/lib/python3.10/site-packages/piexif', 'piexif'),
        ('testkit-env/lib/python3.10/site-packages/calculation', 'calculation'),
        ('testkit-env/lib/python3.10/site-packages/gps_anomaly', 'gps_anomaly'),
        ('testkit-env/lib/python3.10/site-packages/exifread', 'exifread'),
        ('testkit-env/lib/python3.10/site-packages/gpxpy', 'gpxpy'),
        ('testkit-env/lib/python3.10/site-packages/pynmea2', 'pynmea2'),
        ('testkit-env/lib/python3.10/site-packages/flask', 'flask'),
        ('testkit-env/lib/python3.10/site-packages/flaskwebgui.py','.'),
        ('testkit-env/lib/python3.10/site-packages/psutil', 'psutil'),
        ('testkit-env/lib/python3.10/site-packages/requests', 'requests'),
        ('testkit-env/lib/python3.10/site-packages/urllib3', 'urllib3'),
        ('testkit-env/lib/python3.10/site-packages/chardet', 'chardet'),
        ('testkit-env/lib/python3.10/site-packages/certifi', 'certifi'),
        ('testkit-env/lib/python3.10/site-packages/jsonschema','jsonschema'),
        ('testkit-env/lib/python3.10/site-packages/attr', 'attr'),
        ('testkit-env/lib/python3.10/site-packages/pyrsistent','pyrsistent')
    ],
    hiddenimports=[],
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
    name="MapilioKit-Flask",
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
)

app = BUNDLE(exe, name="kit-gui.app", icon=None, bundle_identifier=None)