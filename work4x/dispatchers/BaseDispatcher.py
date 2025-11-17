from redis.typing import ResponseT
import orjson as json
import time
import traceback
import hashlib
import requests

import os
import sys

WORKERS_PATH = os.path.abspath(os.path.dirname(__file__))
WORK4X_PATH = os.path.abspath(os.path.join(WORKERS_PATH, ".."))
ROOT_PATH = os.path.abspath(os.path.join(WORK4X_PATH, ".."))

sys.path.insert(0, ROOT_PATH)
sys.path.insert(0, WORK4X_PATH)
sys.path.insert(0, WORKERS_PATH)


from PIL import Image
from io import BytesIO
import os

from utils.logger import logger
from classes.TaskMessage import TaskMessage, TaskStatus, TaskCallback, TaskType

from work4x.RedisPublisher import RedisPublisher


class BaseDispatcher:
    stream_names: list[str]

    def __init__(self, stream_names, consumer_name=None, group_name='default'):
        self.stream_names = stream_names
        self.group_name = group_name
        if consumer_name is None:
            self.consumer_name = f"consumer-{self.stream_name[0]}"
        else:
            self.consumer_name = consumer_name

        self.redis_pub = RedisPublisher()

    def get_class_name(self):
        return self.__class__.__name__

    def push_task(self, task_id, task: TaskMessage):
        return {}

    def ensure_stream_and_group(self):
        """确保 Stream 和消费组存在"""
        for stream_name in self.stream_names:
            try:
                self.redis_pub.redis.xgroup_create(stream_name, self.group_name, id='$', mkstream=True)
            except Exception as e:
                if 'BUSYGROUP' not in str(e):  # 忽略组已存在的错误
                    raise

            logger.info(f"init stream={stream_name} group={self.group_name}")

    def download_image(self, url):
        logger.info(f"Downloading image from {url}")
        response = requests.get(url, timeout=5)
        img = Image.open(BytesIO(response.content))
        img.save("test.jpg")
        return img

    def run(self):
        logger.info(f'consumer name: {self.consumer_name}')
        # 确保 Stream 和消费组已创建
        self.ensure_stream_and_group()

        """处理 Stream 消息的主循环"""
        stream_ids = ['>' for _ in self.stream_names]

        while True:
            try:
                # 从消费组读取消息
                messages = self.redis_pub.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams=dict(zip(self.stream_names, stream_ids)),  # streams={self.stream_name: '>'},  # '>' 表示读取未被消费的消息
                    count=1,
                    block=1000
                )
            except KeyboardInterrupt:
                logger.info("收到键盘中断信号,等待线程关闭...")
                break
            except Exception as e:
                logger.error(f"Stream reading error: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(1)
                continue

            if not messages:  # 超时，没有新消息
                # logger.debug("no new message")
                continue

            for stream, entries in messages:
                for message_id, message in entries:
                    payload = json.loads(message['payload'])
                    print("payload!")
                    print(payload)

                    task = TaskMessage.model_validate(payload)
                    try:
                        task.statusText = "WAIT"
                        logger.info(f'push_task: type={task.type}, input={task.inputs}')
                        self.push_task(task.id, task)
                    except Exception as e:
                        logger.error(f"run_tasks error : {str(e)}")
                        task_cb = TaskCallback(id=task.id, userId=task.userId, projectId=task.projectId, type=task.type)
                        task_cb.status = TaskStatus.FAIL
                        task_cb.statusText = str(e)
                        self.redis_pub.update_task_status(task_cb)

    def md5(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
