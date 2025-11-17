#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from work4x.workers.video_utils.subtitle import split_subtitle_with_width_control


def load_json_file(file_path):
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_segments(segments, title):
    """打印字幕片段"""
    print(f"\n{title}:")
    print("-" * 50)
    for i, segment in enumerate(segments):
        text = segment.get('text', '')
        start = segment.get('start', 0)
        end = segment.get('end', 0)
        duration = end - start
        print(f"{i+1}. {text} ({start:.3f}s - {end:.3f}s, 持续时间: {duration:.3f}s)")

        # 如果有words字段，也显示相关信息
        if 'words' in segment:
            print(f"   包含 {len(segment['words'])} 个词级时间戳")


def demo_width_control_split():
    """演示宽度控制分割功能"""
    # 输入文件路径
    input_file = r"work4x\workers\video_utils\test\sentences_1214.json"

    # 输出文件路径
    output_file = r"tests\results\width_control_split_demo.json"

    # 视频参数 (使用较小的宽度来测试超宽情况)
    video_width = 358
    video_height = 512
    font_size = 16

    print("字幕宽度控制分割演示")
    print("=" * 50)
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"视频参数: {video_width}x{video_height}, 字体大小: {font_size}")

    # 加载并显示原始字幕
    original_segments = load_json_file(input_file)
    print_segments(original_segments, "原始字幕")

    # 调用处理函数
    split_subtitle_with_width_control(
        input_json_file=input_file,
        output_json_file=output_file,
        video_width=video_width,
        video_height=video_height,
        font_size=font_size
    )

    # 加载并显示处理后的字幕
    processed_segments = load_json_file(output_file)
    print_segments(processed_segments, "处理后字幕")

    print(f"\n处理完成!")
    print(f"- 原始字幕段数: {len(original_segments)}")
    print(f"- 处理后字幕段数: {len(processed_segments)}")

    # 验证时间戳分配是否正确
    print("\n时间戳验证:")
    print("-" * 50)
    for orig_segment in original_segments:
        orig_text = orig_segment.get('text', '')
        orig_start = orig_segment.get('start', 0)
        orig_end = orig_segment.get('end', 0)
        orig_duration = orig_end - orig_start

        # 查找处理后的相关片段
        processed_texts = []
        processed_start = None
        processed_end = None

        for proc_segment in processed_segments:
            proc_text = proc_segment.get('text', '')
            proc_start = proc_segment.get('start', 0)
            proc_end = proc_segment.get('end', 0)

            # 检查处理后的文本是否来自原始文本
            if proc_text in orig_text:
                processed_texts.append(proc_text)
                if processed_start is None:
                    processed_start = proc_start
                processed_end = proc_end

        if processed_start is not None and processed_end is not None:
            processed_duration = processed_end - processed_start
            time_diff = abs(orig_duration - processed_duration)
            print(f"原始: '{orig_text[:30]}...' ({orig_duration:.3f}s)")
            # 修复f-string语法错误
            text_list = ' + '.join([f'"{t}"' for t in processed_texts])
            print(f"处理后: {text_list} ({processed_duration:.3f}s)")
            print(f"时间差: {time_diff:.3f}s {'✓' if time_diff < 0.001 else '⚠'}")
            print()


if __name__ == "__main__":
    demo_width_control_split()
