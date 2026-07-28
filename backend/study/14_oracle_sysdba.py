"""
=============================================================
Oracle SYSDBA 特权连接学习案例
=============================================================

在 Oracle 数据库中，SYS 用户拥有最高权限（类似 Linux 的 root）。
通过 SYSDBA 模式连接可以执行管理操作：创建/删除用户、管理表空间、查看动态性能视图等。

在 FastapiAdmin 中，Oracle 连接模块位于:
  - app/core/oracle/database.py  — OracleManager（单例，管理连接池）
  - app/core/oracle/dependencies.py — FastAPI 依赖注入
  - app/api/v1/module_system/oracle_config/ — 连接配置管理

官方文档: https://python-oracledb.readthedocs.io/en/latest/

安装: pip install oracledb  (Thin 模式，无需 Oracle Client)

运行方式:
    python 14_oracle_sysdba.py

对应 sqlplus 命令:
    sqlplus sys/123456@192.168.190.135:1521/MYCDB as sysdba

本文件演示:
  1. oracledb Thin 模式 SYSDBA 直连
  2. SYSDBA 常用管理查询（版本、表空间、会话、参数）
  3. SQLAlchemy async engine + SYSDBA
  4. asyncio.to_thread 包装同步连接（与项目 test_connection 一致）
  5. SYSDBA 连接池
  6. 错误处理与常见问题
"""

import asyncio
import traceback

import oracledb
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# ============================================================
# 连接参数（根据你的 Oracle 环境修改）
# ============================================================
ORACLE_HOST = "192.168.190.135"
ORACLE_PORT = 1521
ORACLE_SERVICE = "MYCDB"
ORACLE_USER = "sys"
ORACLE_PASSWORD = "123456"

# DSN（Data Source Name）— 对应 sqlplus 中 @ 后面的部分
# sqlplus: sqlplus sys/123456@192.168.190.135:1521/MYCDB as sysdba
# Python:  dsn="192.168.190.135:1521/MYCDB"
ORACLE_DSN = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"


# ============================================================
# 1. oracledb Thin 模式 SYSDBA 直连
# ============================================================
def demo_basic_sysdba_connection():
    """
    🔐 最基本的 SYSDBA 连接。

    关键点:
    - mode=oracledb.AUTH_MODE_SYSDBA  等价于 sqlplus 的 "as sysdba"
    - Thin 模式无需安装 Oracle Client（默认就是 Thin 模式）
    - 连接后 conn 对象可直接执行 SQL

    参数映射对照:
    ┌──────────────────────────────────────────────────────────────┐
    │ sqlplus                                    │ Python          │
    ├──────────────────────────────────────────────────────────────┤
    │ sqlplus sys/123456@host:port/SVC as sysdba │                 │
    │   user     = sys                           │ user="sys"      │
    │   password = 123456                        │ password="..."  │
    │   @host:port/SVC                           │ dsn="host:..."  │
    │   as sysdba                                │ mode=AUTH_MODE_ │
    │                                            │   SYSDBA        │
    └──────────────────────────────────────────────────────────────┘
    """
    print("\n===== 1. 基本 SYSDBA 连接 =====\n")

    conn = oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN,
        mode=oracledb.AUTH_MODE_SYSDBA,  # 🔑 关键: 以 SYSDBA 身份连接
    )

    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM DUAL")
    result = cursor.fetchone()
    print(f"✅ 连接成功! SELECT 1 FROM DUAL = {result[0]}")

    # 验证当前用户和权限
    cursor.execute("SELECT USER FROM DUAL")
    print(f"当前用户: {cursor.fetchone()[0]}")

    cursor.execute("SELECT SYS_CONTEXT('USERENV', 'ISDBA') FROM DUAL")
    print(f"是否 SYSDBA: {cursor.fetchone()[0]}")

    cursor.close()
    conn.close()
    print("连接已关闭。")


# ============================================================
# 2. SYSDBA 常用管理查询
# ============================================================
def demo_sysdba_queries():
    """
    📖 SYSDBA 可以查询普通用户无法访问的动态性能视图（v$xxx）和 DBA 视图。

    常用场景:
    - v$version: 数据库版本信息
    - dba_tablespaces: 表空间信息（FastapiAdmin 表空间模块就查这个）
    - v$session: 当前会话信息
    - v$parameter: 数据库初始化参数
    """
    print("\n===== 2. SYSDBA 常用查询 =====\n")

    conn = oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN,
        mode=oracledb.AUTH_MODE_SYSDBA,
    )
    cursor = conn.cursor()

    # --- 2.1 数据库版本 ---
    print("【数据库版本】")
    cursor.execute("SELECT banner FROM v$version WHERE ROWNUM <= 3")
    for row in cursor.fetchall():
        print(f"  {row[0]}")

    # --- 2.2 表空间概览（与 FastapiAdmin 表空间查询模块对应） ---
    # 对应 app/plugin/module_oracle_tablespace/tablespace/crud.py
    print("\n【表空间概览】")
    cursor.execute("""
        SELECT
            t.tablespace_name,
            t.status,
            ROUND(SUM(d.bytes) / 1024 / 1024, 2) AS total_mb
        FROM dba_tablespaces t
        JOIN dba_data_files d ON t.tablespace_name = d.tablespace_name
        GROUP BY t.tablespace_name, t.status
        ORDER BY total_mb DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<20s} 状态={row[1]:<10s} 大小={row[2]} MB")

    # --- 2.3 活跃会话 ---
    print("\n【活跃会话（前5个）】")
    cursor.execute("""
        SELECT sid, serial#, username, status, program
        FROM v$session
        WHERE type = 'USER' AND status = 'ACTIVE'
        ORDER BY logon_time DESC
        FETCH FIRST 5 ROWS ONLY
    """)
    for row in cursor.fetchall():
        print(f"  SID={row[0]} Serial={row[1]} 用户={row[2]} 状态={row[3]} 程序={row[4]}")

    # --- 2.4 数据库参数 ---
    print("\n【关键数据库参数】")
    cursor.execute("""
        SELECT name, value
        FROM v$parameter
        WHERE name IN ('db_name', 'db_unique_name', 'compatible',
                       'sga_target', 'pga_aggregate_target', 'processes')
        ORDER BY name
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<30s} = {row[1]}")

    cursor.close()
    conn.close()


# ============================================================
# 3. SQLAlchemy async engine + SYSDBA
# ============================================================
async def demo_sqlalchemy_async_sysdba():
    """
    🔗 通过 SQLAlchemy 异步引擎以 SYSDBA 身份连接。

    与 FastapiAdmin 的 OracleManager (app/core/oracle/database.py) 类似,
    区别在于:
    - 项目用 create_async_engine(url) 不带 SYSDBA
    - 这里通过 connect_args={"mode": ...} 传入 SYSDBA 模式

    SQLAlchemy URL 格式:
        oracle+oracledb://user:password@host:port/?service_name=SVC
    """
    print("\n===== 3. SQLAlchemy async engine + SYSDBA =====\n")

    # 构建 SQLAlchemy 连接 URL
    # 注意: 与 oracledb 直连的 DSN 格式略有不同
    # oracledb DSN:     "host:port/service_name"
    # SQLAlchemy URL:   "oracle+oracledb://user:pass@host:port/?service_name=SVC"
    url = (
        f"oracle+oracledb://{ORACLE_USER}:{ORACLE_PASSWORD}"
        f"@{ORACLE_HOST}:{ORACLE_PORT}/?service_name={ORACLE_SERVICE}"
    )

    engine = create_async_engine(
        url,
        # 🔑 connect_args 会传递给底层 oracledb.connect()
        connect_args={"mode": oracledb.AUTH_MODE_SYSDBA},
        echo=False,  # 设为 True 可看到生成的 SQL
    )

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_factory() as session:
        # 查询版本
        result = await session.execute(text("SELECT banner FROM v$version WHERE ROWNUM <= 2"))
        for row in result.fetchall():
            print(f"  版本: {row[0]}")

        # 查询表空间（与项目表空间模块查询类似）
        result = await session.execute(text("""
            SELECT tablespace_name, status
            FROM dba_tablespaces
            ORDER BY tablespace_name
        """))
        print("\n  表空间列表:")
        for row in result.fetchall():
            print(f"    {row[0]:<20s} {row[1]}")

    await engine.dispose()
    print("\n✅ 异步引擎已关闭。")


# ============================================================
# 4. asyncio.to_thread 包装同步连接
# ============================================================
async def demo_async_to_thread():
    """
    🔄 与 FastapiAdmin 的 test_connection() 一致的模式。

    oracledb.connect() 是同步阻塞调用，在 async 函数中直接调用会阻塞事件循环。
    使用 asyncio.to_thread() 将同步调用放到线程池执行。

    对应文件: app/api/v1/module_system/oracle_config/service.py
    中的 test_connection() 方法
    """
    print("\n===== 4. asyncio.to_thread 包装同步连接 =====\n")

    def _sync_connect_and_query():
        """在线程池中执行的同步函数"""
        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            mode=oracledb.AUTH_MODE_SYSDBA,
            tcp_connect_timeout=5,  # 连接超时5秒
        )
        cursor = conn.cursor()

        # 执行一个管理查询
        cursor.execute("SELECT COUNT(*) FROM v$session WHERE type = 'USER'")
        active_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM v$tablespace")
        ts_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()
        return active_count, ts_count

    # 🔑 关键: 用 to_thread 包装同步调用
    active_sessions, tablespace_count = await asyncio.to_thread(_sync_connect_and_query)

    print(f"  当前用户会话数: {active_sessions}")
    print(f"  表空间数量: {tablespace_count}")
    print("✅ 异步包装调用完成（不阻塞事件循环）。")


# ============================================================
# 5. SYSDBA 连接池
# ============================================================
def demo_sysdba_pool():
    """
    🏊 使用连接池管理 SYSDBA 连接，提高性能。

    与 FastapiAdmin 的 OracleManager (app/core/oracle/database.py) 类似,
    OracleManager 使用 SQLAlchemy 的 create_async_engine 内置连接池,
    这里演示直接使用 oracledb 的连接池。

    连接池参数:
    - min: 最小连接数（池初始化时创建的连接数）
    - max: 最大连接数（池允许的最大连接数）
    - increment: 每次扩展时新增的连接数
    """
    print("\n===== 5. SYSDBA 连接池 =====\n")

    pool = oracledb.create_pool(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN,
        mode=oracledb.AUTH_MODE_SYSDBA,
        min=2,       # 最小连接数
        max=5,       # 最大连接数
        increment=1, # 每次扩展增加1个连接
    )

    print(f"  连接池已创建: min={pool.min}, max={pool.max}, 当前打开={pool.opened}")

    # 从池中获取连接执行查询
    conn = pool.acquire()
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello from pool!' FROM DUAL")
    print(f"  查询结果: {cursor.fetchone()[0]}")
    cursor.close()
    pool.release(conn)  # 归还连接到池（不是关闭）

    # 可以并发获取多个连接
    connections = [pool.acquire() for _ in range(3)]
    print(f"  获取3个连接后: 当前打开={pool.opened}")

    # 归还所有连接
    for c in connections:
        pool.release(c)

    pool.close()
    print("✅ 连接池已关闭。")


# ============================================================
# 6. 错误处理
# ============================================================
def demo_error_handling():
    """
    ⚠️ SYSDBA 连接常见错误及处理方式。

    常见 Oracle 错误码:
    - ORA-01017: invalid username/password  — 用户名或密码错误
    - ORA-01031: insufficient privileges     — 权限不足（非 SYSDBA 用户尝试 sysdba 连接）
    - ORA-12154: TNS:could not resolve       — DSN 格式错误或服务名不存在
    - ORA-12541: TNS:no listener             — 监听器未启动或地址错误
    - ORA-12543: TNS:destination host unreachable — 网络不通
    - ORA-28009: connection as SYS should be as SYSDBA — 用 SYS 连接但没加 SYSDBA 模式
    """
    print("\n===== 6. 错误处理 =====\n")

    # --- 6.1 密码错误 ---
    print("【测试: 密码错误】")
    try:
        oracledb.connect(
            user="sys",
            password="wrong_password",
            dsn=ORACLE_DSN,
            mode=oracledb.AUTH_MODE_SYSDBA,
        )
    except oracledb.DatabaseError as e:
        error_obj = e.args[0]
        print(f"  ❌ ORA-{error_obj.code}: {error_obj.message}")
        if error_obj.code == 1017:
            print("  💡 提示: 请检查用户名和密码是否正确")

    # --- 6.2 网络不通 ---
    print("\n【测试: 网络不通（假地址）】")
    try:
        oracledb.connect(
            user="sys",
            password="123456",
            dsn="192.0.2.1:1521/NONEXIST",  # 不可达地址
            mode=oracledb.AUTH_MODE_SYSDBA,
            tcp_connect_timeout=3,  # 缩短超时加快演示
        )
    except oracledb.DatabaseError as e:
        error_obj = e.args[0]
        print(f"  ❌ ORA-{error_obj.code}: {error_obj.message}")
        print("  💡 提示: 请检查主机地址、端口和防火墙设置")
    except TimeoutError:
        print("  ❌ 连接超时")
        print("  💡 提示: 网络不通或监听器未启动")

    # --- 6.3 忘记 SYSDBA 模式 ---
    print("\n【测试: SYS 用户不加 SYSDBA 模式】")
    try:
        oracledb.connect(
            user="sys",
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            # ⚠️ 故意不加 mode=oracledb.AUTH_MODE_SYSDBA
        )
    except oracledb.DatabaseError as e:
        error_obj = e.args[0]
        print(f"  ❌ ORA-{error_obj.code}: {error_obj.message}")
        if error_obj.code == 28009:
            print("  💡 提示: SYS 用户必须以 SYSDBA 或 SYSOPER 身份连接")
            print("         加上 mode=oracledb.AUTH_MODE_SYSDBA 即可")

    print("\n✅ 错误处理演示完成。")


# ============================================================
# 主程序
# ============================================================
async def main():
    """运行所有演示。"""
    print("╔══════════════════════════════════════════════════════╗")
    print("║  Oracle SYSDBA 连接学习案例                          ║")
    print("║  对应 sqlplus: sys/123456@host:port/SVC as sysdba   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"\n连接信息: {ORACLE_USER}@{ORACLE_DSN} (SYSDBA)")

    # === 同步演示 ===
    try:
        demo_basic_sysdba_connection()
        demo_sysdba_queries()
        demo_sysdba_pool()
        demo_error_handling()
    except oracledb.DatabaseError as e:
        print(f"\n❌ 连接失败: {e}")
        print("请检查 Oracle 数据库是否可访问，以及连接参数是否正确。")
        traceback.print_exc()
        return

    # === 异步演示 ===
    try:
        await demo_sqlalchemy_async_sysdba()
        await demo_async_to_thread()
    except Exception as e:
        print(f"\n❌ 异步演示失败: {e}")
        traceback.print_exc()

    print("\n" + "=" * 56)
    print("🎉 所有演示完成！")
    print("=" * 56)


if __name__ == "__main__":
    asyncio.run(main())
