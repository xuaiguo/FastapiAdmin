"""OceanBase Oracle 配置 Service"""

import asyncio
import time

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, BatchSetAvailable
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.ob_oracle.crypto import decrypt_password, encrypt_password
from app.core.ob_oracle.database import ob_oracle_manager

from .crud import ObOracleConfigCRUD
from .schema import (
    PASSWORD_MASK,
    ObOracleConfigCreateSchema,
    ObOracleConfigOutSchema,
    ObOracleConfigQueryParam,
    ObOracleConfigUpdateSchema,
)
from app.api.v1.module_system.ob_module.models import ObOracleConfigModule, ObOracleConfigUser


class ObOracleConfigService:
    """OceanBase Oracle 配置管理服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db
        self.crud = ObOracleConfigCRUD(auth, db)

    async def detail(self, id: int) -> ObOracleConfigOutSchema:
        obj = await self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="该配置不存在")
        return ObOracleConfigOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: ObOracleConfigQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[ObOracleConfigOutSchema]:
        obj_list = await self.crud.get_list(
            search=vars(search) if search else None, order_by=order_by
        )
        return [ObOracleConfigOutSchema.model_validate(obj) for obj in obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: ObOracleConfigQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        offset = (page_no - 1) * page_size
        return await self.crud.page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=vars(search) if search else None,
            out_schema=ObOracleConfigOutSchema,
        )

    async def create(self, data: ObOracleConfigCreateSchema) -> ObOracleConfigOutSchema:
        obj = await self.crud.get(name=data.name)
        if obj:
            raise CustomException(msg="创建失败，实例名称已存在")
        # 加密密码后存储
        data_dict = data.model_dump()
        data_dict["password"] = encrypt_password(data_dict["password"])
        obj = await self.crud.create(data=data_dict)
        return ObOracleConfigOutSchema.model_validate(obj)

    async def update(self, id: int, data: ObOracleConfigUpdateSchema) -> ObOracleConfigOutSchema:
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
        await ob_oracle_manager.invalidate_engine(id)
        return ObOracleConfigOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")
        await self.crud.delete(ids=ids)
        for config_id in ids:
            await ob_oracle_manager.invalidate_engine(config_id)

    async def set_available(self, data: BatchSetAvailable) -> None:
        await self.crud.set(ids=data.ids, status=data.status)
        for config_id in data.ids:
            await ob_oracle_manager.invalidate_engine(config_id)

    async def test_connection(self, id: int) -> dict:
        """测试 OceanBase Oracle 租户连接连通性（使用 SQLAlchemy create_engine）"""
        from urllib.parse import quote_plus

        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError

        obj = await self.crud.get(id=id)
        if not obj:
            raise CustomException(msg="配置不存在")

        start = time.time()
        try:
            password = decrypt_password(obj.password)
            if not password or password == PASSWORD_MASK:
                raise ValueError("密码无效，请在编辑时重新输入密码并保存")

            username = quote_plus(obj.username)
            enc_password = quote_plus(password)
            url = f"oracle+cx_oracle://{username}:{enc_password}@{obj.host}:{obj.port}/?service_name={obj.service_name}"

            def _do_connect():
                engine = create_engine(
                    url,
                    pool_timeout=10,
                )
                try:
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1 FROM DUAL"))
                finally:
                    engine.dispose()

            await asyncio.to_thread(_do_connect)
            latency = round((time.time() - start) * 1000, 2)
            logger.info("✅ OceanBase Oracle 连接测试成功: {} ({}ms)", obj.name, latency)
            return {"success": True, "msg": "连接成功", "latency_ms": latency}
        except (SQLAlchemyError, ValueError, TimeoutError, OSError) as e:
            latency = round((time.time() - start) * 1000, 2)
            logger.warning("❌ OceanBase Oracle 连接测试失败: {} - {}", obj.name, str(e))
            return {"success": False, "msg": f"连接失败: {str(e)}", "latency_ms": latency}

    # ===== 用户分配管理 =====

    async def get_allocated_users(self, config_id: int) -> dict:
        """查询数据源已分配的用户ID列表"""
        db = self.db
        query = select(ObOracleConfigUser.user_id).where(
            ObOracleConfigUser.config_id == config_id
        )
        result = await db.execute(query)
        user_ids = [row[0] for row in result.fetchall()]
        return {"user_ids": user_ids}

    async def allocate_users(self, config_id: int, user_ids: list[int]) -> None:
        """分配用户给数据源（最少选择1个用户）"""
        if len(user_ids) < 1:
            raise CustomException(msg="最少选择1个用户")

        db = self.db
        # 删除旧的关联
        await db.execute(
            delete(ObOracleConfigUser).where(
                ObOracleConfigUser.config_id == config_id
            )
        )
        # 添加新的关联
        for user_id in user_ids:
            db.add(ObOracleConfigUser(config_id=config_id, user_id=user_id))

        logger.info("✅ 数据源用户分配成功: config_id={}, user_ids={}", config_id, user_ids)

    # ===== 模块级数据源过滤 =====

    async def list_for_module(
        self, module_name: str | None = None, user_id: int | None = None
    ) -> list[ObOracleConfigOutSchema]:
        """查询指定模块和用户可见的数据源列表

        - module_name: 仅返回已分配给该模块的数据源
        - user_id: 仅返回已分配给该用户的数据源
        - 两者同时传入时取交集
        - 都不传则返回全部启用的数据源
        """
        from app.api.v1.module_system.ob_oracle_config.model import ObOracleConfigModel

        db = self.db
        query = select(ObOracleConfigModel).where(ObOracleConfigModel.status == 0)

        if module_name:
            module_sub = select(ObOracleConfigModule.config_id).where(
                ObOracleConfigModule.module_name == module_name
            )
            query = query.where(ObOracleConfigModel.id.in_(module_sub))

        if user_id:
            user_sub = select(ObOracleConfigUser.config_id).where(
                ObOracleConfigUser.user_id == user_id
            )
            query = query.where(ObOracleConfigModel.id.in_(user_sub))

        result = await db.execute(query)
        return [ObOracleConfigOutSchema.model_validate(obj) for obj in result.scalars().all()]
