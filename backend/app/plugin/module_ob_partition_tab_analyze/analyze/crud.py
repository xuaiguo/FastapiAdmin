"""OB 分区表分析 CRUD — 查询 DBA 字典视图分析分区表"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schema import ObPartitionTabAnalyzeOutSchema

# ── SQL 拆分策略 ──
# _BASE_SQL_PREFIX: 外层 SELECT + 所有子查询，直到内层 WHERE 后的固定条件
# {动态条件}:       AND p.table_owner = :table_owner / AND p.table_name LIKE :table_name
# _BASE_SQL_SUFFIX: GROUP BY + 闭合括号 + ORDER BY

_BASE_SQL_PREFIX = """
select table_owner,composite,partitioning_type,subpartitioning_type
,case when o_partition_updater='dba_manual' and partitioning_type='LIST' and subpartitioning_type='NONE' and is_max_partition=0 and instr(column_list,'PARTITION_FIELD')=0 then 'none'
      else o_partition_updater end as o_partition_updater
,table_name,is_max_partition,first_partition,final_partition
,plan_auto_interval
,column_list,sub_column_list,auto_interval,global_count,local_count,compression,partition_count,subpartition_count
from
(
select table_owner,composite,partitioning_type,subpartitioning_type,table_name
,max(case when subpartitioning_type!='RANGE' and order_no=1 and (instr(PARTITION_NAME,'PMAX')>0 or instr(PARTITION_NAME,'PDEF')>0 or instr(PARTITION_NAME,'PART_ALL')>0) then 1
          when subpartitioning_type ='RANGE' and suborder_no=1 and (instr(SUBPARTITION_NAME,'SMAX')>0 or instr(SUBPARTITION_NAME,'SDEF')>0) then 1
          else 0 end)  as is_max_partition

,max( case when subpartitioning_type !='RANGE' and PARTITION_POSITION=1 then PARTITION_NAME
           when subpartitioning_type ='RANGE'  and PARTITION_POSITION=1 and SUBPARTITION_POSITION=1 then SUBPARTITION_NAME
        else null  end
 ) as first_partition
,max( case
        when subpartitioning_type !='RANGE' and order_no=1 and (instr(PARTITION_NAME,'PMAX')>0 or instr(PARTITION_NAME,'PDEF')>0 or instr(PARTITION_NAME,'PART_ALL')>0) then PRE_PARTITION_NAME
        when subpartitioning_type !='RANGE' and order_no=1 and (instr(PARTITION_NAME,'PMAX')=0 and instr(PARTITION_NAME,'PDEF')=0 and instr(PARTITION_NAME,'PART_ALL')=0)  then PARTITION_NAME
        when subpartitioning_type ='RANGE'  and order_no=1 and suborder_no<=2 and (instr(SUBPARTITION_NAME,'SMAX')>0 or instr(SUBPARTITION_NAME,'SDEF')>0) then PRE_SUBPARTITION_NAME
        when subpartitioning_type ='RANGE'  and order_no=1 and suborder_no<=2 and (instr(SUBPARTITION_NAME,'SMAX')=0 and instr(SUBPARTITION_NAME,'SDEF')=0) then SUBPARTITION_NAME
        else null  end
 ) as final_partition

,case when b.partitioning_type='HASH' and subpartitioning_type='NONE' then 'none'
      when b.auto_interval is not null then 'dba_auto'
      when instr(column_list,'(DATE)')>0 then 'dba_auto_plan'
      when instr(column_list,'(DATE)')=0 then 'dba_manual'
      else 'none' end  as o_partition_updater

,case when b.partitioning_type='HASH' and subpartitioning_type='NONE' then 'NO'
      when b.auto_interval is not null then 'AUTO'
      when instr(column_list,'(DATE)')>0 then 'YES'
      when instr(column_list,'(DATE)')=0 then 'NO'
      else 'none' end as plan_auto_interval
,column_list,sub_column_list,auto_interval,global_count,local_count,compression
,max(partition_position) as partition_count
,max(case when order_no=1 then subpartition_position else null end) as subpartition_count
from
(
 select  k1.COLUMN_LIST,k2.SUB_COLUMN_LIST,i.global_count,i.local_count,p.*
 from
 (
 select /*+ materialize */ *
 from
 (
  select a.TABLE_OWNER,a.TABLE_NAME
  ,a.COMPOSITE
  ,a2.partitioning_type,a2.subpartitioning_type
  ,a2.interval as auto_interval
  ,a2.def_compression as compression
  ,lag(a.PARTITION_NAME,1,null) over(partition by a.TABLE_OWNER,a.TABLE_NAME order by a.PARTITION_POSITION) as PRE_PARTITION_NAME
  ,a.PARTITION_NAME
  ,dense_rank() over (partition by a.TABLE_OWNER,a.TABLE_NAME order by a.PARTITION_POSITION desc) order_no
  ,a.PARTITION_POSITION
  ,replace(lag(b.SUBPARTITION_NAME,1,null) over(partition by a.TABLE_OWNER,a.TABLE_NAME,a.PARTITION_POSITION order by b.SUBPARTITION_POSITION),a.PARTITION_NAME || '_','') as PRE_SUBPARTITION_NAME
  ,replace(b.SUBPARTITION_NAME,a.PARTITION_NAME || '_','') as SUBPARTITION_NAME
  ,dense_rank() over (partition by a.TABLE_OWNER,a.TABLE_NAME,a.PARTITION_POSITION order by b.SUBPARTITION_POSITION desc) suborder_no
  ,b.SUBPARTITION_POSITION
  from dba_TAB_PARTITIONS a
  join dba_part_tables a2 on(a.TABLE_OWNER=a2.OWNER and a.TABLE_NAME=a2.TABLE_NAME)
  left join dba_TAB_SUBPARTITIONS b on(a.TABLE_OWNER=b.TABLE_OWNER and a.TABLE_NAME=b.TABLE_NAME and a.PARTITION_NAME=b.PARTITION_NAME)
  where a.TABLE_NAME not like 'BIN%'
 ) c where
 (
  (subpartitioning_type in('NONE','HASH'))
  or
  (subpartitioning_type in('RANGE'))
 )
) p
 join
 (
 select /*+ materialize */ a.OWNER,a.NAME as TABLE_NAME
 ,LISTAGG(b.COLUMN_NAME || ' (' || b.DATA_TYPE || ') ', ', ') WITHIN GROUP (ORDER BY b.COLUMN_NAME) AS COLUMN_LIST
 from dba_part_key_columns a join dba_tab_columns b on(a.owner=b.owner and a.name=b.table_name and a.column_name=b.column_name)
 where a.object_type='TABLE'
 group by a.OWNER,a.NAME
) k1 on(p.table_owner=k1.owner and p.table_name=k1.table_name)
 left join
 (
 select /*+ materialize */ a.OWNER,a.NAME as TABLE_NAME
 ,LISTAGG(b.COLUMN_NAME || ' (' || b.DATA_TYPE || ') ', ', ') WITHIN GROUP (ORDER BY b.COLUMN_NAME) AS SUB_COLUMN_LIST
 from dba_subpart_key_columns a join dba_tab_columns b on(a.owner=b.owner and a.name=b.table_name and a.column_name=b.column_name)
 where a.object_type='TABLE'
 group by a.OWNER,a.NAME
 ) k2 on(p.table_owner=k2.owner and p.table_name=k2.table_name)
 left join
 (

 select /*+ materialize */ owner,table_name,partitioning_type,subpartitioning_type
 ,sum(case when locality='GLOBAL' then 1 else 0 end) as GLOBAL_COUNT
 ,sum(case when locality='GLOBAL' and partitioned='YES' then 1 else 0 end) as GLOBAL_PARTITIONED_COUNT
 ,sum(case when locality='LOCAL' then 1 else 0 end) as LOCAL_COUNT
 from
 (
  select c.owner,c.table_name,c.partitioning_type,c.subpartitioning_type
  ,a.index_name,a.uniqueness,a.partitioned
  ,nvl(b.locality,'GLOBAL') as locality
  ,b.alignment,b.def_tablespace_name
  from dba_part_tables c left join dba_indexes a on(c.owner=a.table_owner and c.table_name=a.table_name and a.index_type!='LOB')
  left join dba_part_indexes b on(a.owner=b.owner and a.table_name=b.table_name and a.index_name=b.index_name)
 ) d
 group by owner,table_name,partitioning_type,subpartitioning_type

) i on(p.table_owner=i.owner and p.table_name=i.table_name)
where 1=1
"""

_BASE_SQL_SUFFIX = """
) b
group by table_owner,table_name,composite,partitioning_type,subpartitioning_type,auto_interval,compression,column_list,sub_column_list,global_count,local_count
) c
order by 2,3,4,5
"""


class ObPartitionTabAnalyzeCRUD:
    """OB 分区表分析数据层（只读）"""

    def __init__(self, session: Session) -> None:
        self.db = session

    @staticmethod
    def _build_where_and_params(search: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """根据搜索条件动态构建额外 WHERE 子句和参数"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if search:
            if search.get("table_owner"):
                conditions.append("and p.table_owner = :table_owner")
                params["table_owner"] = search["table_owner"]

            if search.get("table_name"):
                conditions.append("and p.table_name like :table_name")
                params["table_name"] = f"%{search['table_name']}%"

        where_clause = " ".join(conditions) if conditions else ""
        return where_clause, params

    def page(
        self,
        offset: int,
        limit: int,
        search: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """分页查询分区表分析"""
        where_clause, params = self._build_where_and_params(search)

        # 完整数据查询
        full_data_sql = f"{_BASE_SQL_PREFIX} {where_clause} {_BASE_SQL_SUFFIX}"

        # COUNT 查询
        count_sql = text(f"SELECT COUNT(*) FROM ({full_data_sql})")
        count_result = self.db.execute(count_sql, params)
        total = count_result.scalar() or 0

        # DATA 查询（带分页）
        data_sql = text(
            f"{full_data_sql} OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        )
        data_params = {**params, "offset": offset, "limit": limit}
        data_result = self.db.execute(data_sql, data_params)
        rows = data_result.fetchall()
        columns = data_result.keys()

        return {
            "page_no": (offset // limit) + 1 if limit else 1,
            "page_size": limit,
            "total": total,
            "items": [
                ObPartitionTabAnalyzeOutSchema(**{k.lower(): v for k, v in zip(columns, row, strict=True)})
                for row in rows
            ],
            "has_next": offset + limit < total,
        }
