"""
=============================================================
httpx 学习案例 - 异步 HTTP 客户端
=============================================================

httpx 是一个支持同步和异步的 HTTP 客户端库，是 requests 的现代替代品。
在 FastapiAdmin 中，httpx 用于:
  - IP 归属地查询（登录时对外发起 HTTP 请求）
  - 第三方 OAuth 登录（GitHub、Gitee 等）回调验证
  - AI 大模型 API 调用

官方文档: https://www.python-httpx.org/

安装: pip install httpx

运行方式:
    python 12_httpx_client.py
"""

import asyncio
import time


# ============================================================
# 1. 同步请求 - 类似 requests 的用法
# ============================================================
def demo_sync():
    """httpx 的同步 API 与 requests 几乎一样。"""
    import httpx

    print("--- 同步请求 ---")

    response = httpx.get("https://httpbin.org/get", params={"name": "FastapiAdmin"})
    print(f"  状态码: {response.status_code}")
    print(f"  JSON 数据: {response.json().get('args', {})}")

    response = httpx.post(
        "https://httpbin.org/post",
        json={"username": "admin", "action": "login"},
    )
    print(f"  POST 状态码: {response.status_code}")


# ============================================================
# 2. 异步请求 - FastapiAdmin 主要使用方式
# ============================================================
async def demo_async():
    """在 FastAPI 的 async 路由中，必须使用异步 HTTP 客户端。"""
    import httpx

    print("\n--- 异步请求 ---")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("https://httpbin.org/get")
        print(f"  异步 GET 状态码: {response.status_code}")

        response = await client.post(
            "https://httpbin.org/post",
            json={"msg": "来自异步请求"},
        )
        print(f"  异步 POST 状态码: {response.status_code}")


# ============================================================
# 3. 并发请求 - asyncio.gather
# ============================================================
async def demo_concurrent():
    """同时发送多个请求，大幅提升速度。"""
    import httpx

    print("\n--- 并发请求 ---")

    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]

    # 串行
    start = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in urls:
            await client.get(url)
    serial_time = time.time() - start
    print(f"  串行耗时: {serial_time:.1f}秒")

    # 并发
    start = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.get(url) for url in urls]
        await asyncio.gather(*tasks)
    concurrent_time = time.time() - start
    print(f"  并发耗时: {concurrent_time:.1f}秒")
    print(f"  提速: {serial_time / concurrent_time:.1f}x")


# ============================================================
# 4. Client 复用 - 连接池
# ============================================================
async def demo_client_reuse():
    """复用 AsyncClient 利用连接池，避免每次请求新建 TCP 连接。"""
    import httpx

    print("\n--- Client 复用（连接池）---")

    async with httpx.AsyncClient(
        base_url="https://httpbin.org",
        timeout=httpx.Timeout(10.0),
        headers={"User-Agent": "FastapiAdmin/1.0"},
    ) as client:
        r1 = await client.get("/get")
        r2 = await client.get("/ip")
        r3 = await client.get("/user-agent")
        print(f"  3 个请求完成，共享连接池 ✅")
        print(f"  User-Agent: {r3.json().get('user-agent')}")


# ============================================================
# 5. 超时与错误处理
# ============================================================
async def demo_error_handling():
    """httpx 的超时和错误处理。"""
    import httpx

    print("\n--- 超时与错误处理 ---")

    async with httpx.AsyncClient() as client:
        # 超时
        try:
            await client.get("https://httpbin.org/delay/5", timeout=2.0)
        except httpx.TimeoutException:
            print("  ✅ 请求超时被正确捕获")

        # 连接错误
        try:
            await client.get("http://localhost:99999")
        except httpx.ConnectError:
            print("  ✅ 连接错误被正确捕获")

        # HTTP 状态码检查
        response = await client.get("https://httpbin.org/status/404")
        print(f"  404 响应: status={response.status_code}")


# ============================================================
# 6. httpx vs requests 对比
# ============================================================
def comparison():
    """httpx 与 requests 的对比"""
    print("\n--- httpx vs requests ---")
    table = [
        ("同步请求", "requests.get(url)", "httpx.get(url)"),
        ("异步请求", "❌ 不支持", "httpx.AsyncClient()"),
        ("HTTP/2", "❌ 不支持", "✅ 支持"),
        ("连接池", "Session()", "Client() / AsyncClient()"),
        ("超时控制", "timeout=秒(单一)", "Timeout(connect,read,write,pool)"),
    ]
    print(f"  {'功能':12s} {'requests':25s} {'httpx':30s}")
    print(f"  {'─'*12} {'─'*25} {'─'*30}")
    for feature, req, htx in table:
        print(f"  {feature:12s} {req:25s} {htx:30s}")


# ============================================================
# 入口
# ============================================================
async def main():
    print("=" * 60)
    print("httpx 学习案例 - 异步 HTTP 客户端")
    print("=" * 60)

    demo_sync()
    await demo_async()
    await demo_concurrent()
    await demo_client_reuse()
    await demo_error_handling()
    comparison()


if __name__ == "__main__":
    asyncio.run(main())
