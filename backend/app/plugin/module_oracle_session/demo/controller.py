"""
Oracle 会话查询 Controller。

仅查询功能，无增删改。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.oracle.dependencies import get_oracle_session

from .schema import OracleSessionOutSchema, OracleSessionQueryParam
from .service import OracleSessionService

OracleSessionRouter = APIRouter(prefix="/oracle_session", tags=["Oracle 会话查询"])


@OracleSessionRouter.get(
    "/list",
    summary="分页查询 Oracle 会话",
)
async def get_list(
    page_no: int = 1,
    page_size: int = 20,
    service_name: str | None = None,
    schemaname: str | None = None,
    module: str | None = None,
    program: str | None = None,
    status: str | None = None,
    logon_time_start: str | None = None,
    logon_time_end: str | None = None,
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_session:session:query"]))] = None,
) -> JSONResponse:
    search = OracleSessionQueryParam(
        service_name=service_name,
        schemaname=schemaname,
        module=module,
        program=program,
        status=status,
        logon_time_start=logon_time_start,
        logon_time_end=logon_time_end,
    )
    service = OracleSessionService(oracle_db)
    result = await service.page(page_no=page_no, page_size=page_size, search=search)
    return SuccessResponse(data=result, msg="查询成功")


@OracleSessionRouter.get(
    "/detail/{sid}",
    summary="获取 Oracle 会话详情",
    response_model=ResponseSchema[OracleSessionOutSchema],
)
async def get_detail(
    sid: Annotated[int, Path(description="会话SID")],
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_session:session:detail"]))] = None,
) -> JSONResponse:
    service = OracleSessionService(oracle_db)
    result = await service.detail(sid=sid)
    if not result:
        return SuccessResponse(data=None, msg="会话不存在")
    return SuccessResponse(data=result, msg="获取成功")
