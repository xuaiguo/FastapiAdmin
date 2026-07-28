"""OB Oracle SQL 查询 Service"""

from .executor import execute_query


class ObOracleQueryService:
    """OB Oracle SQL 查询服务"""

    @staticmethod
    async def execute(config_id: int, sql: str, max_rows: int = 1000) -> dict:
        """执行 SQL 查询"""
        return await execute_query(config_id, sql, max_rows)
