"""
聊天模块使用示例
展示如何使用基于 Langchain 的聊天功能，包括流式输出和工具调用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from llm import ChatAgent, quick_chat, quick_stream_chat, calculate, get_weather
from llm.config import TextGenerationConfig

cfg = TextGenerationConfig.get_config_from_env()


def example_basic_chat():
    """基础聊天示例"""
    print("\n=== 基础聊天示例 ===")

    # 创建聊天代理
    agent = ChatAgent(
        model_type="openai",
        model_name=cfg.model_name,
        temperature=0.7
    )

    # 进行对话
    try:
        response = agent.chat("你好，介绍一下人工智能是什么？")
        print(f"AI回复: {response}")
    except Exception as e:
        print(f"聊天失败: {e}")


def example_stream_chat():
    """流式聊天示例"""
    print("\n=== 流式聊天示例 ===")

    agent = ChatAgent(
        model_type="openai",
        model_name=cfg.model_name,
        temperature=0.7,
        stream=True  # 启用流式输出
    )

    try:
        print("AI: ", end="", flush=True)
        for chunk in agent.chat("请写一首关于科技的诗", stream=True):
            print(chunk, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"\n流式聊天失败: {e}")


def example_chat_with_tools():
    """带工具调用的聊天示例"""
    print("\n=== 带工具调用的聊天示例 ===")

    # 创建聊天代理
    agent = ChatAgent(
        model_type="openai",
        model_name=cfg.model_name,
        temperature=0.7
    )

    # 注册工具
    agent.register_tool(calculate)
    agent.register_tool(get_weather)

    # 进行带工具的对话
    try:
        response = agent.chat_with_tools("计算一下 123 * 456 等于多少？")
        print(f"AI回复: {response}")

        response = agent.chat_with_tools("今天北京的天气怎么样？")
        print(f"AI回复: {response}")
    except Exception as e:
        print(f"带工具聊天失败: {e}")


def example_quick_chat():
    """快速聊天示例"""
    print("\n=== 快速聊天示例 ===")

    try:
        response = quick_chat("什么是机器学习？")
        print(f"AI回复: {response}")
    except Exception as e:
        print(f"快速聊天失败: {e}")


def example_quick_stream_chat():
    """快速流式聊天示例"""
    print("\n=== 快速流式聊天示例 ===")

    try:
        print("AI: ", end="", flush=True)
        for chunk in quick_stream_chat("请调用工具查询一下今天广东的天气怎么样", model_name=cfg.model_name):
            print(chunk, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"\n快速流式聊天失败: {e}")


def example_conversation():
    """多轮对话示例"""
    print("\n=== 多轮对话示例 ===")

    agent = ChatAgent(
        model_type="openai",
        model_name=cfg.model_name,
        temperature=0.7
    )

    # 第一轮对话
    try:
        response1 = agent.chat("你好，我叫小明")
        print(f"用户: 你好，我叫小明")
        print(f"AI: {response1}")

        # 第二轮对话
        response2 = agent.chat("我刚才说了什么？")
        print(f"用户: 我刚才说了什么？")
        print(f"AI: {response2}")

        # 查看历史记录
        history = agent.get_history()
        print(f"\n聊天历史: {history}")
    except Exception as e:
        print(f"多轮对话失败: {e}")


if __name__ == "__main__":
    # 运行示例
    # example_basic_chat()
    # example_stream_chat()
    # example_chat_with_tools()
    # example_quick_chat()
    example_quick_stream_chat()
    # example_conversation()
