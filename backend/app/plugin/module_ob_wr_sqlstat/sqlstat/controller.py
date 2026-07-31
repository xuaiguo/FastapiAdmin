"""OB SQL 性能统计 Controller"""

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.logger import logger
from app.core.ob_oracle.dependencies import get_ob_oracle_session

from .service import ObWrSqlstatService

ObWrSqlstatRouter = APIRouter(tags=["OceanBase 管理", "SQL 性能统计"])


@ObWrSqlstatRouter.get(
    "/list",
    summary="分页查询 SQL 性能统计",
    response_model=ResponseSchema[dict],
)
async def get_list(
    page_no: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    begin_time: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="开始时间 (yyyy-mm-dd hh24:mi:ss)"),
    end_time: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="结束时间 (yyyy-mm-dd hh24:mi:ss)"),
    parsing_db_name: str | None = Query(None, max_length=128, description="数据库名"),
    sql_id: str | None = Query(None, max_length=64, description="SQL ID"),
    order_by: str | None = Query(None, max_length=64, description="排序字段"),
    order_dir: Literal["asc", "desc"] | None = Query(None, description="排序方向: asc / desc"),
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_wr_sqlstat:sqlstat:query"]))] = None,
) -> JSONResponse:
    search: dict[str, Any] = {}
    if begin_time:
        search["begin_time"] = begin_time
    if end_time:
        search["end_time"] = end_time
    if parsing_db_name:
        search["parsing_db_name"] = parsing_db_name
    if sql_id:
        search["sql_id"] = sql_id

    service = ObWrSqlstatService(ob_db)
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
        logger.error("SQL 性能统计查询失败: {}", e, exc_info=True)
        return ErrorResponse(msg="SQL 性能统计查询失败，请检查数据源配置")
