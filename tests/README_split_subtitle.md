# 字幕分割功能说明

## 功能介绍

本模块提供了一个新的功能函数 `split_subtitle_line_by_width_and_duration`，用于：

1. 判断字幕行是否超出屏幕宽度
2. 对超出宽度的行进行智能分割
3. 确保分割后的每个子句都有足够的显示时间，避免在屏幕上一闪而过

## 函数说明

```python
def split_subtitle_line_by_width_and_duration(self, words_data: List[List], min_display_duration: float = 0.5) -> List[List]:
    """
    判断字幕行是否超出屏幕宽度，如果超出则分割成多个独立行，并确保每个子句有足够的显示时间

    Args:
        words_data: 包含字符及时序信息的列表，格式为 [["字符", 开始时间, 结束时间], ...]
        min_display_duration: 每个分割后子句的最小显示时间（秒），默认0.5秒

    Returns:
        List[List]: 分割后的字幕行列表，每个元素格式为 [文本, 开始时间, 结束时间]
    """
```

## 输入数据格式

输入的 `words_data` 应该是一个列表，其中每个元素都是一个包含三个元素的列表：

- 第一个元素：字符文本
- 第二个元素：字符开始时间（秒）
- 第三个元素：字符结束时间（秒）

示例：

```python
[
    ["您", 0.075, 0.255],
    ["知", 0.255, 0.425],
    ["道", 0.425, 0.555],
    ["吗？", 0.555, 0.895]
]
```

## 使用示例

```python
from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor

# 创建处理器实例
processor = AdvancedMultilingualSubtitleProcessor(video_width=358, video_height=512, font_size=16)

# 准备输入数据（从words.txt读取）
import json
with open("words.txt", "r", encoding="utf-8") as f:
    words_data = json.load(f)

# 分割字幕行
split_lines = processor.split_subtitle_line_by_width_and_duration(words_data, min_display_duration=0.5)

# 输出结果
for i, (text, start_time, end_time) in enumerate(split_lines):
    duration = end_time - start_time
    print(f"第{i+1}行: '{text}' (时间: {start_time:.3f}s - {end_time:.3f}s, 持续: {duration:.3f}s)")
```

## 输出格式

函数返回一个列表，每个元素都是一个包含三个元素的列表：

- 第一个元素：分割后的字幕文本
- 第二个元素：该行字幕的开始时间（秒）
- 第三个元素：该行字幕的结束时间（秒）

## 注意事项

1. 该功能会自动根据视频分辨率和字体大小计算每行的最大视觉宽度
2. 分割时会优先考虑在标点符号处分割，以保持语义完整性
3. 会过滤掉显示时间小于 `min_display_duration` 的短行，避免一闪而过影响观看体验
4. 如果整行文本未超出最大视觉宽度，则不会进行分割，直接返回整行

## 相关文件

- `advanced_multilingual_subtitle.py` - 主模块文件，包含新功能函数
- `words.txt` - 示例输入数据文件
- `demo_split_subtitle.py` - 演示如何使用分割功能
- `demo_split_subtitle_to_ass.py` - 演示如何将分割结果保存为 ASS 字幕文件
