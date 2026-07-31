"""OB JOBS 查询 Schema"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict, field_validator


class ObSchedulerJobsOutSchema(BaseModel):
    """调度任务查询结果"""

    owner: str | None = None
    job_name: str | None = None
    job_style: str | None = None
    job_type: str | None = None
    job_class: str | None = None
    job_action: str | None = None
    repeat_interval: str | None = None
    last_start_date: str | None = None
    next_run_date: str | None = None
    program_name: str | None = None
    schedule_name: str | None = None
    enabled: str | None = None
    state: str | None = None
    comments: str | None = None
    max_run_duration: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def convert_to_str(cls, v):
        if v is None:
            return v
        if isinstance(v, timedelta):
            total = int(v.total_seconds())
            h, m, s = total // 3600, (total % 3600) // 60, total % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        return str(v) if not isinstance(v, str) else v
