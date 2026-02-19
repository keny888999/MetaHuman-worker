import re
import unicodedata


def get_char_width_advanced(char):
    """更精确的字符宽度计算"""
    # 全角字符（中文、日文、韩文、全角符号等）
    if unicodedata.east_asian_width(char) in ('F', 'W'):
        return 2
    # 半角字符
    else:
        return 1


def is_english_word_char(char):
    """判断字符是否为英文单词的一部分（包括字母、连字符和撇号）"""
    return char.isascii() and (char.isalpha() or char in "-'")


def extract_english_word(text, start_pos):
    """从指定位置提取完整的英文单词（包括连字符和撇号）"""
    word = ""
    i = start_pos

    # 提取连续的英文单词字符（包括连字符和撇号）
    while i < len(text) and is_english_word_char(text[i]):
        word += text[i]
        i += 1

    return word, i


def smart_text_wrap_advanced(text, max_width):
    """智能文本换行，正确处理带连字符和撇号的英文单词"""
    import re

    # 使用正则表达式分割文本，保留英文单词（包括连字符和撇号）的完整性
    # 这个正则表达式匹配：
    # 1. 英文单词（可以包含连字符和撇号）
    # 2. 连续的空格
    # 3. 单个非英文非空格字符（如中文）
    tokens = re.findall(r"[a-zA-Z][a-zA-Z'-]*| +|[^a-zA-Z\s]", text)

    lines = []
    current_line = ""
    current_width = 0

    for token in tokens:
        token_width = sum(get_char_width_advanced(c) for c in token)

        # 如果是空格，特殊处理
        if token.isspace():
            # 如果当前行不为空且可以容纳一个空格，添加空格
            if current_line and current_width + 1 <= max_width:
                current_line += " "
                current_width += 1
            # 否则忽略这个空格（特别是行首空格）
            continue

        # 处理其他token
        if current_width + token_width <= max_width:
            current_line += token
            current_width += token_width
        else:
            # 当前行已满，开始新行
            if current_line:
                lines.append(current_line)

            # 如果token本身太长，需要分割
            if token_width > max_width:
                # 对长token进行分割，但尽量避免在连字符或撇号前分割
                if '-' in token:
                    # 尝试在连字符处分割
                    parts = token.split('-')
                    temp_line = ""
                    temp_width = 0

                    for part in parts:
                        part_width = sum(get_char_width_advanced(c) for c in part)
                        hyphen_width = 1  # 连字符宽度

                        # 如果当前部分可以放入临时行
                        if temp_width + part_width + (1 if temp_line else 0) <= max_width:
                            if temp_line:
                                temp_line += '-' + part
                                temp_width += hyphen_width + part_width
                            else:
                                temp_line = part
                                temp_width = part_width
                        else:
                            # 临时行已满，添加到结果
                            if temp_line:
                                lines.append(temp_line)
                            temp_line = part
                            temp_width = part_width

                    # 处理最后一个部分
                    if temp_line:
                        current_line = temp_line
                        current_width = temp_width
                else:
                    # 没有连字符，按字符分割
                    part = ""
                    part_width = 0
                    for char in token:
                        char_width = get_char_width_advanced(char)
                        if part_width + char_width <= max_width:
                            part += char
                            part_width += char_width
                        else:
                            if part:
                                lines.append(part)
                            part = char
                            part_width = char_width

                    current_line = part
                    current_width = part_width
            else:
                current_line = token
                current_width = token_width

    # 添加最后一行
    if current_line:
        lines.append(current_line)

    return lines


if __name__ == "__main__":
    # 测试优化后的函数
    test_texts = [
        "This is a test with words like your's, don't, and well-known.",
        "混合文本 Mixed text with 中文和 English words like state-of-the-art.",
        "Hello world, this is a verylongwordthatneedstobesplit but with-hyphens.",
        "A sentence with multiple-hyphenated-words and regular words.",
        "안녕하세요. 이것은 한국어 테스트 문장입니다. Hello world!",
    ]

    max_width = 30

    for text in test_texts:
        print(f"原文: {text}")
        print("分割结果:")
        lines = smart_text_wrap_advanced(text, max_width)
        for i, line in enumerate(lines, 1):
            width = sum(get_char_width_advanced(c) for c in line)
            print(f"  {i}: '{line}' (宽度: {width})")
        print("-" * 50)
