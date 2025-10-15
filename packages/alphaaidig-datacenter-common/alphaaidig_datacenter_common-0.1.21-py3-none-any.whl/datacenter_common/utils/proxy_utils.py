import os
import json
import time
import threading
import requests  # 添加缺少的requests导入
from pathlib import Path

authKey = os.getenv('QG_AUTH_KEY')
password = os.getenv('QG_AUTH_PASSWORD')

# 创建线程锁确保单例访问
proxy_lock = threading.Lock()

def get_proxy():
    proxyAddr = get_proxy_addr()
    # 账密模式
    proxyUrl = "http://%(user)s:%(password)s@%(server)s" % {
        "user": authKey,
        "password": password,
        "server": proxyAddr,
    }
    proxies = {
        "http": proxyUrl,
        "https": proxyUrl,
    }
    return proxies

def get_proxy_addr():
    with proxy_lock:
        # 构建缓存文件路径
        project_root = Path(__file__).parent.parent.parent
        cache_path = os.path.join(project_root, 'src', 'resource', 'dynamic_ip.json')
        current_time = time.time()
        cached_data = None

        # 尝试读取缓存
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                    # 检查缓存是否过期
                    if current_time < cached_data.get('expire_time', 0):
                        return cached_data['ip'].strip()
            except (json.JSONDecodeError, KeyError):
                # 缓存文件格式错误或数据不完整，视为无效
                pass

        # 缓存无效或不存在，重新获取代理IP
        url = f"https://share.proxy.qg.net/get?key={authKey}&num=1&area=&isp=0&format=txt&seq=\r\n&distinct=true"
        r = requests.get(url)
        ip = r.text.strip()

        # 确保data目录存在
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        # 写入缓存
        with open(cache_path, 'w') as f:
            json.dump({
                'ip': ip,
                'generate_time': current_time,
                'expire_time': current_time + 55  # 55秒后过期
            }, f)

        return ip