#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试边界情况下的words字段时间分配功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_edge_cases():
    """测试边界情况"""
    processor = SubtitleProcessor(video_width=100, video_height=100, font_size=16)

    print("测试边界情况:")

    # 1. 空的words数据
    print("1. 空的words数据:")
    test_segments = [{
        "text": "测试，文本。",
        "start": 1.0,
        "end": 5.0,
        "words": []
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"   处理后有{len(result)}个片段")

    # 2. 没有逗号的文本
    print("2. 没有逗号的文本:")
    test_segments = [{
        "text": "测试文本",
        "start": 1.0,
        "end": 5.0,
        "words": [["测试", 1.0, 3.0], ["文本", 3.0, 5.0]]
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"   处理后有{len(result)}个片段")

    # 3. 不包含在words中的文本（文本不匹配）
    print("3. 文本不匹配的情况:")
    test_segments = [{
        "text": "测试，文本。",
        "start": 1.0,
        "end": 5.0,
        "words": [["不", 1.0, 2.0], ["匹配", 2.0, 5.0]]
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"   处理后有{len(result)}个片段")
    if len(result) > 0:
        print(f"   第一个片段: '{result[0]['text']}' ({result[0]['start']:.1f}-{result[0]['end']:.1f}s)")

    # 4. 时间顺序不正确的words数据
    print("4. 时间顺序不正确的words数据:")
    test_segments = [{
        "text": "测试，文本。",
        "start": 1.0,
        "end": 5.0,
        "words": [["测试，", 3.0, 2.0], ["文本。", 4.0, 5.0]]  # 开始时间大于结束时间
    }]

    result = processor.split_subtitle_if_exceeds_width(test_segments)
    print(f"   处理后有{len(result)}个片段")
    if len(result) > 0:
        print(f"   第一个片段: '{result[0]['text']}' ({result[0]['start']:.1f}-{result[0]['end']:.1f}s)")

    print("边界情况测试完成。")


if __name__ == "__main__":
    test_edge_cases()
