from datetime import datetime
import uuid

class Users():
    def __init__(self) -> None:
        self.login: str = ""
        self.password: str = ""

class AppVersions (): 
    def __init__(self) -> None:
        self.app_name:str = ""
        self.version_type:str = ""
        self.version:str = ""
        self.version_date:datetime 
        self.file_name: uuid = ""

class AppInfo():
    def __init__(self) -> None:
        self.app_name:str = ""
        self.name: str = ""
        self.repository_link: str = ""
        self.latest_version: str = ""
