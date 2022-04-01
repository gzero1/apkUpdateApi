from functools import cmp_to_key
import semver
from ctypes import Union
from typing import List
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Apk, App, AppUser, DownloadHistory

async def get_apps_by_user_id(session: AsyncSession, user_id: str) -> List[App]:
    app_ids: App = (await session.execute(select(AppUser.app_id).filter_by(user_id=user_id))).scalars().all()
    apps: App = (await session.execute(select(App))).scalars().all()

    return [app for app in apps if app.id in app_ids]

async def get_app_by_name(session: AsyncSession, name: str) -> App:
    return (await session.execute(select(App).filter_by(name=name))).scalar()

async def get_apks_by_app_id(session: AsyncSession, app_id: int, filterUnstable = True) -> List[Apk]:
    filterKwargs = {'app_id': app_id } 
    if filterUnstable == True:
        filterKwargs['is_stable'] = True
    return (await session.execute(select(Apk).filter_by(**filterKwargs))).scalars().all()

async def get_latest_apk_by_app_id(session: AsyncSession, app_id: int) -> Apk:
    apks = await get_apks_by_app_id(session, app_id)

    if len(apks) == 0:
        return None

    latest_apk: Union[Apk, None] = sorted(list(apks), key=cmp_to_key(lambda x, y: semver.compare(x.version, y.version)))[-1] 

    return latest_apk

async def get_apk_by_app_id_and_version(session: AsyncSession, app_id: str, version: str) -> Apk:
    return (await session.execute(select(Apk).filter_by(app_id=app_id, version=version))).scalar()
    
async def get_all_downloaded_android_ids_by_name(session: AsyncSession, name: str) -> List[str]:
    app = await get_app_by_name(session, name)

    return (await session.execute(select(DownloadHistory.android_id).filter_by(app_id=app.id))).scalars().all()

async def get_app_download_by_android_id(session: AsyncSession, name: str, android_id: str) -> DownloadHistory:
    app = await get_app_by_name(session, name)

    return (await session.execute(select(DownloadHistory).filter_by(android_id=android_id, app_id=app.id))).scalar()

async def get_total_downloads_by_name(session: AsyncSession, name: str) -> int:
    app = await get_app_by_name(session, name)
    print((await session.execute(select(func.count(DownloadHistory.id)).filter_by(app_id=app.id))).scalar())
    return (await session.execute(select(func.count(DownloadHistory.id)).filter_by(app_id=app.id))).scalar()

async def get_total_updated_by_name(session: AsyncSession, name: str) -> int:
    app = await get_app_by_name(session, name)

    latest_apk = await get_latest_apk_by_app_id(session, app.id)
    if (latest_apk == None):
        return 0

    return (await session.execute(select(func.count(DownloadHistory.id)).filter_by(app_id=app.id, version=latest_apk.version))).scalar()


# async def get_latest_version_by_app_id(session: AsyncSession, app_id: int) -> None:

    