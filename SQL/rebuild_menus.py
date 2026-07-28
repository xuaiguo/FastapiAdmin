"""重建正确的菜单结构"""
import pymysql, uuid
from datetime import datetime

conn = pymysql.connect(host='10.3.94.10', port=3306, user='root', password='fastapiadmin_root', database='fastapiadmin_dev3', charset='utf8mb4')
cur = conn.cursor()
now = datetime.now()

def uid(): return str(uuid.uuid4())

def ins_page(name, order, perm, icon, rn, rp, cp, title, desc, pid):
    cur.execute(
        "INSERT INTO sys_menu (uuid,name,type,`order`,permission,icon,route_name,route_path,"
        "component_path,redirect,hidden,keep_alive,always_show,title,params,affix,link,is_iframe,is_hide_tab,"
        "active_path,show_badge,show_text_badge,scope,status,description,parent_id,is_deleted,created_time,updated_time) "
        "VALUES (%s,%s,2,%s,%s,%s,%s,%s,%s,NULL,0,1,0,%s,NULL,0,NULL,0,0,NULL,0,NULL,'web',0,%s,%s,0,%s,%s)",
        (uid(),name,order,perm,icon,rn,rp,cp,title,desc,pid,now,now))
    return cur.lastrowid

def ins_btn(name, order, perm, pid):
    cur.execute(
        "INSERT INTO sys_menu (uuid,name,type,`order`,permission,redirect,hidden,keep_alive,always_show,"
        "affix,is_iframe,is_hide_tab,show_badge,scope,status,parent_id,is_deleted,created_time,updated_time) "
        "VALUES (%s,%s,3,%s,%s,NULL,0,0,0,0,0,0,0,'web',0,%s,0,%s,%s)",
        (uid(),name,order,perm,pid,now,now))
    return cur.lastrowid

def ins_dir(name, order, icon, rn, rp, desc, pid=None):
    cur.execute(
        "INSERT INTO sys_menu (uuid,name,type,`order`,icon,route_name,route_path,"
        "hidden,keep_alive,always_show,title,affix,is_iframe,is_hide_tab,show_badge,"
        "scope,status,description,parent_id,is_deleted,created_time,updated_time) "
        "VALUES (%s,%s,1,%s,%s,%s,%s,0,1,0,%s,0,0,0,0,'web',0,%s,%s,0,%s,%s)",
        (uid(),name,order,icon,rn,rp,name,desc,pid,now,now))
    return cur.lastrowid

# === Step 1: 清理数据库管理下的错误菜单 ===
cur.execute("SELECT id FROM sys_menu WHERE parent_id=100047 AND is_deleted=0")
wrong_ids = [r[0] for r in cur.fetchall()]

keep_ids = set()
cur.execute("SELECT id FROM sys_menu WHERE parent_id=100047 AND name=%s AND is_deleted=0", ('表空间查询',))
ts_row = cur.fetchone()
if ts_row:
    keep_ids.add(ts_row[0])
    cur.execute("SELECT id FROM sys_menu WHERE parent_id=%s AND is_deleted=0", (ts_row[0],))
    for r in cur.fetchall():
        keep_ids.add(r[0])

delete_ids = [i for i in wrong_ids if i not in keep_ids]
for did in list(delete_ids):
    cur.execute("SELECT id FROM sys_menu WHERE parent_id=%s AND is_deleted=0", (did,))
    for r in cur.fetchall():
        if r[0] not in keep_ids:
            delete_ids.append(r[0])

if delete_ids:
    placeholders = ",".join(str(i) for i in delete_ids)
    cur.execute(f"UPDATE sys_menu SET is_deleted=1 WHERE id IN ({placeholders})")
    print(f"Deleted {len(delete_ids)} wrong menus")

# === Step 2: 系统管理下添加配置菜单 ===
SYS_ID = 1
all_new = []

mid = ins_page("Oracle配置", 11, "module_system:oracle_config:query", "ri:database-line",
    "OracleConfig", "oracleConfig", "module_system/oracleConfig/index", "Oracle配置", "Oracle连接配置管理", SYS_ID)
all_new.append(mid)
for n,o,p in [("新增",1,"create"),("编辑",2,"update"),("删除",3,"delete"),("状态变更",4,"patch"),("测试连接",5,"test"),("详情",6,"detail")]:
    all_new.append(ins_btn(n, o, f"module_system:oracle_config:{p}", mid))

mid = ins_page("OB Oracle配置", 12, "module_system:ob_oracle_config:query", "ri:database-line",
    "ObOracleConfig", "obOracleConfig", "module_system/obOracleConfig/index", "OB Oracle配置", "OceanBase Oracle连接配置", SYS_ID)
all_new.append(mid)
for n,o,p in [("新增",1,"create"),("编辑",2,"update"),("删除",3,"delete"),("状态变更",4,"patch"),("测试连接",5,"test"),("详情",6,"detail"),("分配用户",7,"update")]:
    all_new.append(ins_btn(n, o, f"module_system:ob_oracle_config:{p}", mid))

mid = ins_page("MySQL配置", 13, "module_system:mysql_config:query", "ri:database-line",
    "MysqlConfig", "mysqlConfig", "module_system/mysqlConfig/index", "MySQL配置", "MySQL连接配置管理", SYS_ID)
all_new.append(mid)
for n,o,p in [("新增",1,"create"),("编辑",2,"update"),("删除",3,"delete"),("状态变更",4,"patch"),("测试连接",5,"test"),("详情",6,"detail")]:
    all_new.append(ins_btn(n, o, f"module_system:mysql_config:{p}", mid))

# === Step 3: 案例管理下添加demo ===
EXAMPLE_ID = 7
cur.execute("SELECT id FROM sys_menu WHERE name=%s AND parent_id=%s AND is_deleted=0", ("示例中心", EXAMPLE_ID))
dc_row = cur.fetchone()
DC_ID = dc_row[0] if dc_row else None

if DC_ID:
    mid = ins_page("MySQL数据示例", 2, "module_mysql_demo:demo:detail", "ri:database-line",
        "MysqlDemo", "mysqlDemo", "mysql_demo/mysqlDemo/index", "MySQL数据示例", "MySQL多数据源CRUD示例", DC_ID)
    all_new.append(mid)
    for n,o,p in [("新增",1,"create"),("编辑",2,"update"),("删除",3,"delete"),("详情",4,"detail")]:
        all_new.append(ins_btn(n, o, f"module_mysql_demo:demo:{p}", mid))

mid = ins_page("Oracle数据示例", 2, "module_oracle_demo:demo:detail", "ri:database-line",
    "OracleDemo", "oracleDemo", "oracle_demo/oracleDemo/index", "Oracle数据示例", "Oracle多数据源CRUD示例", EXAMPLE_ID)
all_new.append(mid)
for n,o,p in [("新增",1,"create"),("编辑",2,"update"),("删除",3,"delete"),("详情",4,"detail")]:
    all_new.append(ins_btn(n, o, f"module_oracle_demo:demo:{p}", mid))

mid = ins_page("Oracle会话查询", 3, "module_oracle_session:session:query", "ri:user-search-line",
    "OracleSession", "oracleSession", "oracle_session/oracleSession/index", "Oracle会话查询", "Oracle会话管理", EXAMPLE_ID)
all_new.append(mid)
all_new.append(ins_btn("查询", 1, "module_oracle_session:session:query", mid))
all_new.append(ins_btn("详情", 2, "module_oracle_session:session:detail", mid))

# === Step 4: OceanBase管理 ===
OB_DIR = ins_dir("OceanBase管理", 6, "ri:server-line", "OceanBaseManagement", "/oceanbase", "OceanBase DBA运维管理")
all_new.append(OB_DIR)

ob_tools = [
    ("SQL性能统计", 2, "module_ob_wr_sqlstat:sqlstat:query", "ri:line-chart-line", "ObWrSqlstat", "obWrSqlstat", "ob_wr_sqlstat/obWrSqlstat/index", "SQL性能统计", "WR SQL统计"),
    ("实时SQL性能统计", 3, "module_ob_sqlstat_cur:sqlstat:query", "ri:bar-chart-line", "ObSqlstatCur", "obSqlstatCur", "ob_sqlstat_cur/obSqlstatCur/index", "实时SQL性能统计", "当前SQL性能统计"),
    ("分区表分析", 4, "module_ob_partition_tab_analyze:analyze:query", "ri:table-line", "ObPartitionTabAnalyze", "obPartitionTabAnalyze", "ob_partition_tab_analyze/obPartitionTabAnalyze/index", "分区表分析", "OB分区表分析"),
    ("SQL审计", 5, "module_ob_sql_audit:audit:query", "ri:shield-check-line", "ObSqlAudit", "obSqlAudit", "ob_sql_audit/obSqlAudit/index", "SQL审计", "OB SQL审计"),
    ("JOBS查询", 6, "module_ob_scheduler_jobs:jobs:query", "ri:time-line", "ObSchedulerJobs", "obSchedulerJobs", "ob_scheduler_jobs/obSchedulerJobs/index", "JOBS查询", "OB调度任务"),
    ("SQL查询", 7, "module_ob_oracle_query:query:execute", "ri:terminal-box-line", "ObOracleQuery", "obOracleQuery", "ob_oracle_query/obOracleQuery/index", "SQL查询", "OB SQL查询控制台"),
    ("ProcessList", 8, "module_ob_processlist:processlist:query", "ri:process-line", "ObProcesslist", "obProcesslist", "ob_processlist/obProcesslist/index", "ProcessList", "OB实时进程列表"),
]
for name, order, perm, icon, rn, rp, cp, title, desc in ob_tools:
    mid = ins_page(name, order, perm, icon, rn, rp, cp, title, desc, OB_DIR)
    all_new.append(mid)
    btn_name = "执行" if name == "SQL查询" else "查询"
    all_new.append(ins_btn(btn_name, 1, perm, mid))

mid = ins_page("模块管理", 9, "module_system:ob_module:query", "ri:apps-line",
    "ObModule", "obModule", "system/obModule/index", "模块管理", "模块与数据源分配管理", OB_DIR)
all_new.append(mid)
for n,o,p in [("查询",1,"query"),("新增",2,"create"),("修改",3,"update"),("删除",4,"delete")]:
    all_new.append(ins_btn(n, o, f"module_system:ob_module:{p}", mid))

# === Step 5: 分配角色 ===
all_new.append(OB_DIR)
all_new.append(100047)
for mid in all_new:
    cur.execute("INSERT IGNORE INTO sys_role_menus (role_id, menu_id) VALUES (1, %s)", (mid,))

conn.commit()
print(f"Inserted {len(all_new)} new menus/buttons")

# === Verify ===
print("\n=== System Config Menus ===")
cur.execute("SELECT id,name,`order` FROM sys_menu WHERE parent_id=%s AND is_deleted=0 AND name LIKE %s ORDER BY `order`", (SYS_ID, "%配置%"))
for r in cur.fetchall(): print(f"  {r[0]} | {r[1]} (order={r[2]})")

print("\n=== Example Menus ===")
cur.execute("SELECT id,name,type FROM sys_menu WHERE parent_id=%s AND is_deleted=0 ORDER BY `order`", (EXAMPLE_ID,))
for r in cur.fetchall(): print(f"  {r[0]} | [{r[2]}] {r[1]}")

print("\n=== OceanBase Menus ===")
cur.execute("SELECT id,name,`order` FROM sys_menu WHERE parent_id=%s AND is_deleted=0 ORDER BY `order`", (OB_DIR,))
for r in cur.fetchall(): print(f"  {r[0]} | {r[1]} (order={r[2]})")

print("\n=== DB Management ===")
cur.execute("SELECT id,name FROM sys_menu WHERE parent_id=100047 AND is_deleted=0 ORDER BY `order`")
for r in cur.fetchall(): print(f"  {r[0]} | {r[1]}")

conn.close()
