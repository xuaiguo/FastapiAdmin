"""
=============================================================
Pydantic v2 学习案例 - 数据模型验证
=============================================================

Pydantic v2 是 Python 的数据验证库，FastAPI 深度依赖它。
注意: 本文件专注于数据模型验证，配置管理请参见 05_pydantic_settings.py。

在 FastapiAdmin 中，Pydantic v2 用于:
  - API 请求参数验证（Schema）
  - API 响应数据序列化
  - 自定义验证器
  - 模型继承与组合

官方文档: https://docs.pydantic.dev/latest/

运行方式:
    python 13_pydantic_models.py
"""

from datetime import datetime
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    computed_field,
)


# ============================================================
# 1. 基础模型 - 声明即验证
# ============================================================
class UserCreate(BaseModel):
    """创建用户的请求模型。"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    nickname: str = Field(default="", description="昵称")
    age: int | None = Field(default=None, ge=0, le=200, description="年龄")

    model_config = ConfigDict(str_strip_whitespace=True)


def demo_basic_model():
    """基础模型验证演示"""
    print("--- 基础模型验证 ---")

    # ✅ 有效数据
    user = UserCreate(username="  admin  ", email="admin@example.com", password="123456")
    print(f"  ✅ username='{user.username}' (空格已自动去除)")

    # ❌ 无效数据
    try:
        UserCreate(username="ab", email="not-email", password="123")
    except Exception:
        print("  ❌ 验证失败: 用户名太短、密码太短")

    # 类型自动转换
    user2 = UserCreate(username="test", email="t@x.com", password="password", age="25")
    print(f"  ✅ age={user2.age} (str '25' → int 25)")


# ============================================================
# 2. 自定义验证器
# ============================================================
class UserRegister(UserCreate):
    """用户注册模型 - 带自定义验证器。"""
    confirm_password: str = Field(..., description="确认密码")
    phone: str | None = Field(default=None, description="手机号")

    @field_validator("username")
    @classmethod
    def username_no_special_chars(cls, v: str) -> str:
        forbidden = ["<", ">", "&", '"', "'"]
        if any(c in v for c in forbidden):
            raise ValueError(f"用户名不能包含特殊字符")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v and (len(v) != 11 or not v.isdigit()):
            raise ValueError("手机号必须是11位数字")
        return v

    @model_validator(mode="after")
    def check_passwords_match(self):
        """跨字段验证: 密码一致性"""
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


def demo_validators():
    """验证器演示"""
    print("\n--- 自定义验证器 ---")

    user = UserRegister(
        username="newuser", email="new@example.com",
        password="123456", confirm_password="123456", phone="13800138000",
    )
    print(f"  ✅ 注册成功: {user.username}")

    try:
        UserRegister(username="test", email="t@x.com", password="123456", confirm_password="654321")
    except Exception:
        print("  ❌ 密码不一致被拦截")

    try:
        UserRegister(
            username="<script>alert(1)</script>", email="x@x.com",
            password="123456", confirm_password="123456",
        )
    except Exception:
        print("  ❌ XSS 注入被拦截")


# ============================================================
# 3. 响应模型 - 数据序列化
# ============================================================
class UserResponse(BaseModel):
    """用户响应模型 - 控制返回给前端的数据。"""
    id: int
    username: str
    email: str
    nickname: str = ""
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def display_name(self) -> str:
        return self.nickname or self.username


def demo_response_model():
    """响应模型演示"""
    print("\n--- 响应模型 ---")

    user = UserResponse(
        id=1, username="admin", email="admin@example.com",
        nickname="管理员", created_at=datetime.now(),
    )

    data = user.model_dump()
    print(f"  model_dump(): {list(data.keys())}")

    safe_data = user.model_dump(exclude={"email"})
    print(f"  排除 email: {list(safe_data.keys())}")
    print(f"  display_name: {user.display_name}")


# ============================================================
# 4. 模型继承与部分更新
# ============================================================
class BaseSchema(BaseModel):
    """基础 Schema"""
    model_config = ConfigDict(from_attributes=True)


class PaginationSchema(BaseSchema):
    """分页参数"""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class UserUpdate(BaseSchema):
    """更新用户（所有字段可选）"""
    nickname: str | None = None
    email: str | None = None


def demo_inheritance():
    """模型继承演示"""
    print("\n--- 模型继承 ---")

    pagination = PaginationSchema(page=2, size=10)
    print(f"  分页: page={pagination.page}, size={pagination.size}")

    update = UserUpdate(nickname="新昵称")
    update_data = update.model_dump(exclude_none=True)
    print(f"  部分更新: {update_data}")


# ============================================================
# 5. 枚举类型
# ============================================================
class StatusEnum(int, Enum):
    DISABLED = 0
    NORMAL = 1


class UserWithEnum(BaseSchema):
    username: str
    status: StatusEnum = StatusEnum.NORMAL


def demo_enum():
    """枚举类型演示"""
    print("\n--- 枚举类型 ---")

    user = UserWithEnum(username="admin", status=1)
    print(f"  status={user.status} (int 1 → {user.status.name})")

    try:
        UserWithEnum(username="test", status=99)
    except Exception:
        print("  ❌ 无效枚举值 99 被拦截")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Pydantic v2 学习案例 - 数据模型验证")
    print("=" * 60)

    demo_basic_model()
    demo_validators()
    demo_response_model()
    demo_inheritance()
    demo_enum()
