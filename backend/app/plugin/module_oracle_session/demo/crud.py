"""Oracle 会话查询 CRUD"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.oracle.base_crud import OracleCRUDBase

from .model import OracleSessionModel
from .schema import OracleSessionOutSchema


class OracleSessionCRUD(OracleCRUDBase[OracleSessionModel, Any, Any]):
    """Oracle 会话查询数据层（仅查询）"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=OracleSessionModel, session=session)

    async def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """分页查询 v$session"""
        conditions = self._build_conditions(**(search or {}))
        order = order_by or [{"sid": "asc"}]

        count_sql = select(func.count()).select_from(self.model).where(*conditions)
        count_result = await self.db.execute(count_sql)
        total = count_result.scalar() or 0

        data_sql = (
            select(self.model)
            .where(*conditions)
            .order_by(*self._parse_order(order))
            .offset(offset)
            .limit(limit)
        )
        data_result = await self.db.execute(data_sql)
        rows = list(data_result.scalars().all())

        return {
            "page_no": (offset // limit) + 1 if limit else 1,
            "page_size": limit,
            "total": total,
            "rows": [OracleSessionOutSchema.model_validate(r) for r in rows],
        }
