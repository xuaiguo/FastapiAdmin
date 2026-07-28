"""
=============================================================
APScheduler 学习案例 - 定时任务调度
=============================================================

APScheduler (Advanced Python Scheduler) 是一个任务调度库。
在 FastapiAdmin 中，APScheduler 用于:
  - 定时执行系统维护任务
  - 工作流引擎调度
  - 定时数据同步
  - 支持分布式锁（通过 Redis）

官方文档: https://apscheduler.readthedocs.io/

安装: pip install apscheduler

运行方式:
    python 09_apscheduler_demo.py

本文件演示:
  1. 调度器初始化（与 FastapiAdmin 的 SchedulerUtil 一致）
  2. Cron 表达式定时任务
  3. 间隔执行任务
  4. 一次性延迟任务
  5. 任务管理（增删改查）
  6. 错误处理与事件监听
"""

import asyncio
from datetime import datetime, timedelta


# ============================================================
# 1. 基础调度器使用
# ============================================================
def demo_basic_scheduler():
    """
    基础调度器演示。

    APScheduler 四大组件:
    - Trigger（触发器）: 定义任务何时执行
    - Job Store（任务存储）: 存储已调度的任务
    - Executor（执行器）: 执行任务
    - Scheduler（调度器）: 协调以上组件
    """
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger

    # 创建异步调度器（与 FastapiAdmin 的 SchedulerUtil 类似）
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # ---- Cron 触发器（定时执行）----

    def daily_cleanup():
        """每天凌晨 2:00 执行清理任务"""
        print(f"[{datetime.now()}] 🧹 每日清理任务执行中...")

    scheduler.add_job(
        daily_cleanup,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_cleanup",
        name="每日清理",
        replace_existing=True,
    )

    # Cron 表达式示例
    cron_examples = [
        ("每天 08:30", CronTrigger(hour=8, minute=30)),
        ("每周一 09:00", CronTrigger(day_of_week="mon", hour=9)),
        ("每月1号 00:00", CronTrigger(day=1, hour=0, minute=0)),
        ("每5分钟", CronTrigger(minute="*/5")),
        ("每小时整点", CronTrigger(minute=0)),
        ("工作日 09:00-18:00", CronTrigger(day_of_week="mon-fri", hour="9-18", minute=0)),
    ]

    print("Cron 触发器示例:")
    for desc, _ in cron_examples:
        print(f"  {desc}")

    # ---- Interval 触发器（间隔执行）----

    def health_check():
        """每 30 秒执行健康检查"""
        print(f"[{datetime.now()}] 💓 健康检查...")

    scheduler.add_job(
        health_check,
        trigger=IntervalTrigger(seconds=30),
        id="health_check",
        name="健康检查",
    )

    print("\nInterval 触发器示例:")
    print("  每5秒 / 每10分钟 / 每2小时 / 每7天")

    # ---- Date 触发器（一次性执行）----

    def send_notification():
        """在指定时间发送通知"""
        print(f"[{datetime.now()}] 📨 发送通知...")

    run_time = datetime.now() + timedelta(minutes=1)
    scheduler.add_job(
        send_notification,
        trigger=DateTrigger(run_date=run_time),
        id="send_notification",
        name="发送通知",
    )
    print(f"\nDate 触发器: 将在 {run_time} 执行一次")

    return scheduler


# ============================================================
# 2. 任务管理（增删改查）
# ============================================================
def demo_job_management(scheduler):
    """演示任务的增删改查操作"""
    print("\n--- 任务管理 ---")

    jobs = scheduler.get_jobs()
    print(f"  📋 当前任务数: {len(jobs)}")
    for job in jobs:
        print(f"     - [{job.id}] {job.name} (下次: {job.next_run_time})")

    scheduler.pause_job("health_check")
    print("  ⏸️ 已暂停: health_check")

    scheduler.resume_job("health_check")
    print("  ▶️ 已恢复: health_check")

    from apscheduler.triggers.interval import IntervalTrigger
    scheduler.reschedule_job("health_check", trigger=IntervalTrigger(minutes=5))
    print("  ✏️ 已修改: health_check 改为每5分钟")

    # 恢复为30秒，方便观察执行效果
    scheduler.reschedule_job("health_check", trigger=IntervalTrigger(seconds=30))
    print("  ✏️ 已恢复: health_check 改回每30秒")

    # scheduler.remove_job("send_notification")
    # print("  🗑️ 已删除: send_notification")


# ============================================================
# 3. 带参数的任务
# ============================================================
def demo_parameterized_jobs(scheduler):
    """演示带参数的定时任务"""
    print("\n--- 带参数的任务 ---")

    def generate_report(report_type: str, recipients: list[str]):
        print(f"  📊 生成 {report_type} 报告，发送给: {recipients}")

    scheduler.add_job(
        generate_report,
        trigger="cron",
        hour=15, minute=51,
        args=["daily", ["admin@example.com"]],
        id="daily_report",
        name="每日报告",
    )
    print("  ✅ 已添加: 每日报告（带参数）")


# ============================================================
# 4. 错误处理
# ============================================================
def demo_error_handling(scheduler):
    """演示任务错误处理配置"""
    print("\n--- 错误处理 ---")

    def risky_task():
        import random
        if random.random() < 0.3:
            raise ValueError("模拟任务执行失败")
        print("  ✅ 任务执行成功")

    scheduler.add_job(
        risky_task,
        trigger="interval",
        seconds=20,
        id="risky_task",
        name="不稳定任务",
        max_instances=1,          # 最多1个实例同时运行
        coalesce=True,            # 错过的执行合并为1次
        misfire_grace_time=30,    # 错过30秒内仍执行
    )
    print("  ✅ 已添加: 不稳定任务")
    print("     - max_instances=1: 防止并发执行")
    print("     - coalesce=True: 合并错过的执行")
    print("     - misfire_grace_time=30: 30秒内的错过仍执行")


# ============================================================
# 5. 与 FastapiAdmin 的 SchedulerUtil 对应关系
# ============================================================
def explain_fastapiadmin_integration():
    """
    FastapiAdmin 中 APScheduler 的集成方式:

    1. 初始化 (init_app.py):
       await SchedulerUtil.init_scheduler(redis=app.state.redis)

    2. SchedulerUtil 提供的方法:
       - init_scheduler(redis): 初始化（使用 Redis 分布式锁）
       - add_job(...): 添加任务
       - remove_job(job_id): 删除任务
       - pause_job(job_id): 暂停任务
       - resume_job(job_id): 恢复任务
       - shutdown(wait): 关闭调度器

    3. 分布式锁:
       - Redis 锁防止多实例重复初始化调度器
       - Key: scheduler_job_lock

    4. 关闭 (init_app.py lifespan):
       await SchedulerUtil.shutdown(wait=True)
    """
    print("\n--- FastapiAdmin SchedulerUtil 集成 ---")
    print(explain_fastapiadmin_integration.__doc__)


# ============================================================
# 入口
# ============================================================
async def main():
    print("=" * 60)
    print("APScheduler 学习案例 - 定时任务调度")
    print("=" * 60)

    scheduler = demo_basic_scheduler()

    # 必须先启动调度器，否则 job.next_run_time 不存在
    scheduler.start()

    demo_job_management(scheduler)
    demo_parameterized_jobs(scheduler)
    demo_error_handling(scheduler)
    explain_fastapiadmin_integration()

    print("\n" + "=" * 60)
    print("调度器运行中（演示60秒...）")
    print("=" * 60)

    await asyncio.sleep(60)
    scheduler.shutdown(wait=True)
    print("✅ 调度器已关闭")


if __name__ == "__main__":
    asyncio.run(main())
