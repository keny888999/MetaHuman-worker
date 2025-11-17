#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from work4x.workers.video_utils.subtitle import split_subtitle_with_width_control


def create_test_file():
    """创建测试用的JSON文件"""
    # 创建测试数据
    test_data = [
        {
            "text": "这是一段非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的文本。",
            "start": 0.0,
            "end": 5.0
        },
        {
            "text": "短文本",
            "start": 5.0,
            "end": 6.0
        },
        {
            "text": "没有逗号顿号的文本内容",
            "start": 6.0,
            "end": 8.0
        }
    ]

    # 写入测试文件
    with open(r"tests\results\edge_case_test_input.json", 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)


def test_edge_cases():
    """测试边界情况"""
    # 创建测试文件
    create_test_file()

    # 输入文件路径
    input_file = r"tests\results\edge_case_test_input.json"

    # 输出文件路径
    output_file = r"tests\results\edge_case_test_output.json"

    # 视频参数
    video_width = 358
    video_height = 512
    font_size = 16

    print("边界情况测试")
    print("=" * 50)
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")

    # 调用处理函数
    split_subtitle_with_width_control(
        input_json_file=input_file,
        output_json_file=output_file,
        video_width=video_width,
        video_height=video_height,
        font_size=font_size
    )

    # 读取并显示结果
    with open(output_file, 'r', encoding='utf-8') as f:
        result = json.load(f)

    print("\n处理结果:")
    print("-" * 50)
    for i, segment in enumerate(result):
        text = segment.get('text', '')
        start = segment.get('start', 0)
        end = segment.get('end', 0)
        duration = end - start
        print(f"{i+1}. {text} ({start:.3f}s - {end:.3f}s, 持续时间: {duration:.3f}s)")

    print(f"\n处理完成!")
    print(f"- 输入段数: 3")
    print(f"- 输出段数: {len(result)}")


if __name__ == "__main__":
    test_edge_cases()
