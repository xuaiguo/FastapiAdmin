"""
Oracle CRUD 基类。

精简版 CRUD，仅保留基础增删改查操作。
不含 FastapiAdmin 框架特有的租户过滤、软删除、数据权限等逻辑。
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import asc, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.oracle.base_model import OracleBase

ModelType = TypeVar("ModelType", bound=OracleBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class OracleCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Oracle CRUD 基类。

    与 base_crud.py 中 CRUDBase 的区别:
    - 不含租户隔离（无 tenant_id 过滤）
    - 不含软删除（无 is_deleted 过滤和设置）
    - 不含数据权限（无 data_scope 过滤）
    - 不含 __loader_options__ 预加载
    - 构造函数直接接收 session，不依赖 AuthSchema
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.db = session

    def _get_pk_col(self) -> Any:
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(self.model)
        pk_cols = list(getattr(mapper, "primary_key", []))
        return pk_cols[0] if pk_cols else None

    def _build_conditions(self, **kwargs: Any) -> list:
        conditions = []
        for key, value in kwargs.items():
            if value is None or value == "":
                continue
            if not hasattr(self.model, key):
                continue
            attr = getattr(self.model, key)
            if isinstance(value, tuple):
                seq, val = value
                if seq == "like" and val:
                    conditions.append(attr.like(f"%{val}%"))
                elif seq == "in" and val:
                    conditions.append(attr.in_(val))
                elif seq == "between" and isinstance(val, (list, tuple)) and len(val) == 2:
                    conditions.append(attr.between(val[0], val[1]))
                elif seq in ("eq", "==") and val is not None:
                    conditions.append(attr == val)
                elif seq in ("ne", "!=") and val is not None:
                    conditions.append(attr != val)
                elif seq in ("gt", ">") and val is not None:
                    conditions.append(attr > val)
                elif seq in ("ge", ">=") and val is not None:
                    conditions.append(attr >= val)
                elif seq in ("lt", "<") and val is not None:
                    conditions.append(attr < val)
                elif seq in ("le", "<=") and val is not None:
                    conditions.append(attr <= val)
            else:
                conditions.append(attr == value)
        return conditions

    async def get(self, **kwargs: Any) -> ModelType | None:
        conditions = self._build_conditions(**kwargs)
        if not conditions:
            return None
        sql = select(self.model).where(*conditions)
        result = await self.db.execute(sql)
        return result.scalars().first()

    async def get_list(
        self,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[ModelType]:
        conditions = self._build_conditions(**(search or {}))
        order = order_by or [{"id": "asc"}]
        sql = select(self.model).where(*conditions).order_by(*self._parse_order(order))
        result = await self.db.execute(sql)
        return list(result.scalars().all())

    async def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        conditions = self._build_conditions(**(search or {}))
        order = order_by or [{"id": "asc"}]

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
            "rows": rows,
        }

    async def create(self, data: CreateSchemaType | dict) -> ModelType:
        obj_dict = data if isinstance(data, dict) else data.model_dump()
        obj = self.model(**obj_dict)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, id: int, data: UpdateSchemaType | dict) -> ModelType:
        obj = await self.db.get(self.model, id)
        if not obj:
            raise ValueError(f"记录不存在: {self.model.__tablename__}.id={id}")

        obj_dict = data if isinstance(data, dict) else data.model_dump(exclude_unset=True)
        for key, value in obj_dict.items():
            if hasattr(obj, key) and key != "id":
                setattr(obj, key, value)

        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, ids: list[int]) -> None:
        pk = self._get_pk_col()
        sql = delete(self.model).where(pk.in_(ids))
        await self.db.execute(sql)
        await self.db.flush()

    def _parse_order(self, order: list[dict[str, str]]) -> list:
        columns = []
        for item in order:
            for field, direction in item.items():
                if not hasattr(self.model, field):
                    continue
                column = getattr(self.model, field)
                columns.append(desc(column) if direction.lower() == "desc" else asc(column))
        return columns
