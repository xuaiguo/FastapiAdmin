"""
=============================================================
Uvicorn 学习案例 - ASGI 异步服务器
=============================================================

Uvicorn 是一个轻量级的 ASGI 服务器，专为 Python 异步 Web 框架设计。
在 FastapiAdmin 的 main.py 中，Uvicorn 负责启动和运行 FastAPI 应用。

官方文档: https://www.uvicorn.org/

安装: pip install uvicorn[standard]

运行方式:
    # 方式1: 直接运行本文件
    python 02_uvicorn_server.py

    # 方式2: 命令行启动（推荐，与 main.py 中用法一致）
    uvicorn 02_uvicorn_server:create_app --factory --host 0.0.0.0 --port 8002 --reload

    # 方式3: 在代码中启动（与 main.py 中 uvicorn.run() 用法一致）
    见文件底部的 __main__ 部分
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ============================================================
# 1. 基础应用 - 最简单的 FastAPI + Uvicorn
# ============================================================
def create_basic_app() -> FastAPI:
    """创建基础 FastAPI 应用"""
    app = FastAPI(title="Uvicorn 基础示例")

    @app.get("/")
    async def root():
        return {"message": "Hello 1 from Uvicorn!"}

    @app.get("/health")
    async def health():
        return {"status": "ok", "timestamp": time.time()}

    return app


# ============================================================
# 2. Lifespan 生命周期（与 main.py 中 lifespan 用法一致）
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """
    应用生命周期管理器。

    在 FastapiAdmin 中，lifespan 用于:
    - 初始化数据库
    - 初始化 Redis 连接
    - 初始化定时任务调度器
    - 初始化限流器
    - 关闭时释放资源
    """
    # === 启动阶段 ===
    print("🚀 应用启动中...")
    # 模拟初始化资源（数据库连接池、Redis 等）
    app.state.db_pool = "模拟数据库连接池"
    app.state.redis = "模拟 Redis 连接"
    app.state.startup_time = time.time()
    print("✅ 数据库连接池已初始化")
    print("✅ Redis 连接已建立")

    yield  # <-- 应用在此处开始接收请求

    # === 关闭阶段 ===
    print("\n🛑 应用关闭中...")
    # 模拟释放资源
    app.state.db_pool = None
    app.state.redis = None
    print("✅ 数据库连接池已释放")
    print("✅ Redis 连接已关闭")


def create_app() -> FastAPI:
    """
    工厂函数创建应用（与 main.py 中的 create_app 模式一致）。

    Uvicorn 支持 factory 模式:
        uvicorn module:create_app --factory
    这与 main.py 中的 uvicorn.run(app="main:create_app", factory=True) 等价。
    """
    app = FastAPI(
        title="Uvicorn 完整示例",
        description="演示 Uvicorn 的各项功能",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/")
    async def root():
        return {"message": "Hello 2 from Uvicorn factory!"}

    @app.get("/status")
    async def status(request: Request):
        """展示应用状态（来自 lifespan 初始化）"""
        uptime = time.time() - request.app.state.startup_time
        return {
            "db_pool": request.app.state.db_pool is not None,
            "redis": request.app.state.redis is not None,
            "uptime_seconds": round(uptime, 2),
        }

    @app.get("/slow")
    async def slow_endpoint():
        """模拟慢请求 - 演示 Uvicorn 的异步并发能力"""
        await asyncio.sleep(2)
        return {"message": "这个请求花了 2 秒，但不会阻塞其他请求"}

    @app.get("/concurrent-test")
    async def concurrent_test():
        """快速响应 - 即使 /slow 正在处理，这个请求也能立即返回"""
        return {"message": "立即响应！Uvicorn 是异步的，不会被慢请求阻塞"}

    return app


# ============================================================
# 3. Uvicorn 配置选项详解
# ============================================================
def demonstrate_uvicorn_config():
    """
    演示 Uvicorn 的各种配置选项。

    这些配置在 main.py 中通过 uvicorn.run() 传入:

        uvicorn.run(
            app="main:create_app",     # 应用路径（模块:工厂函数）
            host=settings.SERVER_HOST,  # 监听地址
            port=settings.SERVER_PORT,  # 监听端口
            reload=env == "dev",        # 开发环境开启热重载
            factory=True,               # 使用工厂模式
            log_config=None,            # 禁用默认日志配置（使用自定义日志）
        )
    """
    print(demonstrate_uvicorn_config.__doc__)
    config_options = {
        "基础配置": {
            "app": '"module:create_app" — 应用入口，支持工厂模式',
            "host": '"0.0.0.0" — 监听所有网络接口',
            "port": "8001 — 监听端口",
            "factory": "True — 启用工厂模式，调用 app 字符串指向的函数获取应用实例",
        },
        "开发配置": {
            "reload": "True — 文件变更时自动重启（仅开发环境使用）",
            "reload_dirs": '["app"] — 指定监控目录，减少不必要的文件监控',
            "reload_includes": '["*.py", "*.html"] — 包含特定文件类型',
            "reload_excludes": '["*.pyc", "__pycache__/*"] — 排除特定文件',
        },
        "生产配置": {
            "workers": "4 — 工作进程数（生产环境多进程）",
            "loop": '"auto" — 事件循环实现（auto/asyncio/uvloop）',
            "http": '"auto" — HTTP 协议实现（auto/httptools/h11）',
            "access_log": "True — 是否记录访问日志",
            "proxy_headers": "True — 信任代理转发的请求头",
            "forwarded_allow_ips": '"*" — 允许转发 IP（配合 Nginx 使用）',
        },
        "性能配置": {
            "limit_concurrency": "None — 最大并发连接数",
            "backlog": "2048 — 等待队列长度",
            "limit_max_requests": "None — 单进程最大请求数后重启",
            "timeout_keep_alive": "5 — Keep-Alive 超时秒数",
            "timeout_graceful_shutdown": "None — 优雅关闭等待秒数",
        },
        "日志配置": {
            "log_level": '"info" — 日志级别（critical/error/warning/info/debug/trace）',
            "log_config": "None — 自定义日志配置（传 None 禁用默认配置）",
            "use_colors": "True — 是否在日志中使用彩色输出",
        },
        "SSL 配置": {
            "ssl_keyfile": "None — SSL 私钥文件路径",
            "ssl_certfile": "None — SSL 证书文件路径",
            "ssl_ca_certs": "None — CA 证书文件路径",
        },
    }

    for category, options in config_options.items():
        print(f"\n{'='*50}")
        print(f"📋 {category}")
        print(f"{'='*50}")
        for key, desc in options.items():
            print(f"  {key:25s} → {desc}")


# ============================================================
# 4. Uvicorn 与 ASGI 的关系
# ============================================================
def explain_asgi():
    """
    ASGI (Asynchronous Server Gateway Interface) 说明:

    ┌─────────────┐     ┌──────────┐     ┌─────────────┐
    │   客户端     │────▶│ Uvicorn  │────▶│  FastAPI    │
    │ (浏览器等)   │◀────│ (ASGI    │◀────│  (应用)     │
    └─────────────┘     │  Server) │     └─────────────┘
                        └──────────┘

    - Uvicorn 是 ASGI 服务器，负责处理 HTTP 协议、TCP 连接等底层工作
    - FastAPI 是 ASGI 应用，负责路由、请求处理等业务逻辑
    - Uvicorn 接收请求 → 传给 FastAPI 处理 → FastAPI 返回响应 → Uvicorn 发回客户端

    对比:
    - WSGI (同步): Gunicorn + Flask/Django
    - ASGI (异步): Uvicorn + FastAPI/Starlette
    """
    print(explain_asgi.__doc__)


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Uvicorn 配置选项详解")
    print("=" * 60)
    demonstrate_uvicorn_config()

    print("\n\n")
    explain_asgi()

    print("\n\n" + "=" * 60)
    print("启动 Uvicorn 服务器 (Ctrl+C 停止)")
    print("=" * 60)
    print("访问 http://localhost:8002 查看效果")
    print("同时访问 /slow 和 /concurrent-test 体验异步并发")

    # 与 main.py 中的 uvicorn.run() 用法一致
    uvicorn.run(
        app="02_uvicorn_server:create_app",  # 模块:工厂函数
        host="127.0.0.1",
        port=8002,
        reload=False,       # 直接运行时不开启 reload
        factory=True,       # 启用工厂模式
        log_config=None,    # 使用自定义日志
    )
