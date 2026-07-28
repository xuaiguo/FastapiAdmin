"""
=============================================================
Loguru 学习案例 - 日志框架
=============================================================

Loguru 是一个简洁强大的 Python 日志库，替代标准库 logging。
在 FastapiAdmin 中，Loguru 用于:
  - 全局日志输出（控制台 + 文件）
  - 请求日志记录
  - 错误追踪（自动捕获异常堆栈）
  - 按级别/时间分割日志文件

官方文档: https://loguru.readthedocs.io/

安装: pip install loguru

运行方式:
    python 11_loguru_logging.py
"""

import sys
import time
from pathlib import Path


# ============================================================
# 1. 基础用法 - 开箱即用
# ============================================================
def demo_basic():
    """
    Loguru 最大的优势: 无需配置，导入即可使用。

    对比标准库 logging:
    - logging: 需要创建 logger、设置 handler、formatter、level...
    - loguru: from loguru import logger → 直接 logger.info()
    """
    from loguru import logger

    print("--- 基础日志 ---")

    # 日志级别（从低到高）
    logger.debug("这是 DEBUG 级别 - 调试信息")
    logger.info("这是 INFO 级别 - 一般信息")
    logger.success("这是 SUCCESS 级别 - 操作成功")
    logger.warning("这是 WARNING 级别 - 警告信息")
    logger.error("这是 ERROR 级别 - 错误信息")
    logger.critical("这是 CRITICAL 级别 - 严重错误")


# ============================================================
# 2. 格式化输出
# ============================================================
def demo_formatting():
    """Loguru 支持 {} 占位符和富文本格式。"""
    from loguru import logger

    print("\n--- 格式化输出 ---")

    username = "admin"
    tenant_id = 1
    logger.info("用户 {} 登录成功，租户ID: {}", username, tenant_id)

    logger.info("✅ 数据库初始化完成")
    logger.warning("⚠️ 配置项缺失，使用默认值")
    logger.error("❌ 操作失败: {}", "权限不足")


# ============================================================
# 3. 配置日志输出 - 自定义格式和目标
# ============================================================
def demo_configuration():
    """配置 Loguru 的输出格式和目标（控制台、文件）。"""
    from loguru import logger

    print("\n--- 自定义配置 ---")

    # 移除默认处理器
    logger.remove()

    # 添加控制台输出（自定义格式）
    logger.add(
        sys.stdout,  # 输出到 stdout（与 print 同流，避免 Windows 下顺序错乱）
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )

    # 添加文件输出（按天分割 + 自动清理）
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",       # 每天午夜分割
        retention="7 days",     # 保留 7 天
        compression="zip",      # 旧日志自动压缩
        encoding="utf-8",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )

    logger.info("日志配置完成 - 同时输出到控制台和文件")
    logger.info("日志文件位置: {}", log_dir.absolute())


# ============================================================
# 4. 异常捕获
# ============================================================
def demo_exception():
    """Loguru 的 @logger.catch 装饰器和 logger.exception() 方法。"""
    from loguru import logger

    print("\n--- 异常捕获 ---")

    logger.info("-----------------------------------------------------------------------")
    # 方式1: @logger.catch 装饰器
    @logger.catch
    def risky_division(a: int, b: int) -> float:
        return a / b

    result = risky_division(10, 0)
    print(f"  risky_division(10, 0) = {result}")
    logger.info("-----------------------------------------------------------------------")

    # 方式2: logger.exception() 在 except 块中使用
    try:
        data = {"key": "value"}
        _ = data["nonexistent"]
    except KeyError:
        logger.exception("字典键不存在")
    logger.info("-----------------------------------------------------------------------")

    # 方式3: logger.opt(exception=True)
    try:
        int("not_a_number")
    except ValueError:
        logger.opt(exception=True).warning("类型转换失败，使用默认值 0")
    logger.info("-----------------------------------------------------------------------")

# ============================================================
# 5. 性能计时
# ============================================================
def demo_timing():
    """使用 Loguru 记录代码执行时间"""
    from loguru import logger

    print("\n--- 性能计时 ---")

    start = time.time()
    time.sleep(0.1)
    elapsed = time.time() - start
    logger.info("操作耗时: {:.3f}秒", elapsed)

    class Timer:
        def __init__(self, name: str):
            self.name = name
        def __enter__(self):
            self.start = time.time()
            return self
        def __exit__(self, *args):
            elapsed = time.time() - self.start
            logger.info("{} 耗时: {:.3f}秒", self.name, elapsed)

    with Timer("数据库查询"):
        time.sleep(0.05)

    with Timer("Redis 缓存"):
        time.sleep(0.02)


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Loguru 学习案例 - 日志框架")
    print("=" * 60)

    # 先配置 logger（remove 默认处理器 + 添加自定义处理器）
    demo_configuration()
    # 再运行其他 demo（使用已配置好的 logger）
    demo_basic()
    demo_formatting()
    demo_exception()
    demo_timing()
