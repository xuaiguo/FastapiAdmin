"""
OceanBase Oracle 租户数据库依赖注入。

提供 ob_oracle_db_getter(config_id) 和 get_ob_oracle_session 函数，
用于在 FastAPI 路由中注入 OceanBase Oracle 数据库会话。

由于 cx_oracle 驱动仅支持同步，会话在后台线程中创建和管理，
endpoint 函数仍保持 async 签名。
"""

import asyncio
from collections.abc import AsyncGenerator, Callable

from fastapi import Query
from sqlalchemy.orm import Session

from app.core.ob_oracle.database import ob_oracle_manager


def ob_oracle_db_getter(config_id: int) -> Callable:
    """
    创建 OceanBase Oracle 数据库会话依赖函数（硬编码 config_id）。

    用法:
        @router.get("/list")
        async def list_data(
            ob_db: Session = Depends(ob_oracle_db_getter(1)),
        ):
            result = ob_db.execute(select(...))
    """

    async def _ob_oracle_session_dependency() -> AsyncGenerator[Session, None]:
        factory = await ob_oracle_manager.get_session_factory(config_id)
        session = await asyncio.to_thread(factory)
        _error_occurred = False
        try:
            yield session
        except Exception:
            _error_occurred = True
            raise
        finally:
            await asyncio.to_thread(_close_session, session, not _error_occurred)

    return _ob_oracle_session_dependency


async def get_ob_oracle_session(
    config_id: int = Query(1, description="OceanBase Oracle 数据源 ID"),
) -> AsyncGenerator[Session, None]:
    """
    从请求 query 参数动态读取 config_id 的 OceanBase Oracle 会话依赖。

    用法:
        @router.get("/list")
        async def list_data(
            ob_db: Session = Depends(get_ob_oracle_session),
        ):
            # config_id 从 URL ?config_id=2 自动获取
    """
    factory = await ob_oracle_manager.get_session_factory(config_id)
    session = await asyncio.to_thread(factory)
    _error_occurred = False
    try:
        yield session
    except Exception:
        _error_occurred = True
        raise
    finally:
        await asyncio.to_thread(_close_session, session, not _error_occurred)


def _close_session(session: Session, commit: bool) -> None:
    """在单个线程中完成 session 的 commit/rollback + close，减少 to_thread 开销"""
    try:
        if commit:
            session.commit()
        else:
            session.rollback()
    finally:
        session.close()
