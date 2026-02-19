#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:keny
"""
文本生成 Worker
基于 ServerBase 和 LiteLLM 实现的文本生成服务
"""
import platform
import time
import os
import sys

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)

worker_name = os.path.basename(__file__).split('.')[0]

# 这句于要提前
from work4x.workers.App import app, WorkerApp, Work4xTask,WorkerMetrics
from work4x.workers.llm.text_generator import Metrics
from work4x.classes.TaskRequest import TaskType
from work4x.utils.logger import logger
from work4x.workers.llm.text_generator import quick_stream_generate_with_template
from work4x.workers.llm.templates import templates
from work4x.classes.TaskRequest import TaskRequest
from work4x.config import WORKER_NUM_TEXT_GEN

worker_helper = WorkerApp(app)

@app.task(bind=True, base=Work4xTask,name=TaskType.TEXT_GENERATION.value)
def generateText(self, task_data: dict[str, object], delay=None):
    this: Work4xTask = self

    try:
        request_data = TaskRequest.model_validate(task_data)

        logger.info("开始处理文本生成任务")
        inputs = request_data.inputs

        task_id = self.task_id


        result_text = []
        # 模板文本生成
        template_name = inputs.get('template', None)
        template = str(templates.get(template_name, ""))
        variables = inputs
        logger.info("template:{}", template_name)
        logger.info("variables:{}", variables)

        metrics = Metrics()
        stream = quick_stream_generate_with_template(
            template=template,
            variables=variables,
            model_type='chat_openai',
            temperature=1.0,
            thinking=False,
            metrics=metrics
        )

        for chunk in stream:  # type: ignore
            result_text.append(chunk)
            message = dict(text=chunk)
            this.send_stream_event(task_id, chunk=message)

        text = ''.join(result_text)

        this.usage.input=metrics.input_tokens
        this.usage.output = metrics.output_tokens
        logger.info(f"文本生成任务完成: {this.usage.model_dump()}")
        return this.success(outputs={"text": text})

    except Exception as e:
        logger.error(f"文本生成任务失败: {str(e)}")
        raise e


if __name__ == "__main__":
    worker = WorkerApp(app)
    worker.main(worker_name=worker_name,more_args=["-c",WORKER_NUM_TEXT_GEN])
