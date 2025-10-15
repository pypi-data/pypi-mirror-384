# 转换金额单位的函数
import math

def convert_amount(amount):
    try:
        amount = float(amount)
        # 检查是否为NaN值
        if math.isnan(amount):
            return "-"
        if abs(amount) >= 1e8:
            converted = amount / 1e8
            unit = '亿'
        elif abs(amount) >= 1e4:
            converted = amount / 1e4
            unit = '万'
        else:
            converted = amount
            unit = '元'
        return f"{converted:.2f}{unit}"
    except ValueError:
        return amount