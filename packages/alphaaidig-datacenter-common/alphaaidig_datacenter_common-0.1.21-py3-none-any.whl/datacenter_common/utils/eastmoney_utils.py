import re
import random
import time
import requests
import json  # 添加json模块导入

class EastMoneyUtils:
    """
    东方财富API工具类，提供通用功能如动态参数生成和JSONP数据解析
    """
    # 固定参数
    UT_PARAM = "fa5fd1943c7b386f172d6893dbfba10b"
    WBP2U_PARAM = "8701037485702576%7C0%7C1%7C0%7Cweb"

    @staticmethod
    def generate_jquery_callback() -> str:
        """
        动态生成jQuery回调函数名

        Returns:
            str: 格式为jQuery{随机数}_{时间戳}的回调函数名
        """
        random_num = ''.join([str(random.randint(0, 9)) for _ in range(19)])
        timestamp = int(time.time() * 1000)
        return f"jQuery{random_num}_{timestamp}"

    @staticmethod
    def generate_timestamp() -> int:
        """
        生成当前时间戳(毫秒级)

        Returns:
            int: 当前时间戳
        """
        return int(time.time() * 1000)

    @staticmethod
    def parse_jsonp_response(response_text: str) -> dict:
        """
        解析JSONP格式的响应数据

        Args:
            response_text: JSONP格式的响应文本

        Returns:
            dict: 解析后的JSON数据

        Raises:
            ValueError: 当响应格式不正确时
        """
        # 提取JSONP中的JSON数据
        json_match = re.search(r'jQuery\d+_\d+\((.*)\);', response_text)
        if not json_match:
            raise ValueError("数据格式不正确，无法解析JSONP")

        json_data = json_match.group(1)
        try:
            # 使用json.loads转换为Python对象，而不是使用eval
            return json.loads(json_data)
        except Exception as e:
            raise ValueError(f"解析JSON数据失败: {str(e)}")

    @staticmethod
    def fetch_and_parse_data(url: str) -> dict:
        """
        发送请求并解析JSONP响应

        Args:
            url: API URL

        Returns:
            dict: 解析后的数据

        Raises:
            requests.RequestException: 当请求失败时
            ValueError: 当解析失败时
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            return EastMoneyUtils.parse_jsonp_response(response.text)
        except requests.RequestException as e:
            raise requests.RequestException(f"请求数据失败: {str(e)}")

    @staticmethod
    def format_stock_data(data: dict, field_mapping: dict) -> list:
        """
        格式化股票数据

        Args:
            data: 原始数据
            field_mapping: 字段映射字典

        Returns:
            list: 格式化后的数据列表
        """
        if data.get('rc') != 0 or 'data' not in data or 'diff' not in data['data']:
            raise ValueError(f"数据获取失败: {data.get('rt', '未知错误')}")

        formatted_data = []
        for item in data['data']['diff']:
            row = {}
            for field, name in field_mapping.items():
                if field in item:
                    row[name] = item[field]
            formatted_data.append(row)

        return formatted_data

# 测试代码
if __name__ == '__main__':
    # 测试生成jQuery回调
    print("生成的jQuery回调:", EastMoneyUtils.generate_jquery_callback())

    # 测试生成时间戳
    print("生成的时间戳:", EastMoneyUtils.generate_timestamp())

    # 注意：由于移除了URL构建方法，完整请求测试需要结合上游模块