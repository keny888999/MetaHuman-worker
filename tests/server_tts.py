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
from typing import Dict, Any

from utils.logger import logger
from servers.ServerBase import ServerBase, TaskType, StatusCode
from llm import TextGenerator, TextGeneratorFactory, TextGenerationConfig
from classes import TaskMessage


def print_json(obj):
    print(orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode(), flush=True)


class WorkerTextGeneration(ServerBase):
    """文本生成 Worker 类"""

    def __init__(self, consumer_name=None, group_name=None):
        stream_name = str(TaskType.TEXT_GENERATION.value)

        if consumer_name is None:
            consumer_name = 'worker_' + stream_name + '_' + str(random.randrange(1000, 90000))

        if group_name is None:
            group_name = stream_name + '_group'

        super().__init__(stream_name=stream_name, consumer_name=consumer_name, group_name=group_name)

        # 初始化文本生成器
        self._init_text_generator()

    def _init_text_generator(self):
        """初始化文本生成器"""
        try:
            # 从环境变量获取配置
            cfg = TextGenerationConfig.get_config_from_env()
            print_json(cfg)

            self.generator = TextGeneratorFactory.create_chat_openai_generator(
                api_key=cfg.api_key,
                base_url=cfg.base_url,
                model_name=cfg.model_name,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens
            )

            self.info(f"文本生成器初始化成功: {cfg.model_name}")

        except Exception as e:
            self.error(f"文本生成器初始化失败: {str(e)}")
            raise

    def run_task(self, taskData: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文本生成任务

        Args:
            task: 任务数据，包含inputs字段

        Returns:
            处理结果
        """
        try:
            self.info("开始处理文本生成任务")
            task = TaskMessage.model_validate(taskData)

            # 解析输入数据
            inputs = orjson.loads(task.inputs)

            # 获取任务类型和参数
            generation_type = 'simple'  # simple, template, conversation
            prompt = inputs.get('prompt', '')

            if not prompt:
                raise ValueError("缺少必要的prompt参数")

            # 根据类型执行不同的生成逻辑
            result_text = self._generate_by_type(generation_type, inputs)
            self.info("文本生成任务完成")
            return result_text

        except Exception as e:
            self.error(f"文本生成任务失败: {str(e)}")
            raise e

    def _generate_by_type(self, generation_type: str, inputs: Dict[str, Any]) -> str:
        """根据类型执行文本生成"""

        if generation_type == 'simple':
            # 简单文本生成
            prompt = inputs['prompt']
            return self.generator.generate_text(prompt)

        elif generation_type == 'template':
            # 模板文本生成
            template = inputs.get('template', inputs['prompt'])
            variables = inputs.get('variables', {})
            return self.generator.generate_with_template(template, variables)

        elif generation_type == 'conversation':
            # 对话生成
            messages = inputs.get('messages', [])
            if not messages:
                # 如果没有提供messages，将prompt作为用户消息
                messages = [{"role": "user", "content": inputs['prompt']}]
            return self.generator.generate_conversation(messages)

        else:
            raise ValueError(f"不支持的生成类型: {generation_type}")

    def update_generator_params(self, temperature=None, max_tokens=None):
        """更新生成器参数"""
        if temperature is not None:
            self.generator.set_temperature(temperature)
            self.info(f"更新temperature为: {temperature}")

        if max_tokens is not None:
            self.generator.set_max_tokens(max_tokens)
            self.info(f"更新max_tokens为: {max_tokens}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
文本生成 Worker

环境变量配置:
  OPENAI_API_KEY        OpenAI API密钥
  OPENAI_BASE_URL       OpenAI API基础URL (可选)
  TEXT_GEN_MODEL        模型名称 (默认: gpt-3.5-turbo)
  TEXT_GEN_TEMPERATURE  生成温度 (默认: 0.7)
  TEXT_GEN_MAX_TOKENS   最大token数 (默认: 1000)

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
        app = WorkerTextGeneration(consumer_name=args.name, group_name=args.group)
        app.run()

    except KeyboardInterrupt:
        logger.info("收到退出信号，正在关闭...")
    except Exception as e:
        logger.error(f"Worker启动失败: {str(e)}")
        raise


if __name__ == '__main__':
    main()
