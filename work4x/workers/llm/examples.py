"""
文本生成器使用示例

展示如何使用 LiteLLM 文本生成器进行各种文本生成任务
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from llm import TextGenerator, TextGeneratorFactory, quick_generate, quick_stream_generate, quick_stream_generate_with_template
from utils.logger import logger


api_key = "xxxx"
base_url = "http://127.0.0.1:11434/v1"


def example_basic_generation():
    """基础文本生成示例"""
    print("\n=== 基础文本生成示例 ===")

    # 创建文本生成器
    generator = TextGeneratorFactory.create_chat_openai_generator(
        # api_key="your-api-key-here",  # 如果需要的话
        # base_url="https://api.openai.com/v1",  # 自定义API端点
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500
    )

    # 生成文本
    prompt = "请写一个关于人工智能的简短介绍"
    try:
        result = generator.generate_text(prompt)
        print(f"生成结果: {result}")
    except Exception as e:
        print(f"生成失败: {e}")


def example_template_generation():
    """模板文本生成示例"""
    print("\n=== 模板文本生成示例 ===")

    generator = TextGeneratorFactory.create_chat_openai_generator(api_key="xxx", base_url=base_url, model_name="qwen3:14b", temperature=0.7, max_tokens=5000)

    # 定义模板
    template = """
    请为以下产品写一个营销文案：
    
    产品名称: {product_name}
    产品类型: {product_type}
    主要特点: {features}
    目标用户: {target_audience}
    
    请生成一个吸引人的营销文案。/nothinking
    """

    # 模板变量
    variables = {
        "product_name": "智能手表Pro",
        "product_type": "可穿戴设备",
        "features": "健康监测、长续航、防水",
        "target_audience": "运动爱好者和健康意识用户"
    }

    try:
        result = generator.generate_with_template(template, variables)
        print(f"生成的营销文案: {result}")
    except Exception as e:
        print(f"生成失败: {e}")


def example_conversation_generation():
    """对话生成示例"""
    print("\n=== 对话生成示例 ===")

    generator = TextGeneratorFactory.create_chat_openai_generator()

    # 对话消息
    messages = [
        {"role": "system", "content": "你是一个友善的AI助手，擅长回答技术问题。"},
        {"role": "user", "content": "什么是机器学习？"},
        {"role": "user", "content": "请用简单的语言解释一下"}
    ]

    try:
        result = generator.generate_conversation(messages)
        print(f"AI回复: {result}")
    except Exception as e:
        print(f"对话生成失败: {e}")


def example_local_model():
    """本地模型示例（如Ollama）"""
    print("\n=== 本地模型示例 ===")

    # 如果你有本地部署的模型（如Ollama）
    try:
        generator = TextGeneratorFactory.create_local_generator(
            base_url="http://localhost:11434/v1",  # Ollama默认端点
            model_name="llama2",  # 或其他本地模型
            api_key="dummy"
        )

        result = generator.generate_text("解释什么是深度学习")
        print(f"本地模型生成结果: {result}")
    except Exception as e:
        print(f"本地模型不可用: {e}")


def example_quick_generate():
    """快速生成示例"""
    print("\n=== 快速生成示例 ===")

    try:
        result = quick_generate(
            prompt="写一首关于春天的短诗",
            temperature=0.8,
            max_tokens=200
        )
        print(f"快速生成结果: {result}")
    except Exception as e:
        print(f"快速生成失败: {e}")


def example_parameter_adjustment():
    """参数调整示例"""
    print("\n=== 参数调整示例 ===")

    generator = TextGeneratorFactory.create_chat_openai_generator()

    prompt = "生成一个创意故事开头"

    # 低温度 - 更保守的输出
    generator.set_temperature(0.2)
    try:
        result1 = generator.generate_text(prompt)
        print(f"低温度结果 (0.2): {result1}")
    except Exception as e:
        print(f"低温度生成失败: {e}")

    # 高温度 - 更有创意的输出
    generator.set_temperature(1.0)
    try:
        result2 = generator.generate_text(prompt)
        print(f"高温度结果 (1.0): {result2}")
    except Exception as e:
        print(f"高温度生成失败: {e}")


def example_stream_generation():
    """流式生成示例"""
    print("\n=== 流式生成示例 ===")

    generator = TextGeneratorFactory.create_chat_openai_generator(
        api_key="your-api-key-here",
        base_url="http://127.0.0.1:11434/v1",
        model_name="qwen3:14b",
        temperature=0.7,
        max_tokens=500
    )

    prompt = "请详细介绍一下机器学习的发展历史和未来趋势"

    try:
        print("开始流式生成...")
        print("生成内容: ", end="", flush=True)

        # 流式生成
        for chunk in generator.generate_text(prompt, stream=True):
            print(chunk, end="", flush=True)

        print("\n流式生成完成！")
    except Exception as e:
        print(f"\n流式生成失败: {e}")


def example_quick_stream_generate():
    """快速流式生成示例"""
    print("\n=== 快速流式生成示例 ===")

    try:
        prompt = "写一个关于科技发展的小故事"
        print("开始快速流式生成...")
        print("生成内容: ", end="", flush=True)

        # 使用快速流式生成函数
        for chunk in quick_stream_generate(
            prompt=prompt,
            temperature=0.8,
            max_tokens=300
        ):
            print(chunk, end="", flush=True)

        print("\n快速流式生成完成！")
    except Exception as e:
        print(f"\n快速流式生成失败: {e}")


def example_compare_stream_vs_normal():
    """比较流式生成和普通生成"""
    print("\n=== 流式生成 vs 普通生成对比 ===")

    generator = TextGeneratorFactory.create_chat_openai_generator()
    prompt = "简要介绍一下Python编程语言的特点"

    # 普通生成
    print("\n1. 普通生成模式:")
    try:
        result = generator.generate_text(prompt, stream=False)
        print(f"完整结果: {result}")
    except Exception as e:
        print(f"普通生成失败: {e}")

    # 流式生成
    print("\n2. 流式生成模式:")
    try:
        print("实时输出: ", end="", flush=True)
        for chunk in generator.generate_text(prompt, stream=True):
            print(chunk, end="", flush=True)
        print("\n流式生成完成！")
    except Exception as e:
        print(f"\n流式生成失败: {e}")


def example_template_stream_generation():
    """模板流式生成示例"""
    print("\n=== 模板流式生成示例 ===")

    try:
        generator = TextGeneratorFactory.create_chat_openai_generator()

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

        # 使用新的流式模板功能
        for chunk in generator.generate_with_template(template, variables, stream=True):
            print(chunk, end="", flush=True)

        print("\n模板流式生成完成！")

    except Exception as e:
        print(f"模板流式生成失败: {e}")


def example_quick_template_stream():
    """快速模板流式生成示例"""
    print("\n=== 快速模板流式生成示例 ===")

    try:
        template = "请为{topic}写一个{length}的{style}。"
        variables = {
            "topic": "人工智能的未来发展",
            "length": "简短的段落",
            "style": "科普文章"
        }

        print("快速模板流式输出: ", end="", flush=True)

        # 使用快速模板流式生成函数
        for chunk in quick_stream_generate_with_template(
            template=template,
            variables=variables,
            temperature=0.7,
            max_tokens=200
        ):
            print(chunk, end="", flush=True)

        print("\n快速模板流式生成完成！")
    except Exception as e:
        print(f"\n快速模板流式生成失败: {e}")


if __name__ == "__main__":
    print("LiteLLM 文本生成器示例")
    print("注意: 需要设置 OPENAI_API_KEY 环境变量或在代码中提供API密钥")

    # 运行示例
    # example_basic_generation()
    # example_template_generation()
    # example_conversation_generation()
    # example_local_model()
    # example_quick_generate()
    # example_parameter_adjustment()

    # 流式生成示例
    # example_stream_generation()
    # example_quick_stream_generate()
    # example_compare_stream_vs_normal()
    # example_template_stream_generation()
    # example_quick_template_stream()

    example_template_generation()

    print("\n示例运行完成！")
