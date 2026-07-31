"""MySQL 多数据源示例 CRUD"""

from app.core.mysql.base_crud import MySQLCRUDBase

from .model import MysqlDemoModel
from .schema import MysqlDemoCreateSchema, MysqlDemoUpdateSchema


class MysqlDemoCRUD(MySQLCRUDBase[MysqlDemoModel, MysqlDemoCreateSchema, MysqlDemoUpdateSchema]):
    """MySQL 示例数据层"""
