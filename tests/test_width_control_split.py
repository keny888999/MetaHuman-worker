#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from work4x.workers.video_utils.subtitle import split_subtitle_with_width_control


def test_width_control_split():
    """测试宽度控制分割功能"""
    # 输入文件路径
    input_file = r"work4x\workers\video_utils\test\sentences_1214.json"

    # 输出文件路径
    output_file = r"tests\results\width_control_split_result.json"

    # 视频参数 (使用较小的宽度来测试超宽情况)
    video_width = 358
    video_height = 512
    font_size = 16

    print(f"开始处理字幕文件: {input_file}")
    print(f"视频参数: {video_width}x{video_height}, 字体大小: {font_size}")

    # 调用处理函数
    split_subtitle_with_width_control(
        input_json_file=input_file,
        output_json_file=output_file,
        video_width=video_width,
        video_height=video_height,
        font_size=font_size
    )

    print(f"处理完成，结果保存到: {output_file}")


if __name__ == "__main__":
    test_width_control_split()
