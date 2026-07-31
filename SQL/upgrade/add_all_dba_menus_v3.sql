-- ============================================================
-- FastapiAdmin v3.0.0 自定义 DBA 模块菜单插入脚本
-- 适配新版 sys_menu 表结构（去掉多租户，scope='web'）
-- 执行前请确认已连接到正确的数据库
-- ============================================================

-- ── 0. 创建"数据库管理"顶级目录 ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, redirect, hidden, keep_alive, always_show,
    title, params, affix, link, is_iframe, is_hide_tab,
    active_path, show_badge, show_text_badge, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '数据库管理', 1, 5, NULL, 'ri:database-line', 'DatabaseManagement', '/database',
    NULL, '/database/oracle_config', 0, 1, 1,
    '数据库管理', NULL, 0, NULL, 0, 0,
    NULL, 0, NULL, 'web', 0,
    '多数据源 DBA 管理模块', NULL, 0, NOW(), NOW()
);
SET @db_mgmt_id = LAST_INSERT_ID();


-- ── 1. Oracle 配置管理 ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'Oracle配置', 2, 1, 'module_system:oracle_config:query', 'ri:database-line',
    'OracleConfig', 'oracle_config', 'module_system/oracleConfig/index',
    0, 1, 0, 'Oracle配置', 0, 'web', 0,
    'Oracle 数据库连接配置管理', @db_mgmt_id, 0, NOW(), NOW()
);
SET @ora_cfg_id = LAST_INSERT_ID();
INSERT INTO sys_menu (uuid, name, type, `order`, permission, scope, status, parent_id, is_deleted, created_time, updated_time) VALUES
(UUID(), '新增', 3, 1, 'module_system:oracle_config:create', 'web', 0, @ora_cfg_id, 0, NOW(), NOW()),
(UUID(), '编辑', 3, 2, 'module_system:oracle_config:update', 'web', 0, @ora_cfg_id, 0, NOW(), NOW()),
(UUID(), '删除', 3, 3, 'module_system:oracle_config:delete', 'web', 0, @ora_cfg_id, 0, NOW(), NOW()),
(UUID(), '状态变更', 3, 4, 'module_system:oracle_config:patch', 'web', 0, @ora_cfg_id, 0, NOW(), NOW()),
(UUID(), '测试连接', 3, 5, 'module_system:oracle_config:test', 'web', 0, @ora_cfg_id, 0, NOW(), NOW()),
(UUID(), '详情', 3, 6, 'module_system:oracle_config:detail', 'web', 0, @ora_cfg_id, 0, NOW(), NOW());


-- ── 2. MySQL 配置管理 ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'MySQL配置', 2, 2, 'module_system:mysql_config:query', 'ri:database-line',
    'MysqlConfig', 'mysqlConfig', 'module_system/mysqlConfig/index',
    0, 1, 0, 'MySQL配置', 0, 'web', 0,
    'MySQL 数据库连接配置管理', @db_mgmt_id, 0, NOW(), NOW()
);
SET @mysql_cfg_id = LAST_INSERT_ID();
INSERT INTO sys_menu (uuid, name, type, `order`, permission, scope, status, parent_id, is_deleted, created_time, updated_time) VALUES
(UUID(), '新增', 3, 1, 'module_system:mysql_config:create', 'web', 0, @mysql_cfg_id, 0, NOW(), NOW()),
(UUID(), '编辑', 3, 2, 'module_system:mysql_config:update', 'web', 0, @mysql_cfg_id, 0, NOW(), NOW()),
(UUID(), '删除', 3, 3, 'module_system:mysql_config:delete', 'web', 0, @mysql_cfg_id, 0, NOW(), NOW()),
(UUID(), '状态变更', 3, 4, 'module_system:mysql_config:patch', 'web', 0, @mysql_cfg_id, 0, NOW(), NOW()),
(UUID(), '测试连接', 3, 5, 'module_system:mysql_config:test', 'web', 0, @mysql_cfg_id, 0, NOW(), NOW()),
(UUID(), '详情', 3, 6, 'module_system:mysql_config:detail', 'web', 0, @mysql_cfg_id, 0, NOW(), NOW());


-- ── 3. OB Oracle 配置管理 ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'OB Oracle配置', 2, 3, 'module_system:ob_oracle_config:query', 'ri:database-line',
    'ObOracleConfig', 'obOracleConfig', 'module_system/obOracleConfig/index',
    0, 1, 0, 'OB Oracle配置', 0, 'web', 0,
    'OceanBase Oracle 连接配置管理', @db_mgmt_id, 0, NOW(), NOW()
);
SET @ob_cfg_id = LAST_INSERT_ID();
INSERT INTO sys_menu (uuid, name, type, `order`, permission, scope, status, parent_id, is_deleted, created_time, updated_time) VALUES
(UUID(), '新增', 3, 1, 'module_system:ob_oracle_config:create', 'web', 0, @ob_cfg_id, 0, NOW(), NOW()),
(UUID(), '编辑', 3, 2, 'module_system:ob_oracle_config:update', 'web', 0, @ob_cfg_id, 0, NOW(), NOW()),
(UUID(), '删除', 3, 3, 'module_system:ob_oracle_config:delete', 'web', 0, @ob_cfg_id, 0, NOW(), NOW()),
(UUID(), '状态变更', 3, 4, 'module_system:ob_oracle_config:patch', 'web', 0, @ob_cfg_id, 0, NOW(), NOW()),
(UUID(), '测试连接', 3, 5, 'module_system:ob_oracle_config:test', 'web', 0, @ob_cfg_id, 0, NOW(), NOW()),
(UUID(), '详情', 3, 6, 'module_system:ob_oracle_config:detail', 'web', 0, @ob_cfg_id, 0, NOW(), NOW());


-- ── 4. OB 模块管理 ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'OB模块管理', 2, 4, 'module_system:ob_module:query', 'ri:apps-line',
    'ObModule', 'obModule', 'system/obModule/index',
    0, 1, 0, 'OB模块管理', 0, 'web', 0,
    'OceanBase 模块与数据源分配管理', @db_mgmt_id, 0, NOW(), NOW()
);
SET @ob_mod_id = LAST_INSERT_ID();
INSERT INTO sys_menu (uuid, name, type, `order`, permission, scope, status, parent_id, is_deleted, created_time, updated_time) VALUES
(UUID(), '新增', 3, 1, 'module_system:ob_module:create', 'web', 0, @ob_mod_id, 0, NOW(), NOW()),
(UUID(), '编辑', 3, 2, 'module_system:ob_module:update', 'web', 0, @ob_mod_id, 0, NOW(), NOW()),
(UUID(), '删除', 3, 3, 'module_system:ob_module:delete', 'web', 0, @ob_mod_id, 0, NOW(), NOW());


-- ── 5. OceanBase DBA 工具（挂在"数据库管理"下） ──

-- SQL 查询
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'SQL查询', 2, 10, 'module_ob_oracle_query:query:detail', 'ri:terminal-box-line',
    'ObOracleQuery', 'obOracleQuery', 'ob_oracle_query/obOracleQuery/index',
    0, 1, 0, 'SQL查询', 0, 'web', 0,
    'OceanBase Oracle SQL 查询控制台', @db_mgmt_id, 0, NOW(), NOW()
);

-- 进程列表
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '进程列表', 2, 11, 'module_ob_processlist:processlist:query', 'ri:process-line',
    'ObProcesslist', 'obProcesslist', 'ob_processlist/obProcesslist/index',
    0, 1, 0, '进程列表', 0, 'web', 0,
    'OceanBase 实时进程/会话列表', @db_mgmt_id, 0, NOW(), NOW()
);

-- SQL 审计
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'SQL审计', 2, 12, 'module_ob_sql_audit:audit:query', 'ri:shield-check-line',
    'ObSqlAudit', 'obSqlAudit', 'ob_sql_audit/obSqlAudit/index',
    0, 1, 0, 'SQL审计', 0, 'web', 0,
    'OceanBase SQL 审计日志', @db_mgmt_id, 0, NOW(), NOW()
);

-- SQL 统计（当前）
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'SQL统计(当前)', 2, 13, 'module_ob_sqlstat_cur:sqlstat:query', 'ri:bar-chart-line',
    'ObSqlstatCur', 'obSqlstatCur', 'ob_sqlstat_cur/obSqlstatCur/index',
    0, 1, 0, 'SQL统计(当前)', 0, 'web', 0,
    'OceanBase 当前 SQL 性能统计', @db_mgmt_id, 0, NOW(), NOW()
);

-- SQL 统计(WR)
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'SQL统计(WR)', 2, 14, 'module_ob_wr_sqlstat:sqlstat:query', 'ri:line-chart-line',
    'ObWrSqlstat', 'obWrSqlstat', 'ob_wr_sqlstat/obWrSqlstat/index',
    0, 1, 0, 'SQL统计(WR)', 0, 'web', 0,
    'OceanBase Workload Repository SQL 统计', @db_mgmt_id, 0, NOW(), NOW()
);

-- 调度任务
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '调度任务', 2, 15, 'module_ob_scheduler_jobs:jobs:query', 'ri:time-line',
    'ObSchedulerJobs', 'obSchedulerJobs', 'ob_scheduler_jobs/obSchedulerJobs/index',
    0, 1, 0, '调度任务', 0, 'web', 0,
    'OceanBase 调度任务管理', @db_mgmt_id, 0, NOW(), NOW()
);

-- 分区表分析
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '分区表分析', 2, 16, 'module_ob_partition_tab_analyze:analyze:query', 'ri:table-line',
    'ObPartitionTabAnalyze', 'obPartitionTabAnalyze', 'ob_partition_tab_analyze/obPartitionTabAnalyze/index',
    0, 1, 0, '分区表分析', 0, 'web', 0,
    'OceanBase 分区表分析', @db_mgmt_id, 0, NOW(), NOW()
);


-- ── 6. Oracle DBA 工具 ──

-- Oracle 会话管理
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), 'Oracle会话', 2, 20, 'module_oracle_session:demo:query', 'ri:user-search-line',
    'OracleSession', 'oracleSession', 'oracle_session/oracleSession/index',
    0, 1, 0, 'Oracle会话', 0, 'web', 0,
    'Oracle 会话管理', @db_mgmt_id, 0, NOW(), NOW()
);

-- Oracle 表空间
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '表空间查询', 2, 21, 'module_oracle_tablespace:tablespace:query', 'ri:hard-drive-3-line',
    'OracleTablespace', 'oracle_tablespace', 'oracle_tablespace/oracleTablespace/index',
    0, 1, 0, '表空间查询', 0, 'web', 0,
    'Oracle 表空间使用率查询', @db_mgmt_id, 0, NOW(), NOW()
);


-- ── 7. 将所有新菜单分配给超级管理员角色 ──
SET @admin_role_id = (SELECT id FROM sys_role WHERE name = '超级管理员' AND is_deleted = 0 LIMIT 1);

INSERT INTO sys_role_menus (role_id, menu_id, created_time, updated_time, is_deleted)
SELECT @admin_role_id, id, NOW(), NOW(), 0
FROM sys_menu
WHERE is_deleted = 0
  AND (
    parent_id = @db_mgmt_id
    OR id = @db_mgmt_id
    OR parent_id IN (SELECT id FROM sys_menu WHERE parent_id = @db_mgmt_id AND type = 2)
  );


-- ── 验证 ──
SELECT id, name, type, `order`, permission, parent_id
FROM sys_menu
WHERE parent_id = @db_mgmt_id OR id = @db_mgmt_id
ORDER BY `order`;
