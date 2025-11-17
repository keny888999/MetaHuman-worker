import os
import sys
import time
import traceback
import orjson as json
from celery.events import EventReceiver
from celery import Celery

CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
import paths

from classes.TaskMessage import TaskStatus, TaskCallback
from utils.logger import logger
from typing import Dict, Any, Callable
from RedisPublisher import RedisPublisher
from work4x.config import CELERY_REDIS_HOST, CELERY_REDIS_PORT, CELERY_REDIS_DB

backend_url = f"redis://{CELERY_REDIS_HOST}:{CELERY_REDIS_PORT}/{CELERY_REDIS_DB}"

app = Celery('thread_work')                                # 创建 Celery 实例
app.conf.broker_url = backend_url
app.conf.result_backend = app.conf.broker_url  # pyright: ignore[reportAttributeAccessIssue]
app.conf.worker_send_task_events = True
state = app.events.State()
connections = app.connection()


class WorkerEventReceiver:
    redis_pub: RedisPublisher
    stop_worker_msg = False

    def __init__(self, *args, **kwargs):
        self.redis_pub: RedisPublisher = RedisPublisher(db=0)
        pass

    def started_handler(self, event):
        self.worker_event_handler(event)  # 输出一下
        task_id = event.get('uuid')

        cached = self.redis_pub.get_task_cache(task_id)
        if cached is not None:
            task_cb = TaskCallback(id=task_id)
            task_cb.type = cached.type
            task_cb.userId = cached.userId
            task_cb.projectId = cached.projectId
            task_cb.status = TaskStatus.PROCESSING
            task_cb.statusText = event.get('type')
            logger.info(f"started_handler: {task_cb}")
            self.redis_pub.update_task_status(task_cb)

    def succeeded_handler(self, event):
        self.worker_event_handler(event)  # 输出一下
        task_id = event.get('uuid')

        task_cb = TaskCallback(id=task_id)
        cached = self.redis_pub.get_task_cache(task_id)
        if cached is not None:
            task_cb.type = cached.type
            task_cb.userId = cached.userId
            task_cb.projectId = cached.projectId
            task_cb.status = TaskStatus.SUCCESS
            task_cb.statusText = event.get('type')
            text = str(event.get('result')).strip("'")
            task_cb.outputs = text

            logger.info(f"succeeded_handler: {task_cb}")
            self.redis_pub.update_task_status(task_cb)

    def failed_handler(self, event):
        self.worker_event_handler(event)  # 输出一下
        task_id = event.get('uuid')
        task_cb = TaskCallback(id=task_id)
        cached = self.redis_pub.get_task_cache(task_id)
        if cached is not None:
            task_cb.type = cached.type
            task_cb.userId = cached.userId
            task_cb.projectId = cached.projectId

            task_cb.status = TaskStatus.FAIL
            task_cb.statusText = str(event.get('exception'))
            logger.info(f"failed_handler: {task_cb}")
            self.redis_pub.update_task_status(task_cb)

    def stream_event_handler(self, event):
        self.redis_pub.pub_task_event(event)

    def worker_event_handler(self, event):
        event_type = event.get('type')
        logger.info(f"收到事件 {event_type}\n")

    def run(self):
        event_handlers: Dict[str, Callable] = {
            'task-stream': self.stream_event_handler,
            'task-started': self.started_handler,
            'task-succeeded': self.succeeded_handler,
            'task-failed': self.failed_handler,
            'task-revoked': self.worker_event_handler,
        }

        receiver = EventReceiver(
            connections,
            handlers=event_handlers
        )

        while True:
            try:
                logger.info("worker事件接收器就绪\n")

                for event in receiver.itercapture(timeout=3000, wakeup=True):
                    if self.stop_worker_msg:
                        break
                    time.sleep(0.000000001)
            except KeyboardInterrupt:
                logger.info("收到键盘中断信号")
                self.stop_worker_msg = True
                break

            except Exception as e:
                logger.error(f"事件监控错误: {str(e)}, 1秒后重试...")

            if self.stop_worker_msg:
                break

            time.sleep(1)


if __name__ == '__main__':
    WorkerEventReceiver().run()
