pip install virtualenv

python -m virtualenv mapilio_venv
call .\mapilio_venv\Scripts\activate

pip install -r requirements.txt

python setup.py install --force
mapilio_kit --version

echo "Installation has completed"

echo "Please run 'mapilio_kit --help' to get started"
