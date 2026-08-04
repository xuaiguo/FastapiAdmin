"""插入脱敏管理菜单数据和预置脱敏规则

用法: cd backend && ENVIRONMENT=dev python -m app.scripts.migrations.insert_masking_data

注意: 建表需包含 ModelMixin 的所有字段 (uuid, deleted_time)
"""

import asyncio
from datetime import datetime
from sqlalchemy import text
from app.core.database import async_db_session

# 建表 SQL（含 ModelMixin 完整字段）
CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS sys_data_masking_rule (
        id INT AUTO_INCREMENT PRIMARY KEY,
        uuid VARCHAR(64) NOT NULL DEFAULT '',
        rule_type INT NOT NULL UNIQUE COMMENT '规则类型编号',
        rule_regex VARCHAR(255) NOT NULL COMMENT '正则表达式（必须分组）',
        hide_group INT NOT NULL DEFAULT 2 COMMENT '需要隐藏的分组序号（从1开始）',
        rule_desc VARCHAR(200) NOT NULL DEFAULT '' COMMENT '规则描述',
        created_id INT DEFAULT NULL,
        updated_id INT DEFAULT NULL,
        is_deleted TINYINT(1) NOT NULL DEFAULT 0,
        created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        deleted_time DATETIME DEFAULT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='敏感字段脱敏规则'
    """,
    """
    CREATE TABLE IF NOT EXISTS sys_data_masking_column (
        id INT AUTO_INCREMENT PRIMARY KEY,
        uuid VARCHAR(64) NOT NULL DEFAULT '',
        config_id INT NOT NULL COMMENT '数据源配置ID',
        table_schema VARCHAR(64) NOT NULL DEFAULT '*' COMMENT '库/Schema名（*=所有）',
        table_name VARCHAR(64) NOT NULL DEFAULT '*' COMMENT '表名（*=所有）',
        column_name VARCHAR(64) NOT NULL COMMENT '列名',
        rule_type INT NOT NULL COMMENT '关联脱敏规则类型',
        active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否激活',
        created_id INT DEFAULT NULL,
        updated_id INT DEFAULT NULL,
        is_deleted TINYINT(1) NOT NULL DEFAULT 0,
        created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        deleted_time DATETIME DEFAULT NULL,
        UNIQUE KEY uk_config_table_column (config_id, table_schema, table_name, column_name),
        KEY idx_config_active (config_id, active),
        KEY idx_rule_type (rule_type),
        CONSTRAINT fk_masking_column_config FOREIGN KEY (config_id) REFERENCES sys_ob_oracle_config(id) ON DELETE CASCADE,
        CONSTRAINT fk_masking_column_rule FOREIGN KEY (rule_type) REFERENCES sys_data_masking_rule(rule_type) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='脱敏字段配置'
    """,
]

# 预置脱敏规则
MASKING_RULES = [
    (1, r"^(\d{3})(\d{4})(\d{4})$", 2, "手机号脱敏"),
    (2, r"^(\d{6})(\d{8})(\d{4})$", 2, "身份证号脱敏"),
    (3, r"^(\d{4})(\d+)(\d{4})$", 2, "银行卡号脱敏"),
    (4, r"^([^@]+)(@.+\..+)$", 1, "邮箱脱敏"),
]

MENU_INSERT_SQL = """
INSERT INTO sys_menu (
    name, type, `order`, permission, icon, route_name, route_path,
    component_path, redirect, hidden, keep_alive, always_show, title,
    params, affix, link, is_iframe, is_hide_tab, active_path,
    show_badge, show_text_badge, scope, status, description, parent_id,
    uuid, is_deleted, created_time, updated_time
) VALUES (
    :name, :type, :order_val, :permission, :icon, :route_name, :route_path,
    :component_path, :redirect, :hidden, :keep_alive, :always_show, :title,
    :params, :affix, :link, :is_iframe, :is_hide_tab, :active_path,
    :show_badge, :show_text_badge, :scope, :status, :description, :parent_id,
    :uuid, :is_deleted, :created_time, :updated_time
)
"""


def btn_params(name, perm, order_val, parent_id, uuid_val, now):
    return {
        "name": name, "type": 3, "order_val": order_val,
        "permission": perm,
        "icon": None, "route_name": None, "route_path": None,
        "component_path": None,
        "redirect": None, "hidden": False, "keep_alive": True,
        "always_show": False, "title": name,
        "params": None, "affix": False,
        "link": None, "is_iframe": False, "is_hide_tab": False,
        "active_path": None, "show_badge": False, "show_text_badge": None,
        "scope": "web", "status": 0,
        "description": None,
        "parent_id": parent_id,
        "uuid": uuid_val, "is_deleted": False,
        "created_time": now, "updated_time": now,
    }


async def main():
    now = datetime.now()
    uid = [1000]

    def next_uuid():
        uid[0] += 1
        return f"menu-masking-{uid[0]}"

    async with async_db_session() as session:
        async with session.begin():
            # 0. 建表（如不存在）
            for ddl in CREATE_TABLES:
                await session.execute(text(ddl))
            print("  OK tables ready")

            # 1. 插入预置脱敏规则
            for rule_type, rule_regex, hide_group, rule_desc in MASKING_RULES:
                check = await session.execute(
                    text("SELECT id FROM sys_data_masking_rule WHERE rule_type = :rt"),
                    {"rt": rule_type}
                )
                if check.scalar_one_or_none():
                    print(f"  跳过已存在的规则: {rule_type} - {rule_desc}")
                    continue
                await session.execute(
                    text("""
                        INSERT INTO sys_data_masking_rule
                        (rule_type, rule_regex, hide_group, rule_desc, is_deleted, created_time, updated_time)
                        VALUES (:rule_type, :rule_regex, :hide_group, :rule_desc, 0, :now, :now)
                    """),
                    {
                        "rule_type": rule_type,
                        "rule_regex": rule_regex,
                        "hide_group": hide_group,
                        "rule_desc": rule_desc,
                        "now": now,
                    }
                )
                print(f"  OK 插入规则: {rule_type} - {rule_desc}")

            # 2. 查找 OceanBase管理 菜单ID
            ob_result = await session.execute(
                text("SELECT id FROM sys_menu WHERE name = 'OceanBase管理' AND type = 1 LIMIT 1")
            )
            ob_menu_id = ob_result.scalar_one_or_none()
            if not ob_menu_id:
                print("X 未找到 OceanBase管理 菜单，跳过菜单插入")
                return

            # 3. 检查脱敏管理菜单是否已存在
            check_menu = await session.execute(
                text("SELECT id FROM sys_menu WHERE route_name = 'DataMasking' LIMIT 1")
            )
            if check_menu.scalar_one_or_none():
                print("  脱敏管理菜单已存在，跳过")
                return

            # 4. 插入脱敏管理页面菜单
            page_params = {
                "name": "脱敏管理", "type": 2, "order_val": 10,
                "permission": "ob_oracle_query:masking:query",
                "icon": "ri:shield-keyhole-line",
                "route_name": "DataMasking", "route_path": "dataMasking",
                "component_path": "ob_oracle_query/masking/index",
                "redirect": None, "hidden": False, "keep_alive": True,
                "always_show": False, "title": "脱敏管理",
                "params": None, "affix": False,
                "link": None, "is_iframe": False, "is_hide_tab": False,
                "active_path": None, "show_badge": False, "show_text_badge": None,
                "scope": "web", "status": 0,
                "description": "敏感字段脱敏规则与字段配置管理",
                "parent_id": ob_menu_id,
                "uuid": next_uuid(), "is_deleted": False,
                "created_time": now, "updated_time": now,
            }
            await session.execute(text(MENU_INSERT_SQL), page_params)

            r = await session.execute(text("SELECT LAST_INSERT_ID()"))
            masking_menu_id = r.scalar()
            print(f"  OK 脱敏管理菜单 id: {masking_menu_id}")

            # 5. 插入按钮权限
            for name, perm, order in [
                ("查询", "ob_oracle_query:masking:query", 1),
                ("新增", "ob_oracle_query:masking:create", 2),
                ("修改", "ob_oracle_query:masking:update", 3),
                ("删除", "ob_oracle_query:masking:delete", 4),
            ]:
                await session.execute(
                    text(MENU_INSERT_SQL),
                    btn_params(name, perm, order, masking_menu_id, next_uuid(), now)
                )
            print("  OK 按钮权限: 查询/新增/修改/删除")

    print("\nAll masking data inserted!")


if __name__ == "__main__":
    asyncio.run(main())
