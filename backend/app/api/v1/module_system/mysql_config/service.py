"""MySQL 配置 Service"""

import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.base_schema import AuthSchema, BatchSetAvailable
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.mysql.crypto import decrypt_password, encrypt_password
from app.core.mysql.database import mysql_manager

from .crud import MysqlConfigCRUD
from .schema import (
    PASSWORD_MASK,
    MysqlConfigCreateSchema,
    MysqlConfigOutSchema,
    MysqlConfigQueryParam,
    MysqlConfigUpdateSchema,
)


class MysqlConfigService:
    """MySQL 配置管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db
        self.crud = MysqlConfigCRUD(auth, db)

    async def detail(self, id: int) -> MysqlConfigOutSchema:
        obj = await self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="该配置不存在")
        return MysqlConfigOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: MysqlConfigQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[MysqlConfigOutSchema]:
        obj_list = await self.crud.get_list(
            search=vars(search) if search else None, order_by=order_by
        )
        return [MysqlConfigOutSchema.model_validate(obj) for obj in obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: MysqlConfigQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        offset = (page_no - 1) * page_size
        return await self.crud.page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=vars(search) if search else None,
            out_schema=MysqlConfigOutSchema,
        )

    async def create(self, data: MysqlConfigCreateSchema) -> MysqlConfigOutSchema:
        obj = await self.crud.get(name=data.name)
        if obj:
            raise CustomException(msg="创建失败，实例名称已存在")
        # 加密密码后存储
        data_dict = data.model_dump()
        data_dict["password"] = encrypt_password(data_dict["password"])
        obj = await self.crud.create(data=data_dict)
        return MysqlConfigOutSchema.model_validate(obj)

    async def update(self, id: int, data: MysqlConfigUpdateSchema) -> MysqlConfigOutSchema:
        obj = await self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="更新失败，该配置不存在")
        exist_obj = await self.crud.get(name=data.name)
        if exist_obj and exist_obj.id != id:
            raise CustomException(msg="更新失败，实例名称重复")
        # 加密密码后存储（跳过脱敏密码 ****，保留原密码不变）
        data_dict = data.model_dump()
        if data_dict.get("password") == PASSWORD_MASK:
            logger.info("🔒 跳过密码更新: id={} (前端提交的是脱敏占位符)", id)
            data_dict.pop("password")
        else:
            logger.info("🔑 更新密码: id={}", id)
            data_dict["password"] = encrypt_password(data_dict["password"])
        obj = await self.crud.update(id=id, data=data_dict)
        # 配置变更后失效引擎缓存，下次使用时用新配置重建
        await mysql_manager.invalidate_engine(id)
        return MysqlConfigOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")
        await self.crud.delete(ids=ids)
        for config_id in ids:
            await mysql_manager.invalidate_engine(config_id)

    async def set_available(self, data: BatchSetAvailable) -> None:
        await self.crud.set(ids=data.ids, status=data.status)
        for config_id in data.ids:
            await mysql_manager.invalidate_engine(config_id)

    async def test_connection(self, id: int) -> dict:
        """测试 MySQL 连接连通性"""
        from urllib.parse import quote_plus

        obj = await self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="配置不存在")

        start = time.time()
        try:
            password = decrypt_password(obj.password)
            if not password or password == PASSWORD_MASK:
                raise ValueError("密码无效，请在编辑时重新输入密码并保存")

            username = quote_plus(obj.username)
            pw = quote_plus(password)
            url = f"mysql+aiomysql://{username}:{pw}@{obj.host}:{obj.port}/{obj.database_name}?charset={obj.charset}"

            engine = create_async_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()

            latency = round((time.time() - start) * 1000, 2)
            logger.info("✅ MySQL 连接测试成功: {} ({}ms)", obj.name, latency)
            return {"success": True, "msg": "连接成功", "latency_ms": latency}
        except (SQLAlchemyError, ValueError, TimeoutError, OSError) as e:
            latency = round((time.time() - start) * 1000, 2)
            logger.warning("❌ MySQL 连接测试失败: {} - {}", obj.name, str(e))
            return {"success": False, "msg": f"连接失败: {str(e)}", "latency_ms": latency}
