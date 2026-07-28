"""OB Oracle SQL 查询历史 Service"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException

from .history_crud import QueryHistoryCRUD


class QueryHistoryService:
    """SQL 查询历史服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db
        self.crud = QueryHistoryCRUD(auth, db)

    async def save_history(
        self,
        config_id: int,
        config_name: str | None,
        sql: str,
        status: int = 0,
        elapsed_ms: float | None = None,
        row_count: int | None = None,
        error_msg: str | None = None,
    ) -> None:
        """保存查询历史（失败不影响主流程）"""
        try:
            await self.crud.create(
                data={
                    "config_id": config_id,
                    "config_name": config_name,
                    "sql": sql,
                    "status": status,
                    "elapsed_ms": elapsed_ms,
                    "row_count": row_count,
                    "error_msg": error_msg,
                }
            )
        except Exception:
            pass

    async def page(
        self,
        page_no: int,
        page_size: int,
        config_id: int | None = None,
        status: int | None = None,
    ) -> dict:
        """分页查询历史"""
        search = {}
        if config_id is not None:
            search["config_id"] = config_id
        if status is not None:
            search["status"] = status
        return await self.crud.page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            search=search or None,
            order_by=[{"id": "desc"}],
        )

    async def delete(self, ids: list[int]) -> None:
        """删除历史记录"""
        if not ids:
            raise CustomException(msg="请选择要删除的记录")
        await self.crud.delete(ids=ids)

    async def clear(self) -> None:
        """清空当前用户的历史记录"""
        result = await self.crud.get_list(search={"created_id": self.auth.user.id})
        if result:
            ids = [obj.id for obj in result]
            await self.crud.delete(ids=ids)
