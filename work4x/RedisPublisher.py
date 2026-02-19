import redis
import time
import orjson
import traceback

from work4x.config import TASK_RESPONSE_KEY, TASK_CACHE_KEY, WORKER_REDIS_URL,WORKER_REDIS_DB
from work4x.utils.logger import logger
from work4x.classes.TaskRequest import TaskRequest, TaskStatus, TaskCallback
from typing import Callable, Optional
import threading


class RedisPublisher:
    subscribe_handlers: dict[str, list] = {}
    task_subscribe_enabled = False
    thread_task_subscribe: threading.Thread

    def __init__(self, redis_url:str = f"{WORKER_REDIS_URL}/1"):
        self.redis_url = redis_url
        self.redis: redis.Redis
        self.pubsub = None
        self.thread_task_subscribe = threading.Thread(target=self.thread_subscribe)
        self.thread_task_subscribe.daemon = True

    def connect(self):
        """建立连接"""

        try:
            self.redis = redis.Redis.from_url(self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )

            self.pubsub = self.redis.pubsub()
            # 测试连接
            self.redis.ping()
            for key in self.subscribe_handlers:
                self.pubsub.subscribe(key)

            logger.info("RedisPublisher 连接成功:" + f"{self.redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"RedisPublisher 连接失败: {e}")
            raise

    def publish(self, channel, message, retry_count=1):
        """发布消息，带重试机制"""
        for attempt in range(retry_count):
            try:
                result = self.redis.publish(channel, message)
                return result
            except redis.ConnectionError:
                if attempt < retry_count - 1:
                    logger.error(f"发布失败，尝试重连... ({attempt + 1}/{retry_count})")
                    time.sleep(1)
                    self.connect()
                else:
                    print("发布失败，已达到最大重试次数")
                    raise

    def subscribe(self, channel: str, handler: Callable):
        self.pubsub.subscribe(channel)
        if not channel in self.subscribe_handlers:
            self.subscribe_handlers[channel] = []

        self.subscribe_handlers[channel].append(handler)
        logger.info(f"开始订阅频道: {channel}")

    def unsubscribe(self, channel: str, handler: Optional[Callable]):
        self.pubsub.subscribe(channel)
        list = self.subscribe_handlers.get(channel, None)
        if not list:
            return

        if handler:
            if handler in list:
                list.remove(handler)
        else:
            list.clear()

        if len(list) < 1:
            del self.subscribe_handlers[channel]

        logger.info(f"取消订阅频道: {channel}")

    def task_callback(self, task):
        self.redis.xadd(TASK_RESPONSE_KEY, {'payload': orjson.dumps(task)})

    def get_task_cache(self, task_id: str):
        key = f"{TASK_CACHE_KEY}:{task_id}"
        cached = self.redis.get(key)
        if cached is None:
            return None

        cache_json = orjson.loads(str(cached))
        return TaskRequest.model_validate(cache_json)

    def update_task_status(self, task_cb: TaskCallback):
        try:
            self.redis.xadd(TASK_RESPONSE_KEY, {'payload': orjson.dumps(task_cb.model_dump())})
        except Exception as e:
            logger.error(str(e))

    def close(self):
        """关闭连接"""
        self.redis.close()

    def thread_subscribe(self):
        # 4. 循环监听消息

        for ch in self.subscribe_handlers:
            logger.info(f"正在监听频道 {ch}")

        print("消息订阅器侦听中...")
        while True:
            if not self.task_subscribe_enabled:
                time.sleep(1)
                continue

            try:
                message = self.pubsub.get_message(timeout=3)
                if not message:
                    continue

                if message.get('type', '') == 'message':
                    try:
                        ch = message.get('channel', '')
                        data = message.get('data', None)
                        logger.info(f"收到订阅消息:channel={ch} {data}")
                        listeners = self.subscribe_handlers.get(ch, [])

                        data_json = None
                        if data:
                            data_json = orjson.loads(data)

                        for func in listeners:
                            func(data_json)
                    except Exception as e:
                        logger.error("处理消息回调异常:" + str(e))
                        traceback.print_exc()

            except Exception as e:
                logger.warning("接收订阅线程出错:" + str(e))

    def start_subscribe_listener(self):
        if not self.thread_task_subscribe.is_alive():
            self.thread_task_subscribe.start()
        self.task_subscribe_enabled = True

    def stop_subscribe_listener(self):
        self.task_subscribe_enabled = False


if __name__ == "__main__":
    # 使用示例
    publisher = RedisPublisher()

    data = {
        "taskId": 1,
        "eventType": "progress",
        "eventData": '{"value":85}'
    }
    publisher.publish('TaskWorkerEvent', orjson.dumps(data))
    publisher.close()
