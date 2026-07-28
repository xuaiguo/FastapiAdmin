-- ============================================================
-- OceanBase Oracle 租户菜单数据插入脚本
-- 用途：向已有的 platform_menu 表中插入 OB Oracle 相关菜单
-- 执行前请确认数据库类型（MySQL）
-- ============================================================

-- ── 1. OB Oracle 配置管理（挂在"系统管理"目录下）──
SET @system_menu_id = (SELECT id FROM platform_menu WHERE name = '系统管理' AND type = 1 AND is_deleted = 0 LIMIT 1);

-- 插入"OB Oracle配置"菜单页面
INSERT INTO platform_menu (uuid, name, type, `order`, permission, icon, route_name, route_path, component_path, redirect, hidden, keep_alive, always_show, title, params, affix, client, link, is_iframe, is_hide_tab, active_path, show_badge, show_text_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time, created_id, updated_id, deleted_id, deleted_time, tenant_id)
VALUES (
    UUID(), 'OB Oracle配置', 2, 12, 'module_system:ob_oracle_config:query', 'ri:database-line',
    'ObOracleConfig', 'obOracleConfig', 'module_system/obOracleConfig/index', NULL,
    0, 1, 0, 'OB Oracle配置', NULL, 0, 'pc', NULL, 0, 0, NULL, 0, NULL, 'tenant',
    0, 'OceanBase Oracle租户连接配置管理', @system_menu_id,
    0, NOW(), NOW(), NULL, NULL, NULL, NULL, 1
);
SET @ob_config_id = LAST_INSERT_ID();

INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '新增', 3, 1, 'module_system:ob_oracle_config:create', 'tenant', 0, NULL, @ob_config_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '编辑', 3, 2, 'module_system:ob_oracle_config:update', 'tenant', 0, NULL, @ob_config_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '删除', 3, 3, 'module_system:ob_oracle_config:delete', 'tenant', 0, NULL, @ob_config_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '状态变更', 3, 4, 'module_system:ob_oracle_config:patch', 'tenant', 0, NULL, @ob_config_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '测试连接', 3, 5, 'module_system:ob_oracle_config:test', 'tenant', 0, NULL, @ob_config_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '详情', 3, 6, 'module_system:ob_oracle_config:detail', 'tenant', 0, NULL, @ob_config_id, 0, NOW(), NOW(), 1);


-- ── 2. OB Oracle 数据示例（挂在"案例管理"→"示例中心"目录下）──
SET @demo_center_id = (SELECT id FROM platform_menu WHERE name = '示例中心' AND type = 1 AND is_deleted = 0 LIMIT 1);

INSERT INTO platform_menu (uuid, name, type, `order`, permission, icon, route_name, route_path, component_path, redirect, hidden, keep_alive, always_show, title, params, affix, client, link, is_iframe, is_hide_tab, active_path, show_badge, show_text_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time, created_id, updated_id, deleted_id, deleted_time, tenant_id)
VALUES (
    UUID(), 'OB Oracle数据示例', 2, 5, 'module_ob_oracle_demo:demo:detail', 'ri:database-line',
    'ObOracleDemo', 'obOracleDemo', 'ob_oracle_demo/obOracleDemo/index', NULL,
    0, 1, 0, 'OB Oracle数据示例', NULL, 0, 'pc', NULL, 0, 0, NULL, 0, NULL, 'tenant',
    0, 'OceanBase Oracle租户CRUD示例', @demo_center_id,
    0, NOW(), NOW(), NULL, NULL, NULL, NULL, 1
);
SET @ob_demo_id = LAST_INSERT_ID();

INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '新增', 3, 1, 'module_ob_oracle_demo:demo:create', 'tenant', 0, NULL, @ob_demo_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '编辑', 3, 2, 'module_ob_oracle_demo:demo:update', 'tenant', 0, NULL, @ob_demo_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '删除', 3, 3, 'module_ob_oracle_demo:demo:delete', 'tenant', 0, NULL, @ob_demo_id, 0, NOW(), NOW(), 1);
INSERT INTO platform_menu (uuid, name, type, `order`, permission, scope, status, description, parent_id, is_deleted, created_time, updated_time, tenant_id)
VALUES (UUID(), '详情', 3, 4, 'module_ob_oracle_demo:demo:detail', 'tenant', 0, NULL, @ob_demo_id, 0, NOW(), NOW(), 1);


-- ── 3. 将菜单分配给超级管理员角色 ──
SET @admin_role_id = (SELECT id FROM platform_role WHERE name = '超级管理员' AND is_deleted = 0 LIMIT 1);

INSERT INTO platform_role_menu (role_id, menu_id, created_time, updated_time, is_deleted, tenant_id)
SELECT @admin_role_id, id, NOW(), NOW(), 0, 1
FROM platform_menu
WHERE permission LIKE 'module_system:ob_oracle_config:%'
   OR permission LIKE 'module_ob_oracle_demo:demo:%'
   OR name IN ('OB Oracle配置', 'OB Oracle数据示例');
