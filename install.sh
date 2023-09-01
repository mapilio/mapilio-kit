
echo " __  __    _    ____ ___ _     ___ ___      _  _____ _____"
echo "|  \/  |  / \  |  _ \_ _| |   |_ _/ _ \    | |/ /_ _|_   _|"
echo "| |\/| | / _ \ | |_) | || |    | | | | |   | ' / | |  | |  "
echo "| |  | |/ ___ \|  __/| || |___ | | |_| |   | . \ | |  | |  "
echo "|_|  |_/_/   \_\_|  |___|_____|___\___/    |_|\_\___| |_|  "

python3 -m virtualenv mapilio_venv
. mapilio_venv/bin/activate

python setup.py install --force
mapilio_kit --version

echo "Installation has completed"

