---
name: ob-module-dev
description: 在 FastapiAdmin 项目中开发 OceanBase（Oracle 模式）功能模块的完整指南。当用户需要新建、修改或排查 OB 相关插件模块（module_ob_*）时使用，涵盖 CRUD 型与查询型两种架构、同步/异步调用规范、数据源配置与前端约定。
---

# OceanBase 模块开发技能

## 适用场景

- 新建 OceanBase 功能模块（后端插件 + 前端页面）
- 修改现有 `module_ob_*` 模块
- 排查 OB 模块的连接、异步调用、路由命名问题

## 核心技术约定（必须遵守）

1. **数据库驱动**：OB 模块统一使用 `cx_Oracle` 驱动（仅支持同步操作）
2. **异步包装**：service / crud 层使用同步方法（`def`），controller 层使用异步方法（`async def`），并通过 `await asyncio.to_thread(同步方法)` 包装调用
3. **连接配置**：从 MySQL 元数据库的 `sys_ob_oracle_config` 表按 `config_id` 动态加载 OB 连接信息，不允许硬编码连接串
4. **命名规则**：前端 API 和服务路径以 `ob_{name}` 命名（不带 `module_` 前缀）
5. **前端要求**：所有 OB 页面必须包含 `config_id` 数据源选择器

## 模块两种类型

### Type A：CRUD 型模块
操作 OB 中的业务表，参考 `backend/app/plugin/module_ob_oracle_demo/`

```
module_ob_xxx/
├── __init__.py
└── xxx/
    ├── controller.py   # async def 路由，含 /init_tables 初始化接口
    ├── crud.py         # 同步方法（def）
    ├── model.py        # SQLAlchemy 模型（CRUD 型独有）
    ├── schema.py       # Pydantic schema
    └── service.py      # 同步方法（def）
```
- 必须提供 `/init_tables` 接口用于初始化业务表

### Type B：纯查询型模块
直接查询 OB 系统视图（如 GV$OB_PROCESSLIST、DBA_SQL_AUDIT 等），**无 model.py**，参考 `backend/app/plugin/module_ob_processlist/`

```
module_ob_xxx/
├── __init__.py
└── xxx/
    ├── controller.py   # async def 路由
    ├── crud.py         # 同步方法，执行原生 SQL 查系统视图
    ├── schema.py
    └── service.py      # 同步方法
```

现有查询型模块参考：`module_ob_processlist`、`module_ob_sql_audit`、`module_ob_scheduler_jobs`、`module_ob_sqlstat_cur`、`module_ob_wr_sqlstat`、`module_ob_partition_tab_analyze`、`module_ob_oracle_query`

## 开发步骤

### 1. 确定模块类型
- 需要维护业务表数据 → Type A（CRUD 型）
- 只读查询系统视图 → Type B（查询型）

### 2. 后端实现
1. 在 `backend/app/plugin/` 下创建 `module_ob_{name}/` 目录，按上面对应结构建文件
2. crud/service 写同步方法，接收 `config_id` 参数并动态获取 OB 连接
3. controller 写异步路由：`result = await asyncio.to_thread(service.xxx, config_id, ...)`
4. Type A 模块额外实现 `/init_tables` 路由

### 3. 前端实现
1. API 与服务路径使用 `ob_{name}` 命名（无 `module_` 前缀）
2. 页面顶部添加 `config_id` 数据源选择器（数据来源：OB 连接配置管理页面）
3. 查询前先确认已选择数据源

### 4. 菜单与权限
参考 `SQL/upgrade/add_ob_oracle_menus.sql`，为新模块添加菜单 SQL 并分配权限

## 常见错误（避坑）

- ❌ 在 service/crud 中使用 `async def` → cx_Oracle 不支持异步，必须同步 + `to_thread`
- ❌ controller 直接调用同步方法不加 `asyncio.to_thread` → 阻塞事件循环
- ❌ 硬编码 OB 连接串 → 必须走 `sys_ob_oracle_config` + `config_id`
- ❌ 前端路径加 `module_` 前缀 → 约定为 `ob_{name}`
- ❌ 页面缺少数据源选择器 → 所有 OB 页面必须带 `config_id` 选择
