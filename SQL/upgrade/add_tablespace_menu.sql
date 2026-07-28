-- ============================================================
-- Oracle 表空间查询模块 - 菜单配置 SQL
-- 在 MySQL 数据库中执行，添加"数据库管理"顶级菜单和"表空间查询"子菜单
-- 注意：需手动替换 UUID() 和 NOW() 或由应用层传入
-- ============================================================

-- 1. 插入顶级目录：数据库管理 (type=1)
INSERT INTO platform_menu (
    uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, redirect, hidden, keep_alive, always_show,
    title, params, affix, client, link, is_iframe, is_hide_tab,
    active_path, show_badge, show_text_badge, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '数据库管理', 1, 5, NULL, 'ri:database-line', 'DatabaseManagement', '/database',
    NULL, '/database/oracle_tablespace', 0, 1, 1,
    '数据库管理', NULL, 0, 'pc', NULL, 0, 0,
    NULL, 0, NULL, 'tenant', 0,
    '数据库管理模块', NULL, 0, NOW(), NOW()
);

-- 获取刚插入的父菜单 ID
SET @db_menu_id = LAST_INSERT_ID();

-- 2. 插入菜单页面：表空间查询 (type=2)
INSERT INTO platform_menu (
    uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, redirect, hidden, keep_alive, always_show,
    title, params, affix, client, link, is_iframe, is_hide_tab,
    active_path, show_badge, show_text_badge, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '表空间查询', 2, 1, 'module_oracle_tablespace:tablespace:query', 'ri:hard-drive-3-line',
    'OracleTablespace', 'oracle_tablespace',
    'oracle_tablespace/oracleTablespace/index', NULL, 0, 1, 0,
    '表空间查询', NULL, 0, 'pc', NULL, 0, 0,
    NULL, 0, NULL, 'tenant', 0,
    'Oracle 表空间使用率查询', @db_menu_id, 0, NOW(), NOW()
);

-- 获取表空间菜单 ID
SET @ts_menu_id = LAST_INSERT_ID();

-- 3. 插入按钮权限：查询 (type=3)
INSERT INTO platform_menu (
    uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, redirect, hidden, keep_alive, always_show,
    title, params, affix, client, link, is_iframe, is_hide_tab,
    active_path, show_badge, show_text_badge, scope, status,
    description, parent_id, is_deleted, created_time, updated_time
) VALUES (
    UUID(), '查询', 3, 1, 'module_oracle_tablespace:tablespace:query', NULL,
    NULL, NULL, NULL, NULL, 0, 1, 0,
    '查询', NULL, 0, 'pc', NULL, 0, 0,
    NULL, 0, NULL, 'tenant', 0,
    '查询表空间', @ts_menu_id, 0, NOW(), NOW()
);

-- 验证插入结果
SELECT id, name, type, `order`, permission, parent_id
FROM platform_menu
WHERE name IN ('数据库管理', '表空间查询')
   OR parent_id = @ts_menu_id
ORDER BY parent_id, `order`;
