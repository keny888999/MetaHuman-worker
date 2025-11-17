#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试新增的split_subtitle_if_exceeds_width函数
"""

import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def test_split_if_exceeds():
    """测试split_subtitle_if_exceeds_width函数"""
    # 创建处理器实例
    processor = AdvancedMultilingualSubtitleProcessor(video_width=358, video_height=512, font_size=16)

    # 测试数据
    test_segments = [
        {
            "text": "三分钟解决一个数学难题，五秒钟记住一百个电话号码。",
            "start": 4.735,
            "end": 9.435
        },
        {
            "text": "朋友都说我脑袋里装着永不停歇的马达，",
            "start": 10.075,
            "end": 13.085
        },
        {
            "text": "这本事您说神不神？",
            "start": 20.345,
            "end": 21.775
        }
    ]

    print("原始字幕片段:")
    for i, segment in enumerate(test_segments):
        print(f"  {i+1}. {segment['text']} (持续时间: {segment['end'] - segment['start']:.3f}秒)")

    # 处理字幕
    processed_segments = processor.split_subtitle_if_exceeds_width(test_segments)

    print("\n处理后的字幕片段:")
    for i, segment in enumerate(processed_segments):
        duration = segment['end'] - segment['start']
        print(f"  {i+1}. {segment['text']} (持续时间: {duration:.3f}秒)")

    # 检查是否正确分割
    print("\n处理结果分析:")
    if len(processed_segments) > len(test_segments):
        print("  - 字幕已成功分割")
    else:
        print("  - 字幕未被分割")

    # 验证时间分配
    print("\n时间分配检查:")
    for i, segment in enumerate(processed_segments):
        duration = segment['end'] - segment['start']
        if duration < processor.min_display_time:
            print(f"  - 警告: 第{i+1}个片段显示时间({duration:.3f}秒)小于最小显示时间({processor.min_display_time}秒)")
        else:
            print(f"  - 第{i+1}个片段显示时间({duration:.3f}秒)充足")


if __name__ == "__main__":
    test_split_if_exceeds()
