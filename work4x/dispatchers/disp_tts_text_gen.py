#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
基于 ServerBase 和 LiteLLM 实现的文本生成服务
"""

import argparse
import os
import sys

import orjson

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)

from work4x.dispatchers.BaseDispatcher import BaseDispatcher, TaskType
from work4x.workers.worker_tts import TTS, STT
from work4x.workers.worker_text_gen import generateText
from work4x.utils.logger import logger

def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


streams = [
    str(TaskType.TEXT_TO_SPEECH.value),
    str(TaskType.SPEECH_TO_TEXT.value),
    str(TaskType.TEXT_GENERATION.value),
]


class TextSpeechDisPatcher(BaseDispatcher):
    """文本生成和文本转声音 分发器"""

    def __init__(self, consumer_name=None, group_name=None):
        stream_names = streams

        if consumer_name is None:
            consumer_name = 'dispatcher_tts_text_gen'

        super().__init__(stream_names=stream_names, consumer_name=consumer_name, group_name=group_name)

    def test(event):
        logger.info("test")

    def get_task_func(self, type):
        """
        执行文本生成任务
        Args:
            task: 任务数据，包含inputs字段
        """

        if type == TaskType.TEXT_TO_SPEECH.value:
            return TTS

        if type == TaskType.SPEECH_TO_TEXT.value:
            return STT

        if type == TaskType.TEXT_GENERATION.value:
            return generateText


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
        # 创建并启动w
        disp_app = TextSpeechDisPatcher(consumer_name=args.name, group_name=args.group)
        # start_monitoring_service(app)
        disp_app.run()

    except KeyboardInterrupt:
        logger.info("退出信号，正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise



if __name__ == '__main__':
    main()
