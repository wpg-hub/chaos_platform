from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Enum, JSON, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker, Session
from sqlalchemy.sql import func
import enum

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""), echo=settings.DEBUG)
sync_session_maker = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    return sync_session_maker()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.USER.value)
    email = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    cases = relationship("Case", back_populates="creator")
    executions = relationship("Execution", back_populates="executor")
    schedules = relationship("Schedule", back_populates="creator")


class Folder(Base):
    __tablename__ = "folders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    parent = relationship("Folder", remote_side=[id], backref="children")
    cases = relationship("Case", back_populates="folder")


class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    yaml_content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    case_type = Column(String(50), nullable=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True)
    is_template = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    creator = relationship("User", back_populates="cases")
    folder = relationship("Folder", back_populates="cases")
    tags = relationship("Tag", secondary="case_tags", back_populates="cases")
    executions = relationship("Execution", back_populates="case")
    schedules = relationship("Schedule", back_populates="case")


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default="#409EFF")
    created_at = Column(DateTime, default=func.now())
    
    cases = relationship("Case", secondary="case_tags", back_populates="tags")


class CaseTag(Base):
    __tablename__ = "case_tags"
    
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), nullable=False, default=ExecutionStatus.PENDING.value)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    report_path = Column(String(500), nullable=True)
    log_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    case = relationship("Case", back_populates="executions")
    executor = relationship("User", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    
    execution = relationship("Execution", back_populates="logs")


class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    cron_expr = Column(String(100), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    next_run = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)
    last_status = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    case = relationship("Case", back_populates="schedules")
    creator = relationship("User", back_populates="schedules")
