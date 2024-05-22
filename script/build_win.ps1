$OS="win"
# this is OS arch
# $ARCH=(wmic OS get OSArchitecture)[2]
$MAXSIZE32=python3 -c "import sys; print(sys.maxsize <= 2**32)"
if ($MAXSIZE32 -ceq "True") {
    $ARCH="32bit"
} else {
    $ARCH="64bit"
}

# build
mkdir -Force dist
pyinstaller --version
pyinstaller --noconfirm --distpath dist\win flask_app.spec

# check
$SOURCE="dist\win\MapilioKit-Flask.exe"
dist\win\mapilio-kit.exe --version
$VERSION_OUTPUT=dist\win\mapilio-kit.exe --version
$VERSION=$VERSION_OUTPUT.split(' ')[2]
$TARGET="dist\releases\mapilio-kit-$VERSION-$OS-$ARCH.exe"

# package
mkdir -Force dist\releases
Copy-Item "$SOURCE" "$TARGET"

# sha256
Get-FileHash $TARGET -Algorithm SHA256 | Select-Object Hash > "$TARGET.sha256.txt"

# summary
Get-ChildItem dist\releases