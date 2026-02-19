import time

class StreamAckCleaner:
    def __init__(self, redis_client):
        self.r = redis_client
        
    def cleanup_acked_periodically(self, stream_name, consumer_group, interval_seconds=60):
        """定期清理已确认的消息"""
        while True:
            self.cleanup_acked(stream_name, consumer_group)
            time.sleep(interval_seconds)
    
    def cleanup_acked(self, stream_name, consumer_group):
        """清理已确认的消息"""
        try:
            # 获取待处理消息信息
            pending = self.r.xpending(stream_name, consumer_group)
            
            if pending['pending'] == 0:
                # 没有待处理消息，可以安全清理所有消息
                # 保留最后100条消息以防万一
                self.r.xtrim(stream_name, maxlen=0)
                return
            
            # 获取最早的待处理消息
            oldest_pending = self.r.xpending_range(
                stream_name, consumer_group,
                min='-', max='+', count=1
            )
            
            if oldest_pending:
                # 使用 MINID 清理已确认的消息
                min_id = oldest_pending[0]['message_id']
                # 删除所有ID小于最早待处理消息ID的消息
                self.r.xtrim(stream_name, minid=min_id, approximate=False)
                
        except Exception as e:
            print(f"StreamAckCleaner Cleanup error: {e}")