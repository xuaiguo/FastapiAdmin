"""
OceanBase Oracle 租户示例 Controller。

演示如何在 controller 中同时使用:
- OceanBase Oracle 数据库会话（get_ob_oracle_session，同步 Session）
- MySQL 认证权限（AuthPermission）

由于 cx_oracle 驱动仅支持同步，Service 方法为普通 def，
endpoint 保持 async 签名并通过 asyncio.to_thread() 包装同步调用。
"""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.ob_oracle.dependencies import get_ob_oracle_session

from .model import ObOracleDemoModel
from .schema import ObOracleDemoCreateSchema, ObOracleDemoOutSchema, ObOracleDemoUpdateSchema
from .service import ObOracleDemoService

ObOracleDemoRouter = APIRouter(prefix="/ob_oracle_demo", tags=["OceanBase Oracle 示例"])


@ObOracleDemoRouter.post("/init_tables", summary="初始化 OceanBase Oracle 示例表")
async def init_tables(
    config_id: int = 1,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_oracle_demo:demo:create"]))] = None,
) -> JSONResponse:
    """在 OceanBase Oracle 数据库中创建序列和 ob_oracle_demo 表（如不存在）。

    注意：使用显式 SEQUENCE + DEFAULT 代替 GENERATED ALWAYS AS IDENTITY，
    以便 create() 可通过 CURRVAL 取回新插入的 ID（会话级，无并发竞争）。
    """
    from app.core.ob_oracle.database import ob_oracle_manager
    from sqlalchemy import text

    from .model import OB_ORACLE_DEMO_SEQ

    engine = await ob_oracle_manager.get_engine(config_id)

    def _create_tables():
        with engine.begin() as conn:
            # 1. 创建序列
            try:
                conn.execute(text(f"SELECT {OB_ORACLE_DEMO_SEQ.name}.NEXTVAL FROM DUAL"))
            except Exception:
                conn.execute(text(
                    f"CREATE SEQUENCE {OB_ORACLE_DEMO_SEQ.name} "
                    f"START WITH {OB_ORACLE_DEMO_SEQ.start} "
                    f"INCREMENT BY {OB_ORACLE_DEMO_SEQ.increment} NOCACHE"
                ))

            # 2. 创建表（使用显式序列 DEFAULT，而非 GENERATED ALWAYS AS IDENTITY）
            conn.execute(text(f"""
                CREATE TABLE {ObOracleDemoModel.__tablename__} (
                    id          NUMBER DEFAULT {OB_ORACLE_DEMO_SEQ.name}.NEXTVAL PRIMARY KEY,
                    name        VARCHAR2(100) NOT NULL,
                    description VARCHAR2(500),
                    status      NUMBER DEFAULT 0
                )
            """))

    def _table_exists():
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM user_tables WHERE table_name = :tbl"
            ), {"tbl": ObOracleDemoModel.__tablename__.upper()})
            return result.scalar() > 0

    if await asyncio.to_thread(_table_exists):
        return SuccessResponse(msg="ob_oracle_demo 表已存在，跳过初始化")

    await asyncio.to_thread(_create_tables)
    return SuccessResponse(msg="OceanBase Oracle 示例表和序列初始化完成")


@ObOracleDemoRouter.get(
    "/detail/{id}",
    summary="获取 OceanBase Oracle 示例详情",
    response_model=ResponseSchema[ObOracleDemoOutSchema],
)
async def get_detail(
    id: Annotated[int, Path(description="示例ID")],
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_oracle_demo:demo:detail"]))],
) -> JSONResponse:
    service = ObOracleDemoService(ob_db)
    result = await asyncio.to_thread(service.detail, id)
    return SuccessResponse(data=result, msg="获取成功")


@ObOracleDemoRouter.get("/list", summary="分页查询 OceanBase Oracle 示例")
async def get_list(
    page_no: int = 1,
    page_size: int = 20,
    name: str | None = None,
    status: int | None = None,
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)] = None,
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_oracle_demo:demo:query"]))] = None,
) -> JSONResponse:
    # 构建搜索条件（转为 ObOracleCRUDBase 需要的元组格式）
    search = {}
    if name:
        search["name"] = ("like", name)
    if status is not None:
        search["status"] = ("eq", status)

    service = ObOracleDemoService(ob_db)
    result = await asyncio.to_thread(service.page, page_no, page_size, search or None)
    return SuccessResponse(data=result, msg="查询成功")


@ObOracleDemoRouter.post(
    "/create",
    summary="创建 OceanBase Oracle 示例",
    response_model=ResponseSchema[ObOracleDemoOutSchema],
)
async def create_obj(
    data: ObOracleDemoCreateSchema,
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_oracle_demo:demo:create"]))],
) -> JSONResponse:
    service = ObOracleDemoService(ob_db)
    result = await asyncio.to_thread(service.create, data)
    return SuccessResponse(data=result, msg="创建成功")


@ObOracleDemoRouter.put(
    "/update/{id}",
    summary="修改 OceanBase Oracle 示例",
    response_model=ResponseSchema[ObOracleDemoOutSchema],
)
async def update_obj(
    data: ObOracleDemoUpdateSchema,
    id: Annotated[int, Path(description="示例ID")],
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_oracle_demo:demo:update"]))],
) -> JSONResponse:
    service = ObOracleDemoService(ob_db)
    result = await asyncio.to_thread(service.update, id, data)
    return SuccessResponse(data=result, msg="修改成功")


@ObOracleDemoRouter.delete("/delete", summary="删除 OceanBase Oracle 示例")
async def delete_obj(
    ids: Annotated[list[int], Body(description="ID列表")],
    ob_db: Annotated[Session, Depends(get_ob_oracle_session)],
    auth: Annotated[dict, Depends(AuthPermission(["module_ob_oracle_demo:demo:delete"]))],
) -> JSONResponse:
    service = ObOracleDemoService(ob_db)
    await asyncio.to_thread(service.delete, ids)
    return SuccessResponse(msg="删除成功")
