#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试字幕分割的碎片化问题和子句宽度问题
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from work4x.workers.video_utils.subtitle import SubtitleProcessor


def test_fragmentation_and_width_issues():
    """测试碎片化和子句宽度问题"""
    # 创建处理器实例，使用较小的宽度以确保文本会被认为超出宽度
    processor = SubtitleProcessor(video_width=100, video_height=100, font_size=16)

    # 测试数据：包含多个逗号的长文本，分割后仍可能超出宽度
    test_segments = [
        {
            "text": "这是一个非常长的句子，包含很多内容，需要分割处理，但是分割后的每个部分仍然可能超出屏幕宽度限制，这就是我们需要解决的问题。",
            "start": 0.0,
            "end": 10.0,
            "words": [
                ["这是", 0.0, 1.0],
                ["一个", 1.0, 2.0],
                ["非常", 2.0, 3.0],
                ["长的", 3.0, 4.0],
                ["句子，", 4.0, 5.0],
                ["包含", 5.0, 6.0],
                ["很多", 6.0, 7.0],
                ["内容，", 7.0, 8.0],
                ["需要", 8.0, 9.0],
                ["分割", 9.0, 10.0],
                ["处理，", 10.0, 11.0],
                ["但是", 11.0, 12.0],
                ["分割", 12.0, 13.0],
                ["后的", 13.0, 14.0],
                ["每个", 14.0, 15.0],
                ["部分", 15.0, 16.0],
                ["仍然", 16.0, 17.0],
                ["可能", 17.0, 18.0],
                ["超出", 18.0, 19.0],
                ["屏幕", 19.0, 20.0],
                ["宽度", 20.0, 21.0],
                ["限制，", 21.0, 22.0],
                ["这", 22.0, 23.0],
                ["就是", 23.0, 24.0],
                ["我们", 24.0, 25.0],
                ["需要", 25.0, 26.0],
                ["解决", 26.0, 27.0],
                ["的", 27.0, 28.0],
                ["问题。", 28.0, 30.0]
            ]
        }
    ]

    print("输入片段:")
    print(f"  文本: {test_segments[0]['text']}")
    print(f"  时间: {test_segments[0]['start']:.1f} - {test_segments[0]['end']:.1f}")
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

    print(f"总共分割成 {len(result)} 个片段")

    # 检查是否存在问题
    if len(result) > 5:
        print("问题1: 分割后过于碎片化")

    # 检查每个片段是否仍可能超出宽度
    for i, segment in enumerate(result):
        char_infos = processor._analyze_text(segment['text'])
        total_width = sum(info.width for info in char_infos)
        if total_width > processor.max_visual_width:
            print(f"问题2: 片段 {i+1} 仍可能超出屏幕宽度 (宽度: {total_width:.2f}, 最大宽度: {processor.max_visual_width:.2f})")


if __name__ == "__main__":
    test_fragmentation_and_width_issues()
