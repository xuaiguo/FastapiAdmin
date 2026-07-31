"""Oracle 配置 Controller"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute

from .schema import (
    OracleConfigCreateSchema,
    OracleConfigOutSchema,
    OracleConfigQueryParam,
    OracleConfigUpdateSchema,
)
from .service import OracleConfigService

OracleConfigRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/oracle_config",
    tags=["系统管理", "Oracle配置管理"],
)


@OracleConfigRouter.get(
    "/list",
    summary="查询Oracle配置",
    response_model=ResponseSchema[PageResultSchema[OracleConfigOutSchema]],
)
async def get_obj_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[OracleConfigQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:oracle_config:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = OracleConfigService(auth, db)
    result = await service.page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询Oracle配置成功")


@OracleConfigRouter.get(
    "/detail/{id}",
    summary="获取Oracle配置详情",
    response_model=ResponseSchema[OracleConfigOutSchema],
)
async def get_obj_detail_controller(
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:oracle_config:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = OracleConfigService(auth, db)
    result = await service.detail(id=id)
    return SuccessResponse(data=result, msg="获取Oracle配置详情成功")


@OracleConfigRouter.post(
    "/create",
    summary="创建Oracle配置",
    response_model=ResponseSchema[OracleConfigOutSchema],
)
async def create_obj_controller(
    data: OracleConfigCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:oracle_config:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = OracleConfigService(auth, db)
    result = await service.create(data=data)
    return SuccessResponse(data=result, msg="创建Oracle配置成功")


@OracleConfigRouter.put(
    "/update/{id}",
    summary="修改Oracle配置",
    response_model=ResponseSchema[OracleConfigOutSchema],
)
async def update_obj_controller(
    data: OracleConfigUpdateSchema,
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:oracle_config:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = OracleConfigService(auth, db)
    result = await service.update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改Oracle配置成功")


@OracleConfigRouter.delete(
    "/delete",
    summary="删除Oracle配置",
    response_model=ResponseSchema[None],
)
async def delete_obj_controller(
    ids: Annotated[list[int], Body(description="ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:oracle_config:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = OracleConfigService(auth, db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除Oracle配置成功")


@OracleConfigRouter.patch(
    "/status/batch",
    summary="批量修改Oracle配置状态",
    response_model=ResponseSchema[None],
)
async def batch_set_available_controller(
    data: BatchSetAvailable,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:oracle_config:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = OracleConfigService(auth, db)
    await service.set_available(data=data)
    return SuccessResponse(msg="批量修改Oracle配置状态成功")


@OracleConfigRouter.post(
    "/test/{id}",
    summary="测试Oracle连接",
    response_model=ResponseSchema[dict],
)
async def test_connection_controller(
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:oracle_config:test"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = OracleConfigService(auth, db)
    result = await service.test_connection(id=id)
    if result.get("success"):
        return SuccessResponse(data=result, msg="连接成功")
    return ErrorResponse(data=result, msg=result.get("msg", "连接失败"), status_code=200)
