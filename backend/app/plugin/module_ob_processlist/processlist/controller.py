"""OB ProcessList 查询 Controller"""

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.logger import logger
from app.core.ob_oracle.dependencies import get_ob_oracle_session

from .service import ObProcesslistService

ObProcesslistRouter = APIRouter(tags=["OceanBase 管理", "ProcessList"])


@ObProcesslistRouter.get(
    "/list",
    summary="分页查询 ProcessList",
    response_model=ResponseSchema[dict],
)
async def get_list(
    page_no: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: str | None = Query(None, max_length=128, description="用户"),
    db: str | None = Query(None, max_length=128, description="数据库"),
    state: str | None = Query(None, max_length=64, description="状态"),
    info: str | None = Query(None, max_length=256, description="SQL 文本"),
    user_client_ip: str | None = Query(None, max_length=64, description="客户端IP"),
    sql_id: str | None = Query(None, max_length=64, description="SQL ID"),
    trace_id: str | None = Query(None, max_length=64, description="Trace ID"),
    order_by: str | None = Query(None, max_length=64, description="排序字段"),
    order_dir: Literal["asc", "desc"] | None = Query(None, description="排序方向"),
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_processlist:processlist:query"]))] = None,
) -> JSONResponse:
    search: dict[str, Any] = {}
    if user:
        search["user"] = user
    if db:
        search["db"] = db
    if state:
        search["state"] = state
    if info:
        search["info"] = info
    if user_client_ip:
        search["user_client_ip"] = user_client_ip
    if sql_id:
        search["sql_id"] = sql_id
    if trace_id:
        search["trace_id"] = trace_id

    service = ObProcesslistService(ob_db)
    try:
        result = await asyncio.to_thread(
            service.page,
            page_no=page_no,
            page_size=page_size,
            search=search or None,
            order_by=order_by,
            order_dir=order_dir,
        )
        return SuccessResponse(data=result, msg="查询成功")
    except Exception as e:
        logger.error("ProcessList 查询失败: {}", e, exc_info=True)
        return ErrorResponse(msg="ProcessList 查询失败，请检查数据源配置")
