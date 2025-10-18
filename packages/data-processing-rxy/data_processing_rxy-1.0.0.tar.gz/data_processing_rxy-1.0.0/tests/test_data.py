# tests/test_data.py
from data_processing import (
    normalize, moving_average,
    TextCleaner, variance, DataAnalyzer
)

def test_normalize():
    assert normalize([1, 2, 3]) == [0.0, 0.5, 1.0]

def test_text_cleaner():
    cleaner = TextCleaner()
    assert cleaner.clean("Hello, World! This is a TEST.") == "hello world this a test"

def test_data_analyzer():
    analyzer = DataAnalyzer([1, 2, 3, 4, 5])
    assert analyzer.mean() == 3.0