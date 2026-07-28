"""
=============================================================
Typer 学习案例 - CLI 命令行框架
=============================================================

Typer 是一个基于 Python 类型提示的 CLI 框架，由 FastAPI 的作者开发。
在 FastapiAdmin 的 main.py 中，Typer 用于构建 `run`、`revision`、`upgrade` 三个子命令。

官方文档: https://typer.tiangolo.com/

安装: pip install typer

运行方式:
    python 01_typer_cli.py                    # 查看帮助
    python 01_typer_cli.py hello              # 基础命令
    python 01_typer_cli.py hello --name 张三   # 带选项的命令
    python 01_typer_cli.py greet 李四          # 带参数的命令
    python 01_typer_cli.py calc add 10 20     # 子命令组
"""

from typing import Annotated, Optional

import typer

# ============================================================
# 1. 创建 Typer 应用（与 main.py 中 fastapiadmin_cli = typer.Typer() 相同）
# ============================================================
app = typer.Typer(
    help="Typer 学习案例 - 演示各种 CLI 功能",
    add_completion=False,  # 禁用自动补全脚本生成
)


# ============================================================
# 2. 基础命令 - 最简单的命令定义
# ============================================================
@app.command()
def hello(
    # 使用 Annotated 定义选项（--name），与 main.py 中的写法一致
    name: Annotated[str, typer.Option("--name", help="你的名字")] = "世界",
    count: Annotated[int, typer.Option("--count", help="重复次数")] = 1,
) -> None:
    """打招呼命令 - 演示基础选项用法"""
    for _ in range(count):
        # typer.secho 支持彩色输出，main.py 中也使用了此功能
        typer.secho(f"你好, {name}!", fg=typer.colors.GREEN)


# ============================================================
# 3. 必填参数 - typer.Argument vs typer.Option
# ============================================================
@app.command()
def greet(
    # Argument 是必填的位置参数（不需要 --前缀）
    name: Annotated[str, typer.Argument(help="被问候人的名字（必填）")],
    # Option 是可选的命名参数（需要 --前缀）
    formal: Annotated[bool, typer.Option("--formal", help="是否使用正式语气")] = False,
) -> None:
    """问候命令 - 演示 Argument（必填）和 Option（可选）的区别"""
    if formal:
        typer.echo(f"尊敬的 {name} 先生/女士，您好！")
    else:
        typer.echo(f"嘿, {name}!")


# ============================================================
# 4. 子命令组 - 类似 main.py 中的 revision/upgrade 分组
# ============================================================
# 创建子命令组
calc_app = typer.Typer(help="计算器命令组")


@calc_app.command("add")
def calc_add(
    a: Annotated[float, typer.Argument(help="第一个数字")],
    b: Annotated[float, typer.Argument(help="第二个数字")],
) -> None:
    """加法"""
    result = a + b
    typer.echo(f"{a} + {b} = {result}")


@calc_app.command("multiply")
def calc_multiply(
    a: Annotated[float, typer.Argument(help="第一个数字")],
    b: Annotated[float, typer.Argument(help="第二个数字")],
) -> None:
    """乘法"""
    result = a * b
    typer.echo(f"{a} × {b} = {result}")


# 将子命令组注册到主应用
app.add_typer(calc_app, name="calc")


# ============================================================
# 5. 枚举类型选项 - 与 main.py 中 EnvironmentEnum 用法一致
# ============================================================
from enum import Enum


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@app.command()
def log(
    level: Annotated[LogLevel, typer.Option("--level", help="日志级别")] = LogLevel.INFO,
    message: Annotated[str, typer.Argument(help="日志消息")] = "默认消息",
) -> None:
    """日志命令 - 演示枚举类型选项（Typer 自动验证输入值）"""
    # 根据级别显示不同颜色
    color_dict = {
        LogLevel.DEBUG: typer.colors.BLUE,
        LogLevel.INFO: typer.colors.GREEN,
        LogLevel.WARNING: typer.colors.YELLOW,
        LogLevel.ERROR: typer.colors.RED,
    }
    typer.secho(f"[{level.value.upper()}] {message}", fg=color_dict[level])


# ============================================================
# 6. 回调函数 (Callback) - 在所有子命令执行前运行
# ============================================================
@app.callback()
def main_callback(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="显示详细信息")] = False,
) -> None:
    """
    Typer 学习案例 CLI

    这是全局回调，在任何子命令之前执行。
    适合做全局初始化（如 main.py 中设置环境变量）。
    """
    if verbose:
        typer.echo("🔧 详细模式已开启")


# ============================================================
# 7. 确认提示与进度条
# ============================================================
@app.command()
def deploy(
    target: Annotated[str, typer.Argument(help="部署目标")] = "staging",
    force: Annotated[bool, typer.Option("--force", "-f", help="跳过确认")] = False,
) -> None:
    """部署命令 - 演示确认提示和进度条"""
    if not force:
        # typer.confirm 会提示用户确认
        confirmed = typer.confirm(f"确定要部署到 {target} 吗？")
        if not confirmed:
            typer.echo("已取消部署")
            raise typer.Exit(code=1)

    # 进度条演示
    with typer.progressbar(range(100), label=f"正在部署到 {target}") as progress:
        import time
        for item in progress:
            time.sleep(0.02)  # 模拟工作

    typer.secho(f"✅ 部署到 {target} 完成！", fg=typer.colors.GREEN)


# ============================================================
# 入口（与 main.py 的 if __name__ == "__main__" 一致）
# ============================================================
if __name__ == "__main__":
    app()
