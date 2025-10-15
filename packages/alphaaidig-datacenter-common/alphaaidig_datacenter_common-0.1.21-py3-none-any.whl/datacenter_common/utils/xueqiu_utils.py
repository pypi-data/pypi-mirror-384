import json
from typing import Dict, Optional, Any
from curl_cffi import requests as curl_requests
from curl_cffi import BrowserTypeLiteral
import random
from pathlib import Path

class XueQiuUtils:
    """
    雪球API工具类，用于访问雪球API并获取cookie
    """
    
    @staticmethod
    def get_chrome_browsers() -> list:
        """
        从BrowserTypeLiteral中过滤出所有Chrome浏览器类型

        Returns:
            list: Chrome浏览器类型列表
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
        生成雪球请求头

        Args:
            cookie: 可选的Cookie字符串

        Returns:
            Dict[str, str]: 请求头字典
        """
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
        }

        # 如果提供了Cookie，则添加到请求头
        if cookie:
            headers["Cookie"] = cookie

        return headers
    
    @staticmethod
    def get_xuqiu_cookies() -> Dict[str, str]:
        """
        从xueqiu.json文件中读取cookie信息
        
        Returns:
            Dict[str, str]: 从文件中读取的cookie字典
        """
        try:
            # 获取xueqiu.json文件路径
            project_root = Path(__file__).parent.parent.parent
            xuqiu_json_path = project_root / "src" / "resource" / "xueqiu.json"
            
            # 读取文件内容
            with open(xuqiu_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 返回cookies字段
            return data.get("cookies", {})
        except Exception as e:
            print(f"[DEBUG] 从xueqiu.json读取cookie失败: {str(e)}")
            return {}
    
    @staticmethod
    def _basic_request(url: str, params: Dict[str, Any] = None, cookie: Optional[str] = None) -> curl_requests.Response:
        """
        基础请求方法，不自动添加xueqiu.json中的cookie
        用于获取cookie的方法内部调用
        
        Args:
            url: 请求的URL
            params: 请求参数
            cookie: 可选的Cookie字符串
        
        Returns:
            curl_requests.Response: 请求响应对象
        """
        # 生成请求头
        headers = XueQiuUtils.generate_headers(cookie)

        try:
            # 从BrowserTypeLiteral中获取并随机选择一个Chrome浏览器类型
            chrome_browsers = XueQiuUtils.get_chrome_browsers()
            if not chrome_browsers:
                raise Exception("未找到可用的Chrome浏览器类型")
            
            chrome_browser = random.choice(chrome_browsers)
            
            # 发送请求，curl_cffi会自动设置对应的User-Agent
            response = curl_requests.get(
                url,
                params=params,
                headers=headers,
                impersonate=chrome_browser,
                timeout=20
            )
            
            response.raise_for_status()  # 检查请求是否成功
            return response
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")

    @staticmethod
    def request_with_headers(url: str, params: Dict[str, Any] = None, cookie: Optional[str] = None) -> curl_requests.Response:
        """
        使用生成的请求头发送请求到雪球，自动从xueqiu.json添加cookie

        Args:
            url: 请求的URL
            params: 请求参数
            cookie: 可选的Cookie字符串，如果未提供则从xueqiu.json获取

        Returns:
            curl_requests.Response: 请求响应对象

        Raises:
            Exception: 当请求失败时抛出异常
        """
        # 如果没有提供cookie，则尝试从xueqiu.json中获取
        if not cookie:
            cookies_dict = XueQiuUtils.get_xuqiu_cookies()
            if cookies_dict:
                # 构建cookie字符串
                cookie = '; '.join([f"{k}={v}" for k, v in cookies_dict.items()])
        
        # 调用基础请求方法
        return XueQiuUtils._basic_request(url, params, cookie)

    @staticmethod
    def test_xueqiu_connection() -> Dict[str, Any]:
        """
        测试访问雪球地址并获取cookie（不依赖已存储的cookie）
        
        Returns:
            Dict[str, Any]: 包含状态、cookie和响应信息的字典
        """
        result = {
            "status": False,
            "message": "",
            "cookies": {},
            "response_info": {}
        }
        
        try:
            # 雪球的股票行情页面，常用于测试连接
            xueqiu_url = "https://xueqiu.com/S/SH600000"
            
            # 直接调用基础请求方法，不使用已存储的cookie
            response = XueQiuUtils._basic_request(xueqiu_url)
            
            # 提取cookie信息
            cookies = response.cookies.get_dict()
            
            # 构建结果
            result["status"] = True
            result["message"] = "访问雪球成功"
            result["cookies"] = cookies
            result["response_info"] = {
                "status_code": response.status_code,
                "url": response.url,
                "content_length": len(response.content),
                "headers": dict(response.headers)
            }
            
        except Exception as e:
            result["message"] = f"访问雪球失败: {str(e)}"
            print(f"[DEBUG] 访问雪球失败: {str(e)}")
        
        return result
    
    @staticmethod
    def get_cookies(url: str = "https://xueqiu.com/S/SH600000", params: Dict[str, Any] = None, filter_tokens: bool = False) -> Dict[str, str]:
        """
        获取雪球网站的cookie信息（不依赖已存储的cookie）
        
        Args:
            url: 要访问的雪球URL，默认使用股票页面以获取完整cookie
            params: 请求参数，可选
            filter_tokens: 是否只返回关键的token，默认为False
        
        Returns:
            Dict[str, str]: 获取到的cookie字典，如果获取失败则返回空字典
        
        Raises:
            Exception: 当请求过程中发生错误时抛出异常
        """
        try:
            # 使用股票页面URL以获取完整的cookie
            if url == "https://xueqiu.com/":
                url = "https://xueqiu.com/S/SH600000"
                
            # 直接调用基础请求方法，不使用已存储的cookie
            response = XueQiuUtils._basic_request(url, params)
            
            # 提取cookie信息
            cookies = response.cookies.get_dict()
            
            return cookies
        except Exception as e:
            print(f"[DEBUG] 获取雪球cookie失败: {str(e)}")
            raise Exception(f"获取雪球cookie失败: {str(e)}")

# 测试代码
if __name__ == '__main__':
    # 测试访问雪球并获取cookie
    test_result = XueQiuUtils.test_xueqiu_connection()
    print("\n测试结果:")
    print(json.dumps(test_result, ensure_ascii=False, indent=2))
    
    # 测试单独获取cookie的功能（完整cookie）
    try:
        print("\n\n测试单独获取完整cookie功能:")
        cookies = XueQiuUtils.get_cookies()
        print(f"获取到的cookie数量: {len(cookies)}")
        print("cookie详情:")
        for key, value in cookies.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"测试get_cookies失败: {str(e)}")
        
    # 测试获取关键token
    try:
        print("\n\n测试获取关键token功能:")
        key_tokens = XueQiuUtils.get_cookies(filter_tokens=True)
        print(f"获取到的关键token数量: {len(key_tokens)}")
        print("关键token详情:")
        for key, value in key_tokens.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"测试获取关键token失败: {str(e)}")