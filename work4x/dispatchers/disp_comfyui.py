import argparse

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.dispatchers.BaseDispatcher import BaseDispatcher, TaskType, logger

from work4x.workers.worker_comfyui import generate_video, clone_voice,image_gen

class comfyuiDisPatcher(BaseDispatcher):
    def __init__(self, consumer_name=None, group_name=None):
        stream_names = [TaskType.VIDEO_GENERATION.value, TaskType.CLONE_VOICE.value, TaskType.IMAGE_GENERATION.value ]

        if consumer_name is None:
            consumer_name = 'dispatcher_comfyui'

        if group_name is None:
            group_name = 'comfyui_group_0'

        super().__init__(stream_names=stream_names, consumer_name=consumer_name, group_name=group_name)

    def get_task_func(self,type:str):
        """
        执行文本生成任务
        Args:
            task: 任务数据，包含inputs字段
        """
        logger.info(f"type:{type}")

        if type == TaskType.VIDEO_GENERATION.value:
            return generate_video

        if type == str(TaskType.CLONE_VOICE.value):
            return clone_voice

        if type == str(TaskType.IMAGE_GENERATION.value):
            return image_gen


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
        comfyuiDisPatcher(consumer_name=args.name, group_name=args.group).run()
    except KeyboardInterrupt:
        logger.info("退出信号，正在关闭...")
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise


# app.control.revoke("42")
# check_task_cancellation("50")
main()


'''
def check_task_cancellation(task_id):
    i = app.control.inspect()

    # 1. 获取当前正在执行的任务 (STARTED状态)
    active_tasks = i.active()
    if active_tasks:
        for worker, tasks_list in active_tasks.items():
            for task_info in tasks_list:
                print(f"Worker: {worker}, Active Task ID: {task_info['id']}")

    # 2. 获取已被Worker预留（预取）的任务 (通常这些任务已从队列取出，但尚未开始执行)
    reserved_tasks = i.reserved()
    if reserved_tasks:
        for worker, tasks_list in reserved_tasks.items():
            for task_info in tasks_list:
                print(f"Worker: {worker}, Reserved Task ID: {task_info['id']}")

    # 3. 获取已安排（调度）的定时或延迟任务
    scheduled_tasks = i.scheduled()
    if scheduled_tasks:
        for worker, tasks_list in scheduled_tasks.items():
            for task_info in tasks_list:
                # 注意：scheduled返回的结构略有不同，任务ID在 'request' 字典中
                task_id = task_info['request']['id']
                print(f"Worker: {worker}, Scheduled Task ID: {task_id}")

    result = app.AsyncResult(task_id)
    print(result)
    print(f"任务是否成功: {result.successful()}")
    print(f"任务是否失败: {result.failed()}")
    print(f"任务是否就绪: {result.ready()}")  # 任务是否完成执行

    if result.state == 'REVOKED':
        print("✅ 任务已被成功取消")
        return True
    elif result.state == 'FAILURE':
        print("❌ 任务执行失败")
        return False
    elif result.state == 'SUCCESS':
        print("✅ 任务执行成功")
        return False
    else:
        print(f"⏳ 任务当前状态: {result.state}")
        return False
'''
