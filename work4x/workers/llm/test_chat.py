"""
聊天模块测试文件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from llm import ChatAgent, quick_chat, quick_stream_chat


def test_basic_chat():
    """测试基础聊天功能"""
    print("=== 测试基础聊天功能 ===")

    try:
        # 创建聊天代理
        agent = ChatAgent(
            model_type="openai",
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )

        # 进行简单对话
        response = agent.chat("你好，介绍一下人工智能是什么？")
        print(f"AI回复: {response}")
        print("✓ 基础聊天功能测试通过\n")

    except Exception as e:
        print(f"✗ 基础聊天功能测试失败: {e}\n")


def test_stream_chat():
    """测试流式聊天功能"""
    print("=== 测试流式聊天功能 ===")

    try:
        agent = ChatAgent(
            model_type="openai",
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            streaming=True
        )

        print("AI: ", end="", flush=True)
        chunks_received = 0
        for chunk in agent.chat("请写一首关于科技的短诗", stream=True):
            print(chunk, end="", flush=True)
            chunks_received += 1
        print()  # 换行

        if chunks_received > 0:
            print("✓ 流式聊天功能测试通过\n")
        else:
            print("✗ 流式聊天功能测试失败: 没有收到任何数据块\n")

    except Exception as e:
        print(f"✗ 流式聊天功能测试失败: {e}\n")


def test_quick_functions():
    """测试便捷函数"""
    print("=== 测试便捷函数 ===")

    try:
        # 测试快速聊天
        response = quick_chat("什么是机器学习？")
        print(f"快速聊天回复: {response}")

        # 测试快速流式聊天
        print("快速流式聊天: ", end="", flush=True)
        chunks_received = 0
        for chunk in quick_stream_chat("讲一个简短的笑话"):
            print(chunk, end="", flush=True)
            chunks_received += 1
        print()  # 换行

        if chunks_received > 0:
            print("✓ 便捷函数测试通过\n")
        else:
            print("✗ 便捷函数测试失败: 没有收到任何数据块\n")

    except Exception as e:
        print(f"✗ 便捷函数测试失败: {e}\n")


if __name__ == "__main__":
    print("开始测试聊天模块...\n")

    test_basic_chat()
    test_stream_chat()
    test_quick_functions()

    print("所有测试完成！")
