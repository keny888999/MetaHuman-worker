#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
文本生成 Worker
基于 ServerBase 和 LiteLLM 实现的文本生成服务
"""
import platform

print(platform.system())

if platform.system() == 'Windows':
    from eventlet import monkey_patch
    monkey_patch(thread=True, select=True, httpx=True)

import orjson
from typing import Dict, Any
import time
import os
import sys

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)

# 这句于要提前
from WorkerApp import App
from work4x.config import WORKER_NUM_TEXT_GEN

os.environ.pop('http_proxy', None)
# os.environ.pop('https_proxy', None)
#

from celery.events.dispatcher import EventDispatcher
from utils.logger import logger
from workers.llm.config import TextGenerationConfig
from workers.llm.text_generator import quick_stream_generate_with_template
from workers.llm.templates import templates

app = App('worker_text_gen', worker_concurrency=WORKER_NUM_TEXT_GEN)

dispatcher: EventDispatcher | None = None

model_cfg = TextGenerationConfig.get_config_from_env()


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


def init():
    """初始化文本生成器"""
    try:
        global dispatcher
        print_json(model_cfg)
        dispatcher = app.events.Dispatcher(app.connection())

    except Exception as e:
        logger.error(f"文本生成器初始化失败: {str(e)}")
        raise


@app.task(bind=True)
def generateText(self, task: dict[str, object], delay=None):
    """
    执行文本生成任务

    Args:
        task: 任务数据，包含inputs字段

    Returns:
        处理结果
    """

    if dispatcher is None:
        init()

    try:
        logger.info("开始处理文本生成任务")
        inputs = orjson.loads(str(task.get("inputs")))

        if delay is None:
            delay = 0.5

        time.sleep(delay)  # 延迟执行，让 started信号更新task更安全,不至于秒执行的情况，马上被 success 结果覆盖
        logger.info(f"delay {delay} second to run..")

        # 获取任务类型和参数
        generation_type = 'template'  # simple, template, conversation

        # 根据类型执行不同的生成逻辑

        task_id = self.request.id

        result_text = []
        # 模板文本生成
        template_name = inputs.get('template')
        template = str(templates.get(template_name))
        variables = inputs.get('variables', {})

        print("template", template)
        print("\nvariables", variables)

        stream = quick_stream_generate_with_template(
            template=template,
            variables=variables,
            model_type='chat_openai',
            model_name=model_cfg.model_name,
            api_key=model_cfg.api_key,
            base_url=model_cfg.base_url,
            temperature=1.6,
            thinking=False
        )

        for chunk in stream:
            result_text.append(chunk)
            dispatcher.send(type="task-stream", content={"outputs": chunk}, task_type=task.get("type"), project_id=task.get("projectId"), uuid=task_id)

        text = ''.join(result_text)
        logger.info("文本生成任务完成:\n")
        logger.info(text)
        return text

    except Exception as e:
        logger.error(f"文本生成任务失败: {str(e)}")
        raise e


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='')
    # parser.add_argument('worker', type=str, default='', help='batch size')
    # parser.add_argument('-P', type=str, default='gevent', help='batch size')

    worker = app.Worker()
    worker.start()

    # test()
