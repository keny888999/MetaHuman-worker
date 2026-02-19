# complete_event_consumer.py
import json
import pickle
import time
import threading
from enum import Enum
import logging
from datetime import datetime
from typing import Dict, List, Callable, Optional
import redis
from work4x.config import TASK_RESPONSE_KEY,TASK_DEFAULT_GROUP
from work4x.workers.backend.work4x_backend import EventType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendEventConsumer:
    """完整的任务事件消费者"""
    
    def __init__(
        self,
        redis_url: str = 'redis://localhost:6379/1',
        consumer_name: str = None,
        group_name: str = TASK_DEFAULT_GROUP,
        process_started: bool = True,
        process_progress: bool = True,
        process_results: bool = True
    ):
        self.redis_client = redis.from_url(redis_url,decode_responses=True)
        self.consumer_name = consumer_name or f'consumer_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        self.group_name= group_name or TASK_DEFAULT_GROUP
        
        # 配置要处理的事件类型
        self.process_started = process_started
        self.process_progress = process_progress
        self.process_results = process_results
        
        # 事件处理器映射
        self.event_handlers: Dict[str, List[Callable]] = {}
        for x in EventType:
            self.event_handlers[x.value] = []

        # 运行状态
        self.running = False
        self.consumer_threads = []
        
        # 初始化Stream和消费者组
        self._init_streams()
    
    def _init_streams(self):
        self._ensure_consumer_group(TASK_RESPONSE_KEY, self.group_name)
    
    def _ensure_consumer_group(self, stream_name, group_name):
        """确保消费者组存在"""
        try:
            # 检查Stream是否存在
            try:
                self.redis_client.xinfo_stream(stream_name)
            except redis.exceptions.ResponseError:
                logger.warning(f"Stream不存在,重新创建: {stream_name}")
                self.redis_client.xadd(stream_name, {'init': 'stream_created'})
                self.redis_client.xtrim(stream_name, 0)  # 清空初始化消息

            # 检查消费者组
            groups = self.redis_client.xinfo_groups(stream_name)
            group_exists = any(group['name'] == group_name for group in groups)
            
            if not group_exists:
                self.redis_client.xgroup_create(
                    name=stream_name,
                    groupname=group_name,
                    id='0',
                    mkstream=True
                )
                logger.info(f"创建消费者组: {group_name} for {stream_name}")
                
        except redis.exceptions.ResponseError as e:
            if 'BUSYGROUP' in str(e):
                logger.debug(f"消费者组已存在: {group_name}")
            else:
                logger.error(f"创建消费者组失败: {e}")
        except Exception as e:
            logger.error(f"初始化Stream组异常: {e}")
    
    def register_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            logger.info(f"注册处理器 for {event_type}")
        else:
            logger.warning(f"未知的事件类型: {event_type}")
    
    def process_event(self, event: Dict):
        """处理单个事件"""
        payload=json.loads(event.get('payload'))
        event_type = payload.get('eventType')
        
        if not event_type:
            logger.warning("事件缺少event_type字段")
            logger.info(event)
            return

        logger.info(f"\nevent_type={event_type} ,  event={event}\n\n")
        
        # 调用所有注册的处理器
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                logger.error(f"事件处理器异常: {e}", exc_info=True)
    
    def thread_consume_stream(self, stream_name, group_name):
        """消费单个Stream"""
        logger.info(f"开始消费Stream: {stream_name}, group_name={group_name}")
        
        while self.running:
            try:
                # 读取消息
                messages = self.redis_client.xreadgroup(
                    groupname=group_name,
                    consumername=self.consumer_name,
                    streams={stream_name: '>'},
                    count=10,
                    block=5000
                )
                
                if messages:
                    _, items = messages[0]
                    
                    for message_id, data in items:
                        try:
                            # 解析事件
                            event = {'id': message_id, 'stream': stream_name}
                            
                            for k, v in data.items():
                                if isinstance(v, bytes):
                                    v = v.decode()
                                
                                # 特殊字段处理
                                if k in ['meta', 'args', 'kwargs'] and v:
                                    try:
                                        event[k] = json.loads(v)
                                    except:
                                        event[k] = v
                                elif k == 'result' and v:
                                    try:
                                        event[k] = pickle.loads(bytes.fromhex(v))
                                    except:
                                        event[k] = v
                                else:
                                    event[k] = v
                            
                            # 处理事件
                            self.process_event(event)
                            
                            # 确认消息
                            self.redis_client.xack(stream_name, group_name, message_id)
                            
                        except Exception as e:
                            logger.error(f"处理消息失败: {e}", exc_info=True)
                            # 即使失败也确认消息，避免阻塞
                            self.redis_client.xack(stream_name, group_name, message_id)
                else:
                    # 无消息时短暂休眠
                    time.sleep(0.1)
            
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.error(f"Redis连接异常: {e}")
                time.sleep(10)
            except Exception as e:
                logger.error(f"消费Stream异常: {e}", exc_info=True)
                time.sleep(1)
    
    def start(self):
        """启动消费者服务"""
        if self.running:
            logger.warning("消费者已在运行")
            return
        
        self.running = True
        
        # 为每个Stream创建消费线程
        thread = threading.Thread(
            target=self.thread_consume_stream,
            args=(TASK_RESPONSE_KEY, self.group_name),
            daemon=True,
            name=f"Consumer-{TASK_RESPONSE_KEY}"
        )
        thread.start()
        self.consumer_threads.append(thread)
        
        logger.info(f"事件消费者服务已启动，Stream={TASK_RESPONSE_KEY}")
    
    def stop(self):
        """停止消费者服务"""
        self.running = False
        
        for thread in self.consumer_threads:
            thread.join(timeout=10)
        
        self.consumer_threads.clear()
        logger.info("事件消费者服务已停止")