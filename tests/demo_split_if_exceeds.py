#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示split_subtitle_if_exceeds_width函数的完整功能
"""

import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor, split_subtitle_if_exceeds_width_json


def demo_functionality():
    """演示功能"""
    print("=== 字幕智能分割功能演示 ===\n")

    # 1. 使用类方法直接处理数据
    print("1. 使用类方法直接处理数据:")
    processor = AdvancedMultilingualSubtitleProcessor(video_width=358, video_height=512, font_size=16)

    # 示例数据
    test_segments = [
        {
            "text": "三分钟解决一个数学难题，五秒钟记住一百个电话号码。",
            "start": 4.735,
            "end": 9.435
        },
        {
            "text": "这本事您说神不神？",
            "start": 20.345,
            "end": 21.775
        }
    ]

    print("原始数据:")
    for i, segment in enumerate(test_segments):
        duration = segment['end'] - segment['start']
        print(f"  {i+1}. '{segment['text']}' (持续时间: {duration:.3f}秒)")

    # 处理数据
    processed_segments = processor.split_subtitle_if_exceeds_width(test_segments)

    print("\n处理后数据:")
    for i, segment in enumerate(processed_segments):
        duration = segment['end'] - segment['start']
        print(f"  {i+1}. '{segment['text']}' (持续时间: {duration:.3f}秒)")

    # 2. 使用简化接口函数处理JSON文件
    print("\n\n2. 使用简化接口函数处理JSON文件:")
    print("处理文件: sentences_output.json -> sentences_output_split_if_exceeds_demo.json")

    # 使用简化接口
    split_subtitle_if_exceeds_width_json(
        'sentences_output.json',
        './sentences_output_split_if_exceeds_demo.json',
        video_width=358,
        video_height=512,
        font_size=16
    )

    print("处理完成!")

    # 3. 验证结果
    print("\n3. 验证结果:")
    with open('./sentences_output_split_if_exceeds_demo.json', 'r', encoding='utf-8') as f:
        result_segments = json.load(f)

    print(f"生成了 {len(result_segments)} 个字幕片段")

    # 检查时间分配
    processor = AdvancedMultilingualSubtitleProcessor(video_width=358, video_height=512, font_size=16)
    all_adequate = True
    for i, segment in enumerate(result_segments):
        duration = segment['end'] - segment['start']
        if duration < processor.min_display_time:
            print(f"  - 警告: 第{i+1}个片段显示时间不足")
            all_adequate = False

    if all_adequate:
        print("  - ✓ 所有片段显示时间都充足")

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    demo_functionality()
