"""
文本生成配置文件

定义文本生成相关的配置选项和默认值
"""

import os
from typing import Dict, Any
from dataclasses import dataclass, astuple, asdict


dashscope_api_key = "sk-8d6fadb22aeb4d03b23e403909a781f8"
dashscope_api = "https://dashscope.aliyuncs.com/compatible-mode/v1"

os.environ["DASHSCOPE_API_KEY"] = dashscope_api_key
os.environ["DASHSCOPE_API_BASE"] = dashscope_api


@dataclass
class TextModelConfig(object):
    """模型配置类"""
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    temperature: float = 0.9
    max_tokens: int = 10240
    timeout: int = 30


class TextGenerationConfig:
    """文本生成配置类"""

    # 默认配置
    DEFAULT_API_KEY = dashscope_api_key
    DEFAULT_BASE_URL = dashscope_api
    DEFAULT_MODEL = "qwen-flash-2025-07-28"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 40960
    DEFAULT_TIMEOUT = 30  # 秒

    # 模板预设
    PREDEFINED_TEMPLATES = {
        "article_writer": {
            "template": """
            请写一篇关于 {topic} 的文章。
            
            要求：
            - 字数：{word_count} 字左右
            - 风格：{style}
            - 目标读者：{audience}
            
            请确保内容准确、有条理且易于理解。
            """,
            "default_variables": {
                "word_count": "800",
                "style": "专业且易懂",
                "audience": "普通读者"
            }
        },

        "email_composer": {
            "template": """
            请帮我写一封邮件：
            
            收件人：{recipient}
            主题：{subject}
            邮件目的：{purpose}
            语气：{tone}
            
            请写出完整的邮件内容。
            """,
            "default_variables": {
                "tone": "礼貌且专业"
            }
        },

        "code_explainer": {
            "template": """
            请解释以下代码的功能和工作原理：
            
            ```{language}
            {code}
            ```
            
            解释要求：
            - 详细说明代码的功能
            - 解释主要的逻辑流程
            - 指出重要的技术要点
            - 适合 {skill_level} 程序员理解
            """,
            "default_variables": {
                "skill_level": "初级到中级"
            }
        },

        "translator": {
            "template": """
            请将以下文本从 {source_lang} 翻译成 {target_lang}：
            
            原文：
            {text}
            
            翻译要求：
            - 保持原意准确
            - 语言自然流畅
            - 适合 {context} 场景使用
            """,
            "default_variables": {
                "source_lang": "英文",
                "target_lang": "中文",
                "context": "正式"
            }
        },

        "summarizer": {
            "template": """
            请总结以下内容：
            
            {content}
            
            总结要求：
            - 长度：{length}
            - 重点关注：{focus}
            - 目标读者：{audience}
            """,
            "default_variables": {
                "length": "200字以内",
                "focus": "核心要点",
                "audience": "普通读者"
            }
        }
    }

    @classmethod
    def get_config_from_env(cls):
        """从环境变量获取配置"""
        cfg = TextModelConfig()
        cfg.api_key = os.getenv("OPENAI_API_KEY") or cls.DEFAULT_API_KEY
        cfg.base_url = os.getenv("OPENAI_BASE_URL") or cls.DEFAULT_BASE_URL
        cfg.model_name = os.getenv("TEXT_GEN_MODEL", cls.DEFAULT_MODEL)
        cfg.temperature = float(os.getenv("TEXT_GEN_TEMPERATURE", str(cls.DEFAULT_TEMPERATURE)))
        cfg.max_tokens = int(os.getenv("TEXT_GEN_MAX_TOKENS", str(cls.DEFAULT_MAX_TOKENS)))
        cfg.timeout = int(os.getenv("TEXT_GEN_TIMEOUT", str(cls.DEFAULT_TIMEOUT)))
        return cfg

    @classmethod
    def validate_model(cls, model_name: str) -> bool:
        """验证模型名称是否支持"""
        return model_name in cls.SUPPORTED_MODELS

    @classmethod
    def get_template(cls, template_name: str) -> Dict[str, Any]:
        """获取预定义模板"""
        if template_name not in cls.PREDEFINED_TEMPLATES:
            raise ValueError(f"未找到模板: {template_name}")

        return cls.PREDEFINED_TEMPLATES[template_name].copy()

    @classmethod
    def list_templates(cls) -> list:
        """列出所有可用模板"""
        return list(cls.PREDEFINED_TEMPLATES.keys())

    @classmethod
    def validate_temperature(cls, temperature: float) -> bool:
        """验证温度参数"""
        return 0.0 <= temperature <= 2.0

    @classmethod
    def validate_max_tokens(cls, max_tokens: int) -> bool:
        """验证最大token数"""
        return 1 <= max_tokens <= 4096  # 根据模型调整


# 配置验证函数
def validate_config(config: Dict[str, Any]) -> bool:
    """验证配置是否有效"""
    required_fields = ["model_name"]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"缺少必要配置: {field}")

    # 验证温度
    if "temperature" in config and not TextGenerationConfig.validate_temperature(config["temperature"]):
        raise ValueError(f"无效的温度值: {config['temperature']}")

    # 验证最大token数
    if "max_tokens" in config and not TextGenerationConfig.validate_max_tokens(config["max_tokens"]):
        raise ValueError(f"无效的最大token数: {config['max_tokens']}")

    return True


# 默认配置实例
DEFAULT_CONFIG = TextGenerationConfig.get_config_from_env()
