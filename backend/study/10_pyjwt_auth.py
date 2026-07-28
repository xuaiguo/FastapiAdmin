"""
=============================================================
PyJWT 学习案例 - JWT Token 生成与验证
=============================================================

PyJWT 是 Python 的 JWT (JSON Web Token) 库。
在 FastapiAdmin 中，PyJWT 用于用户认证:
  - 登录时生成 access_token 和 refresh_token
  - 请求时验证 Token 有效性
  - JWT payload 仅包含 session_id，完整用户信息存在 Redis 中
  - 支持 Token 滑动过期（TTL 低于 50% 时自动续期）

官方文档: https://pyjwt.readthedocs.io/

安装: pip install PyJWT

运行方式:
    python 10_pyjwt_auth.py
"""

import time
from datetime import datetime, timedelta, timezone

import jwt


# ============================================================
# 1. 基础 Token 生成与验证
# ============================================================
def demo_basic_jwt():
    """
    基础 JWT 操作。

    JWT 结构: Header.Payload.Signature
    - Header: 算法和类型 {"alg": "HS256", "typ": "JWT"}
    - Payload: 数据（可自定义字段）
    - Signature: 签名（用密钥保证不可篡改）
    """
    print("--- 基础 JWT ---")

    SECRET_KEY = "your-secret-key-at-least-32-chars-long!!"  # 生产环境用 settings.SECRET_KEY
    ALGORITHM = "HS256"             # 与 FastapiAdmin 配置一致

    # 生成 Token
    payload = {
        "user_id": 1,
        "username": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),  # 12小时后过期
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"  生成的 Token: {token[:50]}...")

    # 验证 Token
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"  解码结果: user_id={decoded['user_id']}, username={decoded['username']}")

    # 验证过期 Token
    expired_payload = {
        "user_id": 1,
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # 已过期
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    try:
        jwt.decode(expired_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        print("  ✅ 过期 Token 被正确拒绝: ExpiredSignatureError")

    # 验证篡改的 Token
    tampered = token[:-5] + "XXXXX"  # 修改签名部分
    try:
        jwt.decode(tampered, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidSignatureError:
        print("  ✅ 篡改 Token 被正确拒绝: InvalidSignatureError")


# ============================================================
# 2. FastapiAdmin 风格的 Session-based JWT
# ============================================================
def demo_session_jwt():
    """
    FastapiAdmin 的 JWT 设计:
    - Payload 只存 session_id（UUID），不存用户信息
    - 完整用户信息存在 Redis: USER_SESSION:{session_id}
    - 好处: 可以随时让 Token 失效（删除 Redis 中的 session）
    """
    import uuid

    print("\n--- Session-based JWT（FastapiAdmin 风格）---")

    SECRET_KEY = "fastapiadmin-secret-key-at-least-32-chars"
    ALGORITHM = "HS256"

    # 1. 登录时: 生成 session_id 和 Token
    session_id = str(uuid.uuid4())
    payload = {
        "sub": session_id,  # JWT 标准字段 sub = subject（主体）
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        "iat": datetime.now(timezone.utc),  # 签发时间
        "type": "access",   # token 类型: access / refresh
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"  1️⃣ session_id: {session_id}")
    print(f"     access_token: {access_token[:50]}...")

    # 此时应将用户完整信息存入 Redis:
    # await redis.set(f"USER_SESSION:{session_id}", json.dumps(user_info), ex=12*3600)

    # 2. 请求时: 从 Token 取 session_id，再从 Redis 取用户信息
    decoded = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    extracted_session_id = decoded["sub"]
    print(f"  2️⃣ 从 Token 提取 session_id: {extracted_session_id}")
    # user_info = await redis.get(f"USER_SESSION:{extracted_session_id}")

    # 3. 登出时: 删除 Redis 中的 session（Token 自动失效）
    # await redis.delete(f"USER_SESSION:{session_id}")
    print(f"  3️⃣ 删除 Redis session → Token 即使未过期也无法使用")


# ============================================================
# 3. access_token + refresh_token 双 Token 机制
# ============================================================
def demo_dual_token():
    """
    FastapiAdmin 的双 Token 机制:
    - access_token: 短期令牌（12小时），用于 API 请求
    - refresh_token: 长期令牌（12小时），用于刷新 access_token
    - 当 access_token 过期时，前端用 refresh_token 换取新的 access_token
    """
    print("\n--- 双 Token 机制 ---")

    SECRET_KEY = "fastapiadmin-secret-key-at-least-32-chars"
    ALGORITHM = "HS256"
    session_id = "demo-session-001"

    # 生成 access_token
    access_payload = {
        "sub": session_id,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    # 生成 refresh_token
    refresh_payload = {
        "sub": session_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    print(f"  access_token 过期时间: 12小时")
    print(f"  refresh_token 过期时间: 7天")

    # 模拟 Token 刷新流程
    def refresh_access_token(refresh_tok: str) -> str:
        """用 refresh_token 换取新的 access_token"""
        decoded = jwt.decode(refresh_tok, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded.get("type") != "refresh":
            raise ValueError("不是有效的 refresh_token")

        new_payload = {
            "sub": decoded["sub"],
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        }
        return jwt.encode(new_payload, SECRET_KEY, algorithm=ALGORITHM)

    new_token = refresh_access_token(refresh_token)
    print(f"  ✅ Token 刷新成功: {new_token[:50]}...")


# ============================================================
# 4. 滑动过期（Token 续期）
# ============================================================
def demo_sliding_expiration():
    """
    FastapiAdmin 的滑动过期机制:
    - 每次请求检查 Token 剩余 TTL
    - 如果 TTL < 总有效期的 50%，自动续期
    - 用户活跃时 Token 永不过期，长时间不操作才过期
    """
    print("\n--- 滑动过期 ---")

    total_expire = 12 * 3600  # 总有效期 12小时（秒）
    threshold = total_expire * 0.5  # 50% 阈值

    scenarios = [
        ("刚登录", total_expire - 60, "不续期（TTL 充足）"),
        ("使用 5 小时", total_expire - 5 * 3600, "不续期（> 50%）"),
        ("使用 7 小时", total_expire - 7 * 3600, "✅ 续期（< 50%）"),
        ("使用 11 小时", total_expire - 11 * 3600, "✅ 续期（< 50%）"),
    ]

    for desc, remaining_ttl, action in scenarios:
        below_threshold = remaining_ttl < threshold
        print(f"  {desc:15s} → 剩余 {remaining_ttl//3600}h → {action}")


# ============================================================
# 5. JWT 安全最佳实践
# ============================================================
def best_practices():
    """JWT 安全最佳实践"""
    print("\n--- 最佳实践 ---")
    practices = [
        "✅ 密钥足够长且随机（至少 32 字符）",
        "✅ 设置合理的过期时间",
        "✅ 使用 refresh_token 机制，避免频繁重新登录",
        "✅ JWT payload 不要存敏感信息（密码、身份证等）",
        "✅ 配合 Redis session 实现主动失效（登出、踢人）",
        "✅ 生产环境考虑 RS256 非对称加密（公私钥分离）",
        "⚠️ JWT 一旦签发，在过期前无法撤销（除非配合 Redis）",
        "⚠️ Token 必须通过 HTTPS 传输，防止中间人窃取",
    ]
    for p in practices:
        print(f"  {p}")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("PyJWT 学习案例 - JWT Token 生成与验证")
    print("=" * 60)

    demo_basic_jwt()
    demo_session_jwt()
    demo_dual_token()
    demo_sliding_expiration()
    best_practices()
