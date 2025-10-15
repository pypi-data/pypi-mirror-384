from typing import Dict, Optional, Any, List
# 导入curl_cffi.requests
from curl_cffi import requests as curl_requests
from curl_cffi import BrowserTypeLiteral
import random

class BaiduFinanceUtils:
    """
    百度财经API工具类，用于生成请求头和发送请求
    """
    # 移除手动定义的USER_AGENTS列表

    # 从BrowserTypeLiteral中过滤出Chrome浏览器类型
    @staticmethod
    def get_chrome_browsers() -> List[str]:
        """
        从BrowserTypeLiteral中过滤出所有Chrome浏览器类型

        Returns:
            List[str]: Chrome浏览器类型列表
        """
        # 获取BrowserTypeLiteral的所有可能值
        all_browsers = BrowserTypeLiteral.__args__
        
        # 过滤出以'chrome'开头但不是'chrome_android'的类型
        chrome_browsers = [
            browser for browser in all_browsers 
            if browser.startswith('chrome') and not browser.endswith('android')
        ]
        
        return chrome_browsers

    @staticmethod
    def generate_headers(cookie: Optional[str] = None) -> Dict[str, str]:
        """
        生成百度财经API请求头

        Args:
            cookie: 可选的Cookie字符串

        Returns:
            Dict[str, str]: 请求头字典
        """
        # 移除手动选择User-Agent的代码

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
            # 移除手动设置的user-agent
        }

        # 如果提供了Cookie，则添加到请求头
        if cookie:
            headers["Cookie"] = cookie

        return headers

    @staticmethod
    def request_with_headers(base_url: str, params: Dict[str, Any], cookie: Optional[str] = None) -> curl_requests.Response:
        """
        使用生成的请求头发送请求

        Args:
            base_url: 请求的基础URL
            params: 请求参数
            cookie: 可选的Cookie字符串

        Returns:
            curl_requests.Response: 请求响应对象

        Raises:
            Exception: 当请求失败时抛出异常
        """
        # 生成请求头
        headers = BaiduFinanceUtils.generate_headers(cookie)

        try:
            # 从BrowserTypeLiteral中获取并随机选择一个Chrome浏览器类型
            chrome_browsers = BaiduFinanceUtils.get_chrome_browsers()
            if not chrome_browsers:
                raise Exception("未找到可用的Chrome浏览器类型")
            
            chrome_browser = random.choice(chrome_browsers)
            
            # 发送请求，curl_cffi会自动设置对应的User-Agent
            response = curl_requests.get(
                base_url,
                params=params,
                headers=headers,
                impersonate=chrome_browser,
                timeout=10
            )
            
            response.raise_for_status()  # 检查请求是否成功
            return response
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")

# 测试代码
if __name__ == '__main__':
    # 生成不带Cookie的请求头
    headers1 = BaiduFinanceUtils.generate_headers()
    print("不带Cookie的请求头:")
    for key, value in headers1.items():
        print(f"{key}: {value}")

    # 生成带Cookie的请求头
    sample_cookie = "BIDUPSID=22E06F04889B165B03FEF7EF69E7A074; PSTM=1748485024; ..."
    headers2 = BaiduFinanceUtils.generate_headers(sample_cookie)
    print("\n带Cookie的请求头:")
    for key, value in headers2.items():
        print(f"{key}: {value}")