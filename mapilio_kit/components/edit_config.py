import os
from mapilio_kit.components.login import prompt_user_for_user_items
from mapilio_kit.components import auth_config, config
import logging


def edit_config(
        config_file=None,
        user_name=None,
        user_email=None,
        user_password=None,
        jwt=None,
        force_overwrite=False,
        user_key=None,
        gui=None,
        verbose=False,
):
    if gui: return edit_config_gui(user_name,
                                   user_email,
                                   user_password,
                                   config_file=config_file)

    if config_file is None:
        config_file = config.MAPILIO_CONFIG_PATH

    if not os.path.isfile(config_file):
        config.create_config(config_file)

    if jwt:
        if user_name is None or user_key is None:
            pass

        user_items = {
            "SettingsEmail": user_email,
            "SettingsUsername": user_name,
            "SettingsUserPassword": user_password,
            "SettingsUserKey": user_key,
            "user_upload_token": jwt,
        }

        config.update_config(config_file, user_name, user_items)
        return

    if user_key and user_name:  # Manually add user_key
        user_items = {
            "SettingsUsername": "Dummy_SettingsUsername",
            "SettingsEmail": "Dummy_SettingsEmail",
            "SettingsUserKey": user_key,
            "user_upload_token": "Dummy_upload_token",
        }
        config.update_config(config_file, user_name, user_items)
        print("User key added successfully")
        return

    if not user_name:
        if gui is not None:
            user_name = input(
                "Please enter your user_name (this will be used to identify your mail): ")
            print(f"\n Sign in for user {user_name}")
        else:
            return

    # config file must exist at this step
    config_object = config.load_config(config_file)

    # safety check if section exists, otherwise add it
    if user_name in config_object.sections():
        if not force_overwrite:
            if verbose:
                print("Warning, mail exists with the following items : ")
                print(config.load_user(config_object, user_name))
            else:
                print("Warning, mail exists")
                config.load_user(config_object, user_name)
            sure = input(
                "Are you sure you would like to re-authenticate (current parameters will be overwritten) [y,Y,yes,Yes]?"
            )
            if sure not in ["y", "Y", "yes", "Yes"]:
                print(
                    f"Aborting re-authentication. If you would like to re-authenticate mail {user_name}, "
                    f"rerun this command and confirm re-authentication."
                )
                return
    else:
        config_object.add_section(user_name)

    try:
        user_items = prompt_user_for_user_items(user_name, user_password, user_email)
        print("Authentication successfully done. \n")
    except:
        print("Authentication process failed, please try again. \n")
        return False

    config.update_config(config_file, user_name, user_items)
    return True


def edit_config_gui(
        user_name,
        user_email,
        user_password,
        config_file=None
):
    if config_file is None:
        config_file = config.MAPILIO_CONFIG_PATH

    if not os.path.isfile(config_file):
        config.create_config(config_file)

    config_object = config.load_config(config_file)

    config_object.add_section(user_name)

    try:
        data = auth_config.get_upload_token(user_email, user_password)
        upload_token, user_key = data.get("token"), data.get("id")

        if upload_token:
            user_items = {
                "SettingsEmail": user_email,
                "SettingsUsername": user_name,
                "SettingsUserPassword": user_password,
                "SettingsUserKey": str(user_key),
                "user_upload_token": upload_token,
            }

            config.update_config(config_file, user_email, user_items)
            response = {'status': True, "message": "Authentication successfully done", "token": upload_token}
            return response

        else:
            response = {'status': False, "message": data.get("message")[0]}
            return response

    except Exception as e:
        response = {'status': False, "message": f"{str(e)}. Please try again."}
        logging.error(f"Authentication failed: {str(e)}. Please try again.")
        return response
