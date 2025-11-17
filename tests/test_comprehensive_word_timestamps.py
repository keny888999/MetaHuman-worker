#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面测试使用words字段中的字词级时间戳数据进行时间分配的功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_edge_cases():
    """测试边界情况"""
    # 创建处理器实例
    processor = SubtitleProcessor(video_width=358, video_height=512, font_size=16)

    print("测试边界情况:")

    # 1. 空的words数据
    test_segments = [{
        "text": "测试文本，包含逗号。",
        "start": 1.0,
        "end": 5.0,
        "words": []
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"空words数据测试: 处理后有{len(result)}个片段")

    # 2. 没有逗号的文本
    test_segments = [{
        "text": "测试文本没有逗号",
        "start": 1.0,
        "end": 5.0,
        "words": [["测试", 1.0, 2.0], ["文本", 2.0, 3.0], ["没有", 3.0, 4.0], ["逗号", 4.0, 5.0]]
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"无逗号文本测试: 处理后有{len(result)}个片段")

    # 3. 不超出宽度的文本
    test_segments = [{
        "text": "短文本，测试。",
        "start": 1.0,
        "end": 3.0,
        "words": [["短", 1.0, 1.5], ["文本，", 1.5, 2.0], ["测试。", 2.0, 3.0]]
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"不超出宽度测试: 处理后有{len(result)}个片段")

    # 4. 多个逗号的情况
    test_segments = [{
        "text": "第一部分，第二部分，第三部分。",
        "start": 1.0,
        "end": 10.0,
        "words": [
            ["第一", 1.0, 2.0], ["部分，", 2.0, 3.0],
            ["第二", 3.0, 4.0], ["部分，", 4.0, 5.0],
            ["第三", 5.0, 6.0], ["部分。", 6.0, 10.0]
        ]
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"多个逗号测试: 处理后有{len(result)}个片段")
    for i, segment in enumerate(result):
        print(f"  片段{i+1}: {segment['text']} ({segment['start']:.1f}-{segment['end']:.1f}s)")


def test_time_allocation_accuracy():
    """测试时间分配的准确性"""
    processor = SubtitleProcessor(video_width=358, video_height=512, font_size=16)

    print("\n测试时间分配准确性:")

    # 构造一个精确的测试用例
    test_segments = [{
        "text": "你好，世界。",
        "start": 0.0,
        "end": 4.0,
        "words": [
            ["你", 0.0, 1.0],
            ["好，", 1.0, 2.0],
            ["世", 2.0, 3.0],
            ["界。", 3.0, 4.0]
        ]
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)

    print(f"输入文本: {test_segments[0]['text']}")
    print(f"输入时间: {test_segments[0]['start']}-{test_segments[0]['end']}s")
    print(f"处理后片段数: {len(result)}")

    expected_texts = ["你好，", "世界。"]
    expected_times = [(0.0, 2.0), (2.0, 4.0)]

    for i, (segment, expected_text, (expected_start, expected_end)) in enumerate(zip(result, expected_texts, expected_times)):
        print(f"  片段{i+1}:")
        print(f"    文本 - 期望: '{expected_text}', 实际: '{segment['text']}'")
        print(f"    时间 - 期望: {expected_start}-{expected_end}s, 实际: {segment['start']:.1f}-{segment['end']:.1f}s")

        assert segment['text'] == expected_text, f"文本不匹配: 期望'{expected_text}', 实际'{segment['text']}'"
        assert abs(segment['start'] - expected_start) < 0.001, f"开始时间不匹配: 期望{expected_start}, 实际{segment['start']}"
        assert abs(segment['end'] - expected_end) < 0.001, f"结束时间不匹配: 期望{expected_end}, 实际{segment['end']}"

    print("时间分配准确性测试通过！")


if __name__ == "__main__":
    test_edge_cases()
    test_time_allocation_accuracy()
