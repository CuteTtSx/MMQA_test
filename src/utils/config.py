import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """全局配置管理"""
    
    # 项目路径
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    SRC_DIR = PROJECT_ROOT / "src"
    CACHE_DIR = PROJECT_ROOT / ".cache"
    
    # 确保必要目录存在
    CACHE_DIR.mkdir(exist_ok=True)
    
    # API配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # 模型配置
    DECOMPOSER_MODEL = "gpt-4o-mini"  # 问题分解模型
    EMBEDDING_MODEL = "text-embedding-3-small"  # 嵌入模型
    FINETUNING_BASE_MODEL = "Qwen/Qwen2.5-7B"  # 微调基础模型
    
    # MTR算法参数
    MTR_CONFIG = {
        "top_k": 5,                    # 返回top-K张表
        "num_rounds": 3,               # 迭代轮数
        "similarity_threshold": 0.5,   # 相似度阈值
        "question_weight": 0.7,        # 问题相关性权重
        "table_weight": 0.3,           # 表关系权重
    }
    
    # 问题分解器参数
    DECOMPOSER_CONFIG = {
        "temperature": 0.0,
        "max_retries": 3,
        "retry_delay": 1,              # 秒
        "batch_size": 10,              # 批量处理大小
        "cache_enabled": True,
    }
    
    # 微调参数
    FINETUNING_CONFIG = {
        "num_train_epochs": 3,
        "per_device_train_batch_size": 4,
        "per_device_eval_batch_size": 4,
        "learning_rate": 2e-4,
        "warmup_steps": 100,
        "weight_decay": 0.01,
        "logging_steps": 50,
        "eval_steps": 200,
        "save_steps": 200,
        "lora_r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
    }
    
    # 数据集配置
    DATASET_CONFIG = {
        "train_ratio": 0.8,
        "val_ratio": 0.1,
        "test_ratio": 0.1,
    }
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_data_path(cls, filename: str) -> Path:
        """获取数据文件路径"""
        return cls.DATA_DIR / filename
    
    @classmethod
    def get_cache_path(cls, filename: str) -> Path:
        """获取缓存文件路径"""
        return cls.CACHE_DIR / filename
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置有效性"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in .env file")
        if not cls.DATA_DIR.exists():
            raise ValueError(f"Data directory not found: {cls.DATA_DIR}")
        return True
