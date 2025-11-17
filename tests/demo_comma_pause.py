#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多条件句子分割功能演示
展示如何使用多种条件来智能分割长句子
"""

from sentence_timestamp_converter import convert_word_to_sentence_timestamps


def demo_all_conditions():
    """演示所有分割条件"""

    print("多条件句子分割功能演示")
    print("=" * 60)

    # 创建一个复杂的测试用例，包含多种情况
    test_data = [
        # 第一个句子：正常句子
        ["今天", 0.0, 0.3],
        ["天气", 0.3, 0.6],
        ["很好。", 0.6, 0.9],

        # 第二个句子：中间有逗号停顿
        ["但是", 0.9, 1.2],
        ["我们", 1.2, 1.5],
        ["决定", 1.5, 1.8],
        ["去", 1.8, 2.1],
        ["公园，", 2.1, 2.4],  # 逗号后停顿较长
        ["因为", 4.0, 4.3],  # 停顿1.6秒
        ["那里", 4.3, 4.6],
        ["风景", 4.6, 4.9],
        ["很美。", 4.9, 5.2],

        # 第三个句子：以逗号结尾且持续时间超过阈值
        ["这", 5.2, 5.4],
        ["是", 5.4, 5.6],
        ["一个", 5.6, 5.8],
        ["非常", 5.8, 6.0],
        ["非常", 6.0, 6.2],
        ["非常", 6.2, 6.4],
        ["非常", 6.4, 6.6],
        ["非常", 6.6, 6.8],
        ["非常", 6.8, 7.0],
        ["非常", 7.0, 7.2],
        ["非常", 7.2, 7.4],
        ["非常", 7.4, 7.6],
        ["非常", 7.6, 7.8],
        ["非常", 7.8, 8.0],
        ["非常", 8.0, 8.2],
        ["非常", 8.2, 8.4],
        ["非常", 8.4, 8.6],
        ["非常", 8.6, 8.8],
        ["非常", 8.8, 9.0],
        ["非常", 9.0, 9.2],
        ["非常", 9.2, 9.4],
        ["非常", 9.4, 9.6],
        ["非常", 9.6, 9.8],
        ["非常", 9.8, 10.0],
        ["非常", 10.0, 10.2],
        ["非常", 10.2, 10.4],
        ["非常", 10.4, 10.6],
        ["非常", 10.6, 10.8],
        ["非常", 10.8, 11.0],
        ["非常", 11.0, 11.2],
        ["非常", 11.2, 11.4],
        ["非常", 11.4, 11.6],
        ["非常", 11.6, 11.8],
        ["非常", 11.8, 12.0],
        ["长的", 12.0, 12.2],
        ["句子，", 12.2, 15.4]  # 持续时间超过3秒
    ]

    print("测试数据:")
    print("词语\t开始时间\t结束时间")
    print("-" * 30)
    for word, start, end in test_data:
        print(f"{word}\t{start}\t\t{end}")

    print("\n" + "=" * 50)

    # 使用不同的参数组合进行测试
    print("1. 默认参数:")
    result1 = convert_word_to_sentence_timestamps(test_data)
    print(f"分割为 {len(result1)} 个句子:")
    for i, (sentence, start, end) in enumerate(result1):
        duration = end - start
        char_count = len(sentence)
        print(f"  {i+1}. '{sentence}' [{start:.1f}, {end:.1f}] (持续时间: {duration:.1f}秒, 字符数: {char_count})")

    print("\n2. 降低逗号持续时间阈值到2.0秒:")
    result2 = convert_word_to_sentence_timestamps(test_data, comma_duration_threshold=2.0)
    print(f"分割为 {len(result2)} 个句子:")
    for i, (sentence, start, end) in enumerate(result2):
        duration = end - start
        char_count = len(sentence)
        print(f"  {i+1}. '{sentence}' [{start:.1f}, {end:.1f}] (持续时间: {duration:.1f}秒, 字符数: {char_count})")

    print("\n3. 组合所有条件:")
    result3 = convert_word_to_sentence_timestamps(test_data,
                                                  comma_pause_threshold=0.5,
                                                  comma_duration_threshold=2.0,
                                                  max_chars_per_sentence=20)
    print(f"分割为 {len(result3)} 个句子:")
    for i, (sentence, start, end) in enumerate(result3):
        duration = end - start
        char_count = len(sentence)
        print(f"  {i+1}. '{sentence}' [{start:.1f}, {end:.1f}] (持续时间: {duration:.1f}秒, 字符数: {char_count})")


def demo_comma_duration_feature():
    """演示以逗号结尾句子的持续时间分割功能"""
    print("\n" + "=" * 60)
    print("以逗号结尾句子的持续时间分割功能演示")
    print("=" * 60)

    # 创建专门测试逗号持续时间功能的数据
    comma_duration_data = [
        # 正常句子
        ["根据", 0.0, 0.2],
        ["统计", 0.2, 0.4],
        ["结果，", 0.4, 0.8],  # 持续时间0.8秒，未超过阈值

        ["今年", 0.8, 1.0],
        ["GDP", 1.0, 1.2],
        ["增长", 1.2, 1.4],
        ["率为", 1.4, 1.6],
        ["6.7%，", 1.6, 4.8],  # 持续时间3.2秒，超过默认阈值3.0秒

        ["表现", 4.8, 5.0],
        ["超出", 5.0, 5.2],
        ["预期。", 5.2, 5.4]
    ]

    print("以逗号结尾句子的持续时间测试数据:")
    print("词语\t开始时间\t结束时间\t持续时间")
    print("-" * 40)

    # 计算每个词语的持续时间
    for i, (word, start, end) in enumerate(comma_duration_data):
        duration = end - start
        print(f"{word}\t{start}\t\t{end}\t\t{duration:.1f}秒")

        # 计算句子的持续时间
        if '，' in word and i > 0:
            sentence_start = comma_duration_data[0][1] if i == 4 else comma_duration_data[5][1]
            sentence_duration = end - sentence_start
            print(f"\t\t\t\t句子持续时间: {sentence_duration:.1f}秒")

    print("\n" + "=" * 50)

    # 使用不同的逗号持续时间阈值进行测试
    print("1. 使用默认阈值(3.0秒):")
    result1 = convert_word_to_sentence_timestamps(comma_duration_data, comma_duration_threshold=3.0)
    print(f"分割为 {len(result1)} 个句子:")
    for i, (sentence, start, end) in enumerate(result1):
        duration = end - start
        char_count = len(sentence)
        print(f"  {i+1}. '{sentence}' [{start:.1f}, {end:.1f}] (持续时间: {duration:.1f}秒, 字符数: {char_count})")

    print("\n2. 使用较低阈值(2.0秒):")
    result2 = convert_word_to_sentence_timestamps(comma_duration_data, comma_duration_threshold=2.0)
    print(f"分割为 {len(result2)} 个句子:")
    for i, (sentence, start, end) in enumerate(result2):
        duration = end - start
        char_count = len(sentence)
        print(f"  {i+1}. '{sentence}' [{start:.1f}, {end:.1f}] (持续时间: {duration:.1f}秒, 字符数: {char_count})")

    print("\n3. 使用较高阈值(4.0秒):")
    result3 = convert_word_to_sentence_timestamps(comma_duration_data, comma_duration_threshold=4.0)
    print(f"分割为 {len(result3)} 个句子:")
    for i, (sentence, start, end) in enumerate(result3):
        duration = end - start
        char_count = len(sentence)
        print(f"  {i+1}. '{sentence}' [{start:.1f}, {end:.1f}] (持续时间: {duration:.1f}秒, 字符数: {char_count})")


if __name__ == "__main__":
    demo_all_conditions()
    demo_comma_duration_feature()

    print("\n" + "=" * 60)
    print("总结:")
    print("1. 多条件分割功能可以智能处理复杂场景")
    print("2. 逗号停顿时间超过阈值时进行分割")
    print("3. 句子字符数超过限制时进行分割")
    print("4. 以逗号结尾的句子持续时间超过阈值时进行分割")
    print("5. 多种条件可以组合使用，提高分割效果")
