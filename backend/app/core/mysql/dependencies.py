"""
MySQL 多数据源数据库依赖注入。

提供 mysql_db_getter(config_id) 函数，用于在 FastAPI 路由中注入 MySQL 数据库会话。
与现有 dependencies.py 中的 db_getter() 模式一致。
"""

from collections.abc import AsyncGenerator
from typing import Callable

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mysql.database import mysql_manager


def mysql_db_getter(config_id: int) -> Callable:
    """
    创建 MySQL 数据库会话依赖函数（硬编码 config_id）。

    用法:
        @router.get("/list")
        async def list_data(
            mysql_db: AsyncSession = Depends(mysql_db_getter(1)),
        ):
            result = await mysql_db.execute(select(...))
    """

    async def _mysql_session_dependency() -> AsyncGenerator[AsyncSession, None]:
        factory = await mysql_manager.get_session_factory(config_id)
        async with factory() as session:
            async with session.begin():
                yield session

    return _mysql_session_dependency


async def get_mysql_session(
    config_id: int = Query(1, description="MySQL 数据源 ID"),
) -> AsyncGenerator[AsyncSession, None]:
    """
    从请求 query 参数动态读取 config_id 的 MySQL 会话依赖。

    用法:
        @router.get("/list")
        async def list_data(
            mysql_db: AsyncSession = Depends(get_mysql_session),
        ):
            # config_id 从 URL ?config_id=2 自动获取
    """
    factory = await mysql_manager.get_session_factory(config_id)
    async with factory() as session:
        async with session.begin():
            yield session
