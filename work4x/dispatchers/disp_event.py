import os
import sys
import time
from celery.events import EventReceiver
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)
from typing import Dict, Callable

from work4x.utils.logger import logger

from workers.sdk.runninghub.runninghub import RunningHub
from work4x.RedisPublisher import RedisPublisher
from work4x.config import WORKER_REDIS_URL,  WORKER_REDIS_DB
backend_url = f"{WORKER_REDIS_URL}/{WORKER_REDIS_DB}"

from work4x.workers.backend.work4x_consumer import BackendEventConsumer

from work4x.workers.App import app

connections = app.connection()

class WorkerEventReceiver:
    redis_pub: RedisPublisher
    stop_worker_msg = False
    comfyui_tasks: Dict[str, dict[str, str]]= {}
    consumer:BackendEventConsumer

    def __init__(self, *args, **kwargs):
        self.redis_pub: RedisPublisher = RedisPublisher()
        self.redis_pub.connect()
        self.redis_pub.subscribe("TaskCancelMessage", self.on_user_cancel_message)
        self.redis_pub.start_subscribe_listener()

        #consumer = BackendEventConsumer(backend_url,group_name="disp_event")
        #consumer.register_handler(EventType.TASK_STARTED.value, self.started_handler)
        #consumer.register_handler(EventType.TASK_SUCCESS.value, self.succeeded_handler)
        #consumer.start()
        #self.consumer = consumer

    def on_user_cancel_message(self, msg):
        logger.warning("on_cancel_message {}", msg)
        task_id = str(msg["taskId"])
        comfyui_task = self.comfyui_tasks.get(task_id)
        prompt_id = comfyui_task.get("prompt_id")
        api_key=comfyui_task.get("api_key")
        logger.warning("to cancel id={}", prompt_id)
        if prompt_id is not None:
            rh: RunningHub = RunningHub(api_key=api_key)
            rh.cancel(prompt_id)

        app.control.revoke(task_id)

    def started_handler(self, event):
        task_id = event.get('taskId')
        logger.info(f"started_handler:task_id={task_id}")

    def succeeded_handler(self, event: dict):
        task_id = event.get('uuid')
        logger.info(f"succeeded_handler: task_id={task_id}")

        prompt_id = self.comfyui_tasks.get(task_id)
        if prompt_id is not None:
            self.comfyui_tasks.pop(task_id)

    def failed_handler(self, event):
        error_text = str(event.get("exception"))
        logger.error(f"failed_handler: " + error_text)

    def display_event_handler(self, event):
        type=event.get('type') or event.get('eventType')
        logger.info(f"{type}: {event}\n\n")

    def handle_comfyui_started(self, event):
        self.display_event_handler(event)  # 输出一下

        task_id: str = str(event.get('uuid'))
        prompt_id: str = str(event.get('prompt_id'))
        api_key: str = str(event.get('api_key'))
        self.comfyui_tasks[task_id] = dict(prompt_id=prompt_id,api_key=api_key)

    def run(self):
        event_handlers: Dict[str, Callable] = {
            #'task-succeeded': self.display_event_handler,
            #'task-started': self.display_event_handler,
            'task-failed': self.display_event_handler,
            'comfyui-started': self.handle_comfyui_started,
            'task-revoked': self.display_event_handler,
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
