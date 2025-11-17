#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
基于 ServerBase 和 LiteLLM 实现的文本生成服务
"""
import platform
if platform.system() == 'Windows':
    from eventlet import monkey_patch
    monkey_patch(thread=True, select=True)

import orjson
import argparse
import os
import random

import os
import sys

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)

from BaseDispatcher import BaseDispatcher, TaskType
from classes.TaskMessage import TaskMessage, TaskStatus
from workers.worker_tts import text_to_speech
from workers.worker_text_gen import generateText
from utils.logger import logger


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


class TextSpeechDisPatcher(BaseDispatcher):
    """文本生成和文本转声音 分发器"""

    def __init__(self, consumer_name=None, group_name=None):
        stream_names = [str(TaskType.TEXT_TO_SPEECH.value), str(TaskType.TEXT_GENERATION.value)]

        if consumer_name is None:
            consumer_name = 'dispatcher_tts_text_gen'

        if group_name is None:
            group_name = 'tts_text_gen_group_0'

        super().__init__(stream_names=stream_names, consumer_name=consumer_name, group_name=group_name)

    def test(event):
        logger.info("test")

    def push_task(self, task_id: str, task: TaskMessage):
        """
        执行文本生成任务
        Args:
            task: 任务数据，包含inputs字段
        """
        type = task.type
        if type == TaskType.TEXT_TO_SPEECH.value:
            return text_to_speech.apply_async(args=[task.model_dump()], task_id=str(task_id))

        if type == str(TaskType.TEXT_GENERATION.value):
            return generateText.apply_async(args=[task.model_dump()], task_id=str(task_id))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
        使用示例:
  python worker_text_generation.py --name my_worker --group text_gen_group
        """
    )

    parser.add_argument('--name', type=str, required=False, help='消费者名称')
    parser.add_argument('--group', type=str, required=False, help='客户端组ID')

    args = parser.parse_args()
    logger.info(f"启动参数: {args}")

    try:
        # 创建并启动worker
        worker_app = TextSpeechDisPatcher(consumer_name=args.name, group_name=args.group)
        # start_monitoring_service(app)
        worker_app.run()

    except KeyboardInterrupt:
        logger.info("退出信号，正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise


def test():
    import math
    settings = r'{"language": "zh-CN", "character": "sambert-zhijing-v1", "emotion": "neutral", "speed": 1, "pitch": 1, "volume": 0.5}'
    task = TaskMessage.model_validate({
        "headers": {'tenant-id': '1'},
        "id": math.floor(random.randrange(1000, 10000)),
        "userId": 5,
        "projectId": 9,
        "type": TaskType.TEXT_TO_SPEECH,
        "inputs": r'{ "text":"你好啊", "settings":' + settings + "}"
    })
    task.status = 0
    task.statusText = ""

    # job = thumb.apply_async(args=[task.model_dump()], task_id=str(task.id))
    # job = thumb11.apply_async(args=['kkkk'], task_id=str(task.id))
    job = text_to_speech.apply_async(args=[task.model_dump()], task_id=str(task.id))
    results = job.get()
    print(results)


if __name__ == '__main__':
    main()
