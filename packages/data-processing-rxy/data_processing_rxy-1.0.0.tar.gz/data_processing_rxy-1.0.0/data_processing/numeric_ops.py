# data_processing/numeric_ops.py
def normalize(data, min_val=None, max_val=None):
    """归一化数据到 [0,1] 范围"""
    if not data:
        raise ValueError("输入数据不能为空")
    min_val = min(data) if min_val is None else min_val
    max_val = max(data) if max_val is None else max_val
    if max_val == min_val:
        return [0.0 for _ in data]
    return [(x - min_val) / (max_val - min_val) for x in data]

def moving_average(data, window=3):
    """计算滑动平均值"""
    if len(data) < window:
        raise ValueError("数据长度小于窗口大小")
    return [sum(data[i:i+window])/window for i in range(len(data)-window+1)]