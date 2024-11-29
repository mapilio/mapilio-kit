import json
import os
import shutil
import sys
import webbrowser

from flask import Flask, render_template, request, redirect, url_for, jsonify

from mapilio_kit.base import authenticator
from mapilio_kit.components.utilities.edit_config import edit_config
from mapilio_kit.components.geotagging.geotag_property_handler import geotag_property_handler
from mapilio_kit.components.utilities.insert_MAPJson import insert_MAPJson
from mapilio_kit.components.auth.login import list_all_users
from mapilio_kit.components.metadata.metadata_property_handler import metadata_property_handler
from mapilio_kit.components.processing.sequence_property_handler import sequence_property_handler
from mapilio_kit.components.upload.upload import upload

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.expanduser("~"), ".cache", "mapilio", "MapilioKit", "images/")

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


def get_args_mapilio(func):
    arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
    return {arg: None for arg in arg_names}


def check_authenticate():
    global authentication_status, token
    if len(list_all_users()) == 0:
        authentication_status = False
        token = None
    elif len(list_all_users()) >= 2:
        token = None
        authentication_status = False
        remove_accounts()
    else:
        token = list_all_users()[0]['user_upload_token']
        authentication_status = True

    return token, authentication_status


def decompose(import_path, exiftool_path):
    metadata_property_handler(import_path=import_path, exiftool_path=exiftool_path)
    geotag_property_handler(import_path=import_path)
    sequence_property_handler(import_path=import_path)
    insert_MAPJson(import_path=import_path)


@app.route("/", methods=["GET", "POST"])
def index():
    token, authentication_status = check_authenticate()
    if authentication_status:
        return render_template("image-upload.html", token=token)
    else:
        return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def mapilio_login():
    if request.method == 'POST':
        args = get_args_mapilio(edit_config)
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        username = email.split('@')[0]

        args["user_name"] = username
        args["user_email"] = email
        args["user_password"] = str(password)
        args["gui"] = True
        check_authenticate = authenticator().perform_task(args)

        if check_authenticate['status']:
            message = check_authenticate['message']
            token = check_authenticate['token']
            return render_template("image-upload.html", message=message, token=token)
        else:
            message = check_authenticate['message']
            return render_template('login.html', message=message)
    else:
        return render_template('login.html')


@app.route('/logout', methods=['GET'])
def remove_accounts():
    if os.path.exists(MAPILIO_CONFIG_PATH):
        os.remove(MAPILIO_CONFIG_PATH)
        return jsonify(success=True, message="Account successfully removed!"), 200
    else:
        return jsonify(success=True, message="No accounts found!"), 200


@app.route('/image-upload', methods=['GET', 'POST'])
def mapilio_upload_page():
    if request.method == 'GET':
        token, authentication_status = check_authenticate()

        if authentication_status:
            return render_template('image-upload.html', token=token)
        else:
            return redirect(url_for("mapilio_login"))
    elif request.method == 'POST':
        if 'file' not in request.files:
            return jsonify(success=False, message="No file part")
        for file in request.files.getlist('file'):
            if file.filename == '':
                continue
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(UPLOAD_FOLDER + file.filename)

        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        if app.debug:
            path_to_exiftool = "/usr/bin/exiftool"
        else:
            path_to_exiftool = os.path.abspath(os.path.join(bundle_dir, 'exiftool/exiftool'))

        try:
            decompose(import_path=UPLOAD_FOLDER, exiftool_path=path_to_exiftool)
            jsonPath = os.path.join(UPLOAD_FOLDER, "mapilio_image_description.json")
            with open(jsonPath, 'r') as f:
                data = json.load(f)
            total_images = data[-1]["Information"]["total_images"]
            processed_images = data[-1]["Information"]["processed_images"]
            failed_images = data[-1]["Information"]["failed_images"]
            duplicated_images = data[-1]["Information"]["duplicated_images"]
        except:
            return jsonify(success=False, message="An error occurred during metadata properties extraction.")

        try:
            upload_status = upload(import_path=UPLOAD_FOLDER, dry_run=False)
            if upload_status.get("Success"):
                try:
                    shutil.rmtree(UPLOAD_FOLDER)
                    return jsonify(success=True, message="Images uploaded successfully", total_images=total_images,
                                   processed_images=processed_images, failed_images=failed_images, duplicated_images=duplicated_images), 200
                except OSError as err:
                    print(f"Error: {UPLOAD_FOLDER} could not be deleted. - {err}")
                    return jsonify(success=False, message=f"{err}")
            else:
                e = upload_status.get("Error")
                return jsonify(success=False, message=f"Error: {e}"), 500
        except:
            e = upload_status.get("Error")
            return jsonify(success=False, message=f"Error: {e}"), 500
    else:
        return jsonify(success=False, message="Method Not Allowed"), 500


@app.route('/video-upload', methods=['GET', 'POST'])
def mapilio_video_upload_page():
    token, authentication_status = check_authenticate()

    if authentication_status:
        return render_template('video-upload.html', token=token)
    else:
        return redirect(url_for("mapilio_login"))


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8081/")
    app.run(host="0.0.0.0", port=8081, debug=True)
    # FlaskUI(app=app, server="flask", width=1200, height=800, port=8080).run()
