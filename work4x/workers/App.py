import json
import os
import platform
import time
from enum import Enum
from typing import Any

import orjson
from celery import Celery
from celery import Task
from celery.events.dispatcher import EventDispatcher
from pydantic import BaseModel

pwd = os.path.dirname(__file__)
dir_name = os.path.basename(pwd)
WORKERS_PATH = os.path.abspath(pwd)
WORK4X_PATH = os.path.abspath(os.path.join(WORKERS_PATH, ".."))
ROOT_PATH = os.path.abspath(os.path.join(WORK4X_PATH, ".."))

from work4x.RedisPublisher import RedisPublisher
from work4x.workers import app_config

app = Celery("workerApp")  # 创建 Celery 实例
app.config_from_object(app_config)

'''
backend_url = f"redis://{CELERY_REDIS_HOST}:{CELERY_REDIS_PORT}/{CELERY_REDIS_DB}"
app.conf.task_serializer = 'json'
app.conf.broker_url = backend_url
app.conf.result_backend = backend_url
app.conf.timezone = 'Asia/Shanghai'
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True
app.Task.resultrepr_maxsize = 100 * 1024

app.conf.update(
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_track_started=True,
    task_send_success_event=True,
    # 序列化配置
    event_serializer='json',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    # task_remote_tracebacks=False,
    # 启用自定义状态的事件
    task_ignore_result=False,  # 必须为False才能发送状态事件
)

# app.autodiscover_tasks(['workers.worker_*'])
'''


# 可以在运行时动态注册任务


def register_task(task_name, task_func, queue='celery'):
    """动态注册任务"""

    # 创建任务装饰器
    task_decorator = app.task(
        name=task_name,
        bind=True,
        queue=queue
    )

    # 装饰函数
    registered_task = task_decorator(task_func)

    return registered_task


class Work4xEvent(Enum):
    START = "work4x-task-started"
    SUCCESS = "work4x-task-succeeded"
    FAIL = "work4x-task-failed"
    STREAM = "work4x-task-stream"



class UsageItem(BaseModel):
    name: str ="" # task name
    input: int = 0  # token in
    output: int = 0  # token out
    duration: int = 0  # 按音视频时长计费（秒）
    coins: int = 0  # 按点数收费
    money: float = 0.0  # 按金额收费(元)
    costTime: int = 0.0  # 按耗时计费(秒)

class WorkerMetrics(BaseModel):
    startTime: int = 0
    endTime: int = 0
    items:list[UsageItem]=[]
    def __add__(self, other: "WorkerMetrics") -> "WorkerMetrics":
        self.items.extend(other["items"])
        return self


class Work4xTask(Task):
    dispatcher: EventDispatcher
    task_id: Any = None
    task_name: str = None
    metrics: WorkerMetrics = WorkerMetrics()
    usage: UsageItem = UsageItem()

    def broadcast_event(self, event_type: str, event_data={}):
        self.dispatcher.send(type=event_type, uuid=self.task_id, **event_data)  # pyright: ignore[reportArgumentType]

    def send_stream_event(self, task_id, chunk):
        self.backend.store_result(str(task_id), chunk, "STREAM", None, self.request)

    def send_progress_event(self, task_id, chunk):
        self.backend.store_result(str(task_id), chunk, "PROGRESS", None, self.request)

    def on_comfyui_started(self, prompt_id,api_key:str):
        self.send_event("comfyui-started", retry=True,retry_policy=None,prompt_id=prompt_id,api_key=api_key)

    def before_start(self, task_id, args, kwargs):
        print("====before_start====")
        self.task_id = task_id
        self.task_name = getattr(self.request, "task")
        self.usage.name=self.task_name
        self.metrics.startTime=int(time.time() * 1000)
        super().before_start(task_id, args, kwargs)

    def on_success(self, retval, task_id, args, kwargs):
        super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    def success(self, outputs, ext_metrics_items:list[UsageItem]=None) -> dict[str, Any]:
        if self.metrics.endTime == 0:
           self.metrics.endTime = int(time.time() * 1000)

        if self.usage.costTime==0:
            self.usage.costTime=int((self.metrics.endTime - self.metrics.startTime) / 1000)

        self.metrics.items = [self.usage]

        if ext_metrics_items:
            self.metrics.items.extend(ext_metrics_items)

        return dict(outputs=outputs, metrics=self.metrics.model_dump())


class WorkerApp:
    app: Celery
    redis: RedisPublisher

    def __init__(self, app: Celery) -> None:
        self.app = app

    @staticmethod
    def print_json(obj):
        print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)

    def init_redis(self, **args):
        self.redis = RedisPublisher(**args)
        self.redis.connect()

    def main(self, worker_name, more_args=[]):
        import argparse
        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-n', '--name', type=str, default=worker_name, help='worker name')
        parser.add_argument('-lv', '--log', type=str, default='info', help='log level')
        parser.add_argument('-c', '--concurrency', type=str, default='1', help='concurrency')
        parser.add_argument('-Q', '--queue', type=str, default=None, help='queue')
        args = parser.parse_args()

        worker_args = [
            'worker',
            f"--loglevel={args.log}",
            f"--concurrency={args.concurrency}",
            f"-n {worker_name}@%h"
        ]

        if platform.system() == 'Windows':
            worker_args.append("-P")
            worker_args.append("threads")
            # worker_args.append("eventlet")

        queue = args.queue
        if not queue:
            queue = worker_name
        worker_args.append("-Q")
        worker_args.append(queue)

        if more_args:
            worker_args.extend(more_args)

        print(f"ARGS:{worker_args}")
        self.app.worker_main(argv=worker_args)
