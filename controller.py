# api.py

import io
import os
from functools import cmp_to_key
from ftplib import FTP, error_perm
from pyexpat import model
from typing import List, Union
from dal import get_apks_by_app_id, get_app_by_name, get_apps_by_user_id, get_latest_apk_by_app_id
from schemas import HTTPError, User, UserDB
from fastapi import APIRouter, Depends, File, Form, Response, HTTPException, UploadFile
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from fastapi_users import BaseUserManager, models
from authentication import current_active_user, fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import schemas
import semver
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import models
from fastapi_users.manager import (
    BaseUserManager,
    InvalidPasswordException,
    UserAlreadyExists
)
from fastapi_users.router.common import ErrorCode, ErrorModel
from database import Apk, App, AppUser, UserTable, get_async_session
router = APIRouter()
load_dotenv()

@router.get("/apps")
async def get_apps( session: AsyncSession = Depends(get_async_session), user: UserTable = Depends(current_active_user)):
    return await get_apps_by_user_id(session, user.id)
    

@router.get("/info/{name}")
async def get_app_info(name: str, session: AsyncSession = Depends(get_async_session), _ = Depends(current_active_user)):
    app = await get_app_by_name(session, name)
    if (app == None):
        raise HTTPException(status_code=404, detail="Não foi possível achar o aplicativo")
    latest_apk = await get_latest_apk_by_app_id(session, app.id)
    
    return {**app.__dict__, "latest_version": latest_apk.version if latest_apk is not None else None}

@router.post("/upload/{name}")
async def create_file(
    name: str,
    file: bytes = File(...),
    version: str = Form(...),
    is_stable: bool = Form(True),
    session: AsyncSession = Depends(get_async_session),
    _ = Depends(current_active_user)):

    print(is_stable)
    if (not semver.VersionInfo.isvalid(version)):
        raise HTTPException(status_code=400, detail="Versão não formatada corretamente")
    
    app = await get_app_by_name(session, name)

    apks = await get_apks_by_app_id(session, app.id)

    
    
    # Convention will be {name}_{parsed_semver}.apk like biju3_6_3-beta.apk
    filename = '{}{}'.format(app.name, version.replace('.', '_'))

    try:
        ftp = FTP('theddy.top')
        ftp.login('app@theddy.top', os.environ.get('FTP_PASS'))

        ftp.cwd('updater')
        file_like = io.BytesIO(file)

        ftp.storbinary(f'STOR ./{filename}.apk', file_like)

        ftp.quit()

        if (version not in map(lambda apk: apk.version, apks)):
            new_apk = Apk(app=app,app_id=app.id, is_stable=is_stable, version=version)
            session.add(new_apk)
            await session.commit()
            await session.flush()

    except error_perm:
        raise HTTPException(status_code=401, detail="FTP recusou a conexão")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Erro na conexão com FTP")

    

    return {"filesize": len(file)}

@router.get("/download/{name}/latest")
async def download_file(name: str, session: AsyncSession = Depends(get_async_session)):

    app = await get_app_by_name(session, name)
    if (app == None):
        raise HTTPException(status_code=404, detail="Aplicativo não encontrado")

    latest_apk = await get_latest_apk_by_app_id(session, app.id)

    # Convention will be {name}_{parsed_semver}.apk like biju3_6_3-beta.apk
    filename = '{}{}'.format(app.name, latest_apk.version.replace('.', '_'))
    
    _bytes = bytearray()
    try:
        ftp = FTP('theddy.top')
        ftp.login('app@theddy.top', os.environ.get('FTP_PASS'))
        ftp.cwd('./updater')
        ftp.retrbinary(f'RETR ./{filename}.apk', lambda byte: _bytes.extend(byte))

        ftp.quit()

    except error_perm as e:
        if ('No such file or directory' in e.args[0]):
            raise HTTPException(status_code=401, detail=f"Arquivo {filename}.apk não existe no FTP")
        raise HTTPException(status_code=401, detail="FTP recusou a conexão")
    except Exception:
        raise HTTPException(status_code=401, detail="Erro na conexão com ftp")

    return Response(bytes(_bytes), media_type='application/vnd.android.package-archive')

@router.post(
    "/auth/register", 
    response_model=schemas.UserDB,
    status_code=status.HTTP_201_CREATED,
    name="register:register", 
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.REGISTER_USER_ALREADY_EXISTS: {
                            "summary": "A user with this email already exists.",
                            "value": {
                                "detail": ErrorCode.REGISTER_USER_ALREADY_EXISTS
                            },
                        },
                        ErrorCode.REGISTER_INVALID_PASSWORD: {
                            "summary": "Password validation failed.",
                            "value": {
                                "detail": {
                                    "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                                    "reason": "Password should be"
                                    "at least 3 characters",
                                }
                            },
                        },
                    }
                }
            },
        },
    },
)
async def register(
    request: Request,
    user: schemas.UserCreate,  # type: ignore
    user_manager: BaseUserManager[models.UC, models.UD] = Depends(fastapi_users.get_user_manager),
    _ = Depends(current_active_user)
):
    try:
        created_user = await user_manager.create(user, safe=True, request=request)
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
        )
    except InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                "reason": e.reason,
            },
        )

    return created_user

