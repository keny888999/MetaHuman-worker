import redis
import orjson
import time

# 创建 Redis 连接
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True,)

# 发布消息到频道


def publish_message(channel, message):
    r.publish(channel, message)
    print(f"已发布消息到频道 '{channel}': {message}")


# 示例：发布多条消息
for i in range(5):
    data = {
        "taskId": 1,
        "eventType": "progress",
        "eventData": '{"value":85}'
    }
    publish_message('TaskWorkerEvent', orjson.dumps(data))
    time.sleep(1)
