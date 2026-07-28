"""
=============================================================
FastAPI-Limiter 学习案例 - API 请求限流
=============================================================

fastapi-limiter 是基于 Redis 的请求限流库。
在 FastapiAdmin 中，限流器用于保护 API 不被过度请求。

官方文档: https://github.com/long2ice/fastapi-limiter

安装: pip install fastapi-limiter

运行方式:
    python 08_fastapi_limiter.py
    （需要本地运行 Redis 服务）

本文件演示:
  1. 限流器初始化（与 init_app.py 一致）
  2. 路由级限流
  3. 自定义限流策略
  4. 限流回调处理

FastapiAdmin 中的限流配置:
  - 每个路由组: 200 次请求 / 10 秒
  - 使用 Redis 作为计数器后端
  - 自定义回调函数返回友好错误信息
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as aioredis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter


# ============================================================
# 1. 限流回调函数（与 FastapiAdmin 的 http_limit_callback 一致）
# ============================================================
async def http_limit_callback(request: Request, response: Response, expire: int):
    """
    当请求超过限流阈值时调用。

    参数（fastapi-limiter 库自动传入）:
    - request:  当前请求
    - response: 当前响应（保留，未使用）
    - expire:   剩余冷却时间（毫秒）

    注意：
    - 签名必须是 async def (request, response, expire)
    - 必须 raise 异常，不能 return 响应！
      因为 RateLimiter 是 Depends() 依赖，FastAPI 会忽略依赖的返回值，
      只有抛出的异常才会被异常处理器捕获并返回给客户端。
    """
    from math import ceil
    retry_after = ceil(expire / 1000)
    raise HTTPException(
        status_code=429,
        detail={
            "code": 429,
            "msg": f"请求过于频繁，请 {retry_after} 秒后再试",
            "data": {"Retry-After": retry_after},
            "success": False,
        },
    )


async def ws_limit_callback(ws, expire: int):
    """WebSocket 请求限流回调"""
    from math import ceil
    retry_after = ceil(expire / 1000)
    await ws.close(code=1008, reason=f"请求过于频繁，{retry_after} 秒后重试")


# ============================================================
# 2. 应用生命周期（初始化/关闭限流器）
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """
    在 lifespan 中初始化和关闭限流器。
    与 FastapiAdmin init_app.py 中的一致。
    """
    redis = aioredis.Redis(
        host="10.3.94.10",
        port=6379,
        db=2,
        password="fastapiadmin_redis",
        decode_responses=True,
    )

    try:
        await redis.ping()
        app.state.redis = redis
        await FastAPILimiter.init(
            redis=redis,
            prefix="study:limiter",
            http_callback=http_limit_callback,
            ws_callback=ws_limit_callback,
        )
        print("✅ 请求限流器初始化完成")
    except Exception:
        print("⚠️ Redis 不可用，限流器未初始化")
        app.state.redis = None

    yield

    if app.state.redis:
        await FastAPILimiter.close()
        await redis.close()
        print("✅ 请求限流器已关闭")


# ============================================================
# 3. 创建 FastAPI 应用
# ============================================================
app = FastAPI(
    title="FastAPI-Limiter 学习案例",
    description="演示 API 请求限流功能",
    lifespan=lifespan,
)


# ============================================================
# 4. 路由级限流 - 使用 RateLimiter 依赖
# ============================================================
@app.get("/api/public", dependencies=[Depends(RateLimiter(times=5, seconds=10))])
async def public_endpoint():
    """
    公开接口 - 10秒内最多5次请求。

    在 FastapiAdmin 中:
        app.include_router(router, dependencies=[Depends(RateLimiter(times=200, seconds=10))])
    """
    return {"msg": "这是公开接口", "timestamp": time.time()}


@app.get("/api/strict", dependencies=[Depends(RateLimiter(times=2, seconds=10))])
async def strict_endpoint():
    """严格限流接口 - 10秒内最多2次请求"""
    return {"msg": "这是严格限流接口", "timestamp": time.time()}


# ============================================================
# 5. 限流原理说明
# ============================================================
def explain_limiter():
    """
    FastAPI-Limiter 工作原理:

    1. 基于 Redis INCR + EXPIRE 实现滑动窗口计数:
        key = "prefix:{client_ip}:{route_path}"
        INCR key → 计数器 +1
        EXPIRE key seconds → 设置过期时间
        if count > times: return 429

    2. FastapiAdmin 中的配置:
       - 前缀: fastapiadmin:request_limiter:
       - 限制: 200 次 / 10 秒（每个路由组）

    3. 生产建议:
       - 配合 Nginx 限流形成双重保护
       - 对敏感接口（登录、支付）设置更严格的限制
    """
    print(explain_limiter.__doc__)


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    explain_limiter()

    print("\n" + "=" * 60)
    print("启动 FastAPI-Limiter 学习案例服务器")
    print("=" * 60)
    print("访问 http://localhost:8004/docs 查看 API 文档")
    print("测试限流: curl http://localhost:8004/api/public (10秒内最多5次)")

    uvicorn.run(app, host="127.0.0.1", port=8004)
