# 字词级时间戳转句子级时间戳工具

## 功能说明

本工具用于将字词级的字幕时间戳转换为句子级时间戳。输入格式为 `[word, start_time, end_time]` 的数组，输出为 `(sentence, start_time, end_time)` 的数组。

工具支持多种智能分割条件，以提高字幕的可读性：

1. 基于句子结束标点符号的自然分割
2. 基于逗号停顿时间的分割
3. 基于句子字符数限制的分割
4. 基于以逗号结尾句子持续时间的分割

## 使用方法

### 1. 基本转换函数

```python
from sentence_timestamp_converter import convert_word_to_sentence_timestamps

# 示例数据
word_timestamps = [
    ["您", 0.075, 0.255],
    ["知", 0.255, 0.425],
    ["道", 0.425, 0.555],
    ["吗？", 0.555, 0.895],
    ["我", 1.095, 1.255],
    ["这", 1.255, 1.365],
    ["双", 1.365, 1.585],
    ["手", 1.585, 1.785],
    ["啊，", 1.785, 2.165],
    ["能", 2.245, 2.445],
    ["同", 2.445, 2.685],
    ["时", 2.685, 2.925],
    ["玩", 2.925, 3.105],
    ["转", 3.105, 3.335],
    ["五", 3.335, 3.525],
    ["种", 3.525, 3.705],
    ["乐", 3.705, 3.845],
    ["器。", 3.845, 4.115]
]

# 转换为句子级时间戳（使用所有默认参数）
sentence_timestamps = convert_word_to_sentence_timestamps(word_timestamps)

# 输出结果
for sentence, start, end in sentence_timestamps:
    duration = end - start
    char_count = len(sentence)
    print(f"'{sentence}' [{start:.3f}, {end:.3f}] (持续时间: {duration:.3f}秒, 字符数: {char_count})")
```

输出结果：

```
'您知道吗？' [0.075, 0.895] (持续时间: 0.820秒, 字符数: 5)
'我这双手啊，能同时玩转五种乐器。' [1.095, 4.115] (持续时间: 3.020秒, 字符数: 16)
```

### 2. 使用所有参数进行自定义转换

```python
# 使用所有自定义参数
sentence_timestamps = convert_word_to_sentence_timestamps(
    word_timestamps,
    comma_pause_threshold=1.0,          # 逗号停顿时间阈值（秒）
    comma_duration_threshold=3.0,       # 以逗号结尾句子的持续时间阈值（秒）
    max_chars_per_sentence=20           # 每个句子的最大字符数
)
```

### 3. 自定义分隔符转换函数

```python
from sentence_timestamp_converter import convert_with_custom_splitter

# 使用自定义分隔符模式
sentence_timestamps = convert_with_custom_splitter(word_timestamps, r'[.!?。！？]+')
```

### 4. 文件操作函数

```python
from sentence_timestamp_converter import load_word_timestamps_from_file, save_sentence_timestamps_to_file

# 从文件加载字词时间戳
word_timestamps = load_word_timestamps_from_file("words.txt")

# 转换
sentence_timestamps = convert_word_to_sentence_timestamps(
    word_timestamps,
    comma_pause_threshold=0.5,
    comma_duration_threshold=2.0,
    max_chars_per_sentence=15
)

# 保存结果到文件
save_sentence_timestamps_to_file(sentence_timestamps, "sentences_output.json")
```

## 函数说明

### `convert_word_to_sentence_timestamps(word_timestamps, comma_pause_threshold=1.0, comma_duration_threshold=3.0, max_chars_per_sentence=20)`

将字词级时间戳转换为句子级时间戳

**参数:**

- `word_timestamps`: 字词级时间戳列表，格式为 `[[word, start_time, end_time], ...]`
- `comma_pause_threshold`: 逗号停顿时间阈值（秒），超过此时间的逗号会被视为句子分隔符，默认为 1.0 秒
- `comma_duration_threshold`: 以逗号结尾的句子持续时间阈值（秒），超过此时间的句子会被分割，默认为 3.0 秒
- `max_chars_per_sentence`: 每个句子的最大字符数，超过此数量的句子会被分割，默认为 20 个字符

**返回:**

- 句子级时间戳列表，格式为 `[(sentence, start_time, end_time), ...]`

### `convert_with_custom_splitter(word_timestamps, splitter_pattern)`

使用自定义分隔符模式将字词级时间戳转换为句子级时间戳

**参数:**

- `word_timestamps`: 字词级时间戳列表，格式为 `[[word, start_time, end_time], ...]`
- `splitter_pattern`: 正则表达式模式，用于匹配句子分隔符，默认为 `r'[.!?。！？]+'`

**返回:**

- 句子级时间戳列表，格式为 `[(sentence, start_time, end_time), ...]`

### `load_word_timestamps_from_file(file_path)`

从文件加载字词时间戳数据

**参数:**

- `file_path`: 包含字词时间戳数据的文件路径

**返回:**

- 字词级时间戳列表

### `save_sentence_timestamps_to_file(sentence_timestamps, file_path)`

将句子时间戳保存到文件

**参数:**

- `sentence_timestamps`: 句子级时间戳列表
- `file_path`: 输出文件路径

**返回:**

- 保存是否成功

## 支持的句子结束标点符号

默认支持以下句子结束标点符号：

- `.` (英文句号)
- `。` (中文句号)
- `!` (英文感叹号)
- `！` (中文感叹号)
- `?` (英文问号)
- `？` (中文问号)

## 多条件分割功能说明

工具支持多种智能分割条件，以适应不同的应用场景：

### 1. 基于逗号停顿时间的分割

当句子中间有逗号，且逗号后的停顿时间超过设定阈值时，将逗号前的部分分割为独立句子。

### 2. 基于句子字符数限制的分割

当句子的字符数超过设定限制时，将句子分割为更小的片段，避免单行字幕过长。

### 3. 基于以逗号结尾句子持续时间的分割

当以逗号结尾的句子持续时间超过设定阈值时，将其作为一个独立句子处理。

### 使用场景示例：

假设有以下字词时间戳：

```
["这是", 0.0, 1.0],
["一个", 1.0, 2.0],
["很长", 2.0, 3.0],
["的", 3.0, 4.0],
["句子，", 4.0, 7.5]  // 持续时间3.5秒，超过默认阈值3.0秒
```

根据不同参数设置：

- 逗号持续时间阈值为 3.0 秒：会将这个以逗号结尾的长句子作为独立句子处理
- 逗号持续时间阈值为 4.0 秒：不会分割，会等待句号等结束标点

## 注意事项

1. 函数会自动处理无效数据格式，忽略不完整的条目
2. 对于没有结束标点符号的文本，会将整个文本作为一个句子处理
3. 输入数据可以包含多个句子，函数会自动按标点符号分割
4. 时间戳精度保持到毫秒级别
5. 多种分割条件可以组合使用，以获得最佳效果
