import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """全局配置管理。"""

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    TMP_DATA_DIR = PROJECT_ROOT / "tmp_data"
    SRC_DIR = PROJECT_ROOT / "src"
    OUTPUTS_DIR = PROJECT_ROOT / "outputs"
    CACHE_DIR = PROJECT_ROOT / ".cache"
    DECOMPOSITION_CACHE_DIR = CACHE_DIR / "decomposition_cache"
    SIMILARITY_CACHE_DIR = CACHE_DIR / "similarity_cache"
    MTR_OUTPUT_DIR = OUTPUTS_DIR / "MTR_evaluate"
    TEXT2SQL_OUTPUT_DIR = OUTPUTS_DIR / "qwen_text2sql_lora"
    TEXT2SQL_FINAL_CHECKPOINT_DIR = TEXT2SQL_OUTPUT_DIR / "final_checkpoint"
    TEXT2SQL_EVAL_PREDICTIONS_FILE = TEXT2SQL_OUTPUT_DIR / "eval_predictions.jsonl"

    for _dir in (
        DATA_DIR,
        TMP_DATA_DIR,
        OUTPUTS_DIR,
        CACHE_DIR,
        DECOMPOSITION_CACHE_DIR,
        SIMILARITY_CACHE_DIR,
        MTR_OUTPUT_DIR,
        TEXT2SQL_OUTPUT_DIR,
        TEXT2SQL_FINAL_CHECKPOINT_DIR,
    ):
        _dir.mkdir(parents=True, exist_ok=True)

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

    DECOMPOSER_MODEL = os.getenv("DECOMPOSER_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    TABLE_MODEL = os.getenv("TABLE_MODEL", "osunlp/TableLlama")
    FINETUNING_BASE_MODEL = os.getenv("FINETUNING_BASE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

    SYNTHESIZED_TWO_TABLE_FILE = DATA_DIR / "Synthesized_two_table.json"
    SYNTHESIZED_THREE_TABLE_FILE = DATA_DIR / "Synthesized_three_table.json"

    TWO_TABLE_SCHEMA_FILE = TMP_DATA_DIR / "two_table_only_schema.json"
    THREE_TABLE_SCHEMA_FILE = TMP_DATA_DIR / "three_table_only_schema.json"

    QA_SQL_TWO_TABLE_FILE = DATA_DIR / "QA_SQL_two_table.json"
    QA_SQL_THREE_TABLE_FILE = DATA_DIR / "QA_SQL_three_table.json"

    GLOBAL_TABLE_POOL_TWO_FILE = DATA_DIR / "global_table_pool_two.json"
    GLOBAL_TABLE_POOL_THREE_FILE = DATA_DIR / "global_table_pool_three.json"

    FINETUNING_TRAIN_JSON = DATA_DIR / "finetuning_train.json"
    FINETUNING_VAL_JSON = DATA_DIR / "finetuning_val.json"
    FINETUNING_TEST_JSON = DATA_DIR / "finetuning_test.json"
    FINETUNING_TRAIN_JSONL = DATA_DIR / "finetuning_train.jsonl"
    FINETUNING_VAL_JSONL = DATA_DIR / "finetuning_val.jsonl"
    FINETUNING_TEST_JSONL = DATA_DIR / "finetuning_test.jsonl"

    PREPROCESS_CONFIG = {
        "two_table_raw": SYNTHESIZED_TWO_TABLE_FILE,
        "three_table_raw": SYNTHESIZED_THREE_TABLE_FILE,
        "two_table_schema": TWO_TABLE_SCHEMA_FILE,
        "three_table_schema": THREE_TABLE_SCHEMA_FILE,
        "two_table_qa": QA_SQL_TWO_TABLE_FILE,
        "three_table_qa": QA_SQL_THREE_TABLE_FILE,
        "two_table_pool": GLOBAL_TABLE_POOL_TWO_FILE,
        "three_table_pool": GLOBAL_TABLE_POOL_THREE_FILE,
    }

    DATASET_CONFIG = {
        "train_ratio": 0.8,
        "val_ratio": 0.1,
        "test_ratio": 0.1,
        "seed": 42,
    }

    MTR_CONFIG = {
        "top_k": 3,
        "num_rounds": 2,
        "top_k_per_round": 10,
        "similarity_threshold": 0.5,
        "question_weight": 0.7,
        "table_weight": 0.3,
        "retrieval_mode": "current",
        "hybrid_gap12_threshold": 0.015,
        "hybrid_gap13_threshold": 0.03,
        "hybrid_rerank_alpha": 0.75,
        "hybrid_rerank_beta": 0.25,
        "hybrid_expand_per_seed": 2,
    }

    DECOMPOSER_CONFIG = {
        "model": DECOMPOSER_MODEL,
        "temperature": 0.0,
        "max_retries": 3,
        "retry_delay": 1,
        "batch_size": 10,
        "cache_enabled": True,
        "cache_dir": DECOMPOSITION_CACHE_DIR,
    }
    
    SIMILARITY_SCORING_METHOD = "embedding_dot" # 默认是embedding_dot

    SIMILARITY_CONFIG = {
        "question_table_scoring_method": SIMILARITY_SCORING_METHOD,  # embedding_dot 是点积; tablellama 是模型计算
        "model_name": TABLE_MODEL if SIMILARITY_SCORING_METHOD == "tablellama" else EMBEDDING_MODEL,
        # "embedding_local_path": SIMILARITY_CACHE_DIR / "models" / "bge-base-en-v1.5",
        "embedding_local_path": r"E:\programEdit\huggingface_cache\hub\models--BAAI--bge-base-en-v1.5\snapshots\a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
        "use_gpu": True,
        "cache_dir": SIMILARITY_CACHE_DIR,
        "embedding_persist_enabled": True,
        "chroma_persist_dir": SIMILARITY_CACHE_DIR / "chroma_db",
        "chroma_collection_prefix": "semantic_similarity",
        "tablellama_use_fp16": True,
        "tablellama_max_new_tokens": 16,
    }

    FINETUNING_CONFIG = {
        "max_length": 1024,
        "num_train_epochs": 3,
        "per_device_train_batch_size": 4,
        "per_device_eval_batch_size": 4,
        "gradient_accumulation_steps": 8,
        "learning_rate": 2e-4,
        "warmup_steps": 100,
        "weight_decay": 0.01,
        "logging_steps": 50,
        "eval_steps": 200,
        "save_steps": 200,
        "save_total_limit": 2,
        "max_new_tokens": 256,
        "lora_r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
    }

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def get_data_path(cls, filename: str) -> Path:
        return cls.DATA_DIR / filename

    @classmethod
    def get_tmp_data_path(cls, filename: str) -> Path:
        return cls.TMP_DATA_DIR / filename

    @classmethod
    def get_output_path(cls, filename: str) -> Path:
        return cls.OUTPUTS_DIR / filename

    @classmethod
    def get_mtr_output_path(cls, filename: str) -> Path:
        return cls.MTR_OUTPUT_DIR / filename

    @classmethod
    def get_text2sql_output_path(cls, filename: str) -> Path:
        return cls.TEXT2SQL_OUTPUT_DIR / filename

    @classmethod
    def get_cache_path(cls, filename: str) -> Path:
        return cls.CACHE_DIR / filename

    @classmethod
    def get_table_pool_tasks(cls):
        return [
            (cls.SYNTHESIZED_THREE_TABLE_FILE, cls.GLOBAL_TABLE_POOL_THREE_FILE),
            (cls.SYNTHESIZED_TWO_TABLE_FILE, cls.GLOBAL_TABLE_POOL_TWO_FILE),
        ]

    @classmethod
    def get_question_extraction_tasks(cls):
        return [
            (cls.SYNTHESIZED_THREE_TABLE_FILE, cls.QA_SQL_THREE_TABLE_FILE),
            (cls.SYNTHESIZED_TWO_TABLE_FILE, cls.QA_SQL_TWO_TABLE_FILE),
        ]

    @classmethod
    def get_schema_extraction_tasks(cls):
        return [
            (cls.SYNTHESIZED_THREE_TABLE_FILE, cls.THREE_TABLE_SCHEMA_FILE),
            (cls.SYNTHESIZED_TWO_TABLE_FILE, cls.TWO_TABLE_SCHEMA_FILE),
        ]

    @classmethod
    def validate(cls, require_openai: bool = False) -> bool:
        if require_openai and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in .env file")
        if not cls.DATA_DIR.exists():
            raise ValueError(f"Data directory not found: {cls.DATA_DIR}")
        return True
