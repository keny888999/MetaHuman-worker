"""
基于 LiteLLM 的文本生成器
支持多种 LLM 模型进行文本生成
"""
import os
from threading import local
from typing import Optional, Dict, Any, List, Union, Generator

from agno.models.metrics import Metrics
from work4x.utils.logger import logger
from agno.agent import Agent
# from agno.media import Image
from agno.models.dashscope import DashScope
from agno.models.litellm.litellm_openai import LiteLLMOpenAI
from agno.agent import Agent, RunOutput

# from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools import Toolkit

from work4x.workers.llm.config import TextGenerationConfig
model_cfg = TextGenerationConfig.get_config_from_env()


class CommonTools(Toolkit):
    """计算字符长度的工具
    Args:
        text (str): 需要计算的文本
    """

    def count_words(self, text: str):
        print("[count_words]")
        print(text)
        return len(text)


class TextGenerator:
    """基于 LiteLLM 的文本生成器"""

    def __init__(self,
                 model_type: str = "chat_openai",
                 model_name: str = model_cfg.model_name,
                 api_key: Optional[str] = model_cfg.api_key,
                 base_url: Optional[str] = model_cfg.base_url,
                 temperature: float = model_cfg.temperature,
                 max_tokens: int = model_cfg.max_tokens, **kwargs):
        """
        初始化文本生成器

        Args:
            model_type: 模型类型 ("openai", "dashscope")
            model_name: 模型名称
            api_key: API密钥
            base_url: API基础URL (用于自定义端点)
            temperature: 生成温度
            max_tokens: 最大token数
        """
        self.model_type = model_type
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.base_url = base_url

        # 设置API密钥
        if api_key:
            if model_type == "dashscope":
                os.environ["DASHSCOPE_API_KEY"] = api_key
            else:
                os.environ["OPENAI_API_KEY"] = api_key
        elif not os.getenv("OPENAI_API_KEY") and not os.getenv("DASHSCOPE_API_KEY"):
            logger.warning("未设置 API 密钥环境变量")

        # 设置基础URL (用于支持自定义API端点)
        if base_url:
            if model_type == "dashscope":
                os.environ["DASHSCOPE_API_BASE"] = base_url
            else:
                os.environ["OPENAI_BASE_URL"] = base_url

        logger.info(f"文本生成器已初始化: {model_type} - {model_name}")

    def _prepare_messages(self, prompt: str) -> List[Dict[str, str]]:
        """准备消息格式"""
        return [{"role": "user", "content": prompt}]

    def generate_text(self, prompt: str, stream: bool = False, thinking: bool = False, **kwargs):  # -> Union[str, Generator[str, None, None]]:
        """
        生成文本

        Args:
            prompt: 输入提示
            stream: 是否使用流式生成
            **kwargs: 额外参数

        Returns:
            如果 stream=False: 返回完整的生成文本 (str)
            如果 stream=True: 返回生成器 (Generator[str, None, None])
        """
        try:
            system_prompt = kwargs.get("system_prompt", "你是一个写作能手")

            logger.info(f"系统提示词:{system_prompt}")
            logger.info(f"开始生成文本，提示: {prompt}...，\n流式模式: {stream}")

            model = LiteLLMOpenAI(
                id=self.model_name,
                # enable_thinking=thinking,
                api_key=self.api_key,
                base_url=str(self.base_url),
                max_tokens=self.max_tokens,
                temperature=kwargs.get("temperature") or self.temperature or 1.0
            )

            '''model = DashScope(
                id=self.model_name,
                enable_thinking=thinking,
                api_key=self.api_key,
                base_url=str(self.base_url),
                max_tokens=self.max_tokens,
                temperature=kwargs.get("temperature") or self.temperature or 1.0
            )'''

            metrics = kwargs.get("metrics")
            _metrics = Metrics()

            def post_hook(run_output: RunOutput):
                nonlocal metrics, _metrics

                '''
                print({
                    "input_tokens": run_output.metrics.input_tokens,
                    "output_tokens": run_output.metrics.output_tokens,
                    "total_tokens": run_output.metrics.total_tokens
                })
                '''

                _metrics += run_output.metrics

                if metrics is not None:
                    metrics.input_tokens = _metrics.input_tokens
                    metrics.output_tokens = _metrics.output_tokens
                    metrics.total_tokens = _metrics.total_tokens

            agent = Agent(
                model=model,
                instructions=[system_prompt],
                # tools=[CommonTools()],
                post_hooks=[post_hook]
            )

            response = agent.run(prompt, stream=stream)
            if stream:
                def output_stream():
                    thinking_prefix_written = False
                    for chunk in response:  # type: ignore
                        if hasattr(chunk, 'reasoning_content') and chunk.reasoning_content:
                            content = chunk.reasoning_content
                            if not thinking_prefix_written:
                                thinking_prefix_written = True
                                content = "<think>" + content
                                # print(content, end='', flush=True)
                            yield content
                        elif hasattr(chunk, 'content') and chunk.content:
                            content = chunk.content
                            if thinking_prefix_written:
                                thinking_prefix_written = False
                                content = "</think>" + content
                            # print(content, end='', flush=True)
                            yield content

                return output_stream()
            else:
                return response.content

        except Exception as e:
            logger.error(f"文本生成失败: {str(e)}")
            raise

    def generate_with_template(self, template: str, variables: Dict[str, Any], stream: bool = False, thinking: bool = False, **kwargs):  # -> Union[str, Generator[str, None, None]]:
        """
        使用模板生成文本

        Args:
            template: 提示模板
            variables: 模板变量
            stream: 是否使用流式生成

        Returns:
            如果 stream=False: 返回完整的生成文本 (str)
            如果 stream=True: 返回生成器 (Generator[str, None, None])
        """
        try:
            logger.info(f"使用模板生成文本，变量: {variables}，流式模式: {stream}")

            # 格式化模板
            formatted_prompt = template.format(**variables)
            return self.generate_text(formatted_prompt, stream=stream, thinking=thinking, **kwargs)

        except Exception as e:
            logger.error(f"模板文本生成失败: {str(e)}")
            raise

    def generate_conversation(self, messages: List[Dict[str, str]]) -> str:
        """
        生成对话响应

        Args:
            messages: 消息列表，格式: [{"role": "system/user/assistant", "content": "内容"}]

        Returns:
            生成的响应
        """
        try:
            logger.info(f"生成对话响应，消息数: {len(messages)}")
            return ""

        except Exception as e:
            logger.error(f"对话生成失败: {str(e)}")
            raise

    def set_temperature(self, temperature: float):
        """设置生成温度"""
        self.temperature = temperature
        logger.info(f"温度已设置为: {temperature}")

    def set_max_tokens(self, max_tokens: int):
        """设置最大token数"""
        self.max_tokens = max_tokens
        logger.info(f"最大token数已设置为: {max_tokens}")

    @staticmethod
    def create_openai_generator(api_key: Optional[str] = None,
                                base_url: Optional[str] = None,
                                model_name: str = "gpt-3.5-turbo-instruct",
                                **kwargs):
        """创建OpenAI文本生成器"""
        return TextGenerator(
            model_type="openai",
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            **kwargs
        )

    @staticmethod
    def create_chat_openai_generator(api_key: Optional[str] = None,
                                     base_url: Optional[str] = None,
                                     model_name: str = "gpt-3.5-turbo",
                                     **kwargs):
        """创建ChatOpenAI文本生成器"""
        return TextGenerator(
            model_type="chat_openai",
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            **kwargs
        )

    @staticmethod
    def create_local_generator(base_url: str,
                               model_name: str = "gpt-3.5-turbo",
                               api_key: str = "dummy",
                               **kwargs):
        """创建本地模型生成器（如Ollama等）"""
        return TextGenerator(
            model_type="chat_openai",
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            **kwargs
        )


# 便捷函数
def quick_generate(prompt: str,
                   stream: bool = False,
                   **kwargs):
    """
    快速生成文本的便捷函数

    Args:
        prompt: 输入提示
        model_type: 模型类型
        model_name: 模型名称
        api_key: API密钥
        base_url: API基础URL
        stream: 是否使用流式生成
        **kwargs: 其他参数

    Returns:
        如果 stream=False: 返回完整的生成文本 (str)
        如果 stream=True: 返回生成器 (Generator[str, None, None])
    """
    generator = TextGenerator(
        **kwargs
    )
    return generator.generate_text(prompt, stream=stream)


def quick_stream_generate(prompt: str,
                          **kwargs):  # -> Generator[str, None, None]:
    """
    快速流式生成文本的便捷函数

    Args:
        prompt: 输入提示
        model_type: 模型类型
        model_name: 模型名称
        api_key: API密钥
        base_url: API基础URL
        **kwargs: 其他参数

    Returns:
        生成器 (Generator[str, None, None])
    """
    generator = TextGenerator(
        **kwargs
    )
    result = generator.generate_text(prompt, stream=True)
    if isinstance(result, str):
        # 如果返回的是字符串，将其转换为生成器
        def single_yield():
            yield result
        return single_yield()
    return result


def quick_stream_generate_with_template(template: str,
                                        variables: Dict[str, Any],
                                        thinking: bool = False,
                                        **kwargs):  # -> Generator[str, None, None]:
    """
    快速模板流式生成文本的便捷函数

    Args:
        template: 提示模板
        variables: 模板变量
        model_type: 模型类型
        model_name: 模型名称
        api_key: API密钥
        base_url: API基础URL
        **kwargs: 其他参数

    Returns:
        生成器 (Generator[str, None, None])
    """
    generator = TextGenerator(
        **kwargs
    )
    result = generator.generate_with_template(template, variables, stream=True, thinking=thinking, **kwargs)
    if isinstance(result, str):
        # 如果返回的是字符串，将其转换为生成器
        def single_yield():
            yield result
        return single_yield()
    return result


def quick_generate_with_template(template: str,
                                 variables: Dict[str, Any],
                                 thinking: bool = False,
                                 **kwargs):
    """
    快速模板流式生成文本的便捷函数

    Args:
        template: 提示模板
        variables: 模板变量
        model_type: 模型类型
        model_name: 模型名称
        api_key: API密钥
        base_url: API基础URL
        **kwargs: 其他参数

    Returns:
        生成器 (Generator[str, None, None])
    """
    generator = TextGenerator(
        **kwargs
    )
    result = generator.generate_with_template(template, variables, stream=False, thinking=thinking, **kwargs)
    return result
