import os
from typing import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy import GUID
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker, relationship, validates
from sqlalchemy.schema import Column
from sqlalchemy.types import String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from dotenv import load_dotenv
from schemas import UserDB
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

Base: DeclarativeMeta = declarative_base()

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Apk(Base):
    __tablename__ = 'apk'
    
    id = Column(Integer, primary_key=True, index=True)
    app = relationship('App')
    app_id = Column(Integer, ForeignKey('app.id'))
    is_stable = Column(Boolean)
    version = Column(String(20))
    uploaded_at = Column(DateTime, server_default=func.now())

class AppUser(Base):
    __tablename__ = 'appuser'

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey('app.id'))
    user_id = Column(GUID, ForeignKey('user.id'))

class App(Base):
    __tablename__ = 'app'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    display_name = Column(String(50))
    repo_url = Column(String(100))
    # users = relationship('UserTable', secondary=AppUser.__table__, backref='app')

class UserTable(Base, SQLAlchemyBaseUserTable):
    # applications = relationship('App', secondary=AppUser.__table__, backref='user')
    ...

class DownloadHistory(Base):
    __tablename__ = 'download_history'

    id = Column(Integer, primary_key=True, index=True)
    imei = Column(String(16))
    app_id = Column(Integer, ForeignKey('app.id'))
    version = Column(String(20))
    downloaded_at = Column(DateTime, server_default=func.now())

    @validates('imei')
    def validate_imei(self, key, imei):
        if len(imei) < 15:
            raise ValueError('invalid imei')
        return imei

    


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(UserDB, session, UserTable)

