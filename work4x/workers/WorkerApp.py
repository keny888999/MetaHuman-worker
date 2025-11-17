from celery import Celery
import os
import sys
import platform

WORKERS_PATH = os.path.abspath(os.path.dirname(__file__))
WORK4X_PATH = os.path.abspath(os.path.join(WORKERS_PATH, ".."))
ROOT_PATH = os.path.abspath(os.path.join(WORK4X_PATH, ".."))

sys.path.insert(0, ROOT_PATH)
print(f"ROOT_PATH={ROOT_PATH}")

sys.path.insert(0, WORK4X_PATH)
print(f"WORK4X_PATH={WORK4X_PATH}")

print(f"WORKERS_PATH={WORKERS_PATH}")
sys.path.insert(0, WORKERS_PATH)

from work4x.config import CELERY_REDIS_HOST, CELERY_REDIS_PORT, CELERY_REDIS_DB


def App(name: str, worker_concurrency=1, imports=None):

    if not imports:
        imports = name

    app = Celery(name, include=[f"workers.{imports}"])                                # 创建 Celery 实例
    backend_url = f"redis://{CELERY_REDIS_HOST}:{CELERY_REDIS_PORT}/{CELERY_REDIS_DB}"

    app.conf.task_serializer = 'json'
    app.conf.broker_url = backend_url
    app.conf.result_backend = app.conf.broker_url
    app.conf.timezone = 'Asia/Shanghai'
    app.conf.task_default_queue = imports
    app.conf.worker_send_task_events = True
    app.conf.task_send_sent_event = False
    app.Task.resultrepr_maxsize = 100 * 1024

    app.conf.update(
        worker_concurrency=worker_concurrency,
        worker_prefetch_multiplier=1,
        task_track_started=True,
        task_send_success_event=True,
        # 序列化配置
        event_serializer='json',
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        task_remote_tracebacks=False,
        # 启用自定义状态的事件
        task_ignore_result=True,  # 必须为False才能发送状态事件
    )

    if platform.system() == 'Windows':
        app.conf.worker_pool="eventlet"

    print("App(" + name + ")")
    return app
