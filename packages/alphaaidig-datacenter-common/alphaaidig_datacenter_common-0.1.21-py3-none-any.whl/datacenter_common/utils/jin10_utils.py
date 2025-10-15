from curl_cffi import requests as curl_requests
from curl_cffi import BrowserTypeLiteral
import random
from typing import Dict, Any, Optional, List

class Jin10Utils:
    """
    金十数据API工具类，用于生成请求头和发送请求
    """
    # 移除 BASE_URL 常量
    APP_ID = "arU9WZF7TC9m7nWn"
    VERSION = "1.0.1"

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
    def generate_headers(cookie: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        生成金十数据API请求头
    
        Args:
            cookie: 可选的Cookie字符串
            custom_headers: 可选的自定义请求头，将与基础请求头合并
    
        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "origin": "https://xnews.jin10.com/",
            "priority": "u=1, i",
            "referer": "https://xnews.jin10.com/",
            "withcredentials": "true",
            "x-app-id": Jin10Utils.APP_ID,
            "x-token": "",
            "x-version": Jin10Utils.VERSION
        }
    
        # 如果提供了Cookie，则添加到请求头
        if cookie:
            headers["Cookie"] = cookie
    
        # 如果提供了自定义请求头，则合并到基础请求头中
        if custom_headers:
            headers.update(custom_headers)
    
        return headers

    @staticmethod
    def request_with_headers(base_url: str, params: Dict[str, Any], cookie: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        使用生成的请求头发送同步请求

        Args:
            base_url: 请求的基础URL
            params: 请求参数
            cookie: 可选的Cookie字符串

        Returns:
            Dict[str, Any]: 请求响应的JSON数据

        Raises:
            Exception: 当请求失败时抛出异常
        """
        # 生成请求头
        headers = Jin10Utils.generate_headers(cookie)
        if custom_headers:
            headers.update(custom_headers)

        try:
            # 从BrowserTypeLiteral中获取并随机选择一个Chrome浏览器类型
            chrome_browsers = Jin10Utils.get_chrome_browsers()
            if not chrome_browsers:
                raise Exception("未找到可用的Chrome浏览器类型")
            
            chrome_browser = random.choice(chrome_browsers)
            
            # 发送请求，curl_cffi会自动设置对应的User-Agent
            response = curl_requests.get(
                base_url,  # 使用传入的base_url
                params=params,
                headers=headers,
                impersonate=chrome_browser,
                timeout=10
            )
            
            response.raise_for_status()  # 检查请求是否成功
            return response.json()
        except Exception as e:
            raise Exception(f"请求金十数据失败: {str(e)}")

    @staticmethod
    def request_with_headers_text(base_url: str, params: Dict[str, Any], cookie: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None) -> str:
        """
        使用生成的请求头发送同步请求

        Args:
            base_url: 请求的基础URL
            params: 请求参数
            cookie: 可选的Cookie字符串

        Returns:
            str: 请求响应的文本内容

        Raises:
            Exception: 当请求失败时抛出异常
        """
        # 生成请求头
        headers = Jin10Utils.generate_headers(cookie)
        headers["accept_type"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        if custom_headers:
            headers.update(custom_headers)

        try:
            # 从BrowserTypeLiteral中获取并随机选择一个Chrome浏览器类型
            chrome_browsers = Jin10Utils.get_chrome_browsers()
            if not chrome_browsers:
                raise Exception("未找到可用的Chrome浏览器类型")
            
            chrome_browser = random.choice(chrome_browsers)
            
            # 发送请求，curl_cffi会自动设置对应的User-Agent
            response = curl_requests.get(
                base_url,  # 使用传入的base_url
                params=params,
                headers=headers,
                impersonate=chrome_browser,
                timeout=10
            )
            
            response.raise_for_status()  # 检查请求是否成功
            return response.text
        except Exception as e:
            raise Exception(f"请求金十数据失败: {str(e)}")