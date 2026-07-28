"""
=============================================================
Redis 学习案例 - 缓存与会话管理
=============================================================

Redis 在 FastapiAdmin 中用于:
  - 用户会话存储 (USER_SESSION:{session_id})
  - JWT Token 存储 (access_token / refresh_token)
  - 系统参数缓存 (system_config)
  - 数据字典缓存 (system_dict)
  - 租户配置缓存 (tenant_config)
  - 验证码存储 (captcha_codes)
  - 请求限流计数器
  - APScheduler 分布式锁

官方文档: https://redis-py.readthedocs.io/

安装: pip install redis[hiredis]

运行方式:
    python 07_redis_cache.py
    （需要本地运行 Redis 服务，或使用 Docker: docker run -p 6379:6379 redis:7）

本文件演示:
  1. Redis 异步连接
  2. 字符串操作（会话存储）
  3. Hash 操作（用户信息缓存）
  4. 过期时间（Token TTL + 滑动过期）
  5. 管道批量操作
  6. Key 命名规范
"""

import asyncio
import json
import time

import redis.asyncio as redis


# ============================================================
# 1. Redis 异步连接（与 FastapiAdmin 的 redis_connect 一致）
# ============================================================
async def create_redis_connection() -> redis.Redis:
    """
    创建 Redis 异步连接。

    在 FastapiAdmin 中，Redis 连接在 lifespan 阶段创建:
    - init_app.py 的 EVENT_LIST 包含 "app.core.database.redis_connect"
    - 连接创建后存储在 app.state.redis
    """
    r = redis.Redis(
        host="10.3.94.10",
        port=6379,
        db=3,                                      # 与 .env.dev 的 REDIS_DB_NAME=2 一致
        password="fastapiadmin_redis",              # 与 .env.dev 的 REDIS_PASSWORD 一致
        decode_responses=True,                      # 自动解码字节为字符串
    )
    try:
        await r.ping()
        print("✅ Redis 连接成功")
    except redis.ConnectionError:
        print("❌ Redis 连接失败，请确保 Redis 服务正在运行")
        print("   启动 Redis: docker run -d -p 6379:6379 redis:7")
        return None
    return r


# ============================================================
# 2. 用户会话存储（与 FastapiAdmin 的 JWT + Redis 会话一致）
# ============================================================
async def demo_session_storage(r: redis.Redis):
    """
    演示用户会话存储。

    FastapiAdmin 的认证流程:
    1. 用户登录 → 生成 JWT（payload 仅含 session_id）
    2. 完整用户信息存入 Redis: USER_SESSION:{session_id}
    3. 请求时从 JWT 取 session_id → 从 Redis 取用户信息
    4. 滑动过期: TTL 低于 50% 时自动续期
    """
    print("\n--- 用户会话存储 ---")

    session_id = "demo-session-001"
    redis_key = f"USER_SESSION:{session_id}"

    # 存储用户会话信息
    session_data = {
        "user_id": 1,
        "username": "admin",
        "tenant_id": 1,
        "roles": ["admin", "super_admin"],
        "permissions": ["*"],
        "login_time": time.time(),
        "login_ip": "127.0.0.1",
    }

    # SET with TTL
    expire_seconds = 60 * 60 * 12  # 12小时
    await r.set(redis_key, json.dumps(session_data), ex=expire_seconds)
    print(f"  ✅ 会话已存储: {redis_key} (TTL={expire_seconds}s)")

    # 读取会话信息
    cached = await r.get(redis_key)
    if cached:
        user_info = json.loads(cached)
        print(f"  📖 读取会话: 用户={user_info['username']}, 租户={user_info['tenant_id']}")

    # 获取剩余 TTL
    ttl = await r.ttl(redis_key)
    print(f"  ⏰ 剩余 TTL: {ttl}秒")

    # 模拟滑动过期（Token TTL 低于 50% 时续期）
    threshold = expire_seconds * 0.5
    if ttl < threshold:
        await r.expire(redis_key, expire_seconds)
        print(f"  🔄 滑动过期: TTL 已续期到 {expire_seconds}秒")


# ============================================================
# 3. Token 存储
# ============================================================
async def demo_token_storage(r: redis.Redis):
    """
    演示 Token 存储。

    FastapiAdmin 中:
    - access_token: 短期令牌，存储在 Redis
    - refresh_token: 长期令牌，用于刷新 access_token
    """
    print("\n--- Token 存储 ---")

    user_id = 1

    access_key = f"access_token:{user_id}"
    access_token = "eyJhbGciOiJIUzI1NiJ9.demo_token"
    await r.set(access_key, access_token, ex=60 * 60 * 12)
    print(f"  ✅ access_token 已存储")

    refresh_key = f"refresh_token:{user_id}"
    refresh_token = "eyJhbGciOiJIUzI1NiJ9.refresh_demo"
    await r.set(refresh_key, refresh_token, ex=60 * 60 * 24 * 7)
    print(f"  ✅ refresh_token 已存储")

    stored = await r.get(access_key)
    print(f"  🔐 Token 验证: {'有效' if stored else '无效/已过期'}")


# ============================================================
# 4. 系统参数缓存（Hash 类型）
# ============================================================
async def demo_system_cache(r: redis.Redis):
    """
    演示系统参数和数据字典缓存。

    FastapiAdmin 中:
    - ParamsService.init_cache(): 系统参数 → Redis Hash
    - DictDataService.init_cache(): 数据字典 → Redis JSON
    - TenantService.init_cache(): 租户配置 → Redis
    """
    print("\n--- 系统参数缓存 ---")

    # Hash 存储系统参数
    cache_key = "system_config"
    params = {
        "site_name": "FastapiAdmin",
        "site_logo": "/static/logo.png",
        "copyright": "© 2024 FastapiAdmin",
        "captcha_enable": "true",
    }
    await r.hset(cache_key, mapping=params)
    await r.expire(cache_key, 86400)
    print(f"  ✅ 系统参数已缓存到 {cache_key}")

    site_name = await r.hget(cache_key, "site_name")
    print(f"  📖 站点名称: {site_name}")

    all_params = await r.hgetall(cache_key)
    print(f"  📖 所有参数: {all_params}")

    # JSON 存储数据字典
    dict_key = "system_dict"
    dict_data = {
        "sys_user_sex": [
            {"label": "男", "value": "1"},
            {"label": "女", "value": "2"},
        ],
        "sys_normal_disable": [
            {"label": "正常", "value": "1"},
            {"label": "停用", "value": "0"},
        ],
    }
    await r.set(dict_key, json.dumps(dict_data))
    print(f"  ✅ 数据字典已缓存到 {dict_key}")


# ============================================================
# 5. 验证码存储
# ============================================================
async def demo_captcha(r: redis.Redis):
    """
    演示验证码存储。

    FastapiAdmin 中验证码 60 秒过期，验证后立即删除。
    """
    print("\n--- 验证码存储 ---")

    captcha_id = "captcha-uuid-001"
    captcha_key = f"captcha_codes:{captcha_id}"
    captcha_text = "A7x9"

    await r.set(captcha_key, captcha_text, ex=60)
    print(f"  ✅ 验证码已存储 (60秒有效)")

    stored = await r.get(captcha_key)
    if stored and stored.upper() == captcha_text.upper():
        await r.delete(captcha_key)
        print(f"  ✅ 验证码验证成功（一次性使用）")


# ============================================================
# 6. 管道 (Pipeline) 批量操作
# ============================================================
async def demo_pipeline(r: redis.Redis):
    """Pipeline 将多个命令打包一次性发送，减少网络往返。"""
    print("\n--- Pipeline 批量操作 ---")

    pipe = r.pipeline()
    pipe.set("batch:key1", "value1", ex=300)
    pipe.set("batch:key2", "value2", ex=300)
    pipe.set("batch:key3", "value3", ex=300)
    pipe.get("batch:key1")
    pipe.get("batch:key2")
    results = await pipe.execute()
    print(f"  ✅ Pipeline 执行完成，结果: {results}")


# ============================================================
# 7. Redis Key 命名规范（与 RedisInitKeyConfig 一致）
# ============================================================
def demo_key_patterns():
    """FastapiAdmin 中定义的 Redis Key 模式"""
    print("\n--- Redis Key 命名规范 ---")
    patterns = {
        "access_token:{user_id}": "用户的 access_token",
        "refresh_token:{user_id}": "用户的 refresh_token",
        "USER_SESSION:{session_id}": "用户完整会话信息",
        "captcha_codes:{captcha_id}": "图片验证码（60秒过期）",
        "system_config": "系统参数（Hash 类型）",
        "tenant_config": "租户配置（Hash 类型）",
        "system_dict": "数据字典（JSON 字符串）",
        "scheduler_job_lock": "APScheduler 分布式锁",
        "fastapiadmin:request_limiter:{ip}": "请求限流计数器",
    }
    for pattern, desc in patterns.items():
        print(f"  {pattern:50s} → {desc}")


# ============================================================
# 入口
# ============================================================
async def main():
    print("=" * 60)
    print("Redis 学习案例 - 缓存与会话管理")
    print("=" * 60)

    r = await create_redis_connection()
    if r is None:
        print("\n⚠️ 跳过 Redis 演示（无法连接）")
        demo_key_patterns()
        return

    try:
        await demo_session_storage(r)
        await demo_token_storage(r)
        await demo_system_cache(r)
        await demo_captcha(r)
        await demo_pipeline(r)
        demo_key_patterns()

        await r.flushdb()
        print("\n🧹 演示数据已清理")
    finally:
        await r.close()
        print("✅ Redis 连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
