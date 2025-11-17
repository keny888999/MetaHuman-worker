import redis
import time
import orjson

from config import STREAM_CALLBACK_KEY, TASK_HASH_KEY, REDIS_HOST, REDIS_PORT, REDIS_DB
from utils.logger import logger
from classes.TaskMessage import TaskMessage, TaskStatus, TaskCallback


class RedisPublisher:
    subscribe_handlers = {}

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB):
        self.host = host
        self.port = port
        self.db = db
        self.redis: redis.Redis = None
        self.pubsub = None
        self.connect()

    def connect(self):
        """建立连接"""
        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )

            self.pubsub = self.redis.pubsub()
            # 测试连接
            self.redis.ping()
            logger.info("RedisPublisher 连接成功:" + f"{self.host}:{self.port}/{self.db}")
        except redis.ConnectionError as e:
            logger.error(f"RedisPublisher 连接失败: {e}")
            raise

    def publish(self, channel, message, retry_count=3):
        """发布消息，带重试机制"""
        for attempt in range(retry_count):
            try:
                result = self.redis.publish(channel, message)
                self.redis
                return result
            except redis.ConnectionError:
                if attempt < retry_count - 1:
                    logger.error(f"发布失败，尝试重连... ({attempt + 1}/{retry_count})")
                    time.sleep(1)
                    self.connect()
                else:
                    print("发布失败，已达到最大重试次数")
                    raise

    def subscribe(self, channel: str, handler: callable):
        self.pubsub.subscribe(channel)
        self.subscribe_handlers.update({
            "channel": channel,
            "handler": handler
        })
        logger.info(f"开始订阅频道: {channel}")

    def unsubscribe(self, channel: str):
        self.pubsub.subscribe(channel)
        if self.subscribe_handlers.get(channel):
            del self.subscribe_handlers[channel]

        logger.info(f"取消订阅频道: {channel}")

    def task_callback(self, task):
        self.redis.xadd(STREAM_CALLBACK_KEY, {'payload': orjson.dumps(task)})

    def pub_task_event(self, event):
        message = {
            "type": event.get("type"),
            "taskId": event.get("uuid"),
            "taskType": event.get("task_type"),
            "projectId": event.get("project_id"),
            "content": event.get("content"),
        }
        self.redis.publish("TaskWorkerEvent", message=orjson.dumps(message))

    def get_task_cache(self, task_id: str):
        key = f"{TASK_HASH_KEY}:{task_id}"
        cached = self.redis.get(key)
        if cached is None:
            return None

        cache_json = orjson.loads(str(cached))
        return TaskMessage.model_validate(cache_json)

    def update_task_status(self, task_cb: TaskCallback):
        try:
            self.redis.xadd(STREAM_CALLBACK_KEY, {'payload': orjson.dumps(task_cb.model_dump())})
        except Exception as e:
            logger.error(str(e))

    def close(self):
        """关闭连接"""
        self.redis.close()


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
