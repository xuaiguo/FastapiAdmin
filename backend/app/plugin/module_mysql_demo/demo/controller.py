"""
MySQL 多数据源示例 Controller。

演示如何在 controller 中同时使用:
- MySQL 多数据源会话（get_mysql_session）
- MySQL 认证权限（AuthPermission）

所有操作均为 async，无需 asyncio.to_thread（MySQL aiomysql 原生支持异步）。
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.mysql.dependencies import get_mysql_session

from .model import MysqlDemoModel
from .schema import MysqlDemoCreateSchema, MysqlDemoOutSchema, MysqlDemoUpdateSchema
from .service import MysqlDemoService

MysqlDemoRouter = APIRouter(prefix="/mysql_demo", tags=["MySQL 示例"])


@MysqlDemoRouter.post("/init_tables", summary="初始化 MySQL 示例表")
async def init_tables(
    config_id: int = 1,
    auth: Annotated[dict, Depends(AuthPermission(["module_mysql_demo:demo:create"]))] = None,
) -> JSONResponse:
    """在外部 MySQL 数据库中创建 mysql_demo 表（如不存在）"""
    from app.core.mysql.database import mysql_manager

    engine = await mysql_manager.get_engine(config_id)
    async with engine.begin() as conn:
        await conn.run_sync(MysqlDemoModel.__table__.create, checkfirst=True)
    return SuccessResponse(msg="MySQL 示例表初始化完成")


@MysqlDemoRouter.get(
    "/detail/{id}",
    summary="获取 MySQL 示例详情",
    response_model=ResponseSchema[MysqlDemoOutSchema],
)
async def get_detail(
    id: Annotated[int, Path(description="示例ID")],
    mysql_db: Annotated[AsyncSession, Depends(get_mysql_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_mysql_demo:demo:detail"]))],
) -> JSONResponse:
    service = MysqlDemoService(mysql_db)
    result = await service.detail(id=id)
    return SuccessResponse(data=result, msg="获取成功")


@MysqlDemoRouter.get("/list", summary="分页查询 MySQL 示例")
async def get_list(
    page_no: int = 1,
    page_size: int = 20,
    name: str | None = None,
    status: int | None = None,
    mysql_db: Annotated[AsyncSession, Depends(get_mysql_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_mysql_demo:demo:query"]))] = None,
) -> JSONResponse:
    search = {}
    if name:
        search["name"] = ("like", name)
    if status is not None:
        search["status"] = ("eq", status)

    service = MysqlDemoService(mysql_db)
    result = await service.page(page_no=page_no, page_size=page_size, search=search or None)
    return SuccessResponse(data=result, msg="查询成功")


@MysqlDemoRouter.post(
    "/create",
    summary="创建 MySQL 示例",
    response_model=ResponseSchema[MysqlDemoOutSchema],
)
async def create_obj(
    data: MysqlDemoCreateSchema,
    mysql_db: Annotated[AsyncSession, Depends(get_mysql_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_mysql_demo:demo:create"]))],
) -> JSONResponse:
    service = MysqlDemoService(mysql_db)
    result = await service.create(data=data)
    return SuccessResponse(data=result, msg="创建成功")


@MysqlDemoRouter.put(
    "/update/{id}",
    summary="修改 MySQL 示例",
    response_model=ResponseSchema[MysqlDemoOutSchema],
)
async def update_obj(
    data: MysqlDemoUpdateSchema,
    id: Annotated[int, Path(description="示例ID")],
    mysql_db: Annotated[AsyncSession, Depends(get_mysql_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_mysql_demo:demo:update"]))],
) -> JSONResponse:
    service = MysqlDemoService(mysql_db)
    result = await service.update(id=id, data=data)
    return SuccessResponse(data=result, msg="修改成功")


@MysqlDemoRouter.delete("/delete", summary="删除 MySQL 示例")
async def delete_obj(
    ids: Annotated[list[int], Body(description="ID列表")],
    mysql_db: Annotated[AsyncSession, Depends(get_mysql_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_mysql_demo:demo:delete"]))],
) -> JSONResponse:
    service = MysqlDemoService(mysql_db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除成功")
