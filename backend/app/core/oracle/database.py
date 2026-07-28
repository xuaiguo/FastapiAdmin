"""
Oracle 数据库引擎管理器。

懒加载创建 Oracle 异步引擎和会话工厂，按 config_id 缓存。
连接配置从 MySQL 的 sys_oracle_config 表中读取。
"""

from __future__ import annotations

import asyncio
from urllib.parse import quote_plus

import oracledb
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.logger import logger


class OracleManager:
    """
    Oracle 数据库引擎管理器（单例）。

    职责:
    - 根据 config_id 懒加载创建 Oracle 异步引擎
    - 缓存引擎和会话工厂，避免重复创建
    - 应用关闭时统一释放所有连接池
    """

    _instance: OracleManager | None = None

    def __new__(cls) -> OracleManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines = {}
            cls._instance._session_factories = {}
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_engines"):
            self._engines: dict[int, AsyncEngine] = {}
            self._session_factories: dict[int, async_sessionmaker[AsyncSession]] = {}
            self._lock = asyncio.Lock()

    async def _load_config(self, config_id: int) -> dict:
        """从 MySQL 读取 Oracle 连接配置"""
        from app.api.v1.module_system.oracle_config.model import OracleConfigModel
        from app.core.database import async_db_session
        from app.core.oracle.crypto import decrypt_password

        async with async_db_session() as session:
            stmt = select(OracleConfigModel).where(
                OracleConfigModel.id == config_id,
                OracleConfigModel.is_deleted == False,  # noqa: E712
                OracleConfigModel.status == 0,
            )
            result = await session.execute(stmt)
            config = result.scalars().first()
            if not config:
                raise ValueError(f"Oracle 配置不存在或已禁用: config_id={config_id}")
            return {
                "name": config.name,
                "host": config.host,
                "port": config.port,
                "service_name": config.service_name,
                "db_type": config.db_type,
                "username": config.username,
                "password": decrypt_password(config.password),
                "auth_mode": config.auth_mode,
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow,
            }

    def _build_url(self, config: dict) -> str:
        """构建 Oracle 异步连接 URL"""
        username = quote_plus(config["username"])
        password = quote_plus(config["password"])
        host = config["host"]
        port = config["port"]
        service_name = config["service_name"]
        return f"oracle+oracledb://{username}:{password}@{host}:{port}/?service_name={service_name}"

    async def get_engine(self, config_id: int) -> AsyncEngine:
        """获取 Oracle 异步引擎（懒加载 + 缓存）"""
        if config_id in self._engines:
            return self._engines[config_id]

        async with self._lock:
            if config_id in self._engines:
                return self._engines[config_id]

            config = await self._load_config(config_id)
            url = self._build_url(config)

            # 根据连接身份构建 connect_args（SYSDBA/SYSOPER 特权模式）
            connect_args = {}
            if config["auth_mode"] == "SYSDBA":
                connect_args["mode"] = oracledb.AUTH_MODE_SYSDBA
            elif config["auth_mode"] == "SYSOPER":
                connect_args["mode"] = oracledb.AUTH_MODE_SYSOPER

            engine = create_async_engine(
                url,
                pool_size=config["pool_size"],
                max_overflow=config["max_overflow"],
                pool_pre_ping=True,
                pool_recycle=1800,
                connect_args=connect_args,
            )

            self._engines[config_id] = engine
            logger.info("✅ Oracle 引擎已创建: {} ({})", config["name"], config_id)
            return engine

    async def get_session_factory(self, config_id: int) -> async_sessionmaker[AsyncSession]:
        """获取 Oracle 异步会话工厂（懒加载 + 缓存）"""
        if config_id in self._session_factories:
            return self._session_factories[config_id]

        engine = await self.get_engine(config_id)
        factory = async_sessionmaker[AsyncSession](
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._session_factories[config_id] = factory
        return factory

    async def dispose_all(self) -> None:
        """释放所有 Oracle 连接池（应用关闭时调用）"""
        for config_id, engine in self._engines.items():
            await engine.dispose()
            logger.info("✅ Oracle 引擎已释放: config_id={}", config_id)
        self._engines.clear()
        self._session_factories.clear()

    async def invalidate_engine(self, config_id: int) -> None:
        """释放并移除指定 config_id 的缓存引擎（密码或配置变更后调用）"""
        async with self._lock:
            if config_id in self._engines:
                await self._engines[config_id].dispose()
                del self._engines[config_id]
                self._session_factories.pop(config_id, None)
                logger.info("🔄 Oracle 引擎缓存已失效: config_id={}", config_id)


# 全局单例
oracle_manager = OracleManager()
