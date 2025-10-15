import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

class JsonConfigReader:
    """JSON配置读取器，支持多级配置提取"""
    
    def __init__(self, config_path: str):
        """
        初始化配置读取器
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config_data = None
        
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {str(e)}")
    
    def get_value(self, *keys: str, default: Any = None) -> Any:
        """
        获取配置值，支持多级key
        Args:
            *keys: 多级key，如('server', 'deploy_mode')
            default: 默认值
        Returns:
            配置值或默认值
        """
        if self._config_data is None:
            self.load_config()
            
        value = self._config_data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value

    @classmethod
    def from_project_root(cls, relative_path: str) -> 'JsonConfigReader':
        """
        从项目根目录创建配置读取器
        Args:
            relative_path: 相对于项目根目录的路径
        Returns:
            JsonConfigReader实例
        """
        project_root = Path(__file__).parent.parent.parent
        config_path = os.path.join(project_root, relative_path)
        return cls(config_path)

def main():
    """测试配置读取功能"""
    try:
        # 测试读取配置
        reader = JsonConfigReader.from_project_root('config.json')
        
        # 测试获取多层配置
        print("\n测试多层配置:")
        value = reader.get_value('server', 'deploy_mode', default='sse')
        print(f"server.deploy_mode配置: {value}")
        
        # 测试不存在的配置
        print("\n测试不存在的配置:")
        value = reader.get_value('not_exist', 'key', default='默认值')
        print(f"不存在的配置返回: {value}")
        
    except Exception as e:
        print(f"配置读取测试失败: {str(e)}")

if __name__ == "__main__":
    main()