"""OB ProcessList 查询 Schema"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class ObProcesslistOutSchema(BaseModel):
    """ProcessList 查询结果"""

    id: int | None = None
    svr_ip: str | None = None
    user: str | None = None
    host: str | None = None
    db: str | None = None
    tenant: str | None = None
    command: str | None = None
    time: int | None = None
    total_time: int | None = None
    state: str | None = None
    info: str | None = None
    user_client_ip: str | None = None
    user_host: str | None = None
    sql_id: str | None = None
    trans_id: str | int | None = None
    trace_id: str | None = None
    top_trace_id: str | None = None
    module: str | None = None
    action: str | None = None
    client_info: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def convert_to_str(cls, v):
        if v is None:
            return v
        if isinstance(v, (str, int, float, bool)):
            return v
        if isinstance(v, Decimal):
            return float(v)
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(v, date):
            return v.strftime("%Y-%m-%d")
        if isinstance(v, timedelta):
            total = int(v.total_seconds())
            h, m, s = total // 3600, (total % 3600) // 60, total % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        if isinstance(v, bytes):
            return v.hex()
        return str(v)
