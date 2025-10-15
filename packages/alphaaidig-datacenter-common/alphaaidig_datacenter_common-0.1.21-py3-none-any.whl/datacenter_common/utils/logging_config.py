import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

# 日志配置
DEFAULT_LOG_DIR = "/var/log/fina_mcp_server"
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(log_dir: Optional[str] = None, log_level: int = LOG_LEVEL):
    """
    设置全局日志配置，与systemd配置配合工作
    
    Args:
        log_dir: 日志文件目录路径，如果为None则从环境变量读取或使用默认值
        log_level: 日志级别
    """
    # 检查是否在systemd环境中运行
    is_systemd = os.environ.get('JOURNAL_STREAM') is not None
    
    # 如果没有指定日志目录，则从环境变量获取，否则使用默认值
    if log_dir is None:
        log_dir = os.environ.get('FINA_LOG_DIR', DEFAULT_LOG_DIR)
    
    # 确保日志目录存在
    try:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # 如果无法创建日志目录，使用工程目录下的logs目录
        project_root = Path(__file__).parent.parent.parent
        log_dir = str(project_root / "logs")
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        print(f"警告: 无法创建日志目录 {DEFAULT_LOG_DIR}，使用工程目录下的日志目录 {log_dir}")
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # 配置根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    
    # 在systemd环境中，只添加控制台处理器（systemd会捕获stdout/stderr）
    # 但在所有环境中都添加文件处理器，以便日志可以被下载分析
    if is_systemd:
        logging.info("在systemd环境中运行，日志将由systemd管理，同时也会写入文件")
    
    # 创建控制台处理器（仅在非systemd环境中添加）
    if not is_systemd:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 创建文件处理器（带轮转）- 在所有环境中都添加
    log_file = os.path.join(log_dir, "fina_mcp_server.log")
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"警告: 无法创建文件日志处理器: {e}")
    
    # 创建错误日志文件处理器 - 在所有环境中都添加
    try:
        error_log_file = os.path.join(log_dir, "fina_mcp_server_error.log")
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        root_logger.addHandler(error_file_handler)
    except Exception as e:
        print(f"警告: 无法创建错误日志文件处理器: {e}")
    
    logging.info(f"日志系统初始化完成，日志目录: {log_dir}")

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger实例
    
    Args:
        name: logger名称
        
    Returns:
        logging.Logger: logger实例
    """
    return logging.getLogger(name)