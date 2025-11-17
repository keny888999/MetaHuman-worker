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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dispatchers.BaseDispatcher import BaseDispatcher, TaskType
from classes.TaskMessage import TaskMessage, TaskStatus
from workers.worker_thumb import thumb
from utils.logger import logger


class UtilsDisPatcher(BaseDispatcher):
    def __init__(self, consumer_name=None, group_name=None):
        stream_names = [str(TaskType.IMAGE_THUMB.value)]

        if consumer_name is None:
            consumer_name = 'dispatcher_utils'

        if group_name is None:
            group_name = 'utils_group_0'

        super().__init__(stream_names=stream_names, consumer_name=consumer_name, group_name=group_name)

    def push_task(self, task_id: str, task: TaskMessage):
        """
        执行文本生成任务
        Args:
            task: 任务数据，包含inputs字段
        """
        type = task.type
        if type == TaskType.IMAGE_THUMB.value:
            return thumb.apply_async(args=[task.model_dump()], task_id=str(task_id))


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
        UtilsDisPatcher(consumer_name=args.name, group_name=args.group).run()
    except KeyboardInterrupt:
        logger.info("退出信号，正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise


main()
