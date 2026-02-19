import os
import sys
import atexit
import signal
import subprocess
import time
from os import name

from celery import Celery
from celery.schedules import crontab
from work4x.workers.App import app,WorkerApp
from work4x.workers.schedule.StreamAckCleaner import StreamAckCleaner
from work4x.utils.logger import logger
from work4x.config import WORKER_REDIS_URL,WORKER_REDIS_DB
backend_url = f"redis://{WORKER_REDIS_URL}/{WORKER_REDIS_DB}"

worker_name="clean_ack"
clean_tasks=[
    dict(stream_name="celery:events:progress",consumer_group="progress_consumers"),
    dict(stream_name="celery:events:started",consumer_group="started_consumers")
]

app.conf.update(
    task_ignore_result=False,
    result_backend=backend_url,
)

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # 每10秒执行一次
    print("on_after_configure 信号触发!")
    sender.add_periodic_task(10.0, clean_ack.s(), name='clean_ack')

    # 每周一早上7:30执行
    #sender.add_periodic_task(
    #    crontab(hour=7, minute=30, day_of_week=1),
    #    add.s(16, 16),
    #    name='add every monday at 7:30',
    #)

@app.task(name="run_clean",queue="clean_ack")
def clean_ack():
    for task in clean_tasks:
        stream_name = task["stream_name"]
        try:
           logger.info(f"cleaup [{stream_name}] ...")
           cleaner.cleanup_acked(**task)
        except Exception as e:
            logger.error(f"run_clean({stream_name}) failed: {str(e)}")

    return "finished"

# 注册信号处理器
def signal_handler(signum, frame):
    """信号处理函数"""
    print(f"\n收到信号 {signum}，正在停止所有 Celery 进程...")
    # 1. 首先尝试优雅地停止 worker
    try:
        # 发送 TERM 信号给当前进程组
        os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
    except:
        pass
    sys.exit(0)


def cleanup_celery_processes():
    """清理所有 Celery 进程"""
    import subprocess as sp
    print("清理 beat 进程...")
    commands = [
        ['pkill', '-9', '-f', 'job_clean_ack'],
    ]
    for cmd in commands:
        try:
            sp.run(cmd, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        except:
            pass
    # 额外等待
    time.sleep(1)


# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
atexit.register(cleanup_celery_processes)

cleaner=StreamAckCleaner(app.backend.client)
worker_app = WorkerApp(app)
worker_app.main("clean_ack",more_args=["--beat","-c 1"])