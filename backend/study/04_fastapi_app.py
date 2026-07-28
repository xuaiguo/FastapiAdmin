"""
=============================================================
FastAPI 学习案例 - Web 框架核心功能
=============================================================

FastAPI 是一个高性能的 Python Web 框架，基于类型提示自动生成 API 文档。
在 FastapiAdmin 中，FastAPI 用于构建整个后端 API 系统。

官方文档: https://fastapi.tiangolo.com/

安装: pip install fastapi

运行方式:
    python 04_fastapi_app.py
    然后访问 http://localhost:8003/docs 查看 Swagger 文档

本文件演示 FastAPI 在 FastapiAdmin 中使用的核心功能:
  1. 工厂模式创建应用
  2. Lifespan 生命周期
  3. 路由与路由分组
  4. 依赖注入 (Depends)
  5. 中间件 (Middleware)
  6. 异常处理
  7. 静态文件服务
  8. 自定义 API 文档
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# ============================================================
# 1. Lifespan 生命周期（与 init_app.py 中 lifespan 一致）
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """
    FastAPI 生命周期管理器。

    在 FastapiAdmin 中用于初始化:
    - 数据库（自动建表 + 种子数据）
    - Redis 连接
    - 系统参数缓存
    - 定时任务调度器
    - 请求限流器
    """
    # --- 启动阶段 ---
    print("🚀 [Lifespan] 应用启动...")

    # 模拟数据库初始化
    app.state.db_initialized = True
    print("✅ 数据库初始化完成")

    # 模拟 Redis 连接
    app.state.redis_connected = True
    print("✅ Redis 连接已建立")

    # 模拟缓存初始化
    app.state.cache = {"system_params": {}, "dict_data": {}}
    print("✅ 缓存初始化完成")

    yield  # <-- 应用在此处开始接收请求

    # --- 关闭阶段 ---
    print("\n🛑 [Lifespan] 应用关闭...")
    app.state.redis_connected = False
    print("✅ Redis 连接已释放")
    app.state.db_initialized = False
    print("✅ 数据库连接已关闭")


# ============================================================
# 2. Pydantic 数据模型（Schema）
# ============================================================
class UserCreate(BaseModel):
    """创建用户的请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    created_at: str


class SuccessResponse(BaseModel):
    """
    统一成功响应格式。
    与 FastapiAdmin 中的 SuccessResponse 一致。
    """
    code: int = 200
    msg: str = "success"
    data: Any = None
    success: bool = True


# ============================================================
# 3. 依赖注入 (Depends)
# ============================================================
"""
FastapiAdmin 的依赖注入链:

Controller endpoint
  ├── Depends(db_getter)              → AsyncSession
  ├── Depends(redis_getter)           → Redis
  └── Depends(AuthPermission([...]))  → AuthSchema
       └── Depends(get_current_user)  [链式依赖]
"""


# 模拟数据库会话依赖
async def get_db():
    """
    模拟数据库会话依赖。

    在 FastapiAdmin 中，db_getter() 使用 yield 实现请求级事务:
    - 请求开始 → BEGIN 事务
    - 请求成功 → COMMIT
    - 请求异常 → ROLLBACK
    """
    print("📦 [DB] 开启数据库会话")
    db_session = {"id": "mock-session-001"}  # 模拟 AsyncSession
    try:
        yield db_session
    finally:
        print("📦 [DB] 关闭数据库会话")


# 模拟认证依赖
async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, "从请求头获取 token"] = None,
) -> dict:
    """
    模拟获取当前用户。

    在 FastapiAdmin 中:
    1. 从请求头提取 JWT token
    2. 解码获取 session_id
    3. 从 Redis 获取完整用户信息
    """
    # 模拟用户信息
    return {
        "id": 1,
        "username": "admin",
        "tenant_id": 1,
        "is_superuser": True,
    }


# 模拟权限检查
class RequirePermission:
    """
    权限检查依赖（与 FastapiAdmin 中 AuthPermission 类似）。

    用法:
        @router.get("/users")
        async def list_users(auth=Depends(RequirePermission("system:user:list"))):
            ...
    """

    def __init__(self, *permissions: str):
        self.permissions = permissions

    async def __call__(self, user: Annotated[dict, Depends(get_current_user)]) -> dict:
        # 超级管理员跳过权限检查
        if user.get("is_superuser"):
            return user
        # 检查权限（简化演示）
        print(f"🔐 [Auth] 检查权限: {self.permissions}")
        return user


# ============================================================
# 4. 路由与路由分组
# ============================================================
from fastapi import APIRouter

# 创建路由分组（与 FastapiAdmin 中各模块路由一致）
system_router = APIRouter(prefix="/system", tags=["系统管理"])
user_router = APIRouter(prefix="/user", tags=["用户管理"])


@system_router.get("/info")
async def system_info(request: Request):
    """系统信息"""
    return {
        "app_name": request.app.title,
        "db_initialized": getattr(request.app.state, "db_initialized", False),
        "redis_connected": getattr(request.app.state, "redis_connected", False),
    }


@user_router.get("/list", response_model=SuccessResponse)
async def list_users(
    db: Annotated[dict, Depends(get_db)],
    auth: Annotated[dict, Depends(RequirePermission("system:user:list"))],
):
    """
    用户列表 - 演示完整的依赖注入链。

    执行顺序:
    1. get_db() → 创建数据库会话
    2. get_current_user() → 从 token 获取用户
    3. RequirePermission() → 检查权限
    4. 执行业务逻辑
    """
    users = [
        {"id": 1, "username": "admin", "email": "admin@example.com", "created_at": "2024-01-01"},
        {"id": 2, "username": "test", "email": "test@example.com", "created_at": "2024-01-02"},
    ]
    return SuccessResponse(data=users)


@user_router.post("/create", response_model=SuccessResponse)
async def create_user(
    user_data: UserCreate,
    db: Annotated[dict, Depends(get_db)],
    auth: Annotated[dict, Depends(RequirePermission("system:user:create"))],
):
    """创建用户 - 演示 Pydantic 请求验证"""
    new_user = UserResponse(
        id=3,
        username=user_data.username,
        email=user_data.email,
        created_at="2024-06-30",
    )
    return SuccessResponse(data=new_user.model_dump())


# ============================================================
# 5. 异常处理（与 FastapiAdmin 的 CustomException 一致）
# ============================================================
class CustomException(Exception):
    """
    自定义异常类（与 FastapiAdmin 中 CustomException 一致）。

    FastapiAdmin 中所有业务错误都抛出此异常，
    然后由异常处理器统一捕获并返回结构化 JSON。
    """

    def __init__(self, msg: str = "服务器异常", code: int = 500, status_code: int = 500):
        self.msg = msg
        self.code = code
        self.status_code = status_code


def register_exceptions(app: FastAPI) -> None:
    """
    注册异常处理器（与 init_app.py 中 register_exceptions 一致）。
    """

    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "msg": exc.msg,
                "data": None,
                "success": False,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "msg": exc.detail,
                "data": None,
                "success": False,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "msg": f"服务器内部错误: {str(exc)}",
                "data": None,
                "success": False,
            },
        )


# ============================================================
# 6. 中间件（与 FastapiAdmin 的中间件管道一致）
# ============================================================
def register_middlewares(app: FastAPI) -> None:
    """
    注册中间件。

    FastapiAdmin 中间件执行顺序（从外到内）:
    CORS → RequestLog → GZip → CorrelationId → TenantMiddleware → 业务路由

    注意: add_middleware 是栈式添加，后添加的先执行。
    """
    # CORS 中间件（与 FastapiAdmin 中 CustomCORSMiddleware 类似）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip 压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 自定义请求日志中间件（演示）
    @app.middleware("http")
    async def request_log_middleware(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"📝 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        response.headers["X-Process-Time"] = str(process_time)
        return response


# ============================================================
# 7. 工厂函数创建应用（与 main.py 中 create_app 一致）
# ============================================================
def create_app() -> FastAPI:
    """
    工厂模式创建 FastAPI 应用。

    这是 FastapiAdmin 的应用创建模式:
    1. 创建 FastAPI 实例
    2. 注册异常处理器
    3. 注册中间件
    4. 注册路由
    5. 注册静态文件
    """
    app = FastAPI(
        title="🎉 FastAPI 学习案例 🎉",
        version="1.0.0",
        description="演示 FastapiAdmin 中使用的 FastAPI 核心功能",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 注册异常处理器
    register_exceptions(app)

    # 注册中间件
    register_middlewares(app)

    # 注册路由分组
    app.include_router(system_router, prefix="/api/v1")
    app.include_router(user_router, prefix="/api/v1")

    # 测试异常处理的端点
    @app.get("/api/v1/test-error")
    async def test_error():
        raise CustomException(msg="这是一个自定义错误", code=400, status_code=400)
        #raise HTTPException(400,'这是一个自定义HTTPException错误')


    # 健康检查端点
    @app.get("/api/v1/health")
    async def health():
        return {"status": "ok", "timestamp": time.time()}

    return app


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    print("启动 FastAPI 学习案例服务器...")
    print("访问 http://localhost:8003/docs 查看 Swagger 文档")
    print("访问 http://localhost:8003/redoc 查看 ReDoc 文档")
    print()

    uvicorn.run(
        "04_fastapi_app:create_app",
        host="127.0.0.1",
        port=8003,
        factory=True,
        reload=False,
    )
