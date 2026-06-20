from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException
from app.core.logger import logger

from .crud import LoginLogCRUD, OperationLogCRUD
from .schema import (
    LoginLogCreateSchema,
    LoginLogDetailOutSchema,
    LoginLogOutSchema,
    LoginLogQueryParam,
    OperationLogCreateSchema,
    OperationLogDetailOutSchema,
    OperationLogOutSchema,
    OperationLogQueryParam,
)


class LoginLogService:
    """
    登录日志管理服务

    提供登录日志 CRUD、清理过期日志等业务能力。
    """

    @classmethod
    async def detail_service(cls, auth: AuthSchema, id: int) -> LoginLogDetailOutSchema:
        return await LoginLogCRUD(auth).get_or_404(id=id, out_schema=LoginLogDetailOutSchema)

    @classmethod
    async def page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: LoginLogQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        search_dict = vars(search) if search else None
        order_by_list = order_by or [{"updated_time": "desc"}]
        offset = (page_no - 1) * page_size

        result = await LoginLogCRUD(auth).page(
            offset=offset,
            limit=page_size,
            order_by=order_by_list,
            search=search_dict,
            out_schema=LoginLogOutSchema,
        )
        return result

    @classmethod
    async def create_service(cls, auth: AuthSchema, data: LoginLogCreateSchema) -> LoginLogDetailOutSchema:
        obj = await LoginLogCRUD(auth).create(data=data)
        if not obj:
            raise CustomException(msg="创建失败")
        return LoginLogDetailOutSchema.model_validate(obj)

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")

        existing = await LoginLogCRUD(auth).list(search={"id": ("in", ids)})
        existing_map = {obj.id for obj in existing}
        for nid in ids:
            if nid not in existing_map:
                raise CustomException(msg=f"删除失败，ID为{nid}的数据不存在")

        await LoginLogCRUD(auth).delete(ids=ids)


class OperationLogService:
    """
    操作日志管理服务

    提供操作日志记录、分页查询、清理过期日志等业务能力。
    """

    @staticmethod
    async def cleanup_operation_log() -> None:
        """
        定时任务：清理超过保留期的操作日志和登录日志。

        清理 created_time < now - retention_days 的记录。
        保留期从全局参数 `operation_log_retention_days` 读取，默认 90 天。

        返回:
        - bool: 清理完成返回 True。
        """
        from datetime import datetime, timedelta

        from sqlalchemy import delete

        from app.core.database import async_db_session

        from .model import LoginLogModel, OperationLogModel

        retention_days = 90  # 默认 90 天，可通过系统参数覆盖
        # 尝试从系统参数读取自定义保留期
        try:
            from app.api.v1.module_system.params.model import ParamsModel

            async with async_db_session() as _s:
                from sqlalchemy import select

                result = await _s.execute(select(ParamsModel.config_value).where(ParamsModel.config_key == "operation_log_retention_days").limit(1))
                row = result.scalar()
                if row is not None:
                    retention_days = int(row)
        except Exception:
            pass  # 读取失败使用默认值

        cutoff = datetime.now() - timedelta(days=retention_days)
        async with async_db_session() as session:
            op_stmt = delete(OperationLogModel).where(OperationLogModel.created_time < cutoff)
            op_result = await session.execute(op_stmt)

            login_stmt = delete(LoginLogModel).where(LoginLogModel.created_time < cutoff)
            login_result = await session.execute(login_stmt)

            await session.commit()
            logger.info(f"操作日志清理完成: 操作日志 {op_result.rowcount} 条, 登录日志 {login_result.rowcount} 条")
            return True

    @classmethod
    async def create_service(cls, auth: AuthSchema, data: OperationLogCreateSchema) -> OperationLogDetailOutSchema:
        """
        创建操作日志。

        参数:
        - auth (AuthSchema): 认证信息模型。
        - data (OperationLogCreateSchema): 操作日志创建模型。

        返回:
        - OperationLogDetailOutSchema: 新创建的操作日志。

        异常:
        - CustomException: 创建失败时抛出。
        """
        crud = OperationLogCRUD(auth)
        obj = await crud.create(data=data)
        if not obj:
            raise CustomException(msg="创建失败")
        return OperationLogDetailOutSchema.model_validate(obj)

    @classmethod
    async def page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: OperationLogQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        """
        分页查询操作日志。

        参数:
        - auth (AuthSchema): 认证信息模型。
        - page_no (int): 页码。
        - page_size (int): 每页数量。
        - search (OperationLogQueryParam | None): 查询参数。
        - order_by (list[dict[str, str]] | None): 排序参数。

        返回:
        - dict: 分页数据。
        """
        crud = OperationLogCRUD(auth)
        return await crud.page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"id": "desc"}],
            search=vars(search) if search else None,
            out_schema=OperationLogOutSchema,
        )

    @classmethod
    async def detail_service(cls, auth: AuthSchema, id: int) -> OperationLogDetailOutSchema:
        """
        获取操作日志详情。

        参数:
        - auth (AuthSchema): 认证信息模型。
        - id (int): 操作日志ID。

        返回:
        - OperationLogDetailOutSchema: 操作日志详情。
        """

        crud = OperationLogCRUD(auth)
        return await crud.get_or_404(id=id, out_schema=OperationLogDetailOutSchema)

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除操作日志。

        参数:
        - auth (AuthSchema): 认证信息模型。
        - ids (list[int]): 操作日志ID列表。

        异常:
        - CustomException: 删除失败时抛出。

        返回:
        - None
        """
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")
        existing = await OperationLogCRUD(auth).list(search={"id": ("in", ids)})
        existing_map = {obj.id for obj in existing}
        for nid in ids:
            if nid not in existing_map:
                raise CustomException(msg="删除失败，该数据不存在")
        crud = OperationLogCRUD(auth)
        await crud.delete(ids)
