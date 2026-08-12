-- ============================================================
-- OB 租户表大小统计（ob_table_data_size）菜单插入脚本
-- 适配当前 sys_menu 表结构（去掉多租户，scope='web'）
-- 菜单挂在「OceanBase管理」目录（route_path='/oceanbase'）下
--
-- 表结构要点（实测验证）：
--   1. sys_menu 的 is_iframe / is_hide_tab / show_badge 为 NOT NULL 且无默认值，必须显式赋值
--   2. sys_role_menus 只有 (role_id, menu_id) 两列
--   3. 脚本含幂等防护，重复执行不会产生重复菜单
-- 执行前请确认已连接到正确的数据库
-- ============================================================

-- ── 0. 定位「OceanBase管理」目录 ──
SET @ob_dir_id = (
    SELECT id FROM sys_menu
    WHERE name = 'OceanBase管理' AND route_path = '/oceanbase' AND is_deleted = 0
    LIMIT 1
);

-- ── 1. 插入菜单（表大小统计，已存在则跳过） ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, is_iframe, is_hide_tab,
    show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), '表大小统计', 2,
    IFNULL((SELECT MAX(`order`) FROM sys_menu WHERE parent_id = @ob_dir_id AND is_deleted = 0), 0) + 1,
    'module_ob_table_data_size:size:query', 'ri:pie-chart-2-line',
    'ObTableDataSize', 'obTableDataSize', 'ob_table_data_size/obTableDataSize/index',
    0, 1, 0, '表大小统计', 0, 0, 0,
    0, 'web', 0, 'OceanBase 租户表大小统计', @ob_dir_id, 0, NOW(), NOW()
FROM DUAL
WHERE @ob_dir_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu
    WHERE permission = 'module_ob_table_data_size:size:query' AND type = 2 AND is_deleted = 0
);

-- 无论是否新插入，均按 permission 定位菜单 ID（保证幂等）
SET @menu_id = (
    SELECT id FROM sys_menu
    WHERE permission = 'module_ob_table_data_size:size:query' AND type = 2 AND is_deleted = 0
    LIMIT 1
);

-- ── 2. 插入查询按钮（已存在则跳过） ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, hidden, keep_alive, always_show,
    affix, is_iframe, is_hide_tab, show_badge, scope, status, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), '查询', 3, 1, 'module_ob_table_data_size:size:query', 0, 0, 0,
    0, 0, 0, 0, 'web', 0, @menu_id, 0, NOW(), NOW()
FROM DUAL
WHERE @menu_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu
    WHERE permission = 'module_ob_table_data_size:size:query' AND type = 3
      AND parent_id = @menu_id AND is_deleted = 0
);

-- ── 3. 分配给超级管理员角色（去重） ──
SET @admin_role_id = (SELECT id FROM sys_role WHERE name = '超级管理员' AND is_deleted = 0 LIMIT 1);

INSERT INTO sys_role_menus (role_id, menu_id)
SELECT @admin_role_id, id
FROM sys_menu
WHERE is_deleted = 0
  AND (id = @menu_id OR parent_id = @menu_id)
  AND id NOT IN (SELECT menu_id FROM sys_role_menus WHERE role_id = @admin_role_id);

-- ── 验证 ──
SELECT id, name, type, `order`, permission, parent_id
FROM sys_menu
WHERE id = @menu_id OR parent_id = @menu_id
ORDER BY type, `order`;
