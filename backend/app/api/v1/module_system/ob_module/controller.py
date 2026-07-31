"""OB 模块管理 Controller"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from pydantic import BaseModel
from sqlalchemy import delete, select

from app.api.v1.module_system.menu.model import MenuModel
from app.api.v1.module_system.ob_module.models import (
    ObModule,
    ObModuleParentMenu,
    ObOracleConfigModule,
)
from app.api.v1.module_system.ob_oracle_config.model import ObOracleConfigModel
from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema
from app.core.dependencies import AuthPermission, db_getter
from sqlalchemy.ext.asyncio import AsyncSession

router = ObModuleRouter = APIRouter(prefix="/ob_module", tags=["OB 模块管理"])


class ParentMenuConfig(BaseModel):
    """父菜单配置响应模型"""
    menu_id: int
    menu_name: str


class ModuleResponse(BaseModel):
    """模块响应模型"""
    id: int
    module_name: str
    module_label: str
    source_type: int
    status: int
    config_ids: list[int]
    parent_menu_name: str


class AllocateConfigsRequest(BaseModel):
    """分配数据源请求模型"""
    module_name: str
    config_ids: list[int]


class AddModuleRequest(BaseModel):
    """添加模块请求模型"""
    module_name: str
    module_label: str


class UpdateModuleRequest(BaseModel):
    """修改模块请求模型"""
    module_label: str


# ===== 父菜单配置管理 =====

@router.get("/parent_menus", response_model=ResponseSchema[list[ParentMenuConfig]])
async def list_parent_menus(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """查询所有配置的父菜单"""
    result = await db.execute(select(ObModuleParentMenu))
    parent_menus = result.scalars().all()

    data = [
        ParentMenuConfig(menu_id=pm.menu_id, menu_name=pm.menu_name)
        for pm in parent_menus
    ]
    return SuccessResponse(data=data)


@router.post("/parent_menus", response_model=ResponseSchema[None])
async def add_parent_menu(
    menu_id: int,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """添加父菜单配置"""
    # 查询菜单是否存在
    menu = await db.execute(select(MenuModel).where(MenuModel.id == menu_id))
    menu = menu.scalar_one_or_none()
    if not menu:
        return ErrorResponse(msg="菜单不存在")

    # 检查是否已配置
    existing = await db.execute(
        select(ObModuleParentMenu).where(ObModuleParentMenu.menu_id == menu_id)
    )
    if existing.scalar_one_or_none():
        return ErrorResponse(msg="该菜单已配置")

    # 添加配置
    parent_menu = ObModuleParentMenu(menu_id=menu_id, menu_name=menu.title)
    db.add(parent_menu)
    return SuccessResponse(msg="添加成功")


@router.delete("/parent_menus/{menu_id}", response_model=ResponseSchema[None])
async def remove_parent_menu(
    menu_id: int,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """删除父菜单配置"""
    await db.execute(
        delete(ObModuleParentMenu).where(ObModuleParentMenu.menu_id == menu_id)
    )
    return SuccessResponse(msg="删除成功")


# ===== 模块管理 =====

@router.get("/list", response_model=ResponseSchema[list[ModuleResponse]])
async def list_modules(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """查询模块列表（从所有配置的父菜单中提取）"""

    # 查询所有配置的父菜单
    parent_menus_result = await db.execute(select(ObModuleParentMenu))
    parent_menus = parent_menus_result.scalars().all()
    parent_menu_ids = [pm.menu_id for pm in parent_menus]
    parent_menu_map = {pm.menu_id: pm.menu_name for pm in parent_menus}

    modules = []

    if parent_menu_ids:
        menu_query = (
            select(
                MenuModel.route_name,
                MenuModel.title,
                MenuModel.parent_id,
            )
            .where(MenuModel.parent_id.in_(parent_menu_ids))
            .where(MenuModel.route_name.isnot(None))
            .where(
                MenuModel.route_name.like("Ob%")
                | MenuModel.route_name.like("ob_%")
            )
            .where(MenuModel.status == 0)
        )
        menu_result = await db.execute(menu_query)
        menu_rows = menu_result.all()
    else:
        menu_rows = []

    # 查询手动添加的模块
    manual_result = await db.execute(
        select(ObModule).where(ObModule.source_type == 2)
    )
    manual_modules = manual_result.scalars().all()

    # 批量查询所有模块的 config_ids（消除 N+1）
    all_module_names = [row.route_name for row in menu_rows] + [m.module_name for m in manual_modules]
    config_map: dict[str, list[int]] = {}
    if all_module_names:
        config_result = await db.execute(
            select(ObOracleConfigModule.module_name, ObOracleConfigModule.config_id)
            .where(ObOracleConfigModule.module_name.in_(all_module_names))
        )
        for row in config_result.all():
            config_map.setdefault(row.module_name, []).append(row.config_id)

    for row in menu_rows:
        modules.append(ModuleResponse(
            id=0,
            module_name=row.route_name,
            module_label=row.title,
            source_type=1,
            status=0,
            config_ids=config_map.get(row.route_name, []),
            parent_menu_name=parent_menu_map.get(row.parent_id, "未知"),
        ))

    for module in manual_modules:
        modules.append(ModuleResponse(
            id=module.id,
            module_name=module.module_name,
            module_label=module.module_label,
            source_type=module.source_type,
            status=module.status,
            config_ids=config_map.get(module.module_name, []),
            parent_menu_name="手动添加",
        ))

    return SuccessResponse(data=modules)


@router.post("/add", response_model=ResponseSchema[None])
async def add_module(
    request: AddModuleRequest,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:create"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """手动添加模块"""

    # 检查手动添加的模块是否已存在
    existing = await db.execute(
        select(ObModule).where(ObModule.module_name == request.module_name)
    )
    if existing.scalar_one_or_none():
        return ErrorResponse(msg="模块已存在")

    # 检查是否与菜单提取的模块重名
    parent_menus_result = await db.execute(select(ObModuleParentMenu))
    parent_menu_ids = [pm.menu_id for pm in parent_menus_result.scalars().all()]
    if parent_menu_ids:
        menu_existing = await db.execute(
            select(MenuModel.id)
            .where(MenuModel.parent_id.in_(parent_menu_ids))
            .where(MenuModel.route_name == request.module_name)
            .where(MenuModel.status == 0)
        )
        if menu_existing.scalar_one_or_none():
            return ErrorResponse(msg="模块名称与菜单提取的模块重名")

    module = ObModule(
        module_name=request.module_name,
        module_label=request.module_label,
        source_type=2,
        status=0,
    )
    db.add(module)
    return SuccessResponse(msg="添加成功")


@router.post("/allocate_configs", response_model=ResponseSchema[None])
async def allocate_configs(
    request: AllocateConfigsRequest,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """分配数据源给模块"""
    if len(request.config_ids) < 1:
        return ErrorResponse(msg="最少选择1个数据源")

    # 校验 config_ids 是否存在
    valid_result = await db.execute(
        select(ObOracleConfigModel.id).where(ObOracleConfigModel.id.in_(request.config_ids))
    )
    valid_ids = {row[0] for row in valid_result.fetchall()}
    invalid_ids = [cid for cid in request.config_ids if cid not in valid_ids]
    if invalid_ids:
        return ErrorResponse(msg=f"数据源不存在: {invalid_ids}")

    # 删除旧的关联
    await db.execute(
        delete(ObOracleConfigModule).where(
            ObOracleConfigModule.module_name == request.module_name
        )
    )

    # 添加新的关联
    for config_id in request.config_ids:
        db.add(ObOracleConfigModule(
            config_id=config_id,
            module_name=request.module_name,
        ))

    return SuccessResponse(msg="分配成功")


@router.get("/detail/{id}", response_model=ResponseSchema[ModuleResponse])
async def detail_module(
    id: Annotated[int, Path(description="模块ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:query"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """查询手动添加的模块详情"""
    module = await db.execute(
        select(ObModule).where(ObModule.id == id, ObModule.source_type == 2)
    )
    module = module.scalar_one_or_none()
    if not module:
        return ErrorResponse(msg="模块不存在")

    config_result = await db.execute(
        select(ObOracleConfigModule.config_id).where(
            ObOracleConfigModule.module_name == module.module_name
        )
    )
    config_ids = [c[0] for c in config_result.fetchall()]

    return SuccessResponse(data=ModuleResponse(
        id=module.id,
        module_name=module.module_name,
        module_label=module.module_label,
        source_type=module.source_type,
        status=module.status,
        config_ids=config_ids,
        parent_menu_name="手动添加",
    ))


@router.put("/update/{id}", response_model=ResponseSchema[None])
async def update_module(
    data: UpdateModuleRequest,
    id: Annotated[int, Path(description="模块ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:update"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """修改手动添加的模块"""
    module = await db.execute(select(ObModule).where(ObModule.id == id))
    module = module.scalar_one_or_none()
    if not module:
        return ErrorResponse(msg="模块不存在")
    if module.source_type != 2:
        return ErrorResponse(msg="只能修改手动添加的模块")

    module.module_label = data.module_label
    return SuccessResponse(msg="修改成功")


@router.delete("/delete", response_model=ResponseSchema[None])
async def delete_module(
    ids: Annotated[list[int], Body(description="模块ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:ob_module:delete"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
):
    """删除手动添加的模块（同时清除关联的数据源分配）"""
    if not ids:
        return ErrorResponse(msg="请选择要删除的模块")

    # 查询要删除的模块，确保只删手动添加的
    result = await db.execute(select(ObModule).where(ObModule.id.in_(ids)))
    modules_to_delete = result.scalars().all()
    if not modules_to_delete:
        return ErrorResponse(msg="未找到可删除的模块")

    manual_modules = [m for m in modules_to_delete if m.source_type == 2]
    if not manual_modules:
        return ErrorResponse(msg="只能删除手动添加的模块")

    module_names = [m.module_name for m in manual_modules]

    # 清除关联的数据源分配
    await db.execute(
        delete(ObOracleConfigModule).where(
            ObOracleConfigModule.module_name.in_(module_names)
        )
    )

    # 删除模块
    await db.execute(delete(ObModule).where(ObModule.id.in_(ids), ObModule.source_type == 2))

    return SuccessResponse(msg="删除成功")
