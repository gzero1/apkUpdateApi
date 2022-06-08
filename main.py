# Import FastAPI
import os
import controller

from dotenv import load_dotenv
from fastapi import FastAPI
from authentication import auth_backend, fastapi_users
from database import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

load_dotenv()

# Initialize the app
app = FastAPI()

TYPE = os.getenv('DATABASE_URL')
if TYPE.lower() == 'prod':
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
# app.include_router(fastapi_users.get_register_router(), prefix="/auth", tags=["auth"])
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])
app.include_router(controller.router)

@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    print('started up')
    await create_db_and_tables()

# GET operation at route '/'
@app.get('/')
async def root_api():
    # await create_db_and_tables()

    return {"message": "Welcome to App Updater Api"}