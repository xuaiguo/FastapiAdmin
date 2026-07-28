"""
Oracle 数据库依赖注入。

提供 oracle_db_getter(config_id) 函数，用于在 FastAPI 路由中注入 Oracle 数据库会话。
与现有 dependencies.py 中的 db_getter() 模式一致。
"""

from collections.abc import AsyncGenerator
from typing import Callable

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.oracle.database import oracle_manager


def oracle_db_getter(config_id: int) -> Callable:
    """
    创建 Oracle 数据库会话依赖函数（硬编码 config_id）。

    用法:
        @router.get("/list")
        async def list_data(
            oracle_db: AsyncSession = Depends(oracle_db_getter(1)),
        ):
            result = await oracle_db.execute(select(...))
    """

    async def _oracle_session_dependency() -> AsyncGenerator[AsyncSession, None]:
        factory = await oracle_manager.get_session_factory(config_id)
        async with factory() as session:
            async with session.begin():
                yield session

    return _oracle_session_dependency


async def get_oracle_session(
    config_id: int = Query(1, description="Oracle 数据源 ID"),
) -> AsyncGenerator[AsyncSession, None]:
    """
    从请求 query 参数动态读取 config_id 的 Oracle 会话依赖。

    用法:
        @router.get("/list")
        async def list_data(
            oracle_db: AsyncSession = Depends(get_oracle_session),
        ):
            # config_id 从 URL ?config_id=2 自动获取
    """
    factory = await oracle_manager.get_session_factory(config_id)
    async with factory() as session:
        async with session.begin():
            yield session
