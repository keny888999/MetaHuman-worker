#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用真实JSON数据测试新增的split_subtitle_if_exceeds_width函数
"""

import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor


def test_with_real_json_data():
    """使用真实JSON数据测试"""
    # 创建处理器实例
    processor = AdvancedMultilingualSubtitleProcessor(video_width=358, video_height=512, font_size=16)

    # 读取真实数据
    with open('sentences_output.json', 'r', encoding='utf-8') as f:
        test_segments = json.load(f)

    print("原始字幕片段:")
    for i, segment in enumerate(test_segments):
        duration = segment['end'] - segment['start']
        has_comma = "，" in segment['text'] or "、" in segment['text']
        print(f"  {i+1}. '{segment['text']}' (持续时间: {duration:.3f}秒, 有逗号: {has_comma})")

    # 处理字幕
    processed_segments = processor.split_subtitle_if_exceeds_width(test_segments)

    print("\n处理后的字幕片段:")
    for i, segment in enumerate(processed_segments):
        duration = segment['end'] - segment['start']
        has_comma = "，" in segment['text'] or "、" in segment['text']
        print(f"  {i+1}. '{segment['text']}' (持续时间: {duration:.3f}秒, 有逗号: {has_comma})")

    # 检查是否正确分割
    print("\n处理结果分析:")
    if len(processed_segments) > len(test_segments):
        print("  - 字幕已成功分割")
        print(f"  - 原始片段数: {len(test_segments)}")
        print(f"  - 处理后片段数: {len(processed_segments)}")
    else:
        print("  - 字幕未被分割")
        print(f"  - 片段数保持: {len(test_segments)}")

    # 验证时间分配
    print("\n时间分配检查:")
    all_adequate = True
    for i, segment in enumerate(processed_segments):
        duration = segment['end'] - segment['start']
        if duration < processor.min_display_time:
            print(f"  - 警告: 第{i+1}个片段显示时间({duration:.3f}秒)小于最小显示时间({processor.min_display_time}秒)")
            all_adequate = False
        else:
            print(f"  - 第{i+1}个片段显示时间({duration:.3f}秒)充足")

    if all_adequate:
        print("  - ✓ 所有片段显示时间都充足")
    else:
        print("  - ✗ 存在显示时间不足的片段")

    # 保存结果到文件
    with open('./sentences_output_split_if_exceeds_test.json', 'w', encoding='utf-8') as f:
        json.dump(processed_segments, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: ./sentences_output_split_if_exceeds_test.json")


if __name__ == "__main__":
    test_with_real_json_data()
