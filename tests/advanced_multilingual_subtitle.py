#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级多语言字幕换行处理模块
支持中、英、日、韩等多种语言的智能换行

功能：
1. 根据视频分辨率和字体大小自动计算每行最大视觉宽度
2. 支持中、英、日、韩等多语言文本的智能换行
3. 提供基于视觉宽度和显示时间的字幕行分割功能
"""

import pysubs2
import re
import unicodedata
import json
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class LanguageType(Enum):
    """语言类型枚举"""
    CHINESE = "chinese"
    ENGLISH = "english"
    JAPANESE = "japanese"
    KOREAN = "korean"
    OTHER = "other"


@dataclass
class CharacterInfo:
    """字符信息"""
    char: str
    width: float
    language: LanguageType
    is_punctuation: bool
    is_break_punctuation: bool
    is_space: bool


@dataclass
class SubtitleSegment:
    """字幕片段信息"""
    text: str
    start: float
    end: float


class AdvancedMultilingualSubtitleProcessor:
    """高级多语言字幕处理器"""

    def __init__(self, video_width: int, video_height: int, font_size: Optional[int] = None):
        self.video_width = video_width
        self.video_height = video_height
        self.font_size = font_size or max(12, video_width // 40)

        # 计算每行最大视觉宽度
        self.max_visual_width = self._calculate_max_visual_width()

        # 语言识别阈值
        self.language_thresholds = {
            LanguageType.CHINESE: 0.3,   # 中文字符占比阈值
            LanguageType.ENGLISH: 0.3,   # 英文字符占比阈值
            LanguageType.JAPANESE: 0.2,  # 日文字符占比阈值
            LanguageType.KOREAN: 0.2,    # 韩文字符占比阈值
        }

        # 最小显示时间（秒）
        self.min_display_time = 0.5

    def _calculate_max_visual_width(self) -> float:
        """计算每行最大视觉宽度"""
        # 基于视频宽度和字体大小的经验公式
        ref_width = 358
        ref_font_size = 16
        ref_max_char_zh = 18
        ref_visual_width = ref_max_char_zh * 1.8  # 假设参考是:1中文字符宽度约等于2个英文

        scale_factor = (self.video_width / ref_width) * (ref_font_size / self.font_size)
        return ref_visual_width * scale_factor

    def process_subtitle_file(self, input_file: str, output_file: str):
        """处理字幕文件"""
        subs = pysubs2.load(input_file)

        for line in subs:
            if line.text.strip():
                wrapped_text = self.process_line(line.text)
                line.text = wrapped_text

        # 更新样式
        self._update_styles(subs)

        subs.save(output_file)
        print(f"处理完成: 视频分辨率{self.video_width}x{self.video_height}, "
              f"字体大小{self.font_size}px, 最大视觉宽度{self.max_visual_width:.2f}")

    def process_line(self, text: str) -> str:
        """处理单行文本"""
        # 移除现有的换行符
        clean_text = text.replace('\\N', ' ')

        # 如果是带标签的文本
        if '{' in clean_text:
            return self._process_text_with_tags(clean_text)
        else:
            return self._process_plain_text(clean_text)

    def _process_plain_text(self, text: str) -> str:
        """处理纯文本"""
        if not text.strip():
            return text

        # 分析文本中的字符
        char_infos = self._analyze_text(text)

        # 检测主要语言
        primary_language = self._detect_primary_language(char_infos)

        # 根据主要语言选择换行策略
        if primary_language == LanguageType.CHINESE:
            return self._wrap_chinese_text(char_infos)
        elif primary_language == LanguageType.ENGLISH:
            return self._wrap_english_text(char_infos)
        else:
            return self._wrap_mixed_text(char_infos)

    def _process_text_with_tags(self, text: str) -> str:
        """处理带ASS标签的文本"""
        # 提取纯文本内容
        clean_text = re.sub(r'\{[^}]*\}', '', text)

        # 处理纯文本
        processed_clean_text = self._process_plain_text(clean_text)

        # 保留标签信息的简化处理
        # 在实际应用中，可能需要更复杂的标签保留逻辑
        if '{' in text:
            # 如果原文本包含标签，简单地返回处理后的纯文本
            # 更复杂的实现需要将标签重新插入到正确位置
            return processed_clean_text
        return processed_clean_text

    def _analyze_text(self, text: str) -> List[CharacterInfo]:
        """分析文本中的字符"""
        char_infos = []

        for char in text:
            width = self._get_char_visual_width(char)
            language = self._detect_char_language(char)
            is_punctuation = self._is_breakable_punctuation(char)
            is_break_punctuation = self._is_breakable_punctuation(char)
            is_space = char.isspace()

            char_infos.append(CharacterInfo(
                char=char,
                width=width,
                language=language,
                is_punctuation=is_punctuation,
                is_break_punctuation=is_break_punctuation,
                is_space=is_space
            ))

        return char_infos

    def _detect_char_language(self, char: str) -> LanguageType:
        """检测单个字符的语言"""
        # 中文字符
        if '\u4e00' <= char <= '\u9fff':
            return LanguageType.CHINESE

        # 日文平假名
        if '\u3040' <= char <= '\u309f':
            return LanguageType.JAPANESE

        # 日文片假名
        if '\u30a0' <= char <= '\u30ff':
            return LanguageType.JAPANESE

        # 韩文
        if '\uac00' <= char <= '\ud7af':
            return LanguageType.KOREAN

        # 英文字母
        if char.isascii() and char.isalpha():
            return LanguageType.ENGLISH

        return LanguageType.OTHER

    def _detect_primary_language(self, char_infos: List[CharacterInfo]) -> LanguageType:
        """检测文本的主要语言"""
        if not char_infos:
            return LanguageType.OTHER

        # 统计各种语言字符的数量
        language_counts = {
            LanguageType.CHINESE: 0,
            LanguageType.ENGLISH: 0,
            LanguageType.JAPANESE: 0,
            LanguageType.KOREAN: 0,
            LanguageType.OTHER: 0
        }

        total_chars = 0
        for info in char_infos:
            # 只统计非空格、非标点的字符
            if not info.is_space and not info.is_punctuation:
                language_counts[info.language] += 1
                total_chars += 1

        if total_chars == 0:
            return LanguageType.OTHER

        # 计算各语言占比
        language_ratios = {
            lang: count / total_chars
            for lang, count in language_counts.items()
        }

        # 根据阈值判断主要语言
        for lang, threshold in self.language_thresholds.items():
            if language_ratios.get(lang, 0) >= threshold:
                return lang

        # 默认返回英文
        return LanguageType.ENGLISH

    def _get_char_visual_width(self, char: str) -> float:
        """获取字符的视觉宽度"""
        # 确保只传递单个字符给 unicodedata.category
        if len(char) != 1:
            return 1.5  # 默认宽度

        # 控制字符宽度为0
        if unicodedata.category(char).startswith('C'):
            return 0.0

        # 空格
        if char.isspace():
            return 1.0

        # 英文字母和数字
        if char.isascii() and (char.isalpha() or char.isdigit()):
            return 1.0

        # 英文标点符号
        if char in ".,!?;:-":
            return 0.5

        # 中日韩字符通常是方块字符
        if ('\u4e00' <= char <= '\u9fff' or  # 中文
            '\u3040' <= char <= '\u309f' or  # 日文平假名
            '\u30a0' <= char <= '\u30ff' or  # 日文片假名
                '\uac00' <= char <= '\ud7af'):   # 韩文
            return 2.0

        # 拉丁文扩展字符
        if '\u0100' <= char <= '\u017f':  # 拉丁文扩展-A
            return 1.0

        # 其他Unicode字符默认宽度
        return 1.5

    def is_punctuation(self, char: str):
        """判断字符是否是可以换行的标点符号"""
        # 英文标点
        english_punctuation = ".,!?;:-"

        # 中文标点
        chinese_punctuation = "，。！？；：、"

        # 其他语言标点
        other_punctuation = "{}[]~'\"`#$%^&*|"

        all_punctuation = english_punctuation + chinese_punctuation + other_punctuation

        return char in all_punctuation

    def _is_breakable_punctuation(self, char: str) -> bool:
        """判断字符是否是可以换行的标点符号"""
        # 英文标点
        english_punctuation = ".,!?;:-"

        # 中文标点
        chinese_punctuation = "，。！？；：、"

        # 其他语言标点
        other_punctuation = ""

        all_punctuation = english_punctuation + chinese_punctuation + other_punctuation

        return char in all_punctuation

    def _wrap_chinese_text(self, char_infos: List[CharacterInfo]) -> str:
        """处理中文文本换行"""
        return self._wrap_text_by_visual_width(char_infos, prefer_punctuation=True)

    def _wrap_english_text(self, char_infos: List[CharacterInfo]) -> str:
        """处理英文文本换行"""
        # 英文按单词换行
        return self._wrap_text_by_words(char_infos)

    def _wrap_mixed_text(self, char_infos: List[CharacterInfo]) -> str:
        """处理混合语言文本换行"""
        return self._wrap_text_by_visual_width(char_infos, prefer_punctuation=True)

    def _wrap_text_by_visual_width(self, char_infos: List[CharacterInfo], prefer_punctuation: bool = True) -> str:
        """根据视觉宽度换行"""
        # 计算总宽度
        total_width = sum(info.width for info in char_infos)

        # 如果总宽度没有超过最大视觉宽度，直接返回原文本
        if total_width <= self.max_visual_width:
            return ''.join(info.char for info in char_infos)

        lines = []
        current_line = []
        current_width = 0.0

        for i, info in enumerate(char_infos):
            # 如果加上这个字符会超出宽度限制且当前行不为空
            if current_width + info.width > self.max_visual_width and current_line:
                # 查找最佳换行点
                break_point = self._find_best_break_point(current_line, prefer_punctuation)

                if break_point > 0 and break_point < len(current_line):
                    # 在最佳断点处分割
                    line_chars = current_line[:break_point]
                    remaining_chars = current_line[break_point:]

                    lines.append(''.join(c.char for c in line_chars))

                    current_line = remaining_chars + [info]
                    current_width = sum(c.width for c in remaining_chars) + info.width
                else:
                    # 没有找到合适的断点，或者断点不合适，强制换行
                    lines.append(''.join(c.char for c in current_line))
                    current_line = [info]
                    current_width = info.width
            else:
                current_line.append(info)
                current_width += info.width

        # 添加最后一行
        if current_line:
            lines.append(''.join(c.char for c in current_line))

        return '\\N'.join(lines)

    def _wrap_text_by_words(self, char_infos: List[CharacterInfo]) -> str:
        """按单词换行（适用于英文等以空格分隔的语言）"""
        lines = []
        current_line = []
        current_width = 0.0

        i = 0
        while i < len(char_infos):
            # 收集一个完整的单词
            word_chars = []
            word_width = 0.0

            # 记录单词开始位置
            k = i

            # 收集字符直到遇到空格或标点
            while k < len(char_infos):
                info = char_infos[k]
                word_chars.append(info)
                word_width += info.width
                k += 1

                if info.is_space:
                    break

            i = k

            # 如果加上这个单词会超出宽度限制
            if current_width + word_width > self.max_visual_width and current_line:
                # 换行
                lines.append(''.join(c.char for c in current_line))
                current_line = word_chars
                current_width = word_width
            else:
                current_line.extend(word_chars)
                current_width += word_width

        # 添加最后一行
        if current_line:
            lines.append(''.join(c.char for c in current_line))

        return '\\N'.join(lines)

    def _find_best_break_point(self, char_infos: List[CharacterInfo], prefer_punctuation: bool = True) -> int:
        """查找最佳换行点"""
        # 优先在标点符号处分割
        if prefer_punctuation:
            for i in range(len(char_infos) - 1, 0, -1):
                if char_infos[i].is_break_punctuation:
                    return i + 1  # 在标点符号后分割

        # 其次在空格处分割
        for i in range(len(char_infos) - 1, 0, -1):
            if char_infos[i].is_space:
                return i + 1  # 在空格后分割

        # 最后在字符宽度限制处分割
        current_width = 0.0
        for i, info in enumerate(char_infos):
            if current_width + info.width > self.max_visual_width:  # 留一些余量
                return max(1, i)  # 至少保留一个字符
            current_width += info.width

        return len(char_infos)  # 如果没找到合适的点，就在末尾分割

    def _update_styles(self, subs: pysubs2.SSAFile):
        """更新ASS样式以适应视频分辨率"""
        for style_name in subs.styles:
            style = subs.styles[style_name]
            # 更新字体大小
            style.fontsize = self.font_size
            # 根据视频分辨率调整边距
            style.marginl = max(20, self.video_width // 40)
            style.marginr = max(20, self.video_width // 40)
            style.marginv = max(10, self.video_height // 20)

    def _merge_segments_for_min_time(self, segments: List[str], start: float, end: float) -> List[Dict[str, Any]]:
        """合并片段以确保最小显示时间"""
        total_duration = end - start
        min_segments = int(total_duration / self.min_display_time)

        if min_segments <= 1:
            # 时间太短，无法分割，返回整段
            return [{"text": "".join(segments), "start": start, "end": end}]

        if len(segments) <= min_segments:
            # 片段数少于或等于可分割数，直接分配时间
            avg_duration = total_duration / len(segments)
            result = []
            for i, segment in enumerate(segments):
                seg_start = start + i * avg_duration
                seg_end = seg_start + avg_duration
                result.append({"text": segment, "start": seg_start, "end": seg_end})
            return result

        # 片段数多于可分割数，需要合并
        # 简单的合并策略：尽可能均匀分配
        avg_segments_per_group = len(segments) / min_segments
        result = []

        for i in range(min_segments):
            start_idx = int(i * avg_segments_per_group)
            end_idx = int((i + 1) * avg_segments_per_group)
            if i == min_segments - 1:  # 最后一组包含所有剩余片段
                end_idx = len(segments)

            group_segments = segments[start_idx:end_idx]
            group_text = "".join(group_segments)
            seg_start = start + (i * total_duration / min_segments)
            seg_end = start + ((i + 1) * total_duration / min_segments)

            result.append({"text": group_text, "start": seg_start, "end": seg_end})

        return result

    def split_subtitle_if_exceeds_width(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        判断某一行字幕是否超出屏幕宽度，以是否有逗号或顿号作为判断前提。
        如果该行有逗号或顿号，开始判断是否超出屏幕宽度，如果超出，则把该行分割成2个或多个独立行。
        在分割时考虑分割后的子句是否有足够的显示时间，避免在屏幕上一闪而过，影响观感。

        Args:
            segments: 字幕片段列表，每个片段包含text、start、end字段

        Returns:
            处理后的字幕片段列表
        """
        result_segments = []

        for segment in segments:
            text = segment["text"]
            start = segment["start"]
            end = segment["end"]

            # 检查是否包含逗号或顿号
            if "，" in text or "、" in text:
                # 判断是否超出屏幕宽度
                if self._is_text_exceed_width(text):
                    # 分割字幕
                    sub_segments = self._split_text_by_comma(text)

                    # 计算每个子片段的时间分配
                    total_duration = end - start
                    avg_duration = total_duration / len(sub_segments)

                    # 确保每个片段至少有最小显示时间
                    if avg_duration >= self.min_display_time:
                        # 时间充足，按平均分配
                        for i, sub_text in enumerate(sub_segments):
                            sub_start = start + i * avg_duration
                            sub_end = sub_start + avg_duration
                            result_segments.append({
                                "text": sub_text,
                                "start": sub_start,
                                "end": sub_end
                            })
                    else:
                        # 时间不足，合并片段以确保最小显示时间
                        result_segments.extend(self._merge_segments_for_min_time(
                            sub_segments, start, end))
                else:
                    # 未超出宽度，直接添加
                    result_segments.append(segment)
            else:
                # 不包含逗号或顿号，直接添加
                result_segments.append(segment)

        return result_segments

    def _is_text_exceed_width(self, text: str) -> bool:
        """判断文本是否超出最大视觉宽度"""
        char_infos = self._analyze_text(text)
        total_width = sum(info.width for info in char_infos)
        return total_width > self.max_visual_width

    def _split_text_by_comma(self, text: str) -> List[str]:
        """
        根据逗号或顿号分割文本

        Args:
            text: 要分割的文本

        Returns:
            分割后的文本片段列表
        """
        # 使用正则表达式分割，保留分隔符
        parts = re.split(r'([，、])', text)

        # 合并分割后的部分，确保标点符号与前面的文本在一起
        segments = []
        current_segment = ""

        for part in parts:
            if part in ["，", "、"]:
                current_segment += part
                segments.append(current_segment)
                current_segment = ""
            else:
                current_segment += part

        # 添加最后一段（如果没有以标点符号结尾）
        if current_segment:
            segments.append(current_segment)

        # 清理每段文本（去除首尾空格）
        segments = [seg.strip() for seg in segments if seg.strip()]

        return segments

# 简化版接口函数


def process_multilingual_subtitle(input_file: str, output_file: str,
                                  video_width: int, video_height: int,
                                  font_size: Optional[int] = None):
    """
    处理多语言字幕文件

    Args:
        input_file: 输入ASS文件路径
        output_file: 输出ASS文件路径
        video_width: 视频宽度
        video_height: 视频高度
        font_size: 字体大小(可选)
    """
    processor = AdvancedMultilingualSubtitleProcessor(video_width, video_height, font_size)
    processor.process_subtitle_file(input_file, output_file)


def split_subtitle_json_by_comma(input_json_file: str, output_json_file: str,
                                 video_width: int, video_height: int,
                                 font_size: Optional[int] = None):
    """
    处理JSON格式的字幕文件，根据逗号或顿号分割字幕行，并考虑显示时间

    Args:
        input_json_file: 输入JSON文件路径
        output_json_file: 输出JSON文件路径
        video_width: 视频宽度
        video_height: 视频高度
        font_size: 字体大小(可选)
    """
    # 读取输入JSON文件
    with open(input_json_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)

    # 处理字幕
    processor = AdvancedMultilingualSubtitleProcessor(video_width, video_height, font_size)
    processed_segments = processor.split_subtitle_by_comma_with_timing(segments)

    # 写入输出JSON文件
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(processed_segments, f, ensure_ascii=False, indent=2)

    print(f"处理完成: 输入文件{input_json_file}, 输出文件{output_json_file}")


def split_subtitle_if_exceeds_width_json(input_json_file: str, output_json_file: str,
                                         video_width: int, video_height: int,
                                         font_size: Optional[int] = None):
    """
    处理JSON格式的字幕文件，判断某一行字幕是否超出屏幕宽度，
    以是否有逗号或顿号作为判断前提。如果该行有逗号或顿号，开始判断是否超出屏幕宽度，
    如果超出，则把该行分割成2个或多个独立行。在分割时考虑分割后的子句是否有足够的显示时间。

    Args:
        input_json_file: 输入JSON文件路径
        output_json_file: 输出JSON文件路径
        video_width: 视频宽度
        video_height: 视频高度
        font_size: 字体大小(可选)
    """
    # 读取输入JSON文件
    with open(input_json_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)

    # 处理字幕
    processor = AdvancedMultilingualSubtitleProcessor(video_width, video_height, font_size)
    processed_segments = processor.split_subtitle_if_exceeds_width(segments)

    # 写入输出JSON文件
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(processed_segments, f, ensure_ascii=False, indent=2)

    print(f"处理完成: 输入文件{input_json_file}, 输出文件{output_json_file}")


# 使用示例
if __name__ == "__main__":
    video_width = 358
    video_height = 512

    # 处理ASS字幕文件
    processor = AdvancedMultilingualSubtitleProcessor(video_width=video_width, video_height=video_height, font_size=16)
    processor.process_subtitle_file('subtitle.ass', "./output.ass")

    # 处理JSON字幕文件
    split_subtitle_json_by_comma(
        'sentences_output.json',
        './sentences_output_split.json',
        video_width=video_width,
        video_height=video_height,
        font_size=16
    )

    # 新增功能：处理JSON字幕文件，仅在有逗号或顿号且超出宽度时进行分割
    split_subtitle_if_exceeds_width_json(
        'sentences_output.json',
        './sentences_output_split_if_exceeds.json',
        video_width=video_width,
        video_height=video_height,
        font_size=16
    )
