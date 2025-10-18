# data_processing/stats.py
import numpy as np  # 演示依赖外部库

def variance(data):
    """计算方差"""
    if len(data) < 2:
        raise ValueError("至少需要2个数据点")
    mean = sum(data) / len(data)
    return sum((x - mean)**2 for x in data) / (len(data) - 1)

class DataAnalyzer:
    """数据分析仪，基于numpy实现更复杂的统计"""
    def __init__(self, data):
        self.data = np.array(data)  # 转换为numpy数组

    def mean(self):
        """计算均值"""
        return self.data.mean()

    def median(self):
        """计算中位数"""
        return np.median(self.data)

    def correlation(self, other_data):
        """计算与另一个数据集的相关性"""
        return np.corrcoef(self.data, np.array(other_data))[0, 1]