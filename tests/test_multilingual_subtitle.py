import pysubs2
import re
import unicodedata
from math import ceil
from typing import List, Tuple


def multilingual_smart_wrap_by_resolution(input_file, output_file, video_width, video_height, font_size=None):
    """
    根据视频分辨率智能换行（支持多语言）

    Args:
        input_file: 输入ASS文件路径
        output_file: 输出ASS文件路径
        video_width: 视频宽度
        video_height: 视频高度
        font_size: 字体大小(可选，自动计算如果未提供)
    """
    # 根据分辨率自动计算合适的参数
    if font_size is None:
        # 基于视频高度自动计算字体大小
        font_size = max(12, video_width // 40)

    ref_width = 358
    ref_height = 512
    ref_font_size = 16
    ref_chars_per_line = 14

    scale_width = video_width // ref_width

    # 计算每行最大字符数（经验公式）
    font_size = 16
    chars_per_line = int(14 * scale_width)  # calculate_chars_per_line(video_width, font_size)

    subs = pysubs2.load(input_file)

    for line in subs:
        if not line.text.strip():
            continue

        # 移除现有的\N（避免重复）
        clean_text = line.text.replace('\\N', ' ')

        # 提取文本内容（去除ASS标签）
        text_content = re.sub(r'\{[^}]*\}', '', clean_text)

        if len(text_content) > chars_per_line:
            # 多语言智能换行
            wrapped_text = multilingual_smart_wrap_text(clean_text, chars_per_line)
            line.text = wrapped_text

    # 更新样式中的字体大小
    update_styles(subs, font_size, video_width, video_height)

    subs.save(output_file)
    print(f"处理完成: 视频分辨率{video_width}x{video_height}, 字体大小{font_size}px, 每行{chars_per_line}字符")


def multilingual_smart_wrap_text(text, max_chars):
    """多语言智能文本换行"""
    # 如果已经有ASS标签，需要特殊处理
    if '{' in text:
        return multilingual_wrap_text_with_tags(text, max_chars)
    else:
        return multilingual_wrap_plain_text(text, max_chars)


def multilingual_wrap_plain_text(text, max_chars):
    """多语言普通文本换行"""
    if len(text) <= max_chars:
        return text

    # 使用多语言感知的换行算法
    lines = []
    current_line = ""
    current_width = 0

    # 估算每行的最大视觉宽度
    max_visual_width = max_chars * 0.8  # 调整因子，因为英文字符较窄

    i = 0
    while i < len(text):
        char = text[i]

        # 计算当前字符的视觉宽度
        char_width = get_char_visual_width(char)
        new_width = current_width + char_width

        # 检查是否应该在此处分割
        if should_break_at_char(char, current_line, new_width, max_visual_width):
            if current_line.strip():  # 避免添加空行
                lines.append(current_line.strip())
            current_line = char
            current_width = char_width
        else:
            current_line += char
            current_width = new_width

        i += 1

    if current_line.strip():
        lines.append(current_line.strip())

    return '\\N'.join(lines)


def multilingual_wrap_text_with_tags(text, max_chars):
    """处理带ASS标签的多语言文本换行"""
    # 简化的标签处理：提取纯文本部分进行换行分析
    clean_text = re.sub(r'\{[^}]*\}', '', text)

    if len(clean_text) <= max_chars:
        return text

    # 对纯文本进行换行分析
    clean_lines = multilingual_wrap_plain_text(clean_text, max_chars).split('\\N')

    # 重新构建带标签的文本
    result = reconstruct_text_with_tags(text, clean_lines)
    return result


def get_char_visual_width(char):
    """
    获取字符的视觉宽度（相对于英文字母）
    返回值: 1.0 表示标准英文字符宽度
    """
    # 控制字符宽度为0
    if unicodedata.category(char).startswith('C'):
        return 0.0

    # 获取字符的Unicode名称类别
    category = unicodedata.category(char)

    # 英文字母和数字
    if char.isascii() and (char.isalpha() or char.isdigit()):
        return 1.0

    # 英文标点符号
    if char in ",.!?;:-()[]{}":
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


def should_break_at_char(char, current_line, current_width, max_width):
    """
    判断是否应该在当前字符处分割行
    """
    # 如果当前行已经超出了最大宽度，则需要考虑换行
    if current_width > max_width:
        # 优先在空白字符处分割
        if char.isspace():
            return True

        # 其次在标点符号处分割（多语言支持）
        if is_breakable_punctuation(char):
            return True

        # 最后，在字符宽度限制处分割
        return True

    # 即使没超出宽度，如果遇到换行符也分割
    if char in '\n\r':
        return True

    return False


def is_breakable_punctuation(char):
    """
    判断字符是否是可以换行的标点符号（支持多语言）
    """
    # 英文标点
    english_punctuation = ".,!?;:-"

    # 中文标点
    chinese_punctuation = "，。！？；：、"

    # 其他语言标点
    other_punctuation = "()[]{}\"'`"

    all_punctuation = english_punctuation + chinese_punctuation + other_punctuation

    return char in all_punctuation


def reconstruct_text_with_tags(original_text, clean_lines):
    """
    重构带标签的文本
    这是一个简化的实现，实际应用中可能需要更复杂的逻辑
    """
    # 简单地在每行末尾添加换行符（保留原有的标签结构）
    return '\\N'.join(clean_lines)


def calculate_chars_per_line(video_width, font_size):
    """根据视频宽度和字体大小计算每行字符数"""
    # 经验公式：每行字符数 ≈ (视频宽度 * 0.8) / (字体大小 * 0.6)
    # 假设中文字符近似正方形，0.6是宽度系数，0.8是边距系数
    return max(8, min(40, int((video_width * 0.8) / (font_size * 0.6))))


def update_styles(subs, font_size, video_width, video_height):
    """更新ASS样式以适应视频分辨率"""
    for style_name in subs.styles:
        style = subs.styles[style_name]
        # 更新字体大小
        style.fontsize = font_size
        # 根据视频分辨率调整边距
        style.marginl = max(20, video_width // 40)
        style.marginr = max(20, video_width // 40)
        style.marginv = max(10, video_height // 20)


# 更高级的多语言换行实现
class MultilingualTextWrapper:
    """
    多语言文本换行器
    """

    def __init__(self, max_width: float = 100.0):
        self.max_width = max_width

    def wrap_text(self, text: str) -> List[str]:
        """
        对文本进行换行处理
        """
        if not text:
            return []

        # 分割成段落
        paragraphs = text.split('\n')
        result = []

        for paragraph in paragraphs:
            if paragraph.strip():
                wrapped_lines = self._wrap_paragraph(paragraph)
                result.extend(wrapped_lines)
            else:
                result.append("")  # 保留空行

        return result

    def _wrap_paragraph(self, paragraph: str) -> List[str]:
        """
        对单个段落进行换行处理
        """
        # 移除现有的换行符
        clean_text = paragraph.replace('\\N', ' ')

        words = self._split_into_words(clean_text)
        lines = []
        current_line = []
        current_width = 0.0

        for word, width in words:
            # 如果加上这个单词会超出宽度限制
            if current_width + width > self.max_width and current_line:
                # 将当前行加入结果
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = width
            else:
                current_line.append(word)
                current_width += width + 1.0  # 加上空格的宽度

        # 添加最后一行
        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _split_into_words(self, text: str) -> List[Tuple[str, float]]:
        """
        将文本分割成单词并计算每个单词的宽度
        """
        words = []
        current_word = ""
        current_width = 0.0

        for char in text:
            if char.isspace():
                if current_word:
                    words.append((current_word, current_width))
                    current_word = ""
                    current_width = 0.0
            else:
                current_word += char
                current_width += get_char_visual_width(char)

        # 添加最后一个单词
        if current_word:
            words.append((current_word, current_width))

        return words


# 使用示例
if __name__ == "__main__":
    # 示例: 多语言字幕处理
    if False:  # 设置为True以测试
        multilingual_smart_wrap_by_resolution(
            "subtitle.ass",
            "output_multilingual.ass",
            video_width=1280,
            video_height=808,
            font_size=20  # 可选，不指定则自动计算
        )
