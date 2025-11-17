# 字幕宽度控制分割功能说明

## 功能概述

此功能用于处理 JSON 格式的字幕文件，根据屏幕宽度智能分割字幕行，避免字幕超出屏幕显示范围，同时防止过度碎片化。

## 算法逻辑

1. 遍历每一行字幕记录，使用`_is_text_exceed_width`函数判断是否超出屏幕宽度
2. 如果超出，尝试以逗号或顿号作为分隔符分割出多条独立字幕数组 A
3. 判断 A[0]的文字是否超出屏幕宽度：
   - 如果超出，在合适的位置插入换行符
   - 如果没有超出，尝试与下一条 A[1]进行合并，再次判断是否超出屏幕宽度
4. 生成新的 JSON 文件

## 使用方法

```python
from work4x.workers.video_utils.advanced_multilingual_subtitle import split_subtitle_with_width_control

# 调用函数处理字幕文件
split_subtitle_with_width_control(
    input_json_file="input.json",
    output_json_file="output.json",
    video_width=358,
    video_height=512,
    font_size=16
)
```

## 示例

### 输入文件 (sentences_1214.json)

```json
[
  {
    "text": "这款陶瓷茶杯采用高温烧制工艺，釉面光滑细腻，手感温润。",
    "start": 0.175,
    "end": 5.205
  },
  {
    "text": "杯身线条流畅，握感舒适，适合日常使用。",
    "start": 5.415,
    "end": 8.945
  }
]
```

### 输出文件 (处理后)

```json
[
  {
    "text": "这款陶瓷茶杯采用高温烧制工艺，",
    "start": 0.175,
    "end": 2.69
  },
  {
    "text": "釉面光滑细腻，手感温润。",
    "start": 2.69,
    "end": 5.205
  },
  {
    "text": "杯身线条流畅，握感舒适，",
    "start": 5.415,
    "end": 7.18
  },
  {
    "text": "适合日常使用。",
    "start": 7.18,
    "end": 8.945
  }
]
```

## 运行测试

```bash
# 运行演示脚本
python tests/demo_width_control_split.py

# 运行基础测试
python tests/test_width_control_split.py
```

## 特点

1. **智能分割**：优先使用逗号、顿号等语义标点进行分割
2. **避免碎片化**：在分割后尝试合并相邻片段以减少总片段数
3. **时间合理分配**：根据原始时间范围合理分配各片段的时间戳
4. **宽度控制**：确保分割后的每个片段都不超出屏幕显示范围
