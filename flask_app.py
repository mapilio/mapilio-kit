from flask import Flask, render_template, request, redirect, url_for, jsonify
from flaskwebgui import FlaskUI
import webbrowser
import os
import subprocess
import shutil
import re

from mapilio_kit.base import authenticator
from mapilio_kit.components.edit_config import edit_config
from mapilio_kit.components.login import list_all_users

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


@app.route("/", methods=["GET", "POST"])
def index():
    token, authentication_status = check_authenticate()
    if authentication_status:
        return render_template("image-upload.html", token=token)
    else:
        return render_template('login.html')


@app.route('/login', methods=['GET','POST'])
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

        command = f"mapilio_kit upload {UPLOAD_FOLDER} --dry_run"
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                try:
                    shutil.rmtree(UPLOAD_FOLDER)
                    output_lines = result.stderr.split('\n')
                    output_text = '\n'.join(output_lines)

                    total_images_pattern = r'"total_images": (\d+)'
                    processed_images_pattern = r'"processed_images": (\d+)'
                    failed_images_pattern = r'"failed_images": (\d+)'

                    total_images_match = re.search(total_images_pattern, output_text)
                    processed_images_match = re.search(processed_images_pattern, output_text)
                    failed_images_match = re.search(failed_images_pattern, output_text)

                    total_images = int(total_images_match.group(1)) if total_images_match else 0
                    processed_images = int(processed_images_match.group(1)) if processed_images_match else 0
                    failed_images = int(failed_images_match.group(1)) if failed_images_match else 0

                    return jsonify(success=True, message="Images uploaded successfully", total_images=total_images, processed_images=processed_images, failed_images=failed_images), 200
                except OSError as err:
                    print(f"Error: {UPLOAD_FOLDER} could not be deleted. - {err}")
                    return jsonify(success=False, message=f"{err}")
        except subprocess.CalledProcessError as e:
            return jsonify(success=False, message={e}), 500
    else:
        return jsonify(success=False, message="Method Not Allowed"), 500
    error_message = result.stderr.split()
    error_message = ' '.join(error_message)
    error_index = error_message.find("error:")
    if error_index != -1:
        error_message = error_message[error_index:]
    return jsonify(success=False, message=f"Error: {error_message}"), 500


@app.route('/video-upload', methods=['GET', 'POST'])
def mapilio_video_upload_page():
    token, authentication_status = check_authenticate()

    if authentication_status:
        return render_template('video-upload.html', token=token)
    else:
        return redirect(url_for("mapilio_login"))

if __name__ == "__main__":
    # webbrowser.open("http://127.0.0.1:8081/")
    # app.run(host="0.0.0.0", port=8081, debug=True)
    FlaskUI(app=app, server="flask", width=1200, height=800, port=8080).run()
