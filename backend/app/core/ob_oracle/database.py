"""
OceanBase Oracle 租户数据库引擎管理器。

懒加载创建同步引擎和会话工厂，按 config_id 缓存。
连接配置从 MySQL 的 sys_ob_oracle_config 表中读取。
使用 cx_oracle 驱动（OceanBase 版），仅支持同步连接。
"""

from __future__ import annotations

import asyncio
import os
from urllib.parse import quote_plus

import cx_Oracle
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.logger import logger

# 初始化 cx_Oracle 客户端库（必须在任何 Oracle 连接之前调用）
_ob_client_lib = os.environ.get("OB_ORACLE_CLIENT_LIB", r"C:\obclient\lib")
try:
    cx_Oracle.init_oracle_client(lib_dir=_ob_client_lib)
    logger.info("✅ cx_Oracle 客户端已初始化: lib_dir={}", _ob_client_lib)
except cx_Oracle.ProgrammingError:
    # 已经初始化过，忽略
    pass


class ObOracleManager:
    """
    OceanBase Oracle 租户数据库引擎管理器（单例）。

    职责:
    - 根据 config_id 懒加载创建同步引擎
    - 缓存引擎和会话工厂，避免重复创建
    - 应用关闭时统一释放所有连接池

    与 Oracle 版 OracleManager 的区别:
    - 使用 create_engine（同步）而非 create_async_engine
    - 使用 sessionmaker 而非 async_sessionmaker
    - URL 格式为 oracle+cx_oracle:// 而非 oracle+oracledb://
    - 不支持 SYSDBA/SYSOPER 认证模式
    """

    _instance: ObOracleManager | None = None

    def __new__(cls) -> ObOracleManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines = {}
            cls._instance._session_factories = {}
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_engines"):
            self._engines: dict[int, Engine] = {}
            self._session_factories: dict[int, sessionmaker[Session]] = {}
            self._lock = asyncio.Lock()

    async def _load_config(self, config_id: int) -> dict:
        """从 MySQL 读取 OceanBase Oracle 连接配置"""
        from app.api.v1.module_system.ob_oracle_config.model import ObOracleConfigModel
        from app.core.database import async_db_session
        from app.core.ob_oracle.crypto import decrypt_password

        async with async_db_session() as session:
            stmt = select(ObOracleConfigModel).where(
                ObOracleConfigModel.id == config_id,
                ObOracleConfigModel.is_deleted == False,  # noqa: E712
                ObOracleConfigModel.status == 0,
            )
            result = await session.execute(stmt)
            config = result.scalars().first()
            if not config:
                raise ValueError(f"OceanBase Oracle 配置不存在或已禁用: config_id={config_id}")
            return {
                "name": config.name,
                "host": config.host,
                "port": config.port,
                "service_name": config.service_name,
                "username": config.username,
                "password": decrypt_password(config.password),
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow,
            }

    def _build_url(self, config: dict) -> str:
        """构建 OceanBase Oracle 同步连接 URL"""
        username = quote_plus(config["username"])
        password = quote_plus(config["password"])
        host = config["host"]
        port = config["port"]
        service_name = config["service_name"]
        return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={service_name}"

    async def get_engine(self, config_id: int) -> Engine:
        """获取 OceanBase Oracle 同步引擎（懒加载 + 缓存）"""
        if config_id in self._engines:
            return self._engines[config_id]

        async with self._lock:
            if config_id in self._engines:
                return self._engines[config_id]

            config = await self._load_config(config_id)
            url = self._build_url(config)

            # create_engine 可能涉及 DNS 解析，放到线程池避免阻塞事件循环
            engine = await asyncio.to_thread(
                create_engine,
                url,
                pool_size=config["pool_size"],
                max_overflow=config["max_overflow"],
                pool_pre_ping=True,
                pool_recycle=1800,
            )

            self._engines[config_id] = engine
            logger.info("✅ OB Oracle 引擎已创建: {} ({})", config["name"], config_id)
            return engine

    async def get_session_factory(self, config_id: int) -> sessionmaker[Session]:
        """获取 OceanBase Oracle 同步会话工厂（懒加载 + 缓存）"""
        if config_id in self._session_factories:
            return self._session_factories[config_id]

        engine = await self.get_engine(config_id)
        factory = sessionmaker[Session](
            bind=engine,
            class_=Session,
            expire_on_commit=False,
        )
        self._session_factories[config_id] = factory
        return factory

    async def dispose_all(self) -> None:
        """释放所有 OB Oracle 连接池（应用关闭时调用）"""
        for config_id, engine in self._engines.items():
            await asyncio.to_thread(engine.dispose)
            logger.info("✅ OB Oracle 引擎已释放: config_id={}", config_id)
        self._engines.clear()
        self._session_factories.clear()

    async def invalidate_engine(self, config_id: int) -> None:
        """释放并移除指定 config_id 的缓存引擎（密码或配置变更后调用）"""
        async with self._lock:
            if config_id in self._engines:
                await asyncio.to_thread(self._engines[config_id].dispose)
                del self._engines[config_id]
                self._session_factories.pop(config_id, None)
                logger.info("🔄 OB Oracle 引擎缓存已失效: config_id={}", config_id)


# 全局单例
ob_oracle_manager = ObOracleManager()
