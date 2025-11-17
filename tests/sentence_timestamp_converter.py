#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
from typing import List, Tuple, Union, Dict, Any


def convert_word_to_sentence_timestamps(word_timestamps: List[List[Union[str, float]]],
                                        comma_pause_threshold: float = 1.0,
                                        comma_duration_threshold: float = 3.0,
                                        max_chars_per_sentence: int = 20) -> List[Dict[str, Any]]:
    """
    将字词级时间戳转换为句子级时间戳

    Args:
        word_timestamps: 字词级时间戳列表，格式为 [[word, start_time, end_time], ...]
        comma_pause_threshold: 逗号停顿时间阈值（秒），超过此时间的逗号会被视为句子分隔符
        comma_duration_threshold: 以逗号结尾的句子持续时间阈值（秒），超过此时间的句子会被分割
        max_chars_per_sentence: 每个句子的最大字符数，超过此数量的句子会被分割

    Returns:
        句子级时间戳列表，格式为 [{"text": sentence, "start": start_time, "end": end_time, "words": word_timestamps}, ...]

    Examples:
        >>> data = [["你", 0.0, 0.5], ["好", 0.5, 1.0], ["世", 1.0, 1.5], ["界", 1.5, 2.0], ["！", 2.0, 2.5]]
        >>> convert_word_to_sentence_timestamps(data)
        [{'text': '你好世界！', 'start': 0.0, 'end': 2.5, 'words': [['你', 0.0, 0.5], ['好', 0.5, 1.0], ['世', 1.0, 1.5], ['界', 1.5, 2.0], ['！', 2.0, 2.5]]}]
    """
    if not word_timestamps:
        return []

    sentences = []
    current_sentence = ""
    sentence_start_time = None
    sentence_end_time = None
    current_word_timestamps = []  # 保存当前句子的字词时间戳

    # 定义句子结束标点符号
    sentence_endings = {'.', '。', '!', '！', '?', '？'}
    # 定义可能的分隔符
    separators = {',', '，'}  # 逗号

    for i, word_info in enumerate(word_timestamps):
        if len(word_info) != 3:
            continue

        word, start_time, end_time = word_info

        # 初始化句子开始时间
        if sentence_start_time is None:
            sentence_start_time = start_time

        # 添加词语到当前句子
        current_sentence += word
        # 更新句子结束时间为当前词的结束时间
        sentence_end_time = end_time
        # 添加当前词的时间戳到当前句子的字词时间戳列表
        current_word_timestamps.append(word_info)

        # 检查是否是句子结尾标点
        if any(ending in word for ending in sentence_endings):
            # 句子结束，添加到结果列表
            if current_sentence.strip():  # 确保句子不为空
                sentences.append({
                    "text": current_sentence.strip(),
                    "start": sentence_start_time,
                    "end": sentence_end_time,
                    "words": current_word_timestamps.copy()
                })

            # 重置变量以开始新句子
            current_sentence = ""
            sentence_start_time = None
            sentence_end_time = None
            current_word_timestamps = []
        # 检查是否是逗号，并且有下一个词
        elif any(sep in word for sep in separators) and i < len(word_timestamps) - 1:
            # 计算停顿时间（下一个词的开始时间 - 当前词的结束时间）
            next_word_start_time = word_timestamps[i + 1][1]
            pause_duration = next_word_start_time - end_time

            # 计算当前句子的持续时间
            current_duration = sentence_end_time - sentence_start_time

            # 如果满足以下任一条件，则在此处分割句子：
            # 1. 逗号停顿时间超过阈值
            # 2. 当前句子字符数超过最大限制
            if current_duration >= comma_duration_threshold or pause_duration >= comma_pause_threshold or len(current_sentence) >= max_chars_per_sentence:
                if current_sentence.strip():  # 确保句子不为空
                    sentences.append({
                        "text": current_sentence.strip(),
                        "start": sentence_start_time,
                        "end": sentence_end_time,
                        "words": current_word_timestamps.copy()
                    })

                # 重置变量以开始新句子
                current_sentence = ""
                sentence_start_time = None
                sentence_end_time = None
                current_word_timestamps = []
        # 对于以逗号结尾的句子（在句子末尾）
        elif any(sep in word for sep in separators) and i == len(word_timestamps) - 1:
            # 计算当前句子的持续时间
            current_duration = sentence_end_time - sentence_start_time

            # 如果当前句子持续时间超过阈值，则在此处分割句子
            if current_duration >= comma_duration_threshold:
                if current_sentence.strip():  # 确保句子不为空
                    sentences.append({
                        "text": current_sentence.strip(),
                        "start": sentence_start_time,
                        "end": sentence_end_time,
                        "words": current_word_timestamps.copy()
                    })

                # 重置变量以开始新句子
                current_sentence = ""
                sentence_start_time = None
                sentence_end_time = None
                current_word_timestamps = []

    # 处理最后一个句子（如果没有以标点符号结尾）
    if current_sentence.strip():
        # 检查最后一个句子是否需要分割
        if sentence_start_time is not None and sentence_end_time is not None:
            current_duration = sentence_end_time - sentence_start_time
            # 如果句子太长，也进行分割
            if len(current_sentence) > max_chars_per_sentence:
                sentences.append({
                    "text": current_sentence.strip(),
                    "start": sentence_start_time,
                    "end": sentence_end_time,
                    "words": current_word_timestamps.copy()
                })
            # 如果是逗号结尾且持续时间超过阈值，也进行分割
            elif any(sep in current_sentence for sep in separators) and current_duration >= comma_duration_threshold:
                sentences.append({
                    "text": current_sentence.strip(),
                    "start": sentence_start_time,
                    "end": sentence_end_time,
                    "words": current_word_timestamps.copy()
                })
            # 否则作为普通句子处理
            else:
                sentences.append({
                    "text": current_sentence.strip(),
                    "start": sentence_start_time,
                    "end": sentence_end_time,
                    "words": current_word_timestamps.copy()
                })

    return sentences


def convert_with_custom_splitter(word_timestamps: List[List[Union[str, float]]],
                                 splitter_pattern: str = r'[.!?。！？]+') -> List[Dict[str, Any]]:
    """
    使用自定义分隔符模式将字词级时间戳转换为句子级时间戳

    Args:
        word_timestamps: 字词级时间戳列表，格式为 [[word, start_time, end_time], ...]
        splitter_pattern: 正则表达式模式，用于匹配句子分隔符

    Returns:
        句子级时间戳列表，格式为 [{"text": sentence, "start": start_time, "end": end_time, "words": word_timestamps}, ...]
    """
    if not word_timestamps:
        return []

    # 将所有词汇合并为一个字符串，并保留索引映射
    full_text = ""
    index_mapping = []  # [(start_pos, end_pos, word_index), ...]
    word_objects = []   # 保存原始的词对象用于后续引用

    for i, word_info in enumerate(word_timestamps):
        if len(word_info) != 3:
            continue
        word = word_info[0]
        start_pos = len(full_text)
        full_text += word
        end_pos = len(full_text)
        index_mapping.append((start_pos, end_pos, i))
        word_objects.append(word_info)

    # 使用正则表达式分割句子
    sentences_data = []
    last_end = 0
    last_word_index = 0

    for match in re.finditer(splitter_pattern, full_text):
        start, end = match.span()
        # 获取句子文本
        sentence_text = full_text[last_end:end].strip()
        if sentence_text:
            # 找到对应的开始和结束时间
            start_time = None
            end_time = None
            sentence_words = []  # 保存当前句子的字词时间戳

            # 查找句子中第一个和最后一个词的时间戳
            for pos_start, pos_end, word_idx in index_mapping:
                if pos_end <= last_end:
                    continue
                if pos_start >= end:
                    last_word_index = word_idx
                    break

                word_info = word_timestamps[word_idx]
                if len(word_info) == 3:
                    _, word_start, word_end = word_info
                    if start_time is None:
                        start_time = word_start
                    end_time = word_end
                    sentence_words.append(word_info)

            if start_time is not None and end_time is not None:
                sentences_data.append({
                    "text": sentence_text,
                    "start": start_time,
                    "end": end_time,
                    "words": sentence_words
                })

        last_end = end

    # 处理最后一句（如果没有以标点结尾）
    if last_end < len(full_text):
        sentence_text = full_text[last_end:].strip()
        if sentence_text:
            start_time = None
            end_time = None
            sentence_words = []  # 保存当前句子的字词时间戳

            # 查找句子中第一个和最后一个词的时间戳
            for pos_start, pos_end, word_idx in index_mapping:
                if pos_end <= last_end:
                    continue

                word_info = word_timestamps[word_idx]
                if len(word_info) == 3:
                    _, word_start, word_end = word_info
                    if start_time is None:
                        start_time = word_start
                    end_time = word_end
                    sentence_words.append(word_info)

            if start_time is not None and end_time is not None:
                sentences_data.append({
                    "text": sentence_text,
                    "start": start_time,
                    "end": end_time,
                    "words": sentence_words
                })

    return sentences_data


def load_word_timestamps_from_file(file_path: str) -> List[List[Union[str, float]]]:
    """
    从文件加载字词时间戳数据

    Args:
        file_path: 包含字词时间戳数据的文件路径

    Returns:
        字词级时间戳列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # 清理内容，移除换行符和多余的空白字符
            content = content.replace('\n', '').replace('\r', '').replace('\\n', '')
            # 移除可能的首尾括号并解析JSON
            if content.startswith('[') and content.endswith(']'):
                return json.loads(content)
            else:
                raise ValueError("文件内容不是有效的JSON数组格式")
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []


def save_sentence_timestamps_to_file(sentence_timestamps: List[Dict[str, Any]],
                                     file_path: str) -> bool:
    """
    将句子时间戳保存到文件

    Args:
        sentence_timestamps: 句子级时间戳列表
        file_path: 输出文件路径

    Returns:
        保存是否成功
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sentence_timestamps, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False


# 测试函数
if __name__ == "__main__":
    # 示例数据
    sample_data = [
        ["您", 0.075, 0.255], ["知", 0.255, 0.425], ["道", 0.425, 0.555], ["吗？", 0.555, 0.895],
        ["我", 1.095, 1.255], ["这", 1.255, 1.365], ["双", 1.365, 1.585], ["手", 1.585, 1.785],
        ["啊，", 1.785, 2.165], ["能", 2.245, 2.445], ["同", 2.445, 2.685], ["时", 2.685, 2.925],
        ["玩", 2.925, 3.105], ["转", 3.105, 3.335], ["五", 3.335, 3.525], ["种", 3.525, 3.705],
        ["乐", 3.705, 3.845], ["器。", 3.845, 4.115]
    ]

    print("使用示例:")
    print("=" * 50)

    # 方法1: 基本转换（使用所有默认参数）
    print("1. 基本转换结果（默认参数）:")
    result = convert_word_to_sentence_timestamps(sample_data)
    for sentence_data in result:
        sentence = sentence_data["text"]
        start = sentence_data["start"]
        end = sentence_data["end"]
        word_count = len(sentence_data["words"])
        duration = end - start
        char_count = len(sentence)
        print(f"  '{sentence}' [{start:.3f}, {end:.3f}] (持续时间: {duration:.3f}秒, 字符数: {char_count}, 词汇数: {word_count})")

    print("\n" + "=" * 50 + "\n")

    # 方法2: 调整参数以展示新功能
    print("2. 调整参数展示新功能:")
    # 创建一个以逗号结尾且持续时间超过阈值的句子示例
    comma_end_data = [
        ["这", 0.0, 0.5], ["是", 0.5, 1.0], ["一个", 1.0, 1.5],
        ["很长", 1.5, 2.0], ["的", 2.0, 2.5], ["句子，", 2.5, 3.5]  # 持续时间3.5秒，超过默认阈值3.0秒
    ]

    print("以逗号结尾且持续时间超过阈值的句子示例:")
    result = convert_word_to_sentence_timestamps(comma_end_data, comma_duration_threshold=3.0)
    for sentence_data in result:
        sentence = sentence_data["text"]
        start = sentence_data["start"]
        end = sentence_data["end"]
        word_count = len(sentence_data["words"])
        duration = end - start
        char_count = len(sentence)
        print(f"  '{sentence}' [{start:.1f}, {end:.1f}] (持续时间: {duration:.1f}秒, 字符数: {char_count}, 词汇数: {word_count})")

    print("\n" + "=" * 50 + "\n")

    # 方法3: 自定义分隔符转换
    print("3. 自定义分隔符转换结果:")
    result2 = convert_with_custom_splitter(sample_data)
    for sentence_data in result2:
        sentence = sentence_data["text"]
        start = sentence_data["start"]
        end = sentence_data["end"]
        duration = end - start
        char_count = len(sentence)
        print(f"  '{sentence}' [{start:.3f}, {end:.3f}] (持续时间: {duration:.3f}秒, 字符数: {char_count})")

    # 方法4: 从文件加载数据并保存结果
    print("\n" + "=" * 50 + "\n")
    print("4. 从words.txt文件加载数据进行转换:")
    try:
        # 加载完整的数据
        full_data = load_word_timestamps_from_file("words.txt")
        if full_data:
            print(f"成功加载 {len(full_data)} 个字词时间戳")
            # 转换所有数据（使用调整后的参数）
            UN_LIMIT = 10000
            result3 = convert_word_to_sentence_timestamps(full_data,
                                                          comma_pause_threshold=UN_LIMIT,
                                                          comma_duration_threshold=3.0,
                                                          max_chars_per_sentence=UN_LIMIT)
            print(f"转换得到 {len(result3)} 个句子时间戳:")
            for i, sentence_data in enumerate(result3):
                sentence = sentence_data["text"]
                start = sentence_data["start"]
                end = sentence_data["end"]
                word_count = len(sentence_data["words"])
                duration = end - start
                char_count = len(sentence)
                print(f"  {i+1}. '{sentence}' [{start:.3f}, {end:.3f}] (持续时间: {duration:.3f}秒, 字符数: {char_count}, 词汇数: {word_count})")

            # 保存结果到文件
            if save_sentence_timestamps_to_file(result3, "sentences_output.json"):
                print("\n结果已保存到 sentences_output.json")
            else:
                print("\n保存结果失败")
        else:
            print("无法从文件加载数据")
    except FileNotFoundError:
        print("未找到 words.txt 文件，跳过文件测试")
