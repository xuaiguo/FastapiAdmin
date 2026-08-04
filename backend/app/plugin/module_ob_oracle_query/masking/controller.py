"""敏感字段脱敏 — 管理 Controller"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter

from .crud import DataMaskingColumnCRUD, DataMaskingRuleCRUD
from .schema import (
    DataMaskingColumnCreateSchema,
    DataMaskingColumnOutSchema,
    DataMaskingColumnQueryParam,
    DataMaskingColumnUpdateSchema,
    DataMaskingRuleCreateSchema,
    DataMaskingRuleOutSchema,
    DataMaskingRuleUpdateSchema,
)

DataMaskingRouter = APIRouter(prefix="/masking", tags=["OB Oracle 查询", "脱敏管理"])


# ===== 脱敏规则 CRUD =====


@DataMaskingRouter.get(
    "/rules",
    summary="查询脱敏规则列表",
    response_model=ResponseSchema[dict],
)
async def list_rules(
    page: Annotated[PaginationQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingRuleCRUD(auth, db)
    result = await crud.page(
        offset=(page.page_no - 1) * page.page_size,
        limit=page.page_size,
        order_by=[{"rule_type": "asc"}],
    )
    return SuccessResponse(data=result, msg="查询成功")


@DataMaskingRouter.post(
    "/rules",
    summary="创建脱敏规则",
    response_model=ResponseSchema[DataMaskingRuleOutSchema],
)
async def create_rule(
    data: DataMaskingRuleCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingRuleCRUD(auth, db)
    result = await crud.create(data=data.model_dump())
    return SuccessResponse(data=result, msg="创建成功")


@DataMaskingRouter.put(
    "/rules/{id}",
    summary="修改脱敏规则",
    response_model=ResponseSchema[DataMaskingRuleOutSchema],
)
async def update_rule(
    data: DataMaskingRuleUpdateSchema,
    id: Annotated[int, Path(description="规则ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingRuleCRUD(auth, db)
    result = await crud.update(id=id, data=data.model_dump(exclude_unset=True))
    return SuccessResponse(data=result, msg="修改成功")


@DataMaskingRouter.delete(
    "/rules",
    summary="删除脱敏规则",
    response_model=ResponseSchema[None],
)
async def delete_rules(
    ids: Annotated[list[int], Body(description="规则ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingRuleCRUD(auth, db)
    await crud.delete(ids=ids)
    return SuccessResponse(msg="删除成功")


# ===== 脱敏字段配置 CRUD =====


@DataMaskingRouter.get(
    "/columns",
    summary="查询脱敏字段配置列表",
    response_model=ResponseSchema[dict],
)
async def list_columns(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[DataMaskingColumnQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingColumnCRUD(auth, db)
    search_dict = {}
    if search.config_id is not None:
        search_dict["config_id"] = search.config_id
    if search.active is not None:
        search_dict["active"] = search.active
    result = await crud.page(
        offset=(page.page_no - 1) * page.page_size,
        limit=page.page_size,
        search=search_dict or None,
        order_by=[{"id": "desc"}],
    )
    return SuccessResponse(data=result, msg="查询成功")


@DataMaskingRouter.post(
    "/columns",
    summary="添加脱敏字段配置",
    response_model=ResponseSchema[DataMaskingColumnOutSchema],
)
async def create_column(
    data: DataMaskingColumnCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingColumnCRUD(auth, db)
    result = await crud.create(data=data.model_dump())
    return SuccessResponse(data=result, msg="添加成功")


@DataMaskingRouter.put(
    "/columns/{id}",
    summary="修改脱敏字段配置",
    response_model=ResponseSchema[DataMaskingColumnOutSchema],
)
async def update_column(
    data: DataMaskingColumnUpdateSchema,
    id: Annotated[int, Path(description="配置ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingColumnCRUD(auth, db)
    result = await crud.update(id=id, data=data.model_dump(exclude_unset=True))
    return SuccessResponse(data=result, msg="修改成功")


@DataMaskingRouter.delete(
    "/columns",
    summary="删除脱敏字段配置",
    response_model=ResponseSchema[None],
)
async def delete_columns(
    ids: Annotated[list[int], Body(description="配置ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["ob_oracle_query:masking:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    crud = DataMaskingColumnCRUD(auth, db)
    await crud.delete(ids=ids)
    return SuccessResponse(msg="删除成功")
