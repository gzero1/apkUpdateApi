from functools import cmp_to_key
import semver
from ctypes import Union
from typing import List
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Apk, App, AppUser

async def get_apps_by_user_id(session: AsyncSession, user_id: str) -> List[App]:
    app_ids: App = (await session.execute(select(AppUser.app_id).filter_by(user_id=user_id))).scalars().all()
    apps: App = (await session.execute(select(App))).scalars().all()

    return [app for app in apps if app.id in app_ids]

async def get_app_by_name(session: AsyncSession, name: str) -> App:
    return (await session.execute(select(App).filter_by(name=name))).scalar()

async def get_apks_by_app_id(session: AsyncSession, app_id: int) -> List[Apk]:
    return (await session.execute(select(Apk).filter_by(app_id=app_id, is_stable=True))).scalars().all()

async def get_latest_apk_by_app_id(session: AsyncSession, app_id: int) -> Apk:
    apks = await get_apks_by_app_id(session, app_id)

    if len(apks) == 0:
        return None

    latest_apk: Union[Apk, None] = sorted(list(apks), key=cmp_to_key(lambda x, y: semver.compare(x.version, y.version)))[-1] 

    return latest_apk
    

# async def get_latest_version_by_app_id(session: AsyncSession, app_id: int) -> None:

    