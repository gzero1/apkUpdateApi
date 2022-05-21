# api.py


import io
import os
import semver
import schemas
import threading

from datetime import datetime
from typing import Generator, Union
from ftplib import FTP, error_perm
from queue import Queue
from dal import get_all_downloaded_android_ids_by_name, get_apk_by_app_id_and_version, get_apks_by_app_id, get_app_by_name, get_apps_by_user_id, get_latest_apk_by_app_id, get_app_download_by_android_id, get_total_downloads_by_name, get_total_updated_by_name
from dotenv import load_dotenv
from authentication import current_active_user, fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, File, Form, HTTPException
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import models
from fastapi_users import BaseUserManager, models
from fastapi_users.manager import (
    BaseUserManager,
    InvalidPasswordException,
    UserAlreadyExists
)
from fastapi.responses import StreamingResponse
from fastapi_users.router.common import ErrorCode, ErrorModel
from database import Apk, DownloadHistory, UserTable, get_async_session

router = APIRouter()
load_dotenv()

@router.get('/apps')
async def get_apps( session: AsyncSession = Depends(get_async_session), user: UserTable = Depends(current_active_user)):
    return await get_apps_by_user_id(session, user.id)
    

@router.get('/info/{name}')
async def get_app_info(name: str, session: AsyncSession = Depends(get_async_session)):
    app = await get_app_by_name(session, name)
    if (app == None):
        raise HTTPException(status_code=404, detail='Não foi possível achar o aplicativo')
    latest_apk = await get_latest_apk_by_app_id(session, app.id)

    return {
        **app.__dict__, 
        'latest_version': latest_apk.version if latest_apk is not None else None,
        'total_downloads': await get_total_downloads_by_name(session, name),
        'total_updated': await get_total_updated_by_name(session, name)
    }

@router.get('/info/{name}/apks')
async def get_app_info(name: str, session: AsyncSession = Depends(get_async_session)):
    app = await get_app_by_name(session, name)
    if (app == None):
        raise HTTPException(status_code=404, detail='Não foi possível achar o aplicativo')
    apks = await get_apks_by_app_id(session, app.id, filterUnstable=False)

    return apks

@router.post('/info/{name}')
async def set_app_info(name: str, body: schemas.SetAppBody, session: AsyncSession = Depends(get_async_session)):
    app = await get_app_by_name(session, name)
    if (app == None):
        raise HTTPException(status_code=404, detail='Não foi possível achar o aplicativo')

    apk = await get_apk_by_app_id_and_version(session, app.id, body.version)
    if (apk == None):
        raise HTTPException(status_code=400, detail='A versão especificada não existe')
    apk.is_stable = body.is_stable
    await session.commit()
    await session.flush()
    return {'message': 'success'}

@router.post('/upload/{name}')
async def create_file(
    name: str,
    file: bytes = File(...),
    version: str = Form(...),
    is_stable: bool = Form(True),
    session: AsyncSession = Depends(get_async_session),
    _ = Depends(current_active_user)):

    print(is_stable)
    if (not semver.VersionInfo.isvalid(version)):
        raise HTTPException(status_code=400, detail='Versão não formatada corretamente')
    
    app = await get_app_by_name(session, name)

    apks = await get_apks_by_app_id(session, app.id)
    
    # Convention will be {name}{parsed_semver}.apk like biju3_6_3-beta.apk
    filename = '{}{}'.format(app.name, version.replace('.', '_'))

    try:
        ftp = FTP('theddy.top', timeout=5)
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
        raise HTTPException(status_code=401, detail='FTP recusou a conexão')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail='Erro na conexão com FTP')

    

    return {'filesize': len(file)}

@router.get('/download/{name}/latest')
async def download_file(name: str, android_id: Union[str, None] = None, session: AsyncSession = Depends(get_async_session)):

    app = await get_app_by_name(session, name)
    if (app == None):
        raise HTTPException(status_code=404, detail='Aplicativo não encontrado')

    latest_apk = await get_latest_apk_by_app_id(session, app.id)

    # Convention will be {name}{parsed_semver}.apk like biju3_6_3-beta.apk
    filename = '{}{}'.format(app.name, latest_apk.version.replace('.', '_'))
    
    try:
        ftp = FTP('theddy.top', timeout=5)
        ftp.login('app@theddy.top', os.environ.get('FTP_PASS'))
        ftp.cwd('./updater')
        size = ftp.size(f'./{filename}.apk')

        def chunk() -> Generator[bytes, None, None]:
            queue = Queue(maxsize=2048)

            def ftp_threading():
                ftp.retrbinary(f'RETR ./{filename}.apk', callback=queue.put)
                queue.put(None)
            
            ftp_thread = threading.Thread(target=ftp_threading)
            ftp_thread.start()

            while True:
                chunk = queue.get()
                if chunk is not None:
                    yield chunk
                else:
                    ftp.quit()
                    return
        
        if android_id is not None:
            if android_id not in (await get_all_downloaded_android_ids_by_name(session, name)):
                new_download = DownloadHistory(android_id=android_id,app_id=app.id, version=latest_apk.version)
                session.add(new_download)
            else:
                updated_download = await get_app_download_by_android_id(session, name, android_id)
                updated_download.downloaded_at = datetime.now()
            await session.commit()
            await session.flush()
        return StreamingResponse(chunk(), headers={'content-length': str(size)}, media_type='application/vnd.android.package-archive')

    except error_perm as e:
        if ('No such file or directory' in e.args[0]):
            raise HTTPException(status_code=401, detail=f'Arquivo {filename}.apk não existe no FTP')
        raise HTTPException(status_code=401, detail='FTP recusou a conexão')

    except ValueError as e:
        raise HTTPException(status_code=400, detail='android_id inválido')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail='Erro na conexão com ftp')

@router.get('/download_info/{name}')
async def download_info(name: str, android_id: Union[str, None], session: AsyncSession = Depends(get_async_session), _ = Depends(current_active_user)):
    download = await get_app_download_by_android_id(session, name, android_id)
    if download is None:
        raise HTTPException(status_code=404, detail='android_id não existe')
    latest_apk = await get_latest_apk_by_app_id(session, download.app_id)
    return {
        'is_updated': download.version == latest_apk.version,
        'current_version': download.version,
        'downloaded_at': download.downloaded_at
    }

@router.post(
    '/auth/register', 
    response_model=schemas.UserDB,
    status_code=status.HTTP_201_CREATED,
    name='register:register', 
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ErrorModel,
            'content': {
                'application/json': {
                    'examples': {
                        ErrorCode.REGISTER_USER_ALREADY_EXISTS: {
                            'summary': 'A user with this email already exists.',
                            'value': {
                                'detail': ErrorCode.REGISTER_USER_ALREADY_EXISTS
                            },
                        },
                        ErrorCode.REGISTER_INVALID_PASSWORD: {
                            'summary': 'Password validation failed.',
                            'value': {
                                'detail': {
                                    'code': ErrorCode.REGISTER_INVALID_PASSWORD,
                                    'reason': 'Password should be'
                                    'at least 3 characters',
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
                'code': ErrorCode.REGISTER_INVALID_PASSWORD,
                'reason': e.reason,
            },
        )

    return created_user

