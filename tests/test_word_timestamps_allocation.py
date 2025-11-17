#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试使用words字段中的字词级时间戳数据进行时间分配的功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_word_timestamps_allocation():
    """测试使用words字段进行时间分配"""
    # 创建处理器实例
    processor = SubtitleProcessor(video_width=358, video_height=512, font_size=16)

    # 测试数据：包含逗号且超出宽度的文本
    test_segments = [
        {
            "text": "三分钟解决一个数学难题，五秒钟记住一百个电话号码。",
            "start": 4.735,
            "end": 9.435,
            "words": [
                ["三", 4.735, 4.985],
                ["分", 4.985, 5.175],
                ["钟", 5.175, 5.365],
                ["解", 5.365, 5.545],
                ["决", 5.545, 5.675],
                ["一", 5.675, 5.775],
                ["个", 5.775, 5.855],
                ["数", 5.855, 6.005],
                ["学", 6.005, 6.125],
                ["难", 6.125, 6.285],
                ["题，", 6.285, 6.685],
                ["五", 6.935, 7.115],
                ["秒", 7.115, 7.335],
                ["钟", 7.335, 7.665],
                ["记", 7.805, 8.015],
                ["住", 8.015, 8.165],
                ["一", 8.165, 8.405],
                ["百", 8.405, 8.625],
                ["个", 8.625, 8.715],
                ["电", 8.715, 8.845],
                ["话", 8.845, 8.955],
                ["号", 8.955, 9.135],
                ["码。", 9.135, 9.435]
            ]
        }
    ]

    # 调用函数处理
    result = processor.split_subtitle_if_exceeds_width(test_segments)

    print("原始片段:")
    print(f"  文本: {test_segments[0]['text']}")
    print(f"  时间: {test_segments[0]['start']:.3f} - {test_segments[0]['end']:.3f}")
    print(f"  总时长: {test_segments[0]['end'] - test_segments[0]['start']:.3f}秒")
    print()

    print("处理后的片段:")
    for i, segment in enumerate(result):
        duration = segment['end'] - segment['start']
        print(f"  片段 {i+1}:")
        print(f"    文本: {segment['text']}")
        print(f"    时间: {segment['start']:.3f} - {segment['end']:.3f}")
        print(f"    时长: {duration:.3f}秒")
        print()

    # 验证结果
    assert len(result) == 2, f"期望分割成2个片段，实际分割成{len(result)}个片段"
    assert result[0]['text'] == "三分钟解决一个数学难题，", f"第一个片段文本不正确: {result[0]['text']}"
    assert result[1]['text'] == "五秒钟记住一百个电话号码。", f"第二个片段文本不正确: {result[1]['text']}"

    # 验证时间分配是否基于words数据
    # 第一个片段应该从4.735开始，到6.685结束（"题，"的结束时间）
    assert abs(result[0]['start'] - 4.735) < 0.001, f"第一个片段开始时间不正确: {result[0]['start']}"
    assert abs(result[0]['end'] - 6.685) < 0.001, f"第一个片段结束时间不正确: {result[0]['end']}"

    # 第二个片段应该从6.935开始（"五"的开始时间），到9.435结束
    assert abs(result[1]['start'] - 6.935) < 0.001, f"第二个片段开始时间不正确: {result[1]['start']}"
    assert abs(result[1]['end'] - 9.435) < 0.001, f"第二个片段结束时间不正确: {result[1]['end']}"

    print("测试通过！时间分配正确基于words字段的数据。")


def test_without_words_data():
    """测试没有words数据时的回退机制"""
    # 创建处理器实例
    processor = SubtitleProcessor(video_width=358, video_height=512, font_size=16)

    # 测试数据：包含逗号但没有words字段
    test_segments = [
        {
            "text": "三分钟解决一个数学难题，五秒钟记住一百个电话号码。",
            "start": 4.735,
            "end": 9.435
        }
    ]

    # 调用函数处理
    result = processor.split_subtitle_if_exceeds_width(test_segments)

    print("没有words字段的测试:")
    print("原始片段:")
    print(f"  文本: {test_segments[0]['text']}")
    print(f"  时间: {test_segments[0]['start']:.3f} - {test_segments[0]['end']:.3f}")
    print()

    print("处理后的片段:")
    for i, segment in enumerate(result):
        duration = segment['end'] - segment['start']
        print(f"  片段 {i+1}:")
        print(f"    文本: {segment['text']}")
        print(f"    时间: {segment['start']:.3f} - {segment['end']:.3f}")
        print(f"    时长: {duration:.3f}秒")
        print()


if __name__ == "__main__":
    test_word_timestamps_allocation()
    print("-" * 50)
    test_without_words_data()
