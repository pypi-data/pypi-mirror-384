import hashlib
import time
import random
import string
import os

from pathlib import Path

def generate_md5_token(seed: str = None) -> str:
    """生成MD5格式的token
    Args:
        seed: 可选的种子字符串，若未提供则使用当前时间戳和随机字符串
    Returns:
        MD5哈希值的十六进制表示
    """
    # 如果未提供种子，则生成包含时间戳和随机字符串的混合种子
    if not seed:
        timestamp = str(time.time())
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        seed = timestamp + random_str
    
    # 创建MD5哈希对象并更新种子
    md5_hash = hashlib.md5()
    md5_hash.update(seed.encode('utf-8'))
    
    # 返回十六进制表示的哈希值
    return md5_hash.hexdigest()

# 新增方法：验证token是否在.env的AUTH_TOKEN中
def authenticate_token(input_token: str) -> bool:
    """验证输入token是否在环境变量AUTH_TOKEN中
    Args:
        input_token: 待验证的token字符串
    Returns:
        如果token存在于AUTH_TOKEN中，返回True；否则返回False
    """
    # 获取环境变量中的AUTH_TOKEN
    auth_tokens = os.getenv('AUTH_TOKEN', '')
    
    # 检查输入token是否在AUTH_TOKEN中
    return input_token in auth_tokens.split(',')

if __name__ == "__main__":
    # 示例用法
    token = generate_md5_token()
    print(f"生成的MD5 token: {token}")
    
    # 使用自定义种子的示例
    custom_token = generate_md5_token(seed="my_custom_seed_123")
    print(f"使用自定义种子生成的MD5 token: {custom_token}")

    # For testing, ensure .env is loaded by the execution environment
    success = authenticate_token("xxxxxx")
    print(f"Authentication result for 'xxxxxx': {success}")