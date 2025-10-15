import logging
import sys
import os
from pathlib import Path

def setup_logger(name: str = "datacenter") -> logging.Logger:
    """设置并返回配置好的logger实例"""
    
    # 区分开发和生产环境
    if os.environ.get('ENVIRONMENT') == 'production':
        # 生产环境使用标准日志目录
        log_dir = Path("/var/log/datacenter")
        log_dir.mkdir(exist_ok=True, mode=0o755)
    else:
        # 开发环境使用相对路径
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 清除现有的handlers
    logger.handlers.clear()
    
    # 创建formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件handler
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 添加handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建默认logger实例
logger = setup_logger()