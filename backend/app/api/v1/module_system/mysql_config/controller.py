"""MySQL 配置 Controller"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from sqlalchemy.ext.asyncio import AsyncSession

from .schema import (
    MysqlConfigCreateSchema,
    MysqlConfigOutSchema,
    MysqlConfigQueryParam,
    MysqlConfigUpdateSchema,
)
from .service import MysqlConfigService

MysqlConfigRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/mysql_config",
    tags=["系统管理", "MySQL配置管理"],
)


@MysqlConfigRouter.get(
    "/list",
    summary="查询MySQL配置",
    response_model=ResponseSchema[PageResultSchema[MysqlConfigOutSchema]],
)
async def get_obj_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[MysqlConfigQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:mysql_config:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = MysqlConfigService(auth, db)
    result = await service.page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询MySQL配置成功")


@MysqlConfigRouter.get(
    "/detail/{id}",
    summary="获取MySQL配置详情",
    response_model=ResponseSchema[MysqlConfigOutSchema],
)
async def get_obj_detail_controller(
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:mysql_config:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = MysqlConfigService(auth, db)
    result = await service.detail(id=id)
    return SuccessResponse(data=result, msg="获取MySQL配置详情成功")


@MysqlConfigRouter.post(
    "/create",
    summary="创建MySQL配置",
    response_model=ResponseSchema[MysqlConfigOutSchema],
)
async def create_obj_controller(
    data: MysqlConfigCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:mysql_config:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = MysqlConfigService(auth, db)
    result = await service.create(data=data)
    return SuccessResponse(data=result, msg="创建MySQL配置成功")


@MysqlConfigRouter.put(
    "/update/{id}",
    summary="修改MySQL配置",
    response_model=ResponseSchema[MysqlConfigOutSchema],
)
async def update_obj_controller(
    data: MysqlConfigUpdateSchema,
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:mysql_config:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = MysqlConfigService(auth, db)
    result = await service.update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改MySQL配置成功")


@MysqlConfigRouter.delete(
    "/delete",
    summary="删除MySQL配置",
    response_model=ResponseSchema[None],
)
async def delete_obj_controller(
    ids: Annotated[list[int], Body(description="ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:mysql_config:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = MysqlConfigService(auth, db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除MySQL配置成功")


@MysqlConfigRouter.patch(
    "/status/batch",
    summary="批量修改MySQL配置状态",
    response_model=ResponseSchema[None],
)
async def batch_set_available_controller(
    data: BatchSetAvailable,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:mysql_config:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = MysqlConfigService(auth, db)
    await service.set_available(data=data)
    return SuccessResponse(msg="批量修改MySQL配置状态成功")


@MysqlConfigRouter.post(
    "/test/{id}",
    summary="测试MySQL连接",
    response_model=ResponseSchema[dict],
)
async def test_connection_controller(
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:mysql_config:test"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = MysqlConfigService(auth, db)
    result = await service.test_connection(id=id)
    if result.get("success"):
        return SuccessResponse(data=result, msg="连接成功")
    return ErrorResponse(data=result, msg=result.get("msg", "连接失败"), status_code=200)
