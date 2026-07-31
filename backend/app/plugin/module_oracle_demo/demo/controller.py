"""
Oracle 示例 Controller。

演示如何在 controller 中同时使用:
- Oracle 数据库会话（oracle_db_getter）
- MySQL 认证权限（AuthPermission）
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.oracle.dependencies import get_oracle_session

from .model import OracleDemoModel
from .schema import OracleDemoCreateSchema, OracleDemoOutSchema, OracleDemoUpdateSchema
from .service import OracleDemoService

OracleDemoRouter = APIRouter(prefix="/oracle_demo", tags=["Oracle 示例"])


@OracleDemoRouter.post("/init_tables", summary="初始化 Oracle 示例表")
async def init_tables(
    config_id: int = 1,
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_demo:demo:create"]))] = None,
) -> JSONResponse:
    """在 Oracle 数据库中创建 oracle_demo 表（如不存在）"""
    from app.core.oracle.database import oracle_manager

    engine = await oracle_manager.get_engine(config_id)
    async with engine.begin() as conn:
        await conn.run_sync(OracleDemoModel.__table__.create, checkfirst=True)
    return SuccessResponse(msg="Oracle 示例表初始化完成")


@OracleDemoRouter.get(
    "/detail/{id}",
    summary="获取 Oracle 示例详情",
    response_model=ResponseSchema[OracleDemoOutSchema],
)
async def get_detail(
    id: Annotated[int, Path(description="示例ID")],
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_demo:demo:detail"]))],
) -> JSONResponse:
    service = OracleDemoService(oracle_db)
    result = await service.detail(id=id)
    return SuccessResponse(data=result, msg="获取成功")


@OracleDemoRouter.get("/list", summary="分页查询 Oracle 示例")
async def get_list(
    page_no: int = 1,
    page_size: int = 20,
    name: str | None = None,
    status: int | None = None,
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_demo:demo:query"]))] = None,
) -> JSONResponse:
    # 构建搜索条件（转为 OracleCRUDBase 需要的元组格式）
    search = {}
    if name:
        search["name"] = ("like", name)
    if status is not None:
        search["status"] = ("eq", status)

    service = OracleDemoService(oracle_db)
    result = await service.page(page_no=page_no, page_size=page_size, search=search or None)
    return SuccessResponse(data=result, msg="查询成功")


@OracleDemoRouter.post(
    "/create",
    summary="创建 Oracle 示例",
    response_model=ResponseSchema[OracleDemoOutSchema],
)
async def create_obj(
    data: OracleDemoCreateSchema,
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_demo:demo:create"]))],
) -> JSONResponse:
    service = OracleDemoService(oracle_db)
    result = await service.create(data=data)
    return SuccessResponse(data=result, msg="创建成功")


@OracleDemoRouter.put(
    "/update/{id}",
    summary="修改 Oracle 示例",
    response_model=ResponseSchema[OracleDemoOutSchema],
)
async def update_obj(
    data: OracleDemoUpdateSchema,
    id: Annotated[int, Path(description="示例ID")],
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_demo:demo:update"]))],
) -> JSONResponse:
    service = OracleDemoService(oracle_db)
    result = await service.update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改成功")


@OracleDemoRouter.delete("/delete", summary="删除 Oracle 示例")
async def delete_obj(
    ids: list[int],
    oracle_db: Annotated[AsyncSession, Depends(get_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_oracle_demo:demo:delete"]))],
) -> JSONResponse:
    service = OracleDemoService(oracle_db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除成功")
