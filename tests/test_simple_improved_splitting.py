#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试改进后的字幕分割功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_simple_improved():
    """简单测试改进效果"""
    # 创建处理器实例，使用较小的宽度以确保文本会被认为超出宽度
    processor = SubtitleProcessor(video_width=100, video_height=100, font_size=16)

    # 测试文本
    test_text = "这是一个非常长的句子，包含很多内容，需要分割处理，但是分割后的每个部分仍然可能超出屏幕宽度限制。"

    print("输入文本:")
    print(f"  {test_text}")
    print(f"  最大视觉宽度: {processor.max_visual_width:.2f}")
    print()

    # 测试智能分割方法
    intelligent_segments = processor._intelligent_split_text(test_text)
    print("智能分割结果:")
    for i, segment in enumerate(intelligent_segments):
        char_infos = processor._analyze_text(segment)
        total_width = sum(info.width for info in char_infos)
        print(f"  片段 {i+1}: {segment} (宽度: {total_width:.2f})")
    print()

    print(f"智能分割片段数: {len(intelligent_segments)}")

    # 验证结果
    if len(intelligent_segments) <= 4:
        print("✓ 解决了过度碎片化问题")
    else:
        print("✗ 仍然存在过度碎片化问题")

    # 检查所有片段是否在宽度限制内
    all_within_width = True
    for i, segment in enumerate(intelligent_segments):
        char_infos = processor._analyze_text(segment)
        total_width = sum(info.width for info in char_infos)
        if total_width > processor.max_visual_width:
            print(f"✗ 片段 {i+1} 仍超出屏幕宽度 (宽度: {total_width:.2f}, 最大宽度: {processor.max_visual_width:.2f})")
            all_within_width = False

    if all_within_width:
        print("✓ 所有片段都在屏幕宽度限制内")


if __name__ == "__main__":
    test_simple_improved()
