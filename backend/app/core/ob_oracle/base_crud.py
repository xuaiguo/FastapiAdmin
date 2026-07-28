"""
OceanBase Oracle 租户 CRUD 基类。

精简版 CRUD，仅保留基础增删改查操作。
所有方法为同步（非 async），因为 cx_oracle 驱动不支持原生异步。
不含 FastapiAdmin 框架特有的租户过滤、软删除、数据权限等逻辑。
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import asc, delete, desc, func, select, text
from sqlalchemy.orm import Session

from app.core.ob_oracle.base_model import ObOracleBase

ModelType = TypeVar("ModelType", bound=ObOracleBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class ObOracleCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    OceanBase Oracle 租户 CRUD 基类。

    与 Oracle 版 OracleCRUDBase 的区别:
    - 所有方法为同步（普通 def），因为 cx_oracle 无原生 async
    - 使用同步 Session（非 AsyncSession）
    - 其余逻辑相同：不含租户隔离、软删除、数据权限
    """

    def __init__(self, model: type[ModelType], session: Session) -> None:
        self.model = model
        self.db = session

    def _get_pk_col(self) -> Any:
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(self.model)
        pk_cols = list(getattr(mapper, "primary_key", []))
        return pk_cols[0] if pk_cols else None

    def _get_pk_sequence(self) -> Any:
        """获取主键列上绑定的 Sequence 对象（如有）"""
        pk_col = self._get_pk_col()
        if pk_col is None:
            return None
        # SQLAlchemy Column 的 sequences 属性包含绑定的 Sequence 列表
        sequences = getattr(pk_col, "sequences", None)
        if sequences:
            return sequences[0]
        return None

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

    def get(self, **kwargs: Any) -> ModelType | None:
        conditions = self._build_conditions(**kwargs)
        if not conditions:
            return None
        sql = select(self.model).where(*conditions)
        result = self.db.execute(sql)
        return result.scalars().first()

    def get_list(
        self,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[ModelType]:
        conditions = self._build_conditions(**(search or {}))
        order = order_by or [{"id": "asc"}]
        sql = select(self.model).where(*conditions).order_by(*self._parse_order(order))
        result = self.db.execute(sql)
        return list(result.scalars().all())

    def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        conditions = self._build_conditions(**(search or {}))
        order = order_by or [{"id": "asc"}]

        count_sql = select(func.count()).select_from(self.model).where(*conditions)
        count_result = self.db.execute(count_sql)
        total = count_result.scalar() or 0

        data_sql = (
            select(self.model)
            .where(*conditions)
            .order_by(*self._parse_order(order))
            .offset(offset)
            .limit(limit)
        )
        data_result = self.db.execute(data_sql)
        rows = list(data_result.scalars().all())

        return {
            "page_no": (offset // limit) + 1 if limit else 1,
            "page_size": limit,
            "total": total,
            "rows": rows,
        }

    def create(self, data: CreateSchemaType | dict) -> ModelType:
        from sqlalchemy import insert as sa_insert

        obj_dict = data if isinstance(data, dict) else data.model_dump()

        pk_col = self._get_pk_col()
        if pk_col is not None and pk_col.name in obj_dict:
            del obj_dict[pk_col.name]

        stmt = sa_insert(self.model).values(**obj_dict)
        self.db.execute(stmt)
        self.db.flush()

        # 获取新插入行的主键：优先使用 Oracle SEQUENCE CURRVAL（会话级，无并发竞争）
        if pk_col is not None:
            seq = self._get_pk_sequence()
            if seq is not None:
                new_id = self.db.execute(
                    text(f"SELECT {seq.name}.CURRVAL FROM DUAL")
                ).scalar()
                if new_id is not None:
                    return self.db.get(self.model, new_id)

        # 无主键或无序列时的兜底：按主键降序取最后插入行
        if pk_col is not None:
            rows = self.db.execute(select(self.model).order_by(desc(pk_col)).limit(1)).scalars().all()
        else:
            first_col = self.model.__table__.columns[0]
            rows = self.db.execute(select(self.model).order_by(desc(first_col)).limit(1)).scalars().all()
        return rows[0] if rows else None

    def update(self, id: int, data: UpdateSchemaType | dict) -> ModelType:
        obj = self.db.get(self.model, id)
        if not obj:
            raise ValueError(f"记录不存在: {self.model.__tablename__}.id={id}")

        obj_dict = data if isinstance(data, dict) else data.model_dump(exclude_unset=True)
        for key, value in obj_dict.items():
            if hasattr(obj, key) and key != "id":
                setattr(obj, key, value)

        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, ids: list[int]) -> None:
        pk = self._get_pk_col()
        sql = delete(self.model).where(pk.in_(ids))
        self.db.execute(sql)
        self.db.flush()

    def _parse_order(self, order: list[dict[str, str]]) -> list:
        columns = []
        for item in order:
            for field, direction in item.items():
                if not hasattr(self.model, field):
                    continue
                column = getattr(self.model, field)
                columns.append(desc(column) if direction.lower() == "desc" else asc(column))
        return columns
