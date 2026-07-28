"""
=============================================================
Alembic 学习案例 - 数据库迁移工具
=============================================================

Alembic 是 SQLAlchemy 作者开发的数据库迁移工具。
在 FastapiAdmin 的 main.py 中，Alembic 用于:
  - `revision` 命令: 自动生成迁移脚本
  - `upgrade` 命令: 应用迁移到数据库

官方文档: https://alembic.sqlalchemy.org/

安装: pip install alembic

运行方式:
    # 初始化 Alembic 项目（已完成，见 backend/alembic.ini）
    alembic init alembic

    # 生成迁移脚本（对应 main.py 的 revision 命令）
    alembic revision --autogenerate -m "描述信息"

    # 应用迁移（对应 main.py 的 upgrade 命令）
    alembic upgrade head

    # 回滚一个版本
    alembic downgrade -1

    # 查看迁移历史
    alembic history --verbose
"""

# ============================================================
# 1. Alembic 核心概念说明
# ============================================================
"""
Alembic 核心概念:

1) 迁移脚本 (Migration Script):
   - 每个迁移是一个 Python 文件，包含 upgrade() 和 downgrade() 函数
   - upgrade(): 应用变更（创建表、添加列等）
   - downgrade(): 回滚变更（删除表、删除列等）

2) 版本链 (Version Chain):
   - 每个迁移有唯一 revision ID
   - 通过 down_revision 形成链式关系
   - head = 最新版本

3) autogenerate（自动生成）:
   - Alembic 对比 SQLAlchemy 模型定义与实际数据库
   - 自动生成差异迁移脚本
   - 对应 main.py 中: command.revision(alembic_cfg, autogenerate=True)

4) alembic.ini:
   - 配置文件，指定迁移脚本目录和数据库连接
   - main.py 中通过 Config("alembic.ini") 加载
"""


# ============================================================
# 2. 模拟迁移脚本结构（实际由 Alembic 自动生成）
# ============================================================
"""
以下是一个典型的 Alembic 迁移脚本示例（自动生成后的样子）:

文件名: alembic/versions/2024_01_15_create_user_table.py

```python
# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None  # 第一个迁移，没有前驱版本
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # 创建用户表
    op.create_table(
        'sys_user',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    # 创建索引
    op.create_index('ix_sys_user_tenant_id', 'sys_user', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_sys_user_tenant_id', table_name='sys_user')
    op.drop_table('sys_user')
```
"""


# ============================================================
# 3. 在 Python 代码中使用 Alembic API（与 main.py 一致）
# ============================================================
def demonstrate_alembic_api():
    """
    演示如何在 Python 代码中调用 Alembic API。
    这就是 main.py 中 revision 和 upgrade 命令的实现方式。
    """
    from alembic.config import Config
    from alembic import command

    # 加载 alembic.ini 配置（与 main.py 中 alembic_cfg = Config("alembic.ini") 一致）
    alembic_cfg = Config("alembic.ini")

    # --- 常用 Alembic 命令 ---

    # 1. 自动生成迁移脚本（对应 main.py 的 revision 命令）
    # command.revision(alembic_cfg, autogenerate=True, message="创建用户表")

    # 2. 升级到最新版本（对应 main.py 的 upgrade 命令）
    # command.upgrade(alembic_cfg, "head")

    # 3. 升级到特定版本
    # command.upgrade(alembic_cfg, "a1b2c3d4e5f6")

    # 4. 升级 N 个版本
    # command.upgrade(alembic_cfg, "+2")

    # 5. 回滚一个版本
    # command.downgrade(alembic_cfg, "-1")

    # 6. 回滚到特定版本
    # command.downgrade(alembic_cfg, "a1b2c3d4e5f6")

    # 7. 查看当前版本
    # command.current(alembic_cfg)

    # 8. 查看迁移历史
    # command.history(alembic_cfg)

    # 9. 标记当前版本（不执行迁移，只标记版本号）
    # command.stamp(alembic_cfg, "head")

    print("Alembic API 命令列表:")
    print("  command.revision(cfg, autogenerate=True, message='描述')  # 生成迁移")
    print("  command.upgrade(cfg, 'head')                               # 升级到最新")
    print("  command.upgrade(cfg, '+1')                                 # 升级一个版本")
    print("  command.downgrade(cfg, '-1')                               # 回滚一个版本")
    print("  command.current(cfg)                                       # 查看当前版本")
    print("  command.history(cfg)                                       # 查看迁移历史")
    print("  command.stamp(cfg, 'head')                                 # 标记版本")


# ============================================================
# 4. Alembic 环境配置 (env.py) 说明
# ============================================================
"""
Alembic 的 env.py 是迁移运行时的入口脚本。
在 FastapiAdmin 中，env.py 需要做以下配置:

```python
# alembic/env.py 关键部分

from alembic import context
from sqlalchemy import engine_from_config, pool

# 导入所有模型的 Base（让 Alembic 知道所有表结构）
from app.core.database import Base
from app.api.v1.module_system.user.model import UserModel
from app.api.v1.module_system.role.model import RoleModel
# ... 其他模型

target_metadata = Base.metadata

def run_migrations_online() -> None:
    # Alembic 使用同步连接执行 DDL
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # 支持 JSON 比较（用于 JSON 字段变更检测）
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
```
"""


# ============================================================
# 5. 最佳实践
# ============================================================
def best_practices():
    """Alembic 使用最佳实践"""
    practices = [
        "✅ 每次模型变更后立即生成迁移: python main.py revision --env=dev",
        "✅ 迁移前先备份数据库（生产环境）",
        "✅ 检查自动生成的迁移脚本，必要时手动调整",
        "✅ 不要手动修改已应用的迁移脚本",
        "✅ 使用有意义的迁移消息: -m 'add_user_avatar_column'",
        "✅ 在 CI/CD 中自动执行 upgrade 部署",
        "⚠️ autogenerate 不能检测: 列重命名、表重命名、部分类型变更",
        "⚠️ 列重命名需要手动编写迁移脚本（使用 op.alter_column）",
    ]
    print("Alembic 最佳实践:")
    for p in practices:
        print(f"  {p}")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Alembic 数据库迁移学习案例")
    print("=" * 60)

    print("\n--- Alembic API 演示 ---")
    demonstrate_alembic_api()

    print("\n--- 最佳实践 ---")
    best_practices()
