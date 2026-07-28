"""
=============================================================
Pydantic Settings 学习案例 - 配置管理
=============================================================

pydantic-settings 是 Pydantic 的配置管理扩展，自动从环境变量和 .env 文件加载配置。
在 FastapiAdmin 中，setting.py 使用 pydantic-settings 管理所有系统配置。

官方文档: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

安装: pip install pydantic-settings

运行方式:
    python 05_pydantic_settings.py

本文件演示:
  1. 基础配置类定义
  2. 从 .env 文件加载配置
  3. 配置验证与类型转换
  4. 多环境配置（dev/prod）
  5. 嵌套配置模型
  6. @lru_cache 缓存配置单例
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# 1. 基础配置类 - 最简单的配置定义
# ============================================================
class BasicSettings(BaseSettings):
    """
    基础配置示例。

    pydantic-settings 会自动:
    1. 从环境变量中查找匹配的配置项（不区分大小写）
    2. 将字符串值转换为声明的类型
    3. 使用默认值作为后备
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",  # 环境变量前缀，如 APP_DEBUG=true
        case_sensitive=False,
    )

    # 基础类型配置
    APP_NAME: str = "MyApp"
    DEBUG: bool = False
    PORT: int = 8000
    WORKERS: int = 4


# ============================================================
# 2. 从 .env 文件加载（与 FastapiAdmin 的 setting.py 一致）
# ============================================================
class EnvFileSettings(BaseSettings):
    """
    从 .env 文件加载配置。

    在 FastapiAdmin 中:
        model_config = SettingsConfigDict(
            env_file=ENV_DIR / f".env.{os.getenv('ENVIRONMENT')}",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=True,
        )

    这意味着:
    - 根据 ENVIRONMENT 环境变量加载不同的 .env 文件
    - ENVIRONMENT=dev → 加载 .env.dev
    - ENVIRONMENT=prod → 加载 .env.prod
    """

    model_config = SettingsConfigDict(
        # env_file=".env",           # 指定 .env 文件路径
        env_file_encoding="utf-8",
        extra="ignore",             # 忽略 .env 中未声明的额外字段
        case_sensitive=True,        # 区分大小写
    )

    # --- 服务器配置 ---
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8001

    # --- 数据库配置 ---
    DATABASE_TYPE: Literal["mysql", "postgres", "sqlite"] = "mysql"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "fastapiadmin"

    # --- Redis 配置 ---
    REDIS_ENABLE: bool = True
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


# ============================================================
# 3. 配置验证与计算属性
# ============================================================
class ValidatedSettings(BaseSettings):
    """
    带验证和计算属性的配置（与 FastapiAdmin 中 setting.py 的模式一致）。
    """

    model_config = SettingsConfigDict(env_prefix="DEMO_")

    # --- 基础配置 ---
    DATABASE_TYPE: Literal["mysql", "postgres", "sqlite"] = "sqlite"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "testdb"

    POOL_SIZE: int = Field(default=10, ge=1, le=100, description="连接池大小")
    MAX_OVERFLOW: int = Field(default=20, ge=0, description="最大溢出连接数")

    # --- 字段验证器 ---
    @field_validator("DATABASE_PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """验证端口范围"""
        if v < 1 or v > 65535:
            raise ValueError(f"端口号 {v} 不在有效范围 (1-65535)")
        return v

    @field_validator("DATABASE_PASSWORD")
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        """生产环境必须有密码"""
        # 注意: 实际使用时需要获取 ENVIRONMENT 的值
        # 这里简化演示
        return v

    # --- 计算属性（与 FastapiAdmin 中 ASYNC_DB_URI 一致）---
    @property
    def ASYNC_DB_URI(self) -> str:
        """
        异步数据库连接字符串。

        在 FastapiAdmin 中，这个属性根据 DATABASE_TYPE 生成不同的连接字符串:
        - MySQL: mysql+asyncmy://user:pass@host:port/db
        - PostgreSQL: postgresql+asyncpg://user:pass@host:port/db
        - SQLite: sqlite+aiosqlite:///db.sqlite
        """
        if self.DATABASE_TYPE == "mysql":
            return f"mysql+asyncmy://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        elif self.DATABASE_TYPE == "postgres":
            return f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        else:
            return f"sqlite+aiosqlite:///{self.DATABASE_NAME}.db"

    @property
    def SYNC_DB_URI(self) -> str:
        """同步数据库连接字符串（用于 Alembic 迁移）"""
        if self.DATABASE_TYPE == "mysql":
            return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        elif self.DATABASE_TYPE == "postgres":
            return f"postgresql+psycopg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        else:
            return f"sqlite:///{self.DATABASE_NAME}.db"

    @property
    def FASTAPI_CONFIG(self) -> dict[str, Any]:
        """
        FastAPI 应用配置字典。
        与 FastapiAdmin 中的 FASTAPI_CONFIG 属性一致。
        """
        return {
            "title": "🎉 FastapiAdmin 🎉",
            "version": "0.1.0",
            "description": "后台接口文档",
            "docs_url": None,
            "redoc_url": None,
        }


# ============================================================
# 4. 嵌套配置模型
# ============================================================
class JWTConfig(BaseSettings):
    """JWT 认证配置"""
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 12  # 12小时
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 12
    TOKEN_TYPE: str = "Bearer"


class StorageConfig(BaseSettings):
    """存储配置"""
    UPLOAD_FILE_PATH: Path = Path("static/upload")
    ALLOWED_EXTENSIONS: list[str] = [".gif", ".jpg", ".jpeg", ".png"]
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB


# ============================================================
# 5. @lru_cache 缓存单例（与 FastapiAdmin 中 get_settings 一致）
# ============================================================
@lru_cache(maxsize=1)
def get_settings() -> ValidatedSettings:
    """
    获取配置单例。

    @lru_cache(maxsize=1) 确保:
    - 第一次调用时创建 Settings 实例
    - 后续调用直接返回缓存的实例
    - 整个应用生命周期只有一个 Settings 对象

    在 FastapiAdmin 中:
        @lru_cache(maxsize=1)
        def get_settings() -> Settings:
            return Settings()

        settings = get_settings()
    """
    return ValidatedSettings()


# ============================================================
# 6. 多环境配置演示
# ============================================================
def demonstrate_multi_env():
    """
    演示多环境配置切换。

    FastapiAdmin 的做法:
    1. main.py 中通过 --env 参数设置 ENVIRONMENT 环境变量
    2. Settings 根据 ENVIRONMENT 加载不同的 .env 文件
    3. 使用 get_settings.cache_clear() 清除缓存后重新加载
    """
    print("\n--- 多环境配置演示 ---\n")

    # 模拟 dev 环境
    os.environ["ENVIRONMENT"] = "dev"
    print(f"当前环境: {os.getenv('ENVIRONMENT')}")
    print(f"  → 加载 .env.dev 文件")

    # 模拟 prod 环境
    os.environ["ENVIRONMENT"] = "prod"
    print(f"当前环境: {os.getenv('ENVIRONMENT')}")
    print(f"  → 加载 .env.prod 文件")

    # 清除缓存重新加载（与 main.py 中 revision/upgrade 命令一致）
    get_settings.cache_clear()
    print("  → get_settings.cache_clear() 已清除缓存")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Pydantic Settings 学习案例")
    print("=" * 60)

    # 1. 基础配置
    print("\n--- 1. 基础配置 ---")
    basic = BasicSettings()
    print(f"  APP_NAME: {basic.APP_NAME}")
    print(f"  DEBUG: {basic.DEBUG}")
    print(f"  PORT: {basic.PORT}")

    # 2. 环境变量文件配置
    print("\n--- 2. .env 文件配置 ---")
    env_settings = EnvFileSettings()
    print(f"  SERVER: {env_settings.SERVER_HOST}:{env_settings.SERVER_PORT}")
    print(f"  DATABASE: {env_settings.DATABASE_TYPE}://{env_settings.DATABASE_HOST}:{env_settings.DATABASE_PORT}")

    # 3. 验证与计算属性
    print("\n--- 3. 验证与计算属性 ---")
    settings = get_settings()
    print(f"  异步连接: {settings.ASYNC_DB_URI}")
    print(f"  同步连接: {settings.SYNC_DB_URI}")
    print(f"  连接池: size={settings.POOL_SIZE}, overflow={settings.MAX_OVERFLOW}")

    # 4. 多环境演示
    demonstrate_multi_env()

    # 5. 配置优先级说明
    print("\n--- 配置优先级（从高到低）---")
    print("  1. 构造函数传入的参数")
    print("  2. 环境变量")
    print("  3. .env 文件中的值")
    print("  4. 模型字段的默认值")
