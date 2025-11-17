# LiteLLM 文本生成器

基于 LiteLLM 的文本生成模块，支持多种 LLM 模型进行文本生成任务。

## 功能特性

- 🚀 支持多种 OpenAI 模型（GPT-3.5, GPT-4 等）
- 🌐 支持自定义 API 端点（兼容 OpenAI API 的本地模型）
- 📝 支持模板化文本生成
- 💬 支持多轮对话生成
- ⚙️ 灵活的参数配置
- 📊 内置日志记录
- 🔧 预定义模板库
- 🧪 完整的单元测试

## 安装依赖

```bash
# 安装项目依赖
pip install -e .

# 或者直接安装必要的包
pip install litellm
```

## 快速开始

### 1. 设置环境变量

```bash
# 设置 OpenAI API 密钥
export OPENAI_API_KEY="your-api-key-here"

# 可选：设置自定义 API 端点
export OPENAI_BASE_URL="https://api.openai.com/v1"

# 可选：设置模型配置
export TEXT_GEN_MODEL="gpt-3.5-turbo"
export TEXT_GEN_TEMPERATURE="0.7"
export TEXT_GEN_MAX_TOKENS="1000"
```

### 2. 基础使用

```python
from llm import TextGenerator, TextGeneratorFactory, quick_generate

# 方法1: 使用工厂方法创建
generator = TextGeneratorFactory.create_chat_openai_generator()

# 方法2: 直接创建
generator = TextGenerator(
    model_type="chat_openai",
    model_name="gpt-3.5-turbo",
    temperature=0.7
)

# 生成文本
result = generator.generate_text("请写一首关于春天的诗")
print(result)

# 快速生成（一行代码）
result = quick_generate("解释什么是人工智能")
print(result)
```

### 3. 模板生成

```python
# 使用自定义模板
template = """
请为以下产品写一个营销文案：

产品名称: {product_name}
产品特点: {features}
目标用户: {target_audience}

请生成吸引人的营销文案。
"""

variables = {
    "product_name": "智能手表",
    "features": "健康监测、长续航",
    "target_audience": "运动爱好者"
}

result = generator.generate_with_template(template, variables)
print(result)

# 使用预定义模板
from llm.config import TextGenerationConfig

template_info = TextGenerationConfig.get_template("article_writer")
variables = {
    "topic": "人工智能的发展",
    "word_count": "500",
    "style": "科普",
    "audience": "普通读者"
}

result = generator.generate_with_template(
    template_info["template"],
    variables
)
print(result)
```

### 4. 对话生成

```python
# 多轮对话
messages = [
    {"role": "system", "content": "你是一个友善的AI助手"},
    {"role": "user", "content": "什么是机器学习？"},
    {"role": "user", "content": "请用简单的语言解释"}
]

result = generator.generate_conversation(messages)
print(result)
```

## Worker 服务

项目提供了基于 Redis Stream 的 Worker 服务，可以处理异步文本生成任务。

### 启动 Worker

```bash
# 启动文本生成 Worker
python worker_text_generation.py --name my_text_worker --group text_gen_group
```

### 任务格式

发送到 Redis Stream 的任务格式：

```json
{
  "task_id": "unique_task_id",
  "request_id": "unique_request_id",
  "inputs": "{\"type\": \"simple\", \"prompt\": \"你的提示文本\"}"
}
```

支持的生成类型：

1. **简单生成** (`type: "simple"`)

```json
{
  "type": "simple",
  "prompt": "请写一首诗"
}
```

2. **模板生成** (`type: "template"`)

```json
{
  "type": "template",
  "template": "你好，{name}！欢迎来到{place}。",
  "variables": {
    "name": "张三",
    "place": "北京"
  }
}
```

3. **对话生成** (`type: "conversation"`)

```json
{
  "type": "conversation",
  "messages": [
    { "role": "system", "content": "你是一个助手" },
    { "role": "user", "content": "你好" }
  ]
}
```

## 配置选项

### 环境变量

| 变量名                 | 说明            | 默认值                      |
| ---------------------- | --------------- | --------------------------- |
| `OPENAI_API_KEY`       | OpenAI API 密钥 | 必需                        |
| `OPENAI_BASE_URL`      | API 基础 URL    | `https://api.openai.com/v1` |
| `TEXT_GEN_MODEL`       | 模型名称        | `gpt-3.5-turbo`             |
| `TEXT_GEN_TEMPERATURE` | 生成温度        | `0.7`                       |
| `TEXT_GEN_MAX_TOKENS`  | 最大 token 数   | `1000`                      |
| `TEXT_GEN_TIMEOUT`     | 请求超时时间    | `30`                        |

### 支持的模型

- `gpt-3.5-turbo`
- `gpt-3.5-turbo-16k`
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- `gpt-3.5-turbo-instruct`
- `qwen3:14b`
- `qwen-flash-2025-07-28`

### 预定义模板

- `article_writer`: 文章写作
- `email_composer`: 邮件撰写
- `code_explainer`: 代码解释
- `translator`: 文本翻译
- `summarizer`: 内容总结

```python
from llm.config import TextGenerationConfig

# 查看所有模板
templates = TextGenerationConfig.list_templates()
print(templates)

# 获取特定模板
template = TextGenerationConfig.get_template("article_writer")
print(template)
```

## 本地模型支持

支持兼容 OpenAI API 的本地模型（如 Ollama、LocalAI 等）：

```python
# 连接本地 Ollama
generator = TextGeneratorFactory.create_local_generator(
    base_url="http://localhost:11434/v1",
    model_name="llama2",
    api_key="dummy"  # 本地模型通常不需要真实密钥
)

result = generator.generate_text("你好，世界！")
print(result)
```

## 错误处理

``python
try:
result = generator.generate_text("你的提示")
print(result)
except Exception as e:
print(f"生成失败: {e}")

````

## 测试

运行单元测试：

```bash
# 运行所有测试
python -m pytest tests/test_text_generation.py -v

# 或者直接运行测试文件
python tests/test_text_generation.py
````

## 示例代码

查看 `llm/examples.py` 文件获取更多使用示例：

```bash
python llm/examples.py
```

## 注意事项

1. **API 密钥安全**: 不要在代码中硬编码 API 密钥，使用环境变量
2. **网络连接**: 确保网络可以访问 OpenAI API 或您的自定义端点
3. **速率限制**: 注意 API 的速率限制，必要时添加重试逻辑
4. **成本控制**: 合理设置 `max_tokens` 参数控制成本
5. **错误处理**: 生产环境中请添加适当的错误处理逻辑

## 项目结构

```
llm/
├── __init__.py              # 模块入口
├── text_generator.py        # 核心文本生成器
├── config.py               # 配置管理
├── examples.py             # 使用示例
└── README.md               # 说明文档

tests/
└── test_text_generation.py # 单元测试

worker_text_generation.py   # Worker 服务
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 许可证

MIT License

````
# LLM 聊天模块

本模块基于 Langchain 实现，支持文本生成的流式输出和工具调用功能。

## 功能特性

1. **基础聊天**: 支持与大语言模型进行对话
2. **流式输出**: 支持实时流式文本生成
3. **工具调用**: 支持注册和调用自定义工具函数
4. **对话历史**: 自动维护对话历史记录
5. **多模型支持**: 支持 OpenAI、Ollama 等多种模型

## 安装依赖

在项目根目录下运行:

```bash
pip install langchain langchain-openai langchain-community
````

或者使用 uv:

```bash
uv pip install langchain langchain-openai langchain-community
```

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
    model_name="gpt-3.5-turbo",
    streaming=True  # 启用流式输出
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
response = agent.chat_with_tools("计算 123 * 456 等于多少？")
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

## 文件说明

- [chat.py](chat.py): 核心聊天模块实现
- [chat_examples.py](chat_examples.py): 使用示例
- [test_chat.py](test_chat.py): 测试文件
- [CHAT_README.md](CHAT_README.md): 详细使用说明

## 注意事项

1. 使用前请确保已安装必要的依赖包
2. 使用 OpenAI 模型需要有效的 API 密钥
3. 使用 Ollama 模型需要本地运行 Ollama 服务
