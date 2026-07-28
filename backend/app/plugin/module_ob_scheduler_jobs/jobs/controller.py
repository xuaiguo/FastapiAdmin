"""OB JOBS 查询 Controller"""

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.logger import logger
from app.core.ob_oracle.dependencies import get_ob_oracle_session

from .service import ObSchedulerJobsService

ObSchedulerJobsRouter = APIRouter(tags=["OceanBase 管理", "JOBS查询"])


@ObSchedulerJobsRouter.get(
    "/list",
    summary="分页查询调度任务",
    response_model=ResponseSchema[dict],
)
async def get_list(
    page_no: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    owner: str | None = Query(None, max_length=128, description="所有者"),
    job_name: str | None = Query(None, max_length=128, description="任务名称"),
    job_action: str | None = Query(None, max_length=256, description="任务动作"),
    order_by: str | None = Query(None, max_length=64, description="排序字段"),
    order_dir: Literal["asc", "desc"] | None = Query(None, description="排序方向"),
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_scheduler_jobs:jobs:query"]))] = None,
) -> JSONResponse:
    search: dict[str, Any] = {}
    if owner:
        search["owner"] = owner
    if job_name:
        search["job_name"] = job_name
    if job_action:
        search["job_action"] = job_action

    service = ObSchedulerJobsService(ob_db)
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
        logger.error("JOBS 查询失败: {}", e, exc_info=True)
        return ErrorResponse(msg="JOBS 查询失败，请检查数据源配置")
