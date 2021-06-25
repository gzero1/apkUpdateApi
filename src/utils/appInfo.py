from re import A
from flask import app
from flask.json import jsonify
from database.storage import query
from database.model import AppInfo

def getAppInfo(app_name):
    queryString = "Select name, respository_link, latest_version from app_info where app_name = %s"
    queryParameters = (app_name,)
    queryReturn = query(queryString, queryParameters)
    if (queryReturn == []):
        return jsonify({"message": 'Not found', "appInfo": ""}), 404
    appInformation = AppInfo()
    appInformation.name = queryReturn[0][0]
    appInformation.repository_link = queryReturn[0][1]
    appInformation.latest_version = queryReturn[0][2]
    appInformation.app_name = app_name

    return jsonify(
        {
            "message": "Retrieved succesfully!", 
            "appInfo": appInformation.__dict__
        }
    ), 200

