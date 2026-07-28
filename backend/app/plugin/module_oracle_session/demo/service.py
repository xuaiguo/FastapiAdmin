"""Oracle 会话查询 Service"""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .crud import OracleSessionCRUD
from .schema import OracleSessionOutSchema, OracleSessionQueryParam


class OracleSessionService:
    """Oracle 会话查询服务层"""

    def __init__(self, oracle_db: AsyncSession) -> None:
        self.crud = OracleSessionCRUD(session=oracle_db)

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: OracleSessionQueryParam | None = None,
    ) -> dict[str, Any]:
        """分页查询 Oracle 会话"""
        offset = (page_no - 1) * page_size

        conditions: dict[str, Any] = {}
        if search:
            if search.service_name:
                conditions["service_name"] = ("like", search.service_name)
            if search.schemaname:
                conditions["schemaname"] = ("like", search.schemaname)
            if search.module:
                conditions["module"] = ("like", search.module)
            if search.program:
                conditions["program"] = ("like", search.program)
            if search.status:
                conditions["status"] = ("eq", search.status)
            if search.logon_time_start and search.logon_time_end:
                try:
                    conditions["logon_time"] = ("between", [
                        datetime.strptime(search.logon_time_start, "%Y-%m-%d %H:%M:%S"),
                        datetime.strptime(search.logon_time_end, "%Y-%m-%d %H:%M:%S"),
                    ])
                except ValueError:
                    pass  # 格式错误时忽略时间条件
            elif search.logon_time_start:
                try:
                    conditions["logon_time"] = ("ge",
                        datetime.strptime(search.logon_time_start, "%Y-%m-%d %H:%M:%S"),
                    )
                except ValueError:
                    pass
            elif search.logon_time_end:
                try:
                    conditions["logon_time"] = ("le",
                        datetime.strptime(search.logon_time_end, "%Y-%m-%d %H:%M:%S"),
                    )
                except ValueError:
                    pass

        return await self.crud.page(offset=offset, limit=page_size, search=conditions or None)

    async def detail(self, sid: int) -> OracleSessionOutSchema | None:
        """查询会话详情"""
        obj = await self.crud.get(sid=sid)
        if not obj:
            return None
        return OracleSessionOutSchema.model_validate(obj)
