#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试根据逗号或顿号分割字幕的功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_multilingual_subtitle import split_subtitle_json_by_comma


def main():
    # 测试参数
    input_file = "sentences_output.json"
    output_file = "sentences_output_split_test.json"
    video_width = 358
    video_height = 512
    font_size = 16

    print("开始测试根据逗号或顿号分割字幕功能...")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"视频分辨率: {video_width}x{video_height}")
    print(f"字体大小: {font_size}")

    try:
        # 调用处理函数
        split_subtitle_json_by_comma(
            input_json_file=input_file,
            output_json_file=output_file,
            video_width=video_width,
            video_height=video_height,
            font_size=font_size
        )
        print("处理完成!")

        # 读取并显示结果
        with open(output_file, 'r', encoding='utf-8') as f:
            import json
            result = json.load(f)

        print("\n处理结果:")
        for i, segment in enumerate(result):
            print(f"{i+1}. '{segment['text']}' (时间: {segment['start']:.3f}s - {segment['end']:.3f}s, 持续: {segment['end']-segment['start']:.3f}s)")

    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
