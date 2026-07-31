"""Oracle 密码加解密工具。

使用 base64 编码 + 简单混淆，防止密码明文存储在数据库中。
如需更高安全性，可替换为 cryptography.fernet.Fernet。
"""

import base64

_KEY = b"fastapiadmin-oracle-config-key-2024"


def encrypt_password(plain: str) -> str:
    """加密密码"""
    if not plain:
        return plain
    data = plain.encode("utf-8")
    xored = bytes(b ^ _KEY[i % len(_KEY)] for i, b in enumerate(data))
    return base64.b64encode(xored).decode("utf-8")


def decrypt_password(encrypted: str) -> str:
    """解密密码"""
    if not encrypted:
        return encrypted
    try:
        xored = base64.b64decode(encrypted.encode("utf-8"))
        data = bytes(b ^ _KEY[i % len(_KEY)] for i, b in enumerate(xored))
        return data.decode("utf-8")
    except Exception:
        # 兼容历史明文数据：如果解密失败，返回原值
        return encrypted
