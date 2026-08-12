"""OB 租户表大小统计 Controller"""

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.logger import logger
from app.core.ob_oracle.dependencies import get_ob_oracle_session

from .service import ObTableDataSizeService

ObTableDataSizeRouter = APIRouter(tags=["OceanBase 管理", "租户表大小统计"])


@ObTableDataSizeRouter.get(
    "/list",
    summary="分页查询租户表大小统计",
    response_model=ResponseSchema[dict],
)
async def get_list(
    page_no: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svr_ip: str | None = Query(None, max_length=128, description="节点 IP（模糊查询）"),
    database_name: str | None = Query(None, max_length=128, description="数据库名（模糊查询）"),
    object_name: str | None = Query(None, max_length=128, description="表名（模糊查询）"),
    order_by: str | None = Query(None, max_length=64, description="排序字段"),
    order_dir: Literal["asc", "desc"] | None = Query(None, description="排序方向: asc / desc"),
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_table_data_size:size:query"]))] = None,
) -> JSONResponse:
    search: dict[str, Any] = {}
    if svr_ip:
        search["svr_ip"] = svr_ip
    if database_name:
        search["database_name"] = database_name
    if object_name:
        search["object_name"] = object_name

    service = ObTableDataSizeService(ob_db)
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
        logger.error("租户表大小统计查询失败: {}", e, exc_info=True)
        return ErrorResponse(msg="租户表大小统计查询失败，请检查数据源配置")
