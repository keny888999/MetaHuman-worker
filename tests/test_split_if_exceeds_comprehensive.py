#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整测试新增的split_subtitle_if_exceeds_width函数
"""

import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def test_split_if_exceeds_comprehensive():
    """全面测试split_subtitle_if_exceeds_width函数"""
    # 创建处理器实例
    processor = AdvancedMultilingualSubtitleProcessor(video_width=358, video_height=512, font_size=16)

    # 测试数据 - 包含各种情况
    test_segments = [
        {
            "text": "三分钟解决一个数学难题，五秒钟记住一百个电话号码。",  # 有逗号且可能超出宽度
            "start": 4.735,
            "end": 9.435
        },
        {
            "text": "朋友都说我脑袋里装着永不停歇的马达，",  # 有逗号且可能超出宽度
            "start": 10.075,
            "end": 13.085
        },
        {
            "text": "这本事您说神不神？",  # 没有逗号
            "start": 20.345,
            "end": 21.775
        },
        {
            "text": "没有逗号的句子不会被分割。",  # 没有逗号
            "start": 22.000,
            "end": 24.000
        },
        {
            "text": "短句，也不会被分割。",  # 有逗号但不超出宽度
            "start": 25.000,
            "end": 26.000
        }
    ]

    print("原始字幕片段:")
    for i, segment in enumerate(test_segments):
        duration = segment['end'] - segment['start']
        print(f"  {i+1}. '{segment['text']}' (持续时间: {duration:.3f}秒)")

    # 处理字幕
    processed_segments = processor.split_subtitle_if_exceeds_width(test_segments)

    print("\n处理后的字幕片段:")
    for i, segment in enumerate(processed_segments):
        duration = segment['end'] - segment['start']
        print(f"  {i+1}. '{segment['text']}' (持续时间: {duration:.3f}秒)")

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

    # 验证分割逻辑
    print("\n分割逻辑验证:")
    original_with_comma = [s for s in test_segments if "，" in s["text"] or "、" in s["text"]]
    processed_with_comma = [s for s in processed_segments if "，" in s["text"] or "、" in s["text"]]

    print(f"  - 原始包含逗号的片段数: {len(original_with_comma)}")
    print(f"  - 处理后包含逗号的片段数: {len(processed_with_comma)}")

    # 检查没有逗号的句子是否保持不变
    original_without_comma = [s for s in test_segments if "，" not in s["text"] and "、" not in s["text"]]
    processed_without_comma = [s for s in processed_segments if "，" not in s["text"] and "、" not in s["text"]]

    print(f"  - 原始不包含逗号的片段数: {len(original_without_comma)}")
    print(f"  - 处理后不包含逗号的片段数: {len(processed_without_comma)}")

    if len(original_without_comma) == len(processed_without_comma):
        print("  - ✓ 没有逗号的句子保持不变")
    else:
        print("  - ✗ 没有逗号的句子被错误修改")


if __name__ == "__main__":
    test_split_if_exceeds_comprehensive()
