"""
基于 LiteLLM 的文本生成器
支持多种 LLM 模型进行文本生成
"""
import os
import sys
from typing import Optional, Dict, Any, List, Union, Generator

from agno.agent import Agent, RunOutput
from agno.media import Image
from agno.models.dashscope import DashScope
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools import Toolkit
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.utils.pprint import pprint_run_response
from rich.pretty import pprint

db = SqliteDb(db_file="agno.db")

# uv run -m 模式需要这2行代码
CURR_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_PATH)


from templates import templates


class TestTools(Toolkit):
    """TestTools 是一个查询工具

    """

    def __init__(self, **kwargs):
        tools = [
            self.count_words,
            self.whois
        ]
        super().__init__(name="testTools", tools=tools, **kwargs)

    def count_words(self, text: str):
        """计算文字长度的工具

        Args:
            text (string): 输入文字

        Returns:
            int: 返回文本的长度
        """
        print(f"\n\n【count_words:{text}】 len={len(text)}\n\n", flush=True)
        return len(text)

    def whois(self, name: str):
        """whois 是一个查询人物资料的工具
        Args:
            name (str): 人物名称
        Returns:
            str: 返回人物描述
        """
        print("whois")
        if name.find("黎家耀") >= 0:
            return "黎家耀是一个电子工程师, 专门生产音响器材"
        else:
            return "未知人物"


class TextGenerator:
    """基于 LiteLLM 的文本生成器"""

    def __init__(self,
                 model_type: str = "openai",
                 model_name: str = "gpt-3.5-turbo",
                 api_key: str = "",
                 base_url: str = "",
                 temperature: float = 1.0,
                 max_tokens: int = 4096,
                 **kwargs
                 ):
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
            os.environ["DASHSCOPE_API_KEY"] = api_key
            os.environ["DASHSCOPE_API_BASE"] = base_url

    def _prepare_messages(self, prompt: str) -> List[Dict[str, str]]:
        """准备消息格式"""
        return [{"role": "user", "content": prompt}]

    def generate_text(self, prompt: str, stream: bool = False, thinking: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
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
        def post_hook(run_output: RunOutput):
            if kwargs.get("on_complete", None):
                func = kwargs.get("on_complete")
                func(run_output)  # type: ignore

        try:
            print(f"开始生成文本，提示: {prompt[:100]}...，流式模式: {stream}")

            temperature = kwargs.get("temperature", None)

            if temperature is None:
                temperature = self.temperature or 1.0

            model = DashScope(
                id=self.model_name,
                enable_thinking=False,
                api_key=self.api_key,
                base_url=str(self.base_url),
                max_tokens=self.max_tokens,
                temperature=temperature,
                thinking_budget=1024
            )

            print({
                "temperature": model.temperature,
                "enable_thinking": model.enable_thinking,
                "max_tokens": model.max_tokens
            })

            memory_manager = MemoryManager(
                db=db,
                # Select the model used for memory creation and updates. If unset, the default model of the Agent is used.
                model=model,
                # You can also provide additional instructions
                additional_instructions="Don't store the user's real name",
            )

            agent = Agent(
                model=model,
                # db=db,
                # memory_manager=memory_manager,
                # enable_user_memories=True,
                instructions=["生成文案时调用工具来计算文本字数"],
                debug_mode=False,
                markdown=True,
                tools=[],
                post_hooks=[post_hook]
            )

            response = agent.run(prompt, stream=True)
            # agent.print_response(prompt, stream=True)

            if stream:
                def output_stream():
                    thinking_prefix_written = False
                    for chunk in response:  # type: ignore
                        if hasattr(chunk, 'reasoning_content') and chunk.reasoning_content:
                            content = chunk.reasoning_content
                            if not thinking_prefix_written:
                                thinking_prefix_written = True
                                content = "<think>\n\n" + content
                                # print(content, end='', flush=True)
                            yield content
                        elif hasattr(chunk, 'content') and chunk.content:
                            content = chunk.content
                            if thinking_prefix_written:
                                thinking_prefix_written = False
                                content = "\n\n</think>\n\n" + content
                            # print(content, end='', flush=True)
                            yield content

                return output_stream()
            else:
                if hasattr(response, "content"):
                    return str(response.content)
                elif hasattr(response, 'reasoning_content'):
                    return str(response.reasoning_content)
                return ""

        except Exception as e:
            print(f"文本生成失败: {str(e)}")
            raise

    def generate_with_template(self, template: str, variables: Dict[str, Any], stream: bool = False, thinking: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
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
            print(f"使用模板生成文本，变量: {variables}，流式模式: {stream}")

            # 格式化模板
            formatted_prompt = template.format(**variables)
            return self.generate_text(formatted_prompt, stream=stream, thinking=thinking, **kwargs)

        except Exception as e:
            print(f"模板文本生成失败: {str(e)}")
            raise


def quick_stream_generate_with_template(template: str,
                                        variables: Dict[str, Any],
                                        model_type: Optional[str] = "chat_openai",
                                        model_name: Optional[str] = "qwen-flash-2025-07-28",
                                        api_key: Optional[str] = None,
                                        base_url: Optional[str] = None,
                                        stream: Optional[bool] = False,
                                        thinking: Optional[bool] = False,
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
        model_type=str(model_type),
        model_name=str(model_name),
        api_key="sk-8d6fadb22aeb4d03b23e403909a781f8",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    result = generator.generate_with_template(template, variables, stream=bool(stream), thinking=bool(thinking), **kwargs)
    # if isinstance(result, str):
    #    # 如果返回的是字符串，将其转换为生成器
    #    def single_yield():
    #        yield result
    #    return single_yield()

    return result


tp = str(templates.get("audio"))

stream = True
kwargs = {
    "temperature": 0
}


def on_complete(run_output):
    pprint(run_output.metrics)


response = quick_stream_generate_with_template(tp, {"prompt": "今天天气", "tone": "happy", "time": 3, "language": "Chinese"},
                                               thinking=True,
                                               stream=stream,
                                               temperature=1.0,
                                               on_complete=on_complete
                                               )

if stream:
    for chunk in response:
        print(chunk, end="", flush=True)
else:
    print(response)


'''
import requests

data = {
    "model": "qwen-flash",
    "enable_thinking": False,
    "stream": False,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "请写一篇40个字以内的短视频口播文案"
        }
    ]
}
headers = {"Authorization": "Bearer sk-8d6fadb22aeb4d03b23e403909a781f8", "Content-Type": "application/json"}
response = requests.post('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', json=data, headers=headers, timeout=20)
print(response.text)
'''
