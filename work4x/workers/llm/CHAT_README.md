# LLM 聊天模块使用说明

本模块基于 LiteLLM 实现，支持文本生成的流式输出和工具调用功能。

## 功能特性

1. **基础聊天**: 支持与大语言模型进行对话
2. **流式输出**: 支持实时流式文本生成
3. **工具调用**: 支持注册和调用自定义工具函数
4. **对话历史**: 自动维护对话历史记录
5. **多模型支持**: 支持 OpenAI、DashScope 等多种模型

## 安装依赖

项目已经包含必要的依赖，无需额外安装。

## 快速开始

### 1. 基础聊天

```python
from llm import ChatAgent

# 创建聊天代理
agent = ChatAgent(
    model_type="openai",
    model_name="gpt-3.5-turbo",
    api_key="your-api-key"  # 可选，也可通过环境变量设置
)

# 进行对话
response = agent.chat("你好，介绍一下人工智能是什么？")
print(response)
```

### 2. 流式聊天

```python
from llm import ChatAgent

agent = ChatAgent(
    model_type="openai",
    model_name="gpt-3.5-turbo"
)

# 流式输出
for chunk in agent.chat("请写一首诗", stream=True):
    print(chunk, end="", flush=True)
```

### 3. 工具调用

```python
from llm import ChatAgent, calculate, get_weather

agent = ChatAgent(
    model_type="openai",
    model_name="gpt-3.5-turbo"
)

# 注册工具
agent.register_tool(calculate)
agent.register_tool(get_weather)

# 使用工具进行对话
response = agent.chat("计算 123 * 456 等于多少？")
print(response)
```

### 4. 便捷函数

```python
from llm import quick_chat, quick_stream_chat

# 快速聊天
response = quick_chat("什么是机器学习？")
print(response)

# 快速流式聊天
for chunk in quick_stream_chat("讲一个有趣的故事"):
    print(chunk, end="", flush=True)
```

## API 说明

### ChatAgent 类

#### 构造函数

```python
ChatAgent(
    model_type: str = "openai",
    model_name: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
)
```

#### 主要方法

- `chat(message: str, stream: bool = False)` - 进行聊天对话
- `chat_with_tools(message: str, tool_names: List[str] = None, stream: bool = False)` - 使用工具进行聊天
- `register_tool(func: Callable, name: str = None, description: str = None)` - 注册工具函数
- `clear_history()` - 清空聊天历史
- `get_history()` - 获取聊天历史

### 便捷函数

- `quick_chat()` - 快速聊天
- `quick_stream_chat()` - 快速流式聊天

## 工具函数

模块内置了两个示例工具函数：

1. `calculate(expression: str)` - 计算数学表达式
2. `get_weather(city: str)` - 获取天气信息（示例）

## 配置说明

### 环境变量

- `OPENAI_API_KEY` - OpenAI API 密钥
- `OPENAI_BASE_URL` - OpenAI API 基础 URL（用于自定义端点）
- `DASHSCOPE_API_KEY` - DashScope API 密钥
- `DASHSCOPE_API_BASE` - DashScope API 基础 URL

### 支持的模型

1. **OpenAI 系列**

   - `gpt-3.5-turbo`
   - `gpt-4`
   - `gpt-4-turbo`
   - 等其他 OpenAI 模型

2. **DashScope 系列**
   - `qwen3:14b`
   - `qwen-flash-2025-07-28`
   - 等其他 DashScope 模型

## 示例代码

查看 [chat_examples.py](chat_examples.py) 和 [test_chat_litellm.py](test_chat_litellm.py) 文件获取更多使用示例。

## 注意事项

1. 使用前请确保已设置必要的 API 密钥环境变量
2. 工具调用功能需要模型支持 function calling 特性
