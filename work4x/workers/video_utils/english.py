import re
from typing import Optional, Tuple


class EnglishWordValidator:
    """
    混合验证器，结合多种方法
    """

    def __init__(self):
        # 预编译正则表达式
        self.english_char_pattern = re.compile(r'^[a-zA-Z\'-]+$')

        # 常见非英文单词的英文样字符串
        self.false_positives = {
            'a', 'i',  # 单独的字母（也可能是英文单词）
            'id', 'ad', 'am', 'an', 'as', 'at', 'be', 'by', 'do', 'go',
            'he', 'hi', 'if', 'in', 'is', 'it', 'me', 'my', 'no', 'of',
            'oh', 'on', 'or', 'so', 'to', 'up', 'us', 'we'
        }

        # 常见英文缩写
        self.common_abbreviations = {
            'mr', 'mrs', 'ms', 'dr', 'st', 'ave', 'blvd', 'rd',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug',
            'sep', 'oct', 'nov', 'dec', 'mon', 'tue', 'wed', 'thu',
            'fri', 'sat', 'sun'
        }

        # 加载多个词典源
        self.dictionaries = self._load_dictionaries()

    def _load_dictionaries(self):
        """加载多个词典源"""
        dictionaries = []

        # 尝试加载enchant
        try:
            import enchant
            dictionaries.append(('enchant', enchant.Dict("en_US")))
        except:
            pass

        # 尝试加载NLTK
        try:
            from nltk.corpus import words
            dictionaries.append(('nltk', set(w.lower() for w in words.words())))
        except:
            pass

        return dictionaries

    def is_english_word(self, text: str, strict: bool = False) -> Tuple[bool, Optional[str]]:
        """
        判断是否为英文单词

        Args:
            text: 要检查的文本
            strict: 严格模式，对单个字母更严格

        Returns:
            (是否是英文单词, 错误信息/None)
        """
        if not text:
            return False, "空字符串"

        # 1. 基本字符检查
        if not self.english_char_pattern.match(text):
            return False, "包含非英文字符"

        # 2. 长度检查
        if len(text) == 1:
            # 单个字符
            if text.lower() in ['a', 'i']:
                return True, None  # 'a'和'I'是有效的英文单词
            elif strict:
                return False, "单个字母（非'a'或'I'）"
            else:
                # 非严格模式下，单个字母视为可能的缩写
                return True, None

        # 3. 检查常见缩写
        text_lower = text.lower()
        if text_lower in self.common_abbreviations:
            return True, None

        # 4. 使用词典检查
        for dict_name, dictionary in self.dictionaries:
            if dict_name == 'enchant':
                if dictionary.check(text):
                    return True, None
            else:
                if text_lower in dictionary:
                    return True, None

        # 5. 检查缩略形式
        if "'" in text_lower:
            # 处理所有格
            if text_lower.endswith("'s"):
                base = text_lower[:-2]
                for dict_name, dictionary in self.dictionaries:
                    if dict_name == 'enchant':
                        if dictionary.check(base):
                            return True, None
                    elif base in dictionary:
                        return True, None

            # 处理否定缩略
            if text_lower.endswith("n't"):
                base = text_lower[:-3]
                for dict_name, dictionary in self.dictionaries:
                    if dict_name == 'enchant':
                        if dictionary.check(base):
                            return True, None
                    elif base in dictionary:
                        return True, None

        # 6. 词形变化检查（简化的）
        # 这里可以添加复数、时态等检查

        return False, "未在词典中找到"

    def analyze_text(self, text: str) -> dict:
        """
        分析文本，返回详细信息
        """
        is_english, reason = self.is_english_word(text)

        result = {
            "text": text,
            "is_english": is_english,
            "reason": reason if not is_english else None,
            "length": len(text),
            "has_apostrophe": "'" in text,
            "is_title_case": text.istitle(),
            "is_upper": text.isupper(),
            "is_lower": text.islower()
        }

        if is_english:
            # 如果是英文，添加更多信息
            result.update({
                "suggested_correction": None,  # 可以添加拼写建议
                "word_type": self._guess_word_type(text)
            })

        return result

    def _guess_word_type(self, text: str) -> str:
        """猜测单词类型"""
        if len(text) == 1:
            return "article/pronoun" if text.lower() in ['a', 'i'] else "letter"

        if "'" in text.lower():
            return "contraction"

        if text.lower() in self.common_abbreviations:
            return "abbreviation"

        return "regular_word"


if __name__ == "__main__":
    # 第一次需要下载NLTK词典
    # import nltk
    # nltk.download('words')
    # nltk.download('wordnet')

    validator = EnglishWordValidator()
    words_to_check = ["hello", "树", "don't", "it's", "they're", "a", "I", "running"]

    for word in words_to_check:
        is_english, reason = validator.is_english_word(word)
        status = "✓" if is_english else "✗"
        print(f"{status} '{word}' -> {'英文' if is_english else f'非英文 ({reason})'}")
