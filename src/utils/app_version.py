from database.storage import query
from database.model import AppVersions
import semver
import uuid

def checkAppVersion(app_name, version_type, version = 'latest'):
    if (version == 'latest'): 
        queryString = "Select version from app_versions where app_name = %s and version_type = %s order by version_date desc limit 1"
        params = (app_name, version_type)
    else:
        queryString = "Select version from app_versions where app_name = %s and version_type = %s and version = %s order by version_date desc limit 1"
        params = (app_name, version_type, version)

    result = query(queryString, params)
    if (len(result) > 0):
        return result[0][0]
    else:
        return "not found"


def newAppVersion(app: AppVersions):
    resultQuery = checkAppVersion(app.app_name, app.version_type, app.version)
    app.version = app.version.replace("_", ".")
    print(resultQuery)
    if (resultQuery != "not found"):
        queryString = "UPDATE app_versions SET version = %s, version_date = NOW() where app_name = %s and version_type = %s and version = %s"
        queryParams = (app.version, app.app_name, app.version_type, app.version)
    else:
        queryString = "INSERT INTO app_versions (app_name, version, version_type, file_name) VALUES(%s, %s, %s, %s)"
        queryParams = (app.app_name, app.version, app.version_type, app.file_name)

    resultQuery = query(queryString, queryParams, False)

    if (app.version_type == 'stable'):
        returnVersion = query(
                            "Select latest_version from app_info where app_name = %s",
                            (app.app_name,)
                        )
        print(returnVersion[0][0])
        if (semver.compare(returnVersion[0][0], app.version) == -1): # app.version > returnVersion
            query(
                "UPDATE app_info set latest_version = %s where app_name = %s",
                (app.version, app.app_name),
                False
            )


    return 

def saveApk(apk):
    fileName = uuid.uuid4()
    print(fileName)
    apk.save('./apks/fileUpload/' + str(fileName) + '.apk')
    return str(fileName)

def getFileName(appName:str , version:str):
    if (version == "latest"):
        queryString = "Select version.file_name from app_versions as version, app_info as info where version.app_name = info.app_name and version.version = info.latest_version and info.app_name = %s "
        queryParams = (appName,)
    elif (version == "unstable"):
        queryString = "Select file_name from app_versions where app_name = %s and version_type = 'unstable' order by version_date desc limit 1"
        queryString = (appName,)
    else:
        version = version.replace("_", ".")
        queryString = "Select file_name from app_versions where app_name = %s and version = %s "
        queryParams = (appName, version)
    resultQuery = query(queryString, queryParams)
    if (resultQuery == []):
        return ''

    return resultQuery[0][0]
        
#def getLastVersion(app: AppVersions):

    
