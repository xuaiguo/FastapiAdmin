"""
=============================================================
SQLAlchemy 2.0 Async 学习案例 - 异步 ORM
=============================================================

SQLAlchemy 2.0 是 Python 最流行的 ORM，2.0 版本引入了原生异步支持。
在 FastapiAdmin 中，SQLAlchemy 2.0 async 用于所有数据库操作。

官方文档: https://docs.sqlalchemy.org/en/20/

安装: pip install sqlalchemy[asyncio] aiosqlite  (本案例使用 SQLite)

运行方式:
    python 06_sqlalchemy_async.py

本文件演示:
  1. 异步引擎与会话
  2. 声明式模型定义（Mapped 类型）
  3. CRUD 操作
  4. 事务管理（与 FastapiAdmin 的 db_getter 一致）
  5. 关系查询
  6. 查询构建器
"""

import asyncio
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func, select, update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# ============================================================
# 1. 声明式基类（与 FastapiAdmin 的 base_model.py 一致）
# ============================================================
class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 声明式基类。

    在 FastapiAdmin 中，基类包含多个 Mixin:
    - ModelMixin: id, uuid, is_deleted, timestamps
    - TenantMixin: tenant_id
    - UserMixin: created_id, updated_id
    """
    pass


class ModelMixin:
    """
    模型混入（与 FastapiAdmin 的 ModelMixin 一致）。

    提供所有模型共有的字段:
    - id: 主键
    - is_deleted: 软删除标记
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    is_deleted: Mapped[bool] = mapped_column(default=False, comment="软删除标记")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )


class TenantMixin:
    """多租户混入（与 FastapiAdmin 的 TenantMixin 一致）"""
    tenant_id: Mapped[int | None] = mapped_column(index=True, comment="租户ID")


# ============================================================
# 2. 模型定义 - SQLAlchemy 2.0 Mapped 类型
# ============================================================
class User(ModelMixin, TenantMixin, Base):
    """
    用户模型 - 演示 SQLAlchemy 2.0 的 Mapped 类型声明。

    SQLAlchemy 2.0 使用 Mapped[类型] 替代旧的 Column(类型):
    - Mapped[int] → Integer 列
    - Mapped[str] → String 列
    - Mapped[str | None] → 可空 String 列
    - Mapped[bool] → Boolean 列
    """
    __tablename__ = "study_users"

    # mapped_column 替代旧的 Column
    username: Mapped[str] = mapped_column(String(50), unique=True, comment="用户名")
    email: Mapped[str | None] = mapped_column(String(100), comment="邮箱")
    password: Mapped[str] = mapped_column(String(255), comment="密码")
    nickname: Mapped[str] = mapped_column(String(50), default="", comment="昵称")
    status: Mapped[int] = mapped_column(default=1, comment="状态: 0=禁用 1=正常")

    # 关系定义（一对多）
    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class Post(ModelMixin, TenantMixin, Base):
    """文章模型 - 演示外键关系"""
    __tablename__ = "study_posts"

    title: Mapped[str] = mapped_column(String(200), comment="标题")
    content: Mapped[str | None] = mapped_column(Text, comment="内容")
    author_id: Mapped[int] = mapped_column(ForeignKey("study_users.id"), comment="作者ID")

    # 关系定义（多对一）
    author: Mapped["User"] = relationship(back_populates="posts")

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title={self.title})>"


# ============================================================
# 3. 异步引擎与会话工厂
# ============================================================
# 使用 SQLite 异步引擎（无需额外安装数据库）
DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # 内存数据库，适合演示

# 创建异步引擎（与 FastapiAdmin 的 database.py 一致）
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,          # 打印 SQL（开发环境设为 True）
    # 生产环境配置（与 FastapiAdmin setting.py 一致）:
    # pool_size=10,          # 连接池大小
    # max_overflow=20,       # 最大溢出连接
    # pool_timeout=30,       # 获取连接超时
    # pool_recycle=1800,     # 连接回收时间
    # pool_pre_ping=True,    # 连接预检
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期属性（与 FastapiAdmin 一致）
)


# ============================================================
# 4. 请求级事务管理（与 FastapiAdmin 的 db_getter 一致）
# ============================================================
async def db_getter():
    """
    请求级数据库会话生成器。

    在 FastapiAdmin 中，这个函数作为 FastAPI 依赖注入使用:
    - 每个请求获取一个 AsyncSession
    - 请求成功 → 自动 COMMIT
    - 请求失败 → 自动 ROLLBACK

    用法:
        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(db_getter)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
            print("✅ 事务已提交")
        except Exception as e:
            await session.rollback()
            print(f"❌ 事务已回滚: {e}")
            raise
        finally:
            await session.close()


# ============================================================
# 5. CRUD 操作演示
# ============================================================
async def demonstrate_crud(session: AsyncSession):
    """
    完整的 CRUD 操作演示。

    对应 FastapiAdmin 中 CRUDBase 类的各个方法。
    """
    print("\n" + "=" * 60)
    print("CRUD 操作演示")
    print("=" * 60)

    # ---- CREATE (创建) ----
    print("\n--- CREATE ---")

    # 方式1: 直接创建
    user1 = User(
        username="admin",
        email="admin@example.com",
        password="hashed_password_123",
        nickname="管理员",
        tenant_id=1,
    )
    session.add(user1)

    # 方式2: 批量创建
    users = [
        User(username="alice", email="alice@example.com", password="pass1", tenant_id=1),
        User(username="bob", email="bob@example.com", password="pass2", tenant_id=1),
        User(username="charlie", email="charlie@example.com", password="pass3", tenant_id=2),
    ]
    session.add_all(users)
    await session.flush()  # flush 获取自增 ID，但不提交事务
    print(f"  创建了用户: {user1.id} - {user1.username}")
    print(f"  批量创建了 {len(users)} 个用户")

    # 创建文章（关联用户）
    post1 = Post(title="FastAPI 入门", content="FastAPI 是一个...", author_id=user1.id, tenant_id=1)
    post2 = Post(title="SQLAlchemy 2.0 指南", content="SQLAlchemy 2.0...", author_id=user1.id, tenant_id=1)
    session.add_all([post1, post2])
    await session.flush()
    print(f"  创建了文章: {post1.title}, {post2.title}")

    # ---- READ (查询) ----
    print("\n--- READ ---")

    # 查询单个（按主键）
    user = await session.get(User, user1.id)
    print(f"  按 ID 查询: {user}")

    # 条件查询（select 语句）
    stmt = select(User).where(User.tenant_id == 1, User.is_deleted == False)
    result = await session.execute(stmt)
    tenant1_users = result.scalars().all()
    print(f"  租户1的用户数: {len(tenant1_users)}")

    # LIKE 模糊查询
    stmt = select(User).where(User.username.like("a%"))
    result = await session.execute(stmt)
    a_users = result.scalars().all()
    print(f"  用户名以 'a' 开头的: {[u.username for u in a_users]}")

    # IN 查询
    stmt = select(User).where(User.username.in_(["alice", "bob"]))
    result = await session.execute(stmt)
    specific_users = result.scalars().all()
    print(f"  指定用户: {[u.username for u in specific_users]}")

    # 统计查询
    stmt = select(func.count()).select_from(User).where(User.is_deleted == False)
    result = await session.execute(stmt)
    total = result.scalar()
    print(f"  用户总数: {total}")

    # 分页查询
    page, size = 1, 2
    stmt = select(User).offset((page - 1) * size).limit(size).order_by(User.id)
    result = await session.execute(stmt)
    page_users = result.scalars().all()
    print(f"  第 {page} 页（每页 {size} 条）: {[u.username for u in page_users]}")

    # 关系查询（加载关联数据）
    from sqlalchemy.orm import selectinload
    stmt = select(User).options(selectinload(User.posts)).where(User.id == user1.id)
    result = await session.execute(stmt)
    user_with_posts = result.scalar_one()
    print(f"  {user_with_posts.username} 的文章: {[p.title for p in user_with_posts.posts]}")

    # ---- UPDATE (更新) ----
    print("\n--- UPDATE ---")

    # 方式1: 修改对象属性
    user1.nickname = "超级管理员"
    await session.flush()
    print(f"  更新 {user1.username} 的昵称为: {user1.nickname}")

    # 方式2: 批量更新（SQL 级更新，更高效）
    stmt = update(User).where(User.tenant_id == 2).values(status=0)
    await session.execute(stmt)
    print("  批量禁用租户2的所有用户")

    # ---- DELETE (软删除) ----
    print("\n--- DELETE (软删除) ---")

    # FastapiAdmin 使用软删除（is_deleted=True），而非物理删除
    user_to_delete = (await session.execute(
        select(User).where(User.username == "charlie")
    )).scalar_one()
    user_to_delete.is_deleted = True
    await session.flush()
    print(f"  软删除用户: {user_to_delete.username} (is_deleted={user_to_delete.is_deleted})")

    # 验证软删除后的查询
    stmt = select(User).where(User.is_deleted == False)
    result = await session.execute(stmt)
    active_users = result.scalars().all()
    print(f"  当前活跃用户: {[u.username for u in active_users]}")

    await session.commit()


# ============================================================
# 6. 事务演示
# ============================================================
async def demonstrate_transaction(session: AsyncSession):
    """演示事务的提交与回滚"""
    print("\n" + "=" * 60)
    print("事务演示")
    print("=" * 60)

    # 成功提交的事务
    try:
        user = User(username="tx_user", password="pass", tenant_id=1)
        session.add(user)
        await session.commit()
        print("  ✅ 事务提交成功")
    except Exception:
        await session.rollback()
        print("  ❌ 事务提交失败，已回滚")

    # 失败回滚的事务
    try:
        # 尝试插入重复的 username（会触发唯一约束冲突）
        user_dup = User(username="tx_user", password="pass", tenant_id=1)
        session.add(user_dup)
        await session.commit()
        print("  ✅ 事务提交成功")
    except Exception:
        await session.rollback()
        print("  ❌ 事务回滚（预期行为）: 唯一约束冲突")


# ============================================================
# 入口
# ============================================================
async def main():
    """主函数"""
    print("=" * 60)
    print("SQLAlchemy 2.0 Async 学习案例")
    print("=" * 60)

    # 创建所有表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ 数据库表已创建")

    # 执行 CRUD 演示
    async with async_session_factory() as session:
        await demonstrate_crud(session)

    # 执行事务演示
    async with async_session_factory() as session:
        await demonstrate_transaction(session)

    # 清理
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("\n✅ 数据库表已清理")

    await async_engine.dispose()
    print("✅ 引擎已关闭")


if __name__ == "__main__":
    asyncio.run(main())
