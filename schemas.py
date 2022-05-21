# schemas.py
import datetime
from sqlalchemy.orm import Query
from pydantic import BaseModel, validator
from fastapi_users import models

    
class OrmBase(BaseModel):
    # Common properties across orm models
    id: int

    # Pre-processing validator that evaluates lazy relationships before any other validation
    # NOTE: If high throughput/performance is a concern, you can/should probably apply
    #       this validator in a more targeted fashion instead of a wildcard in a base class.
    #       This approach is by no means slow, but adds a minor amount of overhead for every field
    @validator("*", pre=True)
    def evaluate_lazy_columns(cls, v):
        if isinstance(v, Query):
            return v.all()
        return v

    class Config:
        orm_mode = True

class App(OrmBase):
    name: str
    display_name : str
    repo_url: str

# TO support creation and update APIs
class Apk(OrmBase):
    is_stable: bool
    version: str
    app_id: int
    uploaded_at: datetime.datetime


class AppUser(OrmBase):
    app_id = int
    user_id = str


class User(models.BaseUser):
    pass
    

class UserCreate(models.BaseUserCreate):
    pass
    


class UserUpdate(models.BaseUserUpdate):
    pass
    


class UserDB(User, models.BaseUserDB):
    pass

class HTTPError(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised."},
        }

class SetAppBody(BaseModel):
    version: str
    is_stable: bool



