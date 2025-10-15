import numpy as np

# 新增：将 JSON 数据转换为 Markdown 表格的函数
def convert_to_markdown(data):
    if not data:
        return '暂无数据'
        
    try:
        # 先转换整个数据
        converted_data = convert_value(data)
        
        # 处理字典类型
        if isinstance(converted_data, dict):
            if '报告日期' in converted_data:
                # 确保报告日期是可迭代的
                report_dates = converted_data['报告日期']
                if not isinstance(report_dates, (list, tuple, np.ndarray)):
                    report_dates = [report_dates]
                
                headers = ['报告日期'] + [str(item) for item in report_dates]
                rows = []
                
                for key, values in converted_data.items():
                    if key != '报告日期':
                        # 确保值是可迭代的
                        if not isinstance(values, (list, tuple, np.ndarray)):
                            values = [values]
                        row = [key] + [str(convert_value(item)) for item in values]
                        rows.append(row)
                
                markdown_table = '| ' + ' | '.join(headers) + ' |\n'
                markdown_table += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'
                for row in rows:
                    markdown_table += '| ' + ' | '.join(row) + ' |\n'
                return markdown_table
            else:
                return '未找到报告日期数据'
        
        # 处理列表类型
        elif isinstance(converted_data, list):
            if not converted_data:
                return '暂无数据'
                
            headers = list(converted_data[0].keys()) if converted_data else []
            rows = []
            
            for item in converted_data:
                row = [str(convert_value(item.get(header, ''))) for header in headers]
                rows.append(row)
                
            markdown_table = '| ' + ' | '.join(headers) + ' |\n'
            markdown_table += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'
            for row in rows:
                markdown_table += '| ' + ' | '.join(row) + ' |\n'
            return markdown_table
        
        # 处理单个值
        else:
            return str(convert_value(converted_data))
            
    except Exception as e:
        return f"数据转换失败: {str(e)}"

def convert_value(value):
    if isinstance(value, (np.integer, int)):
        return int(value)
    elif isinstance(value, (np.floating, float)):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, (list, tuple)):
        return [convert_value(item) for item in value]
    else:
        return value


class JsonToMarkdownConverter:
    """
    JSON数组转Markdown表格工具类
    将JSON数组转换为标准Markdown表格格式，使用第一条数据的key作为表头
    """
    @staticmethod
    def convert(json_array):
        """
        将JSON数组转换为Markdown表格
        
        Args:
            json_array (list): 包含字典元素的JSON数组
            
        Returns:
            str: 生成的Markdown表格字符串
        """
        if not isinstance(json_array, list):
            raise ValueError("输入必须是JSON数组格式")

        if not json_array:
            return "| 提示 |\n|------|\n| 暂无数据 |"

        # 使用第一条数据的key作为表头
        headers = list(json_array[0].keys())
        
        # 处理表格内容
        markdown_lines = []
        # 添加表头
        markdown_lines.append(f"| {' | '.join(headers)} |")
        # 添加分隔线
        markdown_lines.append(f"| {' | '.join(['---'] * len(headers))} |")
        # 添加数据行
        for item in json_array:
            row_values = []
            for header in headers:
                # 使用现有convert_value处理数据类型转换
                value = convert_value(item.get(header, ''))
                row_values.append(str(value) if value is not None else '')
            markdown_lines.append(f"| {' | '.join(row_values)} |")

        return '\n'.join(markdown_lines)

# 新增：便捷转换函数
def json_array_to_markdown(json_array):
    return JsonToMarkdownConverter.convert(json_array)