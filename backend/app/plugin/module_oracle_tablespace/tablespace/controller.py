"""Oracle 表空间查询 Controller"""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.oracle.dependencies import get_oracle_session

from .service import OracleTablespaceService

OracleTablespaceRouter = APIRouter(
    tags=["数据库管理", "Oracle表空间查询"],
)


@OracleTablespaceRouter.get(
    "/list",
    summary="查询Oracle表空间",
    response_model=ResponseSchema[dict],
)
async def get_list(
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_tablespace:tablespace:query"]))] = None,
    page_no: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tablespace_type: Literal["USER", "TEMP"] | None = Query(None, description="类型: USER / TEMP"),
    tablespace_name: str | None = Query(None, description="表空间名称（模糊匹配）"),
    pct_used_min: float | None = Query(None, description="使用率最小值"),
    pct_used_max: float | None = Query(None, description="使用率最大值"),
    used_mb_min: float | None = Query(None, description="已用MB最小值"),
    used_mb_max: float | None = Query(None, description="已用MB最大值"),
    order_by: str | None = Query(None, description="排序字段"),
    order_dir: str | None = Query(None, description="排序方向: asc / desc"),
) -> JSONResponse:
    search: dict[str, Any] = {}
    if tablespace_type:
        search["tablespace_type"] = tablespace_type
    if tablespace_name:
        search["tablespace_name"] = tablespace_name
    if pct_used_min is not None:
        search["pct_used_min"] = pct_used_min
    if pct_used_max is not None:
        search["pct_used_max"] = pct_used_max
    if used_mb_min is not None:
        search["used_mb_min"] = used_mb_min
    if used_mb_max is not None:
        search["used_mb_max"] = used_mb_max

    try:
        service = OracleTablespaceService(oracle_db)
        result = await service.page(
            page_no=page_no, page_size=page_size, search=search,
            order_by=order_by, order_dir=order_dir,
        )
        return SuccessResponse(data=result)
    except Exception as e:
        return ErrorResponse(msg=f"Oracle 表空间查询失败: {e}")
