python3 -m pip uninstall -y pyinstaller
git clone --depth=1 --branch v5.12.0 https://github.com/pyinstaller/pyinstaller.git pyinstaller_git
cd pyinstaller_git/bootloader # pwd: ./pyinstaller_git/bootloader
python3 ./waf all
git diff
cd ..  # pwd: ./pyinstaller_git
python3 -m pip install .
cd ..  # pwd: ./