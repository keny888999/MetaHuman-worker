# complete_stream_backend.py
import json
import pickle
import uuid
from datetime import datetime
from celery.backends.redis import RedisBackend
import redis
import logging
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional
from work4x.config import TASK_RESPONSE_KEY,TASK_STREAM_KEY

logger = logging.getLogger(__name__)


class EventType(Enum):
    TASK_STARTED = "TASK_STARTED"
    TASK_PROGRESS = "TASK_PROGRESS"
    TASK_SUCCESS = "TASK_SUCCESS"
    TASK_FAILURE = "TASK_FAILURE"
    TASK_REVOKED = "TASK_REVOKED"
    TASK_RETRY = "TASK_RETRY"


class ResponseMessageBase(BaseModel):
    eventType: str
    taskId: str
    taskName: str
    worker: str
    timestamp: str
    headers: dict


class StartMessage(ResponseMessageBase):
    pass


class StreamMessage(ResponseMessageBase):
    outputs: Any
    pass


class ProgressMessage(ResponseMessageBase):
    outputs: Any
    pass

class ResultMessage(ResponseMessageBase):
    state:str
    metrics:Optional[dict]=None
    outputs: Optional[Any]=None
    pass


class EventAwareStreamBackend(RedisBackend):
    """支持完整任务生命周期的事件感知Stream后端"""

    def __init__(self, *args, **kwargs):
        app = kwargs.get('app')
        url = app.conf.get("broker_url")
        kwargs["url"] = url
        super().__init__(*args, **kwargs)
        self.setup_streams_and_groups()

    def setup_streams_and_groups(self):
        """创建多个Stream和消费者组用于不同事件类型"""
        self._ensure_stream_group(TASK_RESPONSE_KEY)

    def _ensure_stream_group(self, stream_name):
        """确保Stream和消费者组存在"""
        try:
            # 检查Stream是否存在
            try:
                self.client.xinfo_stream(stream_name)
            except redis.exceptions.ResponseError:
                # Stream不存在，创建空Stream
                self.client.xadd(stream_name, {'init': 'stream_created'})
                self.client.xtrim(stream_name, 0)  # 清空初始化消息
        except Exception as e:
            logger.error(f"设置Stream组异常: {e}")

    def store_result(self, task_id, result, state, traceback=None, request=None):

        #进度事件流数据通过redis pub/sub 机制发送，不存储到redis
        if state=="STREAM" or state=="PROGRESS":
            return self.pub_stream_message(task_id, result,state,request)

        task_name=""
        if request:
            task_name = getattr(request, "task")

        logger.info(f"store_result: name={task_name} task_id={task_id}  state={state} result={result}")

        """存储任务结果，处理不同状态"""
        if state != 'PROGRESS' and state != 'REVOKED':
            self.store_to_stream(task_id, result, state, traceback, request)

        super().store_result(task_id, result, state, traceback, request)

    #发送文字流信息，主要用于文本生成中的流输出
    def pub_stream_message(self,task_id,result,state,request):
        # 从spring-boot后端传过来的headers
        headers = request.headers or {}

        stream_data = StreamMessage(
            eventType=f'TASK_{state}',
            taskId=task_id,
            taskName=getattr(request, "task"),
            outputs=result,
            headers=headers,
            timestamp=datetime.now().isoformat(),
            worker=getattr(request, 'hostname', '-') if request else '-',
        )
        self.client.publish(TASK_STREAM_KEY,stream_data.model_dump_json())

    def store_to_stream(self, task_id, result, state, traceback=None, request=None):
        """存储结果到Stream"""

        metrics=None
        outputs=None
        if state == "STARTED":
            pass
        elif state == "SUCCESS":
            metrics = result.get("metrics")
            outputs = result.get("outputs")
        elif state=="FAILURE":
            outputs=str(result)

        task_name =""
        headers={}
        if request:
           task_name = self.app.current_task.name
           headers = request.headers

        try:
            result_data = ResultMessage(
                eventType=f'TASK_{state}',
                taskId=task_id,
                taskName=task_name,
                outputs=outputs,
                state=state,
                timestamp=datetime.now().isoformat(),
                headers=headers, #透传caller方的headers
                metrics=metrics,
                worker=getattr(request, 'hostname', '-') if request else '-',
            )

            # 存储到结果Stream
            self._add_to_stream(TASK_RESPONSE_KEY, result_data.model_dump(exclude_none=True))

        except Exception as e:
            logger.error(f"存储结果到Stream失败: {e}")

    def _add_to_stream(self, stream_name, data, maxlen=10000):
        """添加数据到指定的Stream"""
        try:
            # 序列化数据
            if isinstance(data, (dict, list)):
                serialized_data =dict(payload=json.dumps(data,ensure_ascii=False))
            else:
                serialized_data = dict(payload=data)

            '''
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    serialized_data[k] = v #json.dumps(v)
                elif isinstance(v, bytes):
                    serialized_data[k] = v.hex()
                elif v is None:
                    serialized_data[k] = ''
                else:
                    serialized_data[k] = str(v)
            '''

            # 添加到Stream
            self.client.xadd(
                stream_name,
                serialized_data,
                maxlen=maxlen,
                approximate=True
            )

        except Exception as e:
            logger.error(f"添加数据到Stream {stream_name} 失败: {e}")

    def get_events(self, stream_name, consumer_group, consumer_name,
                   event_type=None, task_id=None, count=10, block=5000):
        """从指定Stream获取事件"""
        try:
            messages = self.client.xreadgroup(
                groupname=consumer_group,
                consumername=consumer_name,
                streams={stream_name: '>'},
                count=count,
                block=block
            )

            if not messages:
                return []

            stream_name, items = messages[0]
            events = []

            for item_id, data in items:
                try:
                    # 解析数据
                    event = {'id': item_id}
                    for k, v in data.items():
                        if isinstance(v, bytes):
                            v = v.decode()

                        # 尝试反序列化JSON
                        if k in ['metadata', 'args', 'kwargs'] and v:
                            try:
                                event[k] = json.loads(v)
                            except:
                                event[k] = v
                        elif k == 'result' and v:
                            try:
                                # 尝试反序列化pickle结果
                                event[k] = pickle.loads(bytes.fromhex(v))
                            except:
                                event[k] = v
                        else:
                            event[k] = v

                    # 过滤条件
                    if event_type and event.get('eventType') != event_type:
                        continue
                    if task_id and event.get('taskId') != task_id:
                        continue

                    events.append(event)

                except Exception as e:
                    logger.error(f"解析事件失败: {e}")

            return events

        except Exception as e:
            logger.error(f"从Stream {stream_name} 获取事件失败: {e}")
            return []
