#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sentence_timestamp_converter import convert_word_to_sentence_timestamps


def test_word_timestamps_feature():
    """测试新添加的字词时间戳功能"""
    # 测试数据
    sample_data = [
        ["您", 0.075, 0.255], ["知", 0.255, 0.425], ["道", 0.425, 0.555], ["吗？", 0.555, 0.895],
        ["我", 1.095, 1.255], ["这", 1.255, 1.365], ["双", 1.365, 1.585], ["手", 1.585, 1.785],
        ["啊，", 1.785, 2.165], ["能", 2.245, 2.445], ["同", 2.445, 2.685], ["时", 2.685, 2.925],
        ["玩", 2.925, 3.105], ["转", 3.105, 3.335], ["五", 3.335, 3.525], ["种", 3.525, 3.705],
        ["乐", 3.705, 3.845], ["器。", 3.845, 4.115]
    ]

    # 转换数据
    result = convert_word_to_sentence_timestamps(sample_data)

    print("测试字词时间戳功能:")
    print("=" * 50)

    for i, sentence_data in enumerate(result):
        print(f"句子 {i+1}:")
        print(f"  文本: {sentence_data['text']}")
        print(f"  开始时间: {sentence_data['start']}")
        print(f"  结束时间: {sentence_data['end']}")
        print(f"  字词数量: {len(sentence_data['words'])}")
        print("  字词时间戳:")
        for word_info in sentence_data['words']:
            print(f"    {word_info}")
        print()


if __name__ == "__main__":
    test_word_timestamps_feature()
