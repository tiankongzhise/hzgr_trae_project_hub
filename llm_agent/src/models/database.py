"""数据库模型定义"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


class School(Base):
    """学校信息模型"""
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, comment="学校全称"
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="办学地点"
    )
    supervisor: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="主管部门"
    )
    education_level: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="办学层次"
    )
    institution_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="院校代号"
    )
    institution_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="办学类型"
    )
    is_demonstration: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="是否是示范性院校"
    )
    is_backbone: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="是否是骨干院校"
    )
    is_excellent: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="是否是卓越院校"
    )
    is_chuyi_high_level: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="是否是楚怡高水平院校"
    )
    advantage_majors: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="优势专业"
    )
    advantage_basis: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="优势专业判断依据"
    )
    raw_content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="原始招生简章内容"
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="招生简章来源URL"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<School(id={self.id}, full_name='{self.full_name}')>"


# 全局引擎和会话工厂
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """获取数据库引擎"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database.url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            echo=settings.debug,
        )
        logger.info(f"数据库引擎已创建: {settings.database.url}")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取会话工厂"""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("数据库会话工厂已创建")
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话异常: {e}")
            raise
        finally:
            await session.close()


async def create_tables():
    """创建数据库表"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表已创建")


async def drop_tables():
    """删除数据库表"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("数据库表已删除")


async def close_engine():
    """关闭数据库引擎"""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("数据库引擎已关闭")
