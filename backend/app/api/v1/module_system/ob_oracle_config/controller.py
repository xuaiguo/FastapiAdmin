"""OceanBase Oracle 配置 Controller"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from sqlalchemy.ext.asyncio import AsyncSession

from .schema import (
    ObOracleConfigCreateSchema,
    ObOracleConfigOutSchema,
    ObOracleConfigQueryParam,
    ObOracleConfigUpdateSchema,
)
from .service import ObOracleConfigService

ObOracleConfigRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/ob_oracle_config",
    tags=["系统管理", "OceanBase Oracle配置管理"],
)


@ObOracleConfigRouter.get(
    "/list",
    summary="查询OceanBase Oracle配置",
    response_model=ResponseSchema[PageResultSchema[ObOracleConfigOutSchema]],
)
async def get_obj_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[ObOracleConfigQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    module_name: str | None = Query(None, description="模块名称，传入时按模块过滤数据源"),
) -> JSONResponse:
    service = ObOracleConfigService(auth, db)

    # 按模块过滤：返回该模块+当前用户可见的数据源列表
    if module_name:
        user_id = auth.user.id if auth.user else None
        configs = await service.list_for_module(
            module_name=module_name, user_id=user_id
        )
        # 包装为分页格式以兼容前端
        data = {
            "items": [c.model_dump() for c in configs],
            "total": len(configs),
            "page_no": 1,
            "page_size": len(configs),
        }
        return SuccessResponse(data=data, msg="查询成功")

    result = await service.page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result, msg="查询OceanBase Oracle配置成功")


@ObOracleConfigRouter.get(
    "/detail/{id}",
    summary="获取OceanBase Oracle配置详情",
    response_model=ResponseSchema[ObOracleConfigOutSchema],
)
async def get_obj_detail_controller(
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:detail"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ObOracleConfigService(auth, db)
    result = await service.detail(id=id)
    return SuccessResponse(data=result, msg="获取OceanBase Oracle配置详情成功")


@ObOracleConfigRouter.post(
    "/create",
    summary="创建OceanBase Oracle配置",
    response_model=ResponseSchema[ObOracleConfigOutSchema],
)
async def create_obj_controller(
    data: ObOracleConfigCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ObOracleConfigService(auth, db)
    result = await service.create(data=data)
    return SuccessResponse(data=result, msg="创建OceanBase Oracle配置成功")


@ObOracleConfigRouter.put(
    "/update/{id}",
    summary="修改OceanBase Oracle配置",
    response_model=ResponseSchema[ObOracleConfigOutSchema],
)
async def update_obj_controller(
    data: ObOracleConfigUpdateSchema,
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ObOracleConfigService(auth, db)
    result = await service.update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改OceanBase Oracle配置成功")


@ObOracleConfigRouter.delete(
    "/delete",
    summary="删除OceanBase Oracle配置",
    response_model=ResponseSchema[None],
)
async def delete_obj_controller(
    ids: Annotated[list[int], Body(description="ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ObOracleConfigService(auth, db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除OceanBase Oracle配置成功")


@ObOracleConfigRouter.patch(
    "/status/batch",
    summary="批量修改OceanBase Oracle配置状态",
    response_model=ResponseSchema[None],
)
async def batch_set_available_controller(
    data: BatchSetAvailable,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:patch"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ObOracleConfigService(auth, db)
    await service.set_available(data=data)
    return SuccessResponse(msg="批量修改OceanBase Oracle配置状态成功")


@ObOracleConfigRouter.post(
    "/test/{id}",
    summary="测试OceanBase Oracle连接",
    response_model=ResponseSchema[dict],
)
async def test_connection_controller(
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:test"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ObOracleConfigService(auth, db)
    result = await service.test_connection(id=id)
    if result.get("success"):
        return SuccessResponse(data=result, msg="连接成功")
    return ErrorResponse(data=result, msg=result.get("msg", "连接失败"), status_code=200)


# ===== 用户分配管理 =====

class AllocateUsersRequest(BaseModel):
    """分配用户请求模型"""
    config_id: int
    user_ids: list[int]


@ObOracleConfigRouter.get(
    "/allocated_users/{config_id}",
    summary="查询数据源已分配的用户",
    response_model=ResponseSchema[dict],
)
async def get_allocated_users_controller(
    config_id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    """查询数据源已分配的用户ID列表"""
    service = ObOracleConfigService(auth, db)
    result = await service.get_allocated_users(config_id=config_id)
    return SuccessResponse(data=result, msg="查询成功")


@ObOracleConfigRouter.post(
    "/allocate_users",
    summary="分配用户给数据源",
    response_model=ResponseSchema[dict],
)
async def allocate_users_controller(
    request: AllocateUsersRequest,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_oracle_config:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    """分配用户给数据源（最少选择1个用户）"""
    if len(request.user_ids) < 1:
        return ErrorResponse(msg="最少选择1个用户", status_code=400)

    service = ObOracleConfigService(auth, db)
    await service.allocate_users(
        config_id=request.config_id,
        user_ids=request.user_ids
    )
    return SuccessResponse(msg="分配成功")
