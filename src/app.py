import os
import ssl
from flask.helpers import send_from_directory
from database.model import Users, AppVersions
from utils.app_version import checkAppVersion, newAppVersion, saveApk, getFileName
from utils.appInfo import getAppInfo
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
from utils.login import checkLogin

from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies

app = Flask(__name__)

# Setup the Flask-JWT-Extended extension
# app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
key = os.environ.get('JWTKEY')
app.config["JWT_SECRET_KEY"] = key  # Change this!
jwt = JWTManager(app)

app.config['UPLOAD_FOLDER'] = '/tmp/fileUpload'
app.config['MAX_CONTENT_PATH'] = 150000000
CORS(app, origins=["*"])

# Login
@app.route('/authorize', methods=["POST"])
def authorize():    
    user = Users()
    user.login = request.json["login"]
    user.password = request.json["password"]
    access_token = create_access_token(identity="example_user")
    response = jsonify({"message": "login successful", "token": access_token})
    return response


# Get Application information
@app.route('/getInfo/<app_name>', methods=["GET"])
@jwt_required()
def getInfo(app_name: str):
    return getAppInfo(app_name)


# Upload new version
@app.route('/upload/<app_name>/<version>/<type>', methods=["POST"])
@jwt_required()
def newVersion(app_name: str, type: str, version: str):
    fileName = saveApk(request.files['apk'])

    appData = AppVersions()
    appData.app_name = app_name
    appData.version = version
    appData.version_type = type
    appData.file_name = fileName

    newAppVersion(appData)
    return jsonify({'message': 'New version has been inserted in the system!'})

# Checking latest version
@app.route('/checkVersion/<app_name>/<type>', methods=["GET"])
def checkVersion(app_name, type):
    return jsonify({ "latest_version": checkAppVersion(app_name, type)})


# Download the desired version
@app.route('/download/<app_name>/<version>', methods=["GET"])
def downloadLatestVersion(app_name: str, version: str):
    fileName = getFileName(app_name, version)
    print("fileName: ", fileName)
    if (fileName == ''):
        return jsonify({"message": "Aplication/Version not found"}), 401
    print(fileName)
    return send_from_directory('./apks/fileUpload', f'{fileName}.apk', as_attachment=True, fileName = f"{app_name}.apk")

# ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# ctx.load_cert_chain('cert.pem', 'key.pem')
app.run(host= '0.0.0.0', port= 3432, debug=False)

