import logging
import sys
from pathlib import Path
from typing import Optional
from src.utils.config import Config

class LoggerManager:
    """日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """
        获取或创建logger
        
        Args:
            name: logger名称(通常使用__name__)
            log_file: 可选的日志文件路径
        
        Returns:
            配置好的logger实例
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(Config.LOG_LEVEL)
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
        
        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(Config.LOG_LEVEL)
        
        # 格式化器
        formatter = logging.Formatter(Config.LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # 文件handler(可选)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(Config.LOG_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger
