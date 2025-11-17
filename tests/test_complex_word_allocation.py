#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试复杂情况下的words字段时间分配功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_complex_allocation():
    """测试复杂情况下的时间分配"""
    # 创建处理器实例，使用较小的宽度以确保文本会被认为超出宽度
    processor = SubtitleProcessor(video_width=100, video_height=100, font_size=16)

    # 测试数据：包含多个逗号的文本
    test_segments = [
        {
            "text": "第一部分，第二部分，第三部分。",
            "start": 0.0,
            "end": 9.0,
            "words": [
                ["第一", 0.0, 1.0],
                ["部分，", 1.0, 2.0],
                ["第二", 2.0, 3.0],
                ["部分，", 3.0, 4.0],
                ["第三", 4.0, 5.0],
                ["部分。", 5.0, 9.0]  # 最后一部分时间较长
            ]
        }
    ]

    print("输入片段:")
    print(f"  文本: {test_segments[0]['text']}")
    print(f"  时间: {test_segments[0]['start']:.1f} - {test_segments[0]['end']:.1f}")
    print(f"  Words: {test_segments[0]['words']}")
    print()

    # 调用函数处理
    result = processor.split_subtitle_if_exceeds_width(test_segments)

    print("输出片段:")
    for i, segment in enumerate(result):
        duration = segment['end'] - segment['start']
        print(f"  片段 {i+1}:")
        print(f"    文本: {segment['text']}")
        print(f"    时间: {segment['start']:.3f} - {segment['end']:.3f}")
        print(f"    时长: {duration:.3f}秒")
        print()

    # 验证结果
    assert len(result) == 3, f"期望分割成3个片段，实际分割成{len(result)}个片段"
    assert result[0]['text'] == "第一部分，", f"第一个片段文本不正确: {result[0]['text']}"
    assert result[1]['text'] == "第二部分，", f"第二个片段文本不正确: {result[1]['text']}"
    assert result[2]['text'] == "第三部分。", f"第三个片段文本不正确: {result[2]['text']}"

    # 验证时间分配
    assert abs(result[0]['start'] - 0.0) < 0.001, f"第一个片段开始时间不正确: {result[0]['start']}"
    assert abs(result[0]['end'] - 2.0) < 0.001, f"第一个片段结束时间不正确: {result[0]['end']}"
    assert abs(result[1]['start'] - 2.0) < 0.001, f"第二个片段开始时间不正确: {result[1]['start']}"
    assert abs(result[1]['end'] - 4.0) < 0.001, f"第二个片段结束时间不正确: {result[1]['end']}"
    assert abs(result[2]['start'] - 4.0) < 0.001, f"第三个片段开始时间不正确: {result[2]['start']}"
    assert abs(result[2]['end'] - 9.0) < 0.001, f"第三个片段结束时间不正确: {result[2]['end']}"

    print("复杂情况测试通过！时间分配正确基于words字段的数据。")


def test_real_world_data():
    """测试真实数据"""
    # 使用真实的数据示例
    processor = SubtitleProcessor(video_width=358, video_height=512, font_size=16)

    # 来自sentences_output.json的真实数据
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

    print("真实数据测试:")
    print(f"输入文本: {test_segments[0]['text']}")
    print(f"输入时间: {test_segments[0]['start']:.3f} - {test_segments[0]['end']:.3f}")
    print()

    # 调用函数处理
    result = processor.split_subtitle_if_exceeds_width(test_segments)

    print("输出片段:")
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

    print("真实数据测试通过！时间分配正确基于words字段的数据。")


if __name__ == "__main__":
    test_complex_allocation()
    print("-" * 50)
    test_real_world_data()
