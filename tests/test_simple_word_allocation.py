#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试使用words字段中的字词级时间戳数据进行时间分配的功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_simple_allocation():
    """简单测试时间分配"""
    # 创建处理器实例，使用较小的宽度以确保文本会被认为超出宽度
    processor = SubtitleProcessor(video_width=100, video_height=100, font_size=16)

    # 测试数据：包含逗号且会超出宽度的文本
    test_segments = [
        {
            "text": "你好，世界。",
            "start": 0.0,
            "end": 4.0,
            "words": [
                ["你好，", 0.0, 2.0],
                ["世界。", 2.0, 4.0]
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
    assert len(result) == 2, f"期望分割成2个片段，实际分割成{len(result)}个片段"
    assert result[0]['text'] == "你好，", f"第一个片段文本不正确: {result[0]['text']}"
    assert result[1]['text'] == "世界。", f"第二个片段文本不正确: {result[1]['text']}"

    # 验证时间分配
    assert abs(result[0]['start'] - 0.0) < 0.001, f"第一个片段开始时间不正确: {result[0]['start']}"
    assert abs(result[0]['end'] - 2.0) < 0.001, f"第一个片段结束时间不正确: {result[0]['end']}"
    assert abs(result[1]['start'] - 2.0) < 0.001, f"第二个片段开始时间不正确: {result[1]['start']}"
    assert abs(result[1]['end'] - 4.0) < 0.001, f"第二个片段结束时间不正确: {result[1]['end']}"

    print("测试通过！时间分配正确基于words字段的数据。")


if __name__ == "__main__":
    test_simple_allocation()
