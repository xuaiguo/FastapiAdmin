"""
Oracle 会话查询模型。

映射 Oracle 系统视图 v$session，仅用于查询。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.oracle.base_model import OracleBase


class OracleSessionModel(OracleBase):
    """Oracle v$session 系统视图映射"""

    __tablename__: str = "v$session"

    sid: Mapped[int] = mapped_column("SID", Integer, primary_key=True, comment="会话ID")
    serial_no: Mapped[int] = mapped_column("SERIAL#", Integer, comment="序列号")
    service_name: Mapped[str | None] = mapped_column("SERVICE_NAME", String(200), nullable=True, comment="服务名")
    schemaname: Mapped[str | None] = mapped_column("SCHEMANAME", String(200), nullable=True, comment="Schema名")
    module: Mapped[str | None] = mapped_column("MODULE", String(200), nullable=True, comment="模块名")
    program: Mapped[str | None] = mapped_column("PROGRAM", String(200), nullable=True, comment="程序名")
    status: Mapped[str | None] = mapped_column("STATUS", String(50), nullable=True, comment="状态(ACTIVE/INACTIVE)")
    machine: Mapped[str | None] = mapped_column("MACHINE", String(200), nullable=True, comment="机器名")
    terminal: Mapped[str | None] = mapped_column("TERMINAL", String(200), nullable=True, comment="终端")
    osuser: Mapped[str | None] = mapped_column("OSUSER", String(200), nullable=True, comment="操作系统用户")
    sql_id: Mapped[str | None] = mapped_column("SQL_ID", String(50), nullable=True, comment="SQL ID")
    logon_time: Mapped[datetime | None] = mapped_column("LOGON_TIME", DateTime, nullable=True, comment="登录时间")
    prev_exec_start: Mapped[datetime | None] = mapped_column("PREV_EXEC_START", DateTime, nullable=True, comment="上次执行开始时间")
