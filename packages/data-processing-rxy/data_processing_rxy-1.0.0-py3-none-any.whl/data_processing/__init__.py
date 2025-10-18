# data_processing/__init__.py
# 从子模块导出常用功能
from .numeric_ops import normalize, moving_average
from .text_cleaner import TextCleaner
from .stats import variance, DataAnalyzer

# 定义包信息
__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "A data processing library with numeric, text, and stats tools"