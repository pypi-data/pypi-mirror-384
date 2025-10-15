import ast
import json
from typing import List, Dict, Optional, Any  # 添加Any导入
from utils.config_reader import JsonConfigReader
from pathlib import Path

class FunctionDocParser:
    """解析Python函数文档字符串，提取参数和返回值描述"""
    
    def __init__(self, source_code: str):
        """初始化解析器"""
        self.source_code = source_code
        self.tree = ast.parse(source_code)
    
    def parse_execute_method(self) -> Optional[Dict[str, str]]:
        """解析execute方法的文档字符串，支持异步方法"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.AsyncFunctionDef):  # 检查异步函数
                # print(f"找到异步函数: {node.name}")  # 调试信息
                if node.name == "execute":
                    # print("成功定位异步execute方法")
                    return self._parse_docstring(node)
            elif isinstance(node, ast.FunctionDef):  # 保留对普通函数的检查
                # print(f"找到函数: {node.name}")
                if node.name == "execute":
                    # print("成功定位execute方法")
                    return self._parse_docstring(node)
        # print("遍历结束，未找到execute方法")
        return None
    
    def _parse_docstring(self, node: ast.FunctionDef) -> Dict[str, str]:
        """解析函数文档字符串"""
        docstring = ast.get_docstring(node)
        if not docstring:
            return {}
            
        result = {"args": {}, "returns": "", "raises": ""}
        current_section = None
        
        for line in docstring.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Args:"):
                current_section = "args"
            elif line.startswith("Returns:"):
                current_section = "returns"
            elif line.startswith("Raises:"):
                current_section = "raises"
            elif current_section == "args" and ":" in line:
                # 解析参数描述
                arg_name, desc = line.split(":", 1)
                arg_name = arg_name.strip()
                result["args"][arg_name] = desc.strip()
            elif current_section in ["returns", "raises"] and line:
                # 收集返回值和异常描述
                result[current_section] += line + " "
        
        # 清理多余空格
        for key in ["returns", "raises"]:
            result[key] = result[key].strip()
            
        return result
    
    def parse_to_tool_schema(self, market: str,module_name: str) -> Optional[Dict[str, Any]]:
        """将解析结果转换为Tool类需要的格式"""
        doc_info = self.parse_execute_method()
        if not doc_info:
            return None
            
        # 获取execute方法的文档字符串
        execute_node = None
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == "execute":
                execute_node = node
                break
                
        first_line_desc = ""
        if execute_node:
            docstring = ast.get_docstring(execute_node)
            if docstring:
                first_line_desc = docstring.split('\n')[0].strip()
                if "功能关闭" in first_line_desc:
                    return None
        
        # 从config.json获取market信息并转换为中文
        try:
            # 将市场代码转换为中文名称
            market_map = {
                'zh_a': 'A股',
                'hk': '港股',
                'us': '美股',
                'news': '新闻'
            }
            market = market_map.get(market)
        except Exception as e:
            print(f"获取market配置失败: {str(e)}")
            market = '未知市场'
            
        # 构建inputSchema
        properties = {}
        required = []
        type_mapping = {
            "int": "integer",
            "float": "number",
            "str": "string",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }
        for arg_name, desc in doc_info["args"].items():
            param_type = "string"
            # 尝试从描述中提取类型信息
            for key in type_mapping.keys():
                if key in desc:
                    param_type = type_mapping[key]
                    break
            
            properties[arg_name] = {
                "type": param_type,
                "description": desc
            }
            # 只在description中不包含"可选"或"非必填"时才添加到required
            if "可选参数" not in desc and "非必填参数" not in desc:
                required.append(arg_name)
                
        return {
            "name": module_name,
            "description": f"{market}-{first_line_desc}-{doc_info.get('returns', '')}",  # 添加market前缀
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def get_tools(self, market: str) -> List[Dict[str, Any]]:
        """遍历apis目录下的Python脚本并生成Tool Schema
        
        Args:
            market: 市场类型(zh_a/hk/us)，不允许为空
        """
        
        current_dir = Path(__file__).parent
        apis_dir = current_dir.parent / "apis" / market
        
        tools = []
        
        # 明确的单目录扫描
        search_dir = apis_dir
        if search_dir.exists():
            for py_file in search_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                    
                module_name = py_file.stem
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()
                
                parser = FunctionDocParser(source)
                tool_schema = parser.parse_to_tool_schema(market, module_name)
                if tool_schema:
                    tools.append(tool_schema)
        
        return tools

# 修改使用示例
if __name__ == "__main__":
    parser = FunctionDocParser("")  # 空字符串初始化即可，因为get_tools会自己读取文件
    tools = parser.get_tools("news")
    
    if tools:
        print("生成的所有Tool Schema:")
        for tool in tools:
            print(json.dumps(tool, indent=2, ensure_ascii=False))
            print("-" * 50)
    else:
        print("未找到任何有效的execute方法")