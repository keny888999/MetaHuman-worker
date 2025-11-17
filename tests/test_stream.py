#!/usr/bin/env python3
"""
测试流式生成功能
"""

import os
import sys
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workers.llm import TextGenerator, TextGeneratorFactory, quick_generate, quick_stream_generate, quick_stream_generate_with_template

api_key = "xxxx"
base_url = "http://127.0.0.1:11434/v1"


def test_stream_vs_normal():
    """测试流式生成与普通生成的对比"""
    print("=== 流式生成测试 ===\n")

    # 创建生成器
    try:
        generator = TextGeneratorFactory.create_chat_openai_generator(
            api_key="xxxx",
            base_url="http://127.0.0.1:11434/v1",
            model_name="qwen3:14b",
            temperature=0.7,
            max_tokens=200
        )
        print("生成器创建成功！")
    except Exception as e:
        print(f"生成器创建失败: {e}")
        print("请确保设置了 OPENAI_API_KEY 环境变量")
        return

    prompt = "简要介绍一下人工智能技术的发展历程"

    # 测试普通生成
    print("\n1. 普通生成模式:")
    print("-" * 40)
    start_time = time.time()
    try:
        result = generator.generate_text(prompt, stream=False)
        end_time = time.time()
        print(f"完整结果: {result}")
        print(f"生成时间: {end_time - start_time:.2f}秒")
    except Exception as e:
        print(f"普通生成失败: {e}")

    # 测试流式生成
    print("\n2. 流式生成模式:")
    print("-" * 40)
    start_time = time.time()
    try:
        print("实时输出: ", end="", flush=True)
        for chunk in generator.generate_text(prompt, stream=True):
            print(chunk, end="", flush=True)
            time.sleep(0.01)  # 模拟打字机效果
        end_time = time.time()
        print(f"\n流式生成完成！总时间: {end_time - start_time:.2f}秒")
    except Exception as e:
        print(f"\n流式生成失败: {e}")

    # 测试快速流式生成
    print("\n3. 快速流式生成:")
    print("-" * 40)
    try:
        print("快速流式输出: ", end="", flush=True)
        for chunk in quick_stream_generate(
            prompt="写一个关于技术创新的简短段落",
            temperature=0.8,
            max_tokens=100
        ):
            print(chunk, end="", flush=True)
            time.sleep(0.01)
        print("\n快速流式生成完成！")
    except Exception as e:
        print(f"\n快速流式生成失败: {e}")


def test_stream_with_template():
    """测试模板流式生成"""
    print("\n=== 模板流式生成测试 ===\n")

    try:
        generator = TextGeneratorFactory.create_chat_openai_generator(
            api_key="xxxx",
            base_url="http://127.0.0.1:11434/v1",
            model_name="qwen3:14b",
        )

        template = """
        请为以下产品写一个简短的介绍：
        产品名称: {product_name}
        产品特点: {features}
        
        请用简洁明了的语言介绍这个产品。
        """

        variables = {
            "product_name": "智能语音助手",
            "features": "语音识别、自然语言处理、智能对话"
        }

        print("模板流式生成输出: ", end="", flush=True)

        # 流式模板生成
        for chunk in generator.generate_with_template(template, variables, stream=True):
            print(chunk, end="", flush=True)
            time.sleep(0.01)
        print("\n模板流式生成完成！")

    except Exception as e:
        print(f"模板流式生成失败: {e}")


def test_template_stream_features():
    """测试模板流式生成新功能"""
    print("\n=== 模板流式生成新功能测试 ===\n")

    try:
        generator = TextGeneratorFactory.create_chat_openai_generator(
            api_key="xxxx",
            base_url="http://127.0.0.1:11434/v1",
            model_name="qwen3:14b",
        )

        template = """
        请为以下公司写一个简短的介绍：
        公司名称: {company}
        业务领域: {business}
        核心优势: {advantage}
        
        请用专业而吸引人的语言介绍这家公司。
        """

        variables = {
            "company": "MetaHuman AI",
            "business": "人工智能和自然语言处理",
            "advantage": "先进的模型技术和丰富的应用场景"
        }

        # 测试普通模板生成
        print("1. 普通模板生成:")
        print("-" * 40)
        start_time = time.time()
        result = generator.generate_with_template(template, variables, stream=False)
        end_time = time.time()
        print(f"完整结果: {result}")
        print(f"生成时间: {end_time - start_time:.2f}秒")

        # 测试流式模板生成
        print("\n2. 流式模板生成:")
        print("-" * 40)
        start_time = time.time()
        print("实时输出: ", end="", flush=True)
        for chunk in generator.generate_with_template(template, variables, stream=True):
            print(chunk, end="", flush=True)
            time.sleep(0.01)  # 显示打字机效果
        end_time = time.time()
        print(f"\n流式模板生成完成！总时间: {end_time - start_time:.2f}秒")

        # 测试快速模板流式生成
        print("\n3. 快速模板流式生成:")
        print("-" * 40)
        simple_template = "为{product}写一个{type}的介绍。"
        simple_variables = {
            "product": "智能机器人",
            "type": "简洁有趣"
        }
        print("快速流式输出: ", end="", flush=True)
        for chunk in quick_stream_generate_with_template(
            api_key="xxxx",
            base_url="http://127.0.0.1:11434/v1",
            model_name="qwen3:14b",

            template=simple_template,
            variables=simple_variables,
            temperature=0.8,
            max_tokens=150
        ):
            print(chunk, end="", flush=True)
            time.sleep(0.01)
        print("\n快速模板流式生成完成！")

    except Exception as e:
        print(f"模板流式生成测试失败: {e}")


if __name__ == "__main__":
    print("文本生成器流式功能测试")
    print("=" * 50)

    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: 未设置 OPENAI_API_KEY 环境变量")
        print("如果你有OpenAI API密钥，请设置环境变量：")
        print("export OPENAI_API_KEY='your-api-key'")
        print("或者在代码中直接提供api_key参数")
        print()

    try:
        # test_stream_vs_normal()
        test_stream_with_template()
        # test_template_stream_features()  # 新增的模板流式测试
        print("\n测试完成！")
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中出错: {e}")
