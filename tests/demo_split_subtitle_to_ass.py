#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示如何使用 split_subtitle_line_by_width_and_duration 函数并将结果保存为ASS字幕文件
"""

import json
import sys
import os

# 添加上级目录到Python路径，以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.advanced_multilingual_subtitle import AdvancedMultilingualSubtitleProcessor
import pysubs2


def create_ass_subtitle_from_split_lines(split_lines, output_file: str,
                                         video_width: int = 358, video_height: int = 512):
    """将分割后的字幕行保存为ASS文件"""

    # 创建ASS字幕对象
    subs = pysubs2.SSAFile()

    # 设置样式
    style = subs.styles["Default"]
    style.fontname = "Arial"
    style.fontsize = 16.0
    style.shadow = 0.5
    style.outline = 1.0

    # 添加字幕行
    for i, (text, start_time, end_time) in enumerate(split_lines):
        # 创建字幕事件
        event = pysubs2.SSAEvent(
            start=int(start_time * 1000),  # 转换为毫秒
            end=int(end_time * 1000),      # 转换为毫秒
            text=text
        )
        subs.append(event)

    # 保存文件
    subs.save(output_file)
    print(f"ASS字幕文件已保存到: {output_file}")


def demo_split_subtitle_to_ass():
    """演示字幕分割并保存为ASS文件的功能"""
    # 视频参数
    video_width = 358
    video_height = 512
    font_size = 16

    # 创建处理器实例
    processor = AdvancedMultilingualSubtitleProcessor(video_width, video_height, font_size)

    # 读取words.txt文件
    words_file = "words.txt"
    with open(words_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        # 移除可能的引号和换行符
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        if content.startswith("'") and content.endswith("'"):
            content = content[1:-1]

        # 解析JSON数据
        words_data = json.loads(content)

    print(f"原始数据包含 {len(words_data)} 个词语")
    print(f"最大视觉宽度: {processor.max_visual_width:.2f}")

    # 分割字幕行
    split_lines = processor.split_subtitle_line_by_width_and_duration(words_data, min_display_duration=0.5)

    print(f"\n分割后得到 {len(split_lines)} 行字幕:")
    for i, (text, start_time, end_time) in enumerate(split_lines):
        duration = end_time - start_time
        print(f"  第{i+1}行: '{text}' (时间: {start_time:.3f}s - {end_time:.3f}s, 持续: {duration:.3f}s)")

    # 保存为ASS文件
    output_file = "split_subtitle_output.ass"
    create_ass_subtitle_from_split_lines(split_lines, output_file, video_width, video_height)

    # 检查是否有显示时间不足的行
    short_lines = [line for line in split_lines if (line[2] - line[1]) < 0.5]
    if short_lines:
        print(f"\n注意: 有 {len(short_lines)} 行显示时间小于0.5秒，可能会影响观看体验")


if __name__ == "__main__":
    demo_split_subtitle_to_ass()
