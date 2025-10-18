# data_processing/text_cleaner.py
import re

class TextCleaner:
    """文本清洗工具类，支持去除特殊字符、小写转换等"""
    def __init__(self):
        self.stopwords = {"the", "is", "in", "to", "and"}  # 停用词示例

    def remove_special_chars(self, text):
        """去除特殊字符，只保留字母、数字和空格"""
        return re.sub(r"[^\w\s]", "", text)

    def to_lower(self, text):
        """转换为小写"""
        return text.lower()

    def remove_stopwords(self, text):
        """去除停用词"""
        words = text.split()
        return " ".join([word for word in words if word not in self.stopwords])

    def clean(self, text):
        """一站式清洗：组合所有操作"""
        text = self.remove_special_chars(text)
        text = self.to_lower(text)
        text = self.remove_stopwords(text)
        return text