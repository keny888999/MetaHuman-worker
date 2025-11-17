import redis

# 创建 Redis 连接
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 创建 PubSub 对象
pubsub = r.pubsub()

# 订阅一个或多个频道
pubsub.subscribe('news')

print("开始监听频道 'news'...")
for message in pubsub.listen():
    if message['type'] == 'message':
        print(f"收到消息: {message['data']} (来自频道: {message['channel']})")
