from enum import Enum
from celery import Celery
import os
import sys
import platform
import orjson
from pathlib import Path
from celery.events.dispatcher import EventDispatcher
from celery import Task
import time

pwd = os.path.dirname(__file__)
dir_name = os.path.basename(pwd)
WORKERS_PATH = os.path.abspath(pwd)
WORK4X_PATH = os.path.abspath(os.path.join(WORKERS_PATH, ".."))
ROOT_PATH = os.path.abspath(os.path.join(WORK4X_PATH, ".."))

sys.path.insert(0, ROOT_PATH)
print(f"ROOT_PATH={ROOT_PATH}")

sys.path.insert(0, WORK4X_PATH)
print(f"WORK4X_PATH={WORK4X_PATH}")

print(f"WORKERS_PATH={WORKERS_PATH}")
sys.path.insert(0, WORKERS_PATH)

from work4x.config import WORKER_REDIS_URL, WORKER_REDIS_DB
from classes.TaskRequest import TaskRequest
from RedisPublisher import RedisPublisher


class Work4xEvent(Enum):
    START = "work4x-task-started"
    SUCCESS = "work4x-task-succeeded"
    FAIL = "work4x-task-failed"
    STREAM = "work4x-task-stream"


class Metrics:
    inputTokens: int = 0
    outputTokens: int = 0
    totalTokens: int = 0
    totalTime: int = 0


class Work4xTask(Task):
    metrics: Metrics = Metrics()
    dispatcher: EventDispatcher
    task_id: any = None
    start_time: int = int(time.time())
    end_time: int = 0

    def set_metrics(self, input_tokens=0, output_tokens=0, total_tokens=0):
        self.metrics.inputTokens = input_tokens
        self.metrics.outputTokens = output_tokens
        self.metrics.totalTokens = total_tokens

    def send_event(self, event_type: str, event_data={}):
        self.dispatcher.send(type=event_type, uuid=self.task_id, **event_data)  # pyright: ignore[reportArgumentType]

    def send_stream_event(self, task: TaskRequest, chunk):
        task_data = dict(
            taskType=task.type,
            userId=task.userId,
            userData=task.userData,
            taskId=self.task_id,
            outputs=chunk
        )
        self.send_event(Work4xEvent.STREAM.value, task_data)  # pyright: ignore[reportArgumentType]

    def on_comfyui_started(self, prompt_id):
        self.start_time = int(time.time())  # 重新修正任务开始时间
        self.send_event("comfyui-started", {
            "taskId": prompt_id,
        })

    def before_start(self, task_id, args, kwargs):
        print("====before_start====")
        self.start_time = int(time.time())
        self.task_id = task_id
        self.dispatcher = self.app.events.Dispatcher(self.app.connection())
        self.send_event(Work4xEvent.START.value)
        super().before_start(task_id, args, kwargs)

    def on_success(self, retval, task_id, args, kwargs):
        self.end_time = time.time()
        self.metrics.totalTime = int(self.end_time - self.start_time)
        result = dict(result=retval, metrics=self.metrics.__dict__)
        self.send_event(Work4xEvent.SUCCESS.value, result)
        super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.send_event(Work4xEvent.FAIL.value, dict(exception=str(exc)))
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        super().after_return(status, retval, task_id, args, kwargs, einfo)


def App(name: str, worker_concurrency=1, imports=None):

    # if not imports:
    #    imports = name

    # app = Celery(main=name, include=[f"workers.{imports}"])                                # 创建 Celery 实例
    if not imports:
        imports = []

    app = Celery(main=f"{dir_name}.{name}", include=imports)                  # 创建 Celery 实例
    backend_url = f"{WORKER_REDIS_URL}/{WORKER_REDIS_DB}"

    app.conf.task_serializer = 'json'
    app.conf.broker_url = backend_url
    app.conf.result_backend = app.conf.broker_url
    app.conf.timezone = 'Asia/Shanghai'
    app.conf.task_default_queue = name
    app.conf.worker_send_task_events = True
    app.conf.task_send_sent_event = True
    app.Task.resultrepr_maxsize = 100 * 1024

    app.conf.update(
        task_time_limit=3600,
        worker_concurrency=worker_concurrency,
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

    print("App(" + name + ")")
    return app


class WorkerHelper:
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

    def main(self, worker_name):
        import argparse
        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-n', '--name', type=str, default=worker_name, help='worker name')
        parser.add_argument('-lv', '--log', type=str, default='info', help='log level')
        args = parser.parse_args()

        print("log_level:" + args.log)
        worker_args = ['worker', f"--loglevel={args.log}", f"-n {worker_name}@%h"]

        if platform.system() == 'Windows':
            worker_args.append("-P")
            worker_args.append("eventlet")

        # worker_args.append("-P")
        # worker_args.append("solo")

        self.app.worker_main(argv=worker_args)
