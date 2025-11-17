"""
基于 LiteLLM 的聊天模块
支持文本生成流式输出和工具调用
"""

import json
import os
from typing import List, Dict, Any, Optional, Union, Generator, Callable
from utils.logger import logger
import litellm
from litellm import completion

# 工具注册表
TOOL_REGISTRY = {}


class ChatAgent:
    """基于 LiteLLM 的聊天代理"""

    def __init__(self,
                 model_type: str = "openai",
                 model_name: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None):
        """
        初始化聊天代理

        Args:
            model_type: 模型类型
            model_name: 模型名称
            api_key: API密钥
            base_url: API基础URL
            temperature: 生成温度
            max_tokens: 最大token数
        """
        self.model_type = model_type
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.chat_history = []

        # 设置API密钥
        if api_key:
            if model_name.startswith("dashscope"):
                os.environ["DASHSCOPE_API_KEY"] = api_key
            else:
                os.environ["OPENAI_API_KEY"] = api_key
        elif not os.getenv("OPENAI_API_KEY") and not os.getenv("DASHSCOPE_API_KEY"):
            logger.warning("未设置 API 密钥环境变量")

        # 设置基础URL (用于支持自定义API端点)
        if base_url:
            if model_name.startswith("dashscope"):
                os.environ["DASHSCOPE_API_BASE"] = base_url
            else:
                os.environ["OPENAI_BASE_URL"] = base_url

        self.register_tool(get_weather, "get_weather", "get the weather information")
        logger.info(f"聊天代理已初始化: {model_type} - {model_name}")

    def register_tool(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        """
        注册工具函数

        Args:
            func: 工具函数
            name: 工具名称
            description: 工具描述
        """
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or f"工具 {tool_name}")

        TOOL_REGISTRY[tool_name] = {
            "function": func,
            "name": tool_name,
            "description": tool_description
        }
        logger.info(f"工具已注册: {tool_name}")

    def _prepare_messages(self, message: str) -> List[Dict[str, str]]:
        """准备消息格式"""
        messages = self.chat_history.copy()
        messages.append({"role": "user", "content": message})
        return messages

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        """准备工具定义"""
        tools = []
        for tool_info in TOOL_REGISTRY.values():
            # 简化的工具定义，实际使用中可能需要更详细的参数定义
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "输入参数"
                            }
                        },
                        "required": ["input"]
                    }
                }
            })
        return tools

    def chat(self, message: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        进行聊天对话

        Args:
            message: 用户输入消息
            stream: 是否使用流式输出

        Returns:
            如果 stream=False: 返回完整的响应文本 (str)
            如果 stream=True: 返回生成器 (Generator[str, None, None])
        """
        try:
            logger.info(f"开始聊天对话，消息: {message[:100]}...，流式模式: {stream}")

            # 添加用户消息到历史记录
            self.chat_history.append({"role": "user", "content": message})

            # 准备消息
            messages = self._prepare_messages(message)

            # 准备工具
            tools = self._prepare_tools()

            # 准备参数
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "stream": stream
            }

            if self.max_tokens:
                kwargs["max_tokens"] = self.max_tokens

            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = completion(**kwargs)

            if stream:
                # 流式输出
                def text_stream():
                    full_response = ""
                    tool_calls = []

                    try:
                        for chunk in response:
                            # 检查chunk是否有choices属性
                            if hasattr(chunk, 'choices') and chunk.choices:
                                choice = chunk.choices[0]

                                # 处理内容
                                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content') and choice.delta.content:
                                    content = choice.delta.content
                                    full_response += content
                                    yield content

                                # 处理工具调用
                                if hasattr(choice, 'delta') and hasattr(choice.delta, 'tool_calls') and choice.delta.tool_calls:
                                    for tool_call in choice.delta.tool_calls:
                                        if hasattr(tool_call, 'function') and tool_call.function and hasattr(tool_call.function, 'name'):
                                            tool_calls.append({
                                                "name": tool_call.function.name,
                                                "arguments": getattr(tool_call.function, 'arguments', "") or ""
                                            })

                    except Exception as e:
                        logger.error(f"流式聊天失败: {str(e)}")
                        yield f"错误: {str(e)}"

                    # 处理工具调用
                    if tool_calls:
                        for tool_call in tool_calls:
                            if tool_call["name"] in TOOL_REGISTRY:
                                try:
                                    # 执行工具
                                    tool_func = TOOL_REGISTRY[tool_call["name"]]["function"]
                                    tool_result = tool_func(tool_call["arguments"])

                                    # 添加工具调用和结果到历史记录
                                    self.chat_history.append({
                                        "role": "assistant",
                                        "content": "",
                                        "tool_calls": [{
                                            "name": tool_call["name"],
                                            "arguments": tool_call["arguments"]
                                        }]
                                    })
                                    self.chat_history.append({
                                        "role": "tool",
                                        "name": tool_call["name"],
                                        "content": str(tool_result)
                                    })
                                except Exception as e:
                                    logger.error(f"工具 {tool_call['name']} 调用失败: {str(e)}")

                    # 添加AI消息到历史记录
                    self.chat_history.append({"role": "assistant", "content": full_response})

                return text_stream()
            else:
                # 非流式输出
                content = ""
                tool_calls = []

                # 检查response是否有choices属性
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]

                    # 获取内容
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content') and choice.message.content:
                        content = choice.message.content

                    # 处理工具调用
                    if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                        for tool_call in choice.message.tool_calls:
                            if hasattr(tool_call, 'function') and tool_call.function and hasattr(tool_call.function, 'name'):
                                tool_calls.append({
                                    "name": tool_call.function.name,
                                    "arguments": getattr(tool_call.function, 'arguments', "") or ""
                                })

                # 处理工具调用
                if tool_calls:
                    for tool_call in tool_calls:
                        if tool_call["name"] in TOOL_REGISTRY:
                            try:
                                # 执行工具
                                tool_func = TOOL_REGISTRY[tool_call["name"]]["function"]
                                tool_result = tool_func(tool_call["arguments"])

                                # 添加工具调用和结果到历史记录
                                self.chat_history.append({
                                    "role": "assistant",
                                    "content": "",
                                    "tool_calls": [{
                                        "name": tool_call["name"],
                                        "arguments": tool_call["arguments"]
                                    }]
                                })
                                self.chat_history.append({
                                    "role": "tool",
                                    "name": tool_call["name"],
                                    "content": str(tool_result)
                                })
                            except Exception as e:
                                logger.error(f"工具 {tool_call['name']} 调用失败: {str(e)}")

                # 添加AI消息到历史记录
                self.chat_history.append({"role": "assistant", "content": content})

                return content

        except Exception as e:
            logger.error(f"聊天对话失败: {str(e)}")
            raise

    def chat_with_tools(self, message: str, tool_names: Optional[List[str]] = None,
                        stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        使用工具进行聊天对话

        Args:
            message: 用户输入消息
            tool_names: 要使用的工具名称列表，如果为None则使用所有已注册工具
            stream: 是否使用流式输出

        Returns:
            如果 stream=False: 返回完整的响应文本 (str)
            如果 stream=True: 返回生成器 (Generator[str, None, None])
        """
        # 保存当前工具注册表
        original_tools = TOOL_REGISTRY.copy()

        # 如果指定了工具名称，只保留这些工具
        if tool_names:
            filtered_tools = {}
            for name in tool_names:
                if name in original_tools:
                    filtered_tools[name] = original_tools[name]
            TOOL_REGISTRY.clear()
            TOOL_REGISTRY.update(filtered_tools)

        try:
            # 使用普通聊天方法，它会自动处理工具
            result = self.chat(message, stream=stream)
            return result
        finally:
            # 恢复原始工具注册表
            TOOL_REGISTRY.clear()
            TOOL_REGISTRY.update(original_tools)

    def clear_history(self):
        """清空聊天历史"""
        self.chat_history.clear()
        logger.info("聊天历史已清空")

    def get_history(self) -> List[Dict[str, str]]:
        """获取聊天历史"""
        return self.chat_history


# 便捷函数
def quick_chat(message: str,
               model_type: str = "openai",
               model_name: str = "gpt-3.5-turbo",
               api_key: Optional[str] = None,
               base_url: Optional[str] = None,
               stream: bool = False,
               **kwargs) -> Union[str, Generator[str, None, None]]:
    """
    快速聊天的便捷函数

    Args:
        message: 用户输入消息
        model_type: 模型类型
        model_name: 模型名称
        api_key: API密钥
        base_url: API基础URL
        stream: 是否使用流式输出
        **kwargs: 其他参数

    Returns:
        如果 stream=False: 返回完整的响应文本 (str)
        如果 stream=True: 返回生成器 (Generator[str, None, None])
    """
    agent = ChatAgent(
        model_type=model_type,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    return agent.chat(message, stream=stream)


def quick_stream_chat(message: str,
                      model_type: str = "openai",
                      model_name: str = "gpt-3.5-turbo",
                      api_key: Optional[str] = None,
                      base_url: Optional[str] = None,
                      **kwargs) -> Generator[str, None, None]:
    """
    快速流式聊天的便捷函数

    Args:
        message: 用户输入消息
        model_type: 模型类型
        model_name: 模型名称
        api_key: API密钥
        base_url: API基础URL
        **kwargs: 其他参数

    Returns:
        生成器 (Generator[str, None, None])
    """
    agent = ChatAgent(
        model_type=model_type,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    result = agent.chat_with_tools(message, ["get_weather"], stream=True)
    if isinstance(result, str):
        # 如果返回的是字符串，将其转换为生成器
        def single_yield():
            yield result
        return single_yield()
    return result


# 示例工具函数
def calculate(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression: 数学表达式，例如 "2 + 3 * 4"

    Returns:
        计算结果
    """
    try:
        # 安全地计算表达式
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            return "表达式包含非法字符"

        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"


def get_weather(city: str) -> str:
    """
    获取天气信息

    Args:
        city: 城市名称

    Returns:
        天气信息
    """
    # 这里只是一个示例，实际应该调用天气API
    return f"{city}的天气：晴朗，温度25°C，湿度60%"
