import configparser
import os
import typing as T

import types_fmt as types
MAPILIO_API_ENDPOINT = os.getenv(
    "MAPILIO_API_ENDPOINT", "https://end.mapilio.com/api/"
)
MAPILIO_CDN_ENDPOINT = os.getenv(
    "MAPILIO_CDN_ENDPOINT", "https://cdn.mapilio.com/"
)

# POST METHODS noqa
MAPILIO_API_URL_FUNCTION = 'function/mapilio/imagery/'
MAPILIO_API_ENDPOINT_UPLOAD = MAPILIO_API_ENDPOINT + MAPILIO_API_URL_FUNCTION + 'upload'
MAPILIO_UPLOAD_ENDPOINT_ZIP = MAPILIO_CDN_ENDPOINT + "upload/"

# GET METHODS noqa
URL_CDN = MAPILIO_CDN_ENDPOINT + "im/"
URL_Sequences = MAPILIO_API_ENDPOINT + MAPILIO_API_URL_FUNCTION + "getUploadsWithProject/"
URL_Images = MAPILIO_API_ENDPOINT + MAPILIO_API_URL_FUNCTION + "getUploadsImagesWithProject/"


MAPILIO_CONFIG_PATH = os.getenv(
    "MAPILIO_CONFIG_PATH",
    os.path.join(
        os.path.expanduser("~"),
        ".config",
        "mapilio",
        "configs",
        "CLIENT_USERS",
    ),
)


def load_config(config_path: str) -> configparser.ConfigParser:
    if not os.path.isfile(config_path):
        raise RuntimeError(f"config {config_path} does not exist")
    config = configparser.ConfigParser()
    config.optionxform = str  # type: ignore
    config.read(config_path)
    return config


def save_config(config: configparser.ConfigParser, config_path: str) -> None:
    with open(config_path, "w") as cfg:
        config.write(cfg)


def load_user(config: configparser.ConfigParser, user_name: str) -> types.User:
    user_items = dict(config.items(user_name))
    return T.cast(types.User, user_items)


def add_user(
    config: configparser.ConfigParser, user_name: str, config_path: str
) -> None:
    if user_name not in config.sections():
        config.add_section(user_name)
    else:
        print(f"Error, user {user_name} already exists")
    save_config(config, config_path)

def delete_user(config: configparser.ConfigParser, user_name: str, config_path: str) -> None:
    if user_name in config.sections():
        config.remove_section(user_name)
        save_config(config, config_path)
    else:
        print(f"Error, user {user_name} does not exist")

def set_user_items(
    config: configparser.ConfigParser, user_name: str, user_items: types.User
) -> configparser.ConfigParser:
    for key, val in user_items.items():
        config.set(user_name, key, T.cast(str, val))
    return config


def update_config(config_path: str, user_name: str, user_items: types.User) -> None:
    config = load_config(config_path)
    if user_name not in config.sections():
        add_user(config, user_name, config_path)
    config = set_user_items(config, user_name, user_items)
    save_config(config, config_path)


def create_config(config_path: str) -> None:
    if not os.path.isdir(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path))
    open(config_path, "a").close()