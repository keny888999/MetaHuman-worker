from tokenize import group

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
from classes.TaskRequest import TaskRequest, TaskStatus, TaskCallback, TaskType

from work4x.RedisPublisher import RedisPublisher
from celery.result import AsyncResult
from work4x.workers.backend.work4x_backend import EventType, TASK_RESPONSE_KEY
from work4x.workers.backend.work4x_backend import EventAwareStreamBackend
from work4x.workers.App import app
from work4x.config import TASK_REQUEST_KEY_PREFIX

backend: EventAwareStreamBackend = app.backend

import pickle


# 如果数据是用pickle序列化的
def decode_pickled_bytes(data):
    decoded_dict = {}
    for key, value in data.items():
        decoded_key = key.decode('utf-8') if isinstance(key, bytes) else key
        try:
            # 尝试反序列化
            decoded_dict[decoded_key] = pickle.loads(value)
        except:
            # 如果不是pickle数据，尝试其他解码
            try:
                decoded_dict[decoded_key] = json.loads(value.decode('utf-8'))
            except:
                decoded_dict[decoded_key] = value.decode('utf-8')
    return decoded_dict


class BaseDispatcher:
    stream_names: list[str]

    def __init__(self, stream_names, consumer_name=None, group_name=None):
        stream_names = [TASK_REQUEST_KEY_PREFIX + x for x in stream_names]

        self.stream_names = stream_names
        self.group_name = group_name or "default"
        if consumer_name is None:
            self.consumer_name = f"consumer-{self.stream_name[0]}"
        else:
            self.consumer_name = consumer_name

        self.redis_pub = RedisPublisher()
        self.redis_pub.connect()

    def check_task_cancellation(self, task_id):
        result = AsyncResult(task_id)

        print(f"任务是否成功: {result.successful()}")
        print(f"任务是否失败: {result.failed()}")
        print(f"任务是否就绪: {result.ready()}")  # 任务是否完成执行

        if result.state == 'REVOKED':
            print("✅ 任务已被成功取消")
            return True
        elif result.state == 'FAILURE':
            print("❌ 任务执行失败")
            return False
        elif result.state == 'SUCCESS':
            print("✅ 任务执行成功")
            return False
        else:
            print(f"⏳ 任务当前状态: {result.state}")
            return False

    def get_class_name(self):
        return self.__class__.__name__

    def get_task_func(self, task_id, task: TaskRequest):
        return {}

    def ensure_stream_and_group(self):
        """确保 Stream 和消费组存在"""
        for stream_name in self.stream_names:
            try:
                self.redis_pub.redis.xgroup_create(stream_name, self.group_name, id='$', mkstream=True)
                logger.info(f"init stream={stream_name} group={self.group_name}")
            except Exception as e:
                if 'BUSYGROUP' not in str(e):  # 忽略组已存在的错误
                    raise

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
                messages = backend.client.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams=dict(zip(self.stream_names, stream_ids)),
                    # streams={self.stream_name: '>'},  # '>' 表示读取未被消费的消息
                    count=1,
                    block=1000,
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

            for stream, entries in messages:  # type: ignore
                for message_id, message in entries:
                    try:
                        message = decode_pickled_bytes(message)
                        payload = message['payload']
                        logger.info(payload)
                    except Exception as e:
                        logger.error("payload is invalid json data ")
                        continue

                    try:
                        task = TaskRequest.model_validate(payload)
                        func =self.get_task_func(task.type).s(task.model_dump())
                        func.set(task_id=str(task.taskId))
                        func.set(headers=task.headers)
                        func.apply_async()

                    except Exception as e:
                        traceback.print_exc()
                        task_cb = TaskCallback.model_validate(payload, strict=False)
                        task_cb.status = TaskStatus.FAIL
                        task_cb.statusText = str(e)
                        # self.redis_pub.update_task_status(task_cb)

    def md5(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
