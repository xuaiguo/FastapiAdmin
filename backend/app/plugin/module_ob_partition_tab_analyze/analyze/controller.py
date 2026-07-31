"""OB 分区表分析 Controller"""

import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.logger import logger
from app.core.ob_oracle.dependencies import get_ob_oracle_session

from .service import ObPartitionTabAnalyzeService

ObPartitionTabAnalyzeRouter = APIRouter(tags=["OceanBase 管理", "分区表分析"])


@ObPartitionTabAnalyzeRouter.get(
    "/list",
    summary="分页查询分区表分析",
    response_model=ResponseSchema[dict],
)
async def get_list(
    page_no: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    table_owner: str | None = Query(None, max_length=128, description="表所有者"),
    table_name: str | None = Query(None, max_length=128, description="表名"),
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_partition_tab_analyze:analyze:query"]))] = None,
) -> JSONResponse:
    search: dict[str, Any] = {}
    if table_owner:
        search["table_owner"] = table_owner
    if table_name:
        search["table_name"] = table_name

    service = ObPartitionTabAnalyzeService(ob_db)
    try:
        result = await asyncio.to_thread(
            service.page,
            page_no=page_no,
            page_size=page_size,
            search=search or None,
        )
        return SuccessResponse(data=result, msg="查询成功")
    except Exception as e:
        logger.error("分区表分析查询失败: {}", e, exc_info=True)
        return ErrorResponse(msg="分区表分析查询失败，请检查数据源配置")
