#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path
from typing import List, Tuple


def decode_filename(encoded_filename: str) -> str:
    """
    解码URL编码的文件名
    例如: _E3_81_95_E3_81_A8_E3_81_BF_EF_BC_88_E6_99_BA_E7_BE_8E_EF_BC_89.png
    解码为: さとみ（智美）.png
    """
    try:
        # 移除开头的下划线和文件扩展名
        name_part, ext = os.path.splitext(encoded_filename.replace("(1)", ""))
        if name_part.startswith('_'):
            name_part = name_part[1:]

        # 移除所有下划线，将十六进制字符串分组
        hex_string = name_part.replace('_', '')

        # 将十六进制字符串转换为字节
        try:
            # 每两个字符为一组，转换为字节
            byte_data = bytes.fromhex(hex_string)
            # 解码为UTF-8字符串
            decoded_name = byte_data.decode('utf-8')
            return decoded_name + ext
        except (ValueError, UnicodeDecodeError) as e:
            print(f"警告: 无法解码文件名 '{encoded_filename}': {e}")
            return encoded_filename

    except Exception as e:
        print(f"错误: 处理文件名 '{encoded_filename}' 时出错: {e}")
        return encoded_filename


def get_image_files(directory_path: str) -> List[str]:
    """
    获取目录下所有图像文件
    """
    image_extensions = {'.png'}
    image_files = []

    try:
        directory = Path(directory_path)
        if not directory.exists():
            print(f"错误: 目录 '{directory_path}' 不存在")
            return []

        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path.name)

        print(f"找到 {len(image_files)} 个图像文件")
        return image_files

    except Exception as e:
        print(f"错误: 读取目录 '{directory_path}' 时出错: {e}")
        return []


def create_rename_mapping(file_list: List[str]) -> List[Tuple[str, str]]:
    """
    创建原文件名到解码文件名的映射
    """
    rename_mapping = []

    for original_filename in file_list:
        decoded_filename = decode_filename(original_filename)

        # 只有当解码后的文件名与原文件名不同时才添加到映射中
        if decoded_filename != original_filename:
            rename_mapping.append((original_filename, decoded_filename))
            print(f"映射: '{original_filename}' -> '{decoded_filename}'")
        else:
            print(f"跳过: '{original_filename}' (无需重命名)")

    return rename_mapping


def batch_rename_files(directory_path: str, rename_mapping: List[Tuple[str, str]], dry_run: bool = True) -> None:
    """
    批量重命名文件

    Args:
        directory_path: 目录路径
        rename_mapping: 重命名映射列表
        dry_run: 是否为模拟运行（不实际重命名）
    """
    directory = Path(directory_path)
    success_count = 0
    error_count = 0

    print(f"\n{'=' * 50}")
    print(f"{'模拟运行' if dry_run else '实际执行'} - 批量重命名文件")
    print(f"{'=' * 50}")

    for original_name, new_name in rename_mapping:
        original_path = directory / original_name
        new_path = directory / "aaa" / new_name

        try:
            # 检查原文件是否存在
            if not original_path.exists():
                print(f"错误: 原文件不存在 - {original_name}")
                error_count += 1
                continue

            # 检查目标文件名是否已存在
            if new_path.exists():
                print(f"警告: 目标文件已存在，跳过重命名 - {new_name}")
                continue

            if not dry_run:
                # 实际重命名文件
                original_path.rename(new_path)
                print(f"✓ 重命名成功: {original_name} -> {new_name}")
            else:
                print(f"📋 模拟重命名: {original_name} -> {new_name}")

            success_count += 1

        except Exception as e:
            print(f"✗ 重命名失败: {original_name} -> {new_name} | 错误: {e}")
            error_count += 1

    print(f"\n{'=' * 50}")
    print(f"重命名完成统计:")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {error_count} 个文件")
    print(f"{'=' * 50}")


def main():
    """主函数"""
    # 目标目录
    target_directory = r"m:\下载\2510110039625"

    print("🚀 开始批量文件重命名程序")
    print(f"目标目录: {target_directory}")

    # 步骤1: 获取所有图像文件
    print("\n📁 步骤1: 获取目录下所有图像文件...")
    image_files = get_image_files(target_directory)

    if not image_files:
        print("❌ 未找到任何图像文件，程序结束")
        return

    # 显示前几个文件作为示例
    print("\n前5个文件示例:")
    for i, filename in enumerate(image_files[:5]):
        print(f"  {i+1}. {filename}")
    if len(image_files) > 5:
        print(f"  ... 还有 {len(image_files) - 5} 个文件")

    # 步骤2: 创建重命名映射
    print("\n🔄 步骤2: 解码文件名并创建重命名映射...")
    rename_mapping = create_rename_mapping(image_files)

    if not rename_mapping:
        print("❌ 没有需要重命名的文件，程序结束")
        return

    print(f"\n找到 {len(rename_mapping)} 个需要重命名的文件")

    # 步骤3: 模拟运行
    print("\n🔍 步骤3: 模拟运行...")
    batch_rename_files(target_directory, rename_mapping, dry_run=True)

    # 询问用户是否继续实际重命名
    print("\n" + "=" * 50)
    user_input = input("是否要执行实际的文件重命名？(输入 'yes' 确认): ").strip().lower()

    if user_input == 'yes':
        print("\n✅ 步骤4: 执行实际重命名...")
        batch_rename_files(target_directory, rename_mapping, dry_run=False)
        print("\n🎉 批量重命名完成！")
    else:
        print("\n❌ 用户取消操作，未执行实际重命名")


if __name__ == "__main__":
    main()
