# JSON to ASS 字幕转换工具

## 简介

本工具用于将 JSON 格式的字幕文件转换为 ASS (Advanced SubStation Alpha) 格式，以便在视频播放器中使用。

## JSON 格式要求

输入的 JSON 文件应为包含字幕信息的数组，每个元素包含以下字段：

```json
[
  {
    "text": "字幕文本内容",
    "start": 0.0, // 开始时间（秒）
    "end": 5.0 // 结束时间（秒）
  }
]
```

## 使用方法

### 1. 直接调用函数

```python
from tests.json_to_ass_converter import json_to_ass

# 转换文件
json_to_ass(
    json_file_path="input.json",
    ass_file_path="output.ass",
    title="My Subtitle",
    font_name="Microsoft YaHei",
    font_size=16
)
```

### 2. 命令行调用

```bash
python tests/json_to_ass_converter.py input.json -o output.ass --title "My Subtitle"
```

### 3. 使用示例脚本

参考 `tests/convert_test_json_to_ass.py` 文件：

```python
python tests/convert_test_json_to_ass.py
```

## 自定义样式参数

函数支持多种 ASS 样式参数：

- `font_name`: 字体名称
- `font_size`: 字体大小
- `primary_color`: 主要颜色 (&HBBGGRR format)
- `outline_color`: 轮廓颜色
- `outline`: 轮廓大小
- `shadow`: 阴影大小
- `alignment`: 对齐方式
- `margin_v`: 垂直边距

## 输出示例

生成的 ASS 文件包含标准的脚本信息、样式定义和字幕事件：

```
[Script Info]
Title: Test Subtitle
...

[V4+ Styles]
...

[Events]
Dialogue: 0,00:00:00.00,00:00:02.50,Default,,0,0,0,,这是字幕文本
...
```
