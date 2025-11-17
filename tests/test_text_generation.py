"""
文本生成器测试文件

测试 LiteLLM 文本生成器的各种功能
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.text_generator import TextGenerator, TextGeneratorFactory, quick_generate
from llm.config import TextGenerationConfig, validate_config


class TestTextGenerator(unittest.TestCase):
    """文本生成器测试类"""

    def setUp(self):
        """测试前准备"""
        # 使用模拟的API密钥
        os.environ["OPENAI_API_KEY"] = "test-api-key"

    def tearDown(self):
        """测试后清理"""
        # 清理环境变量
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

    def test_text_generator_init(self):
        """测试文本生成器初始化"""
        generator = TextGenerator(
            model_type="chat_openai",
            model_name="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=100
        )

        self.assertEqual(generator.model_type, "chat_openai")
        self.assertEqual(generator.model_name, "gpt-3.5-turbo")
        self.assertEqual(generator.temperature, 0.5)
        self.assertEqual(generator.max_tokens, 100)

    def test_factory_create_openai_generator(self):
        """测试工厂方法创建OpenAI生成器"""
        generator = TextGeneratorFactory.create_openai_generator(
            model_name="gpt-3.5-turbo-instruct"
        )

        self.assertEqual(generator.model_type, "openai")
        self.assertEqual(generator.model_name, "gpt-3.5-turbo-instruct")

    def test_factory_create_chat_openai_generator(self):
        """测试工厂方法创建ChatOpenAI生成器"""
        generator = TextGeneratorFactory.create_chat_openai_generator(
            model_name="gpt-4"
        )

        self.assertEqual(generator.model_type, "chat_openai")
        self.assertEqual(generator.model_name, "gpt-4")

    def test_factory_create_local_generator(self):
        """测试工厂方法创建本地生成器"""
        generator = TextGeneratorFactory.create_local_generator(
            base_url="http://localhost:11434/v1",
            model_name="llama2"
        )

        self.assertEqual(generator.model_type, "chat_openai")
        self.assertEqual(generator.model_name, "llama2")

    @patch('llm.text_generator.completion')
    def test_generate_text_success(self, mock_completion):
        """测试文本生成成功"""
        # 模拟LLM响应
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "这是生成的文本"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response

        generator = TextGenerator(model_type="chat_openai")
        result = generator.generate_text("测试提示")

        self.assertEqual(result, "这是生成的文本")
        mock_completion.assert_called_once()

    @patch('llm.text_generator.completion')
    def test_generate_with_template_success(self, mock_completion):
        """测试模板生成成功"""
        # 模拟LLM响应
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "生成的模板文本"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response

        generator = TextGenerator(model_type="chat_openai")
        template = "你好，{name}！欢迎来到{place}。"
        variables = {"name": "张三", "place": "北京"}

        result = generator.generate_with_template(template, variables)

        self.assertEqual(result, "生成的模板文本")

    @patch('llm.text_generator.completion')
    def test_generate_conversation_success(self, mock_completion):
        """测试对话生成成功"""
        # 模拟LLM响应
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "对话回复"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response

        generator = TextGenerator(model_type="chat_openai")
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好"}
        ]

        result = generator.generate_conversation(messages)

        self.assertEqual(result, "对话回复")

    def test_set_temperature(self):
        """测试设置温度"""
        generator = TextGenerator(model_type="chat_openai")
        generator.set_temperature(0.9)

        self.assertEqual(generator.temperature, 0.9)

    def test_set_max_tokens(self):
        """测试设置最大token数"""
        generator = TextGenerator(model_type="chat_openai")
        generator.set_max_tokens(500)

        self.assertEqual(generator.max_tokens, 500)

    def test_unsupported_model_type(self):
        """测试不支持的模型类型"""
        # 注意：LiteLLM 不会因为模型类型不支持而抛出异常，所以这个测试不再适用
        # 我们保留这个测试方法，但修改其实现
        generator = TextGenerator(model_type="unsupported_model")
        self.assertEqual(generator.model_type, "unsupported_model")


class TestTextGenerationConfig(unittest.TestCase):
    """文本生成配置测试类"""

    def test_validate_model_valid(self):
        """测试验证有效模型"""
        self.assertTrue(TextGenerationConfig.validate_model("qwen3:14b"))
        self.assertTrue(TextGenerationConfig.validate_model("qwen-flash-2025-07-28"))

    def test_validate_model_invalid(self):
        """测试验证无效模型"""
        self.assertFalse(TextGenerationConfig.validate_model("invalid-model"))

    def test_validate_temperature_valid(self):
        """测试验证有效温度"""
        self.assertTrue(TextGenerationConfig.validate_temperature(0.0))
        self.assertTrue(TextGenerationConfig.validate_temperature(1.0))
        self.assertTrue(TextGenerationConfig.validate_temperature(2.0))

    def test_validate_temperature_invalid(self):
        """测试验证无效温度"""
        self.assertFalse(TextGenerationConfig.validate_temperature(-0.1))
        self.assertFalse(TextGenerationConfig.validate_temperature(2.1))

    def test_validate_max_tokens_valid(self):
        """测试验证有效最大token数"""
        self.assertTrue(TextGenerationConfig.validate_max_tokens(1))
        self.assertTrue(TextGenerationConfig.validate_max_tokens(1000))
        self.assertTrue(TextGenerationConfig.validate_max_tokens(4096))

    def test_validate_max_tokens_invalid(self):
        """测试验证无效最大token数"""
        self.assertFalse(TextGenerationConfig.validate_max_tokens(0))
        self.assertFalse(TextGenerationConfig.validate_max_tokens(5000))

    def test_get_template_valid(self):
        """测试获取有效模板"""
        template = TextGenerationConfig.get_template("article_writer")
        self.assertIn("template", template)
        self.assertIn("default_variables", template)

    def test_get_template_invalid(self):
        """测试获取无效模板"""
        with self.assertRaises(ValueError):
            TextGenerationConfig.get_template("invalid_template")

    def test_list_templates(self):
        """测试列出所有模板"""
        templates = TextGenerationConfig.list_templates()
        self.assertIsInstance(templates, list)
        self.assertIn("article_writer", templates)
        self.assertIn("email_composer", templates)

    def test_validate_config_valid(self):
        """测试验证有效配置"""
        config = {
            "model_name": "qwen-flash-2025-07-28",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        self.assertTrue(validate_config(config))

    def test_validate_config_missing_model(self):
        """测试验证缺少模型的配置"""
        config = {
            "temperature": 0.7,
            "max_tokens": 1000
        }
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_validate_config_invalid_model(self):
        """测试验证无效模型的配置"""
        config = {
            "model_name": "invalid-model",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_validate_config_invalid_temperature(self):
        """测试验证无效温度的配置"""
        config = {
            "model_name": "qwen-flash-2025-07-28",
            "temperature": -0.5,
            "max_tokens": 1000
        }
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_validate_config_invalid_max_tokens(self):
        """测试验证无效最大token数的配置"""
        config = {
            "model_name": "qwen-flash-2025-07-28",
            "temperature": 0.7,
            "max_tokens": 0
        }
        with self.assertRaises(ValueError):
            validate_config(config)


@patch('llm.text_generator.completion')
def test_quick_generate(mock_completion):
    """测试快速生成函数"""
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = "test-api-key"

    # 模拟LLM响应
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "快速生成的文本"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_completion.return_value = mock_response

    try:
        result = quick_generate("测试提示")
        assert result == "快速生成的文本"
    finally:
        # 清理环境变量
        del os.environ["OPENAI_API_KEY"]


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
