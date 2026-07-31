"""OB 实时 SQL 审计 Controller"""

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.logger import logger
from app.core.ob_oracle.dependencies import get_ob_oracle_session

from .service import ObSqlAuditService

ObSqlAuditRouter = APIRouter(tags=["OceanBase 管理", "SQL审计"])


@ObSqlAuditRouter.get(
    "/list",
    summary="分页查询 SQL 审计",
    response_model=ResponseSchema[dict],
)
async def get_list(
    page_no: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    begin_time: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="开始时间 (yyyy-mm-dd hh24:mi:ss)"),
    end_time: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="结束时间 (yyyy-mm-dd hh24:mi:ss)"),
    trace_id: str | None = Query(None, max_length=64, description="Trace ID"),
    sql_id: str | None = Query(None, max_length=64, description="SQL ID"),
    ret_code_min: int | None = Query(None, description="返回码最小值"),
    ret_code_max: int | None = Query(None, description="返回码最大值"),
    memory_min: float | None = Query(None, description="消耗内存MB最小值"),
    memory_max: float | None = Query(None, description="消耗内存MB最大值"),
    order_by: str | None = Query(None, max_length=64, description="排序字段"),
    order_dir: Literal["asc", "desc"] | None = Query(None, description="排序方向"),
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_sql_audit:audit:query"]))] = None,
) -> JSONResponse:
    search: dict[str, Any] = {}
    if begin_time:
        search["begin_time"] = begin_time
    if end_time:
        search["end_time"] = end_time
    if trace_id:
        search["trace_id"] = trace_id
    if sql_id:
        search["sql_id"] = sql_id
    if ret_code_min is not None:
        search["ret_code_min"] = ret_code_min
    if ret_code_max is not None:
        search["ret_code_max"] = ret_code_max
    if memory_min is not None:
        search["memory_min"] = memory_min
    if memory_max is not None:
        search["memory_max"] = memory_max

    service = ObSqlAuditService(ob_db)
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
        logger.error("SQL 审计查询失败: {}", e, exc_info=True)
        return ErrorResponse(msg="SQL 审计查询失败，请检查数据源配置")
