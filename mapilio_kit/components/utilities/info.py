import sys
import time

import requests

from mapilio_kit.components.utilities.config import MAPILIO_CDN_ENDPOINT


def alert_maintenance():
    red_blink = "\033[5;31m"  # ANSI code for blinking red text
    reset = "\033[0m"  # ANSI code to reset formatting
    error_message = "The system is currently undergoing maintenance. Please try again later."

    formatted_message = f"{red_blink}{error_message}{reset}"

    for _ in range(5):  # Blinks 5 times before exiting
        sys.stderr.write(f"{formatted_message}\n")
        sys.stderr.flush()
        time.sleep(0.5)  # Half-second delay between blinks
        sys.stderr.write("\033[F\033[K")  # Move cursor up and clear line
        sys.stderr.flush()
        time.sleep(0.5)

    sys.exit(1)


def maintenance_info():
    url = MAPILIO_CDN_ENDPOINT + "v1/hearbeat-check"
    try:
        response = requests.get(url)
        if response.json()['mode']:
            alert_maintenance()
    except Exception as e:
        alert_maintenance()


def get_latest_version():
    url = "https://raw.githubusercontent.com/mapilio/mapilio-kit/main/mapilio_kit/components/version.py"
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        version_line = [line for line in content.split('\n') if 'VERSION' in line][0]
        latest_version = version_line.split('"')[1]
        return latest_version
    return None


if __name__ == "__main__":
    maintenance_info()
