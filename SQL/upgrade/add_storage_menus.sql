-- ============================================================
-- 数据存储（module_storage）菜单插入脚本
-- 适配当前 sys_menu 表结构（scope='web'）
-- 包含：数据存储目录 + 存储源管理 / 文件管理 / 传输任务 及各自按钮，共 16 个节点
--
-- 表结构要点（实测验证）：
--   1. sys_menu 的 is_iframe / is_hide_tab / show_badge 为 NOT NULL 且无默认值，必须显式赋值
--   2. sys_role_menus 只有 (role_id, menu_id) 两列
--   3. 脚本含幂等防护，重复执行不会产生重复菜单
-- 执行前请确认已连接到正确的数据库
-- ============================================================

-- ── 1. 插入「数据存储」目录（已存在则跳过） ──
INSERT INTO sys_menu (uuid, name, type, `order`, icon, route_name, route_path,
    component_path, redirect, hidden, keep_alive, always_show, title, affix,
    is_iframe, is_hide_tab, show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), '数据存储', 1, 8, 'ri:database-2-line', 'Storage', '/storage',
    NULL, '/storage/source', 0, 1, 0, '数据存储', 0,
    0, 0, 0, 'web', 0, '数据存储', NULL, 0, NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM sys_menu
    WHERE route_path = '/storage' AND type = 1 AND is_deleted = 0
);

SET @storage_dir_id = (
    SELECT id FROM sys_menu
    WHERE route_path = '/storage' AND type = 1 AND is_deleted = 0
    LIMIT 1
);

-- ── 2. 插入三个功能菜单（已存在则跳过） ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, is_iframe, is_hide_tab,
    show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), '存储源管理', 2, 1, 'module_storage:source:query', 'ri:hard-drive-3-line',
    'StorageSource', 'source', 'module_storage/source/index',
    0, 1, 0, '存储源管理', 0, 0, 0,
    0, 'web', 0, '存储源管理', @storage_dir_id, 0, NOW(), NOW()
FROM DUAL
WHERE @storage_dir_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu
    WHERE permission = 'module_storage:source:query' AND type = 2 AND is_deleted = 0
);

INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, is_iframe, is_hide_tab,
    show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), '文件管理', 2, 2, 'module_storage:file:query', 'ri:folder-open-line',
    'StorageFile', 'file', 'module_storage/file/index',
    0, 1, 0, '文件管理', 0, 0, 0,
    0, 'web', 0, '存储文件管理', @storage_dir_id, 0, NOW(), NOW()
FROM DUAL
WHERE @storage_dir_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu
    WHERE permission = 'module_storage:file:query' AND type = 2 AND is_deleted = 0
);

INSERT INTO sys_menu (uuid, name, type, `order`, permission, icon, route_name, route_path,
    component_path, hidden, keep_alive, always_show, title, affix, is_iframe, is_hide_tab,
    show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), '传输任务', 2, 3, 'module_storage:transfer:query', 'ri:swap-transfer-line',
    'StorageTransfer', 'transfer', 'module_storage/transfer/index',
    0, 1, 0, '传输任务', 0, 0, 0,
    0, 'web', 0, '文件传输与工作流', @storage_dir_id, 0, NOW(), NOW()
FROM DUAL
WHERE @storage_dir_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu
    WHERE permission = 'module_storage:transfer:query' AND type = 2 AND is_deleted = 0
);

-- ── 3. 定位三个菜单 ID ──
SET @source_id = (SELECT id FROM sys_menu WHERE permission = 'module_storage:source:query' AND type = 2 AND is_deleted = 0 LIMIT 1);
SET @file_id = (SELECT id FROM sys_menu WHERE permission = 'module_storage:file:query' AND type = 2 AND is_deleted = 0 LIMIT 1);
SET @transfer_id = (SELECT id FROM sys_menu WHERE permission = 'module_storage:transfer:query' AND type = 2 AND is_deleted = 0 LIMIT 1);

-- ── 4. 插入存储源管理按钮（已存在则跳过） ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, hidden, keep_alive, always_show,
    title, affix, is_iframe, is_hide_tab, show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), t.name, 3, t.ord, t.perm, 0, 1, 0, t.name, 0, 0, 0, 0, 'web', 0, t.name, @source_id, 0, NOW(), NOW()
FROM (
    SELECT '存储源查询' AS name, 1 AS ord, 'module_storage:source:query' AS perm
    UNION ALL SELECT '存储源新增', 2, 'module_storage:source:create'
    UNION ALL SELECT '存储源修改', 3, 'module_storage:source:update'
    UNION ALL SELECT '存储源删除', 4, 'module_storage:source:delete'
) t
WHERE @source_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu m
    WHERE m.permission = t.perm AND m.type = 3 AND m.parent_id = @source_id AND m.is_deleted = 0
);

-- ── 5. 插入文件管理按钮（已存在则跳过） ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, hidden, keep_alive, always_show,
    title, affix, is_iframe, is_hide_tab, show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), t.name, 3, t.ord, t.perm, 0, 1, 0, t.name, 0, 0, 0, 0, 'web', 0, t.name, @file_id, 0, NOW(), NOW()
FROM (
    SELECT '文件查询' AS name, 1 AS ord, 'module_storage:file:query' AS perm
    UNION ALL SELECT '文件上传', 2, 'module_storage:file:upload'
    UNION ALL SELECT '文件下载', 3, 'module_storage:file:download'
    UNION ALL SELECT '文件删除', 4, 'module_storage:file:delete'
) t
WHERE @file_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu m
    WHERE m.permission = t.perm AND m.type = 3 AND m.parent_id = @file_id AND m.is_deleted = 0
);

-- ── 6. 插入传输任务按钮（已存在则跳过） ──
INSERT INTO sys_menu (uuid, name, type, `order`, permission, hidden, keep_alive, always_show,
    title, affix, is_iframe, is_hide_tab, show_badge, scope, status, description, parent_id, is_deleted, created_time, updated_time
)
SELECT UUID(), t.name, 3, t.ord, t.perm, 0, 1, 0, t.name, 0, 0, 0, 0, 'web', 0, t.name, @transfer_id, 0, NOW(), NOW()
FROM (
    SELECT '传输任务查询' AS name, 1 AS ord, 'module_storage:transfer:query' AS perm
    UNION ALL SELECT '传输任务新增', 2, 'module_storage:transfer:create'
    UNION ALL SELECT '传输任务修改', 3, 'module_storage:transfer:update'
    UNION ALL SELECT '传输任务删除', 4, 'module_storage:transfer:delete'
) t
WHERE @transfer_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM sys_menu m
    WHERE m.permission = t.perm AND m.type = 3 AND m.parent_id = @transfer_id AND m.is_deleted = 0
);

-- ── 7. 分配给超级管理员角色（目录 + 菜单 + 按钮，去重） ──
SET @admin_role_id = (SELECT id FROM sys_role WHERE name = '超级管理员' AND is_deleted = 0 LIMIT 1);

INSERT INTO sys_role_menus (role_id, menu_id)
SELECT @admin_role_id, id
FROM sys_menu
WHERE is_deleted = 0
  AND (id = @storage_dir_id OR parent_id = @storage_dir_id
       OR parent_id IN (@source_id, @file_id, @transfer_id))
  AND id NOT IN (SELECT menu_id FROM sys_role_menus WHERE role_id = @admin_role_id);

-- ── 验证 ──
SELECT id, name, type, `order`, permission, parent_id
FROM sys_menu
WHERE is_deleted = 0
  AND (id = @storage_dir_id OR parent_id = @storage_dir_id
       OR parent_id IN (@source_id, @file_id, @transfer_id))
ORDER BY type, parent_id, `order`;
