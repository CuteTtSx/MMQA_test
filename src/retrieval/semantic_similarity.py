"""语义相似度计算模块，支持 embedding 点积与 TableLlama 生成式打分。"""

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config


class SemanticSimilarityCalculator:
    """语义相似度计算器。"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        use_gpu: Optional[bool] = None,
        cache_dir: Optional[str] = None,
        question_table_scoring_method: Optional[str] = None,
    ):
        config = Config.SIMILARITY_CONFIG
        self.model_name = model_name or config["model_name"]
        self.use_gpu = config["use_gpu"] if use_gpu is None else use_gpu
        cache_dir = cache_dir or str(config["cache_dir"])
        self.question_table_scoring_method = question_table_scoring_method or config.get(
            "question_table_scoring_method", "embedding_dot"
        )
        self.tablellama_use_fp16 = config.get("tablellama_use_fp16", False)
        self.tablellama_max_new_tokens = config.get("tablellama_max_new_tokens", 16)

        self.embeddings = None
        self.tablellama_tokenizer = None
        self.tablellama_model = None

        # 缓存路径, 暂时没用
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 当前主要使用内存缓存，适合在一次实验中反复复用相同文本的 embedding。
        self._embedding_cache = {}
        self._tablellama_score_cache = {}

        # 根据打分策略初始化模型
        if self.question_table_scoring_method == "embedding_dot":
            self._load_embedding_model()
        elif self.question_table_scoring_method == "tablellama":
            self._load_tablellama_model()
        else:
            raise ValueError(
                f"不支持的问题-表打分方法: {self.question_table_scoring_method}. "
                "可选值为 embedding_dot 或 tablellama"
            )

    def _load_embedding_model(self):
        """按需加载 embedding 模型，仅在 embedding_dot 模式下使用。"""
        print(f"[INFO] 初始化embedding模型: {self.model_name}")
        model_kwargs = {"device": "cuda"} if self.use_gpu else {}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            encode_kwargs={"normalize_embeddings": True},
            model_kwargs=model_kwargs,
        )
        print("[OK] Embedding模型加载完成")

    def _load_tablellama_model(self):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError("启用 TableLlama 打分需要安装 transformers 和 torch") from exc

        print(f"[INFO] 初始化 TableLlama 模型: {self.model_name}")
        self.tablellama_tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path=self.model_name,
            trust_remote_code=True,
            use_fast=False,
        )

        device_map = "auto" if self.use_gpu else None
        torch_dtype = torch.float16 if (self.use_gpu and self.tablellama_use_fp16) else None
        offload_folder = None
        if self.use_gpu:
            offload_folder = str(self.cache_dir / "tablellama_offload") if self.cache_dir else "tablellama_offload"
            Path(offload_folder).mkdir(parents=True, exist_ok=True)

        self.tablellama_model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=self.model_name,
            trust_remote_code=True,
            device_map=device_map,
            torch_dtype=torch_dtype,
            offload_folder=offload_folder,
        )
        print("[OK] TableLlama 模型加载完成")

    def _get_cache_key(self, text: str) -> str:
        """为文本生成稳定缓存键。"""
        return hashlib.md5(text.encode()).hexdigest()

    def _normalize_text(self, text) -> str:
        """把输入统一规整成字符串，避免上游脏数据导致 embedding 计算失败。"""
        if isinstance(text, str):
            return text
        if isinstance(text, dict):
            return str(text.get("question") or text.get("sub_question") or text.get("text") or text)
        return str(text)

    def _embed_text(self, text: str) -> np.ndarray:
        """将单段文本编码为 embedding 向量，并使用内存缓存加速。"""
        if self.embeddings is None:
            raise RuntimeError("当前未加载 embedding 模型，请将 question_table_scoring_method 设为 embedding_dot")

        text = self._normalize_text(text)
        cache_key = self._get_cache_key(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        embedding = np.array(self.embeddings.embed_query(text))
        self._embedding_cache[cache_key] = embedding
        return embedding

    def _format_table_description(self, table_schema: Dict) -> str:
        """把结构化表 schema 格式化成可送入 embedding 模型的文本描述。"""
        table_name = table_schema.get("table_name", "")
        columns = table_schema.get("table_columns", [])
        column_info = []
        for col in columns:
            col_name = col.get("column_name", "")
            col_type = col.get("column_type", "")
            column_info.append(f"{col_name}({col_type})")
        return f"Table: {table_name}. Columns: {', '.join(column_info)}"

    def _build_tablellama_scoring_prompt(self, question: str, table_description: str) -> str:
        instruction = (
            "You are a table understanding model. Score how relevant the given table is for answering the question. "
            "Return only valid JSON in the format {\"score\": number}. "
            "The score must be a float between 0 and 1."
        )
        model_input = (
            f"[Table]\n{table_description}\n\n[Question]\n{question}\n\n"
            "Judge whether this table is useful for answering the question."
        )
        return (
            "Below is an instruction that describes a task, paired with an input that provides further context. "
            "Write a response that appropriately completes the request.\n\n"
            f"### Instruction:\n{instruction}\n\n"
            f"### Input:\n{model_input}\n\n"
            "### Question:\nWhat is the relevance score?\n\n"
            "### Response:\n"
        )

    def _extract_score_from_tablellama_output(self, output_text: str) -> float:
        output_text = output_text.strip()
        try:
            parsed = json.loads(output_text)
            return float(min(max(float(parsed["score"]), 0.0), 1.0))
        except Exception:
            pass

        json_match = re.search(r'"score"\s*:\s*([0-9]*\.?[0-9]+)', output_text)
        if json_match:
            return float(min(max(float(json_match.group(1)), 0.0), 1.0))

        num_match = re.search(r'([0-9]*\.?[0-9]+)', output_text)
        if num_match:
            score = float(num_match.group(1))
            if score > 1.0:
                score /= 100.0
            return float(min(max(score, 0.0), 1.0))
        return 0.0

    def _compute_question_table_similarity_with_tablellama(self, question: str, table_schema: Dict) -> float:
        if self.tablellama_model is None or self.tablellama_tokenizer is None:
            raise RuntimeError("TableLlama 未加载")

        question = self._normalize_text(question)
        table_description = self._format_table_description(table_schema)
        prompt = self._build_tablellama_scoring_prompt(question, table_description)
        cache_key = self._get_cache_key(f"tablellama::{prompt}")
        if cache_key in self._tablellama_score_cache:
            return self._tablellama_score_cache[cache_key]

        import torch

        inputs = self.tablellama_tokenizer(prompt, return_tensors="pt")
        if self.use_gpu and torch.cuda.is_available():
            inputs = {k: v.to(self.tablellama_model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.tablellama_model.generate(
                **inputs,
                max_new_tokens=self.tablellama_max_new_tokens,
                do_sample=False,
                pad_token_id=self.tablellama_tokenizer.eos_token_id,
            )

        generated_ids = outputs[0][inputs["input_ids"].shape[1] :]
        output_text = self.tablellama_tokenizer.decode(generated_ids, skip_special_tokens=True)
        score = self._extract_score_from_tablellama_output(output_text)
        self._tablellama_score_cache[cache_key] = score
        return score

    def compute_question_table_similarity(self, question: str, table_schema: Dict) -> float:
        """根据配置的方法计算单个问题与单张表之间的语义相似度。"""
        if self.question_table_scoring_method == "tablellama":
            return self._compute_question_table_similarity_with_tablellama(question, table_schema)

        question_embedding = self._embed_text(question)
        table_description = self._format_table_description(table_schema)
        table_embedding = self._embed_text(table_description)
        similarity = float(np.dot(question_embedding, table_embedding))
        return similarity

    def compute_question_tables_similarity(self, question: str, tables_schemas: List[Dict]) -> List[Tuple[str, float]]:
        """计算问题与多张表的相似度，并按分数从高到低排序。"""
        similarities = []
        for table_schema in tables_schemas:
            table_name = table_schema.get("table_name", "unknown")
            similarity = self.compute_question_table_similarity(question, table_schema)
            similarities.append((table_name, similarity))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities

    def compute_table_relationship_score(self, table1: Dict, table2: Dict) -> float:
        """计算两张表的拓扑关系强度。"""
        t1_cols = {col.get("column_name", "") for col in table1.get("table_columns", [])}
        t2_cols = {col.get("column_name", "") for col in table2.get("table_columns", [])}
        t1_pk = table1.get("primary_key")
        t2_pk = table2.get("primary_key")
        t1_fks = set(table1.get("foreign_keys", []))
        t2_fks = set(table2.get("foreign_keys", []))

        has_strong_link = False

        # 1. 表1的外键连到表2的主键，并且相关字段在两张表中都真实存在。
        if t2_pk and (t2_pk in t1_fks) and (t2_pk in t1_cols) and (t2_pk in t2_cols):
            has_strong_link = True

        # 2. 反向检查：表2的外键连到表1的主键。
        if t1_pk and (t1_pk in t2_fks) and (t1_pk in t2_cols) and (t1_pk in t1_cols):
            has_strong_link = True

        # 3. 两张表共享外键字段，常见于桥接表或中间关系表。
        shared_fks = (t1_fks & t2_fks) & t1_cols & t2_cols
        if shared_fks:
            has_strong_link = True

        # 当前评分策略比较激进：有强连接直接给 1.0，否则退化为一个低底分 0.1。
        return 1.0 if has_strong_link else 0.1

        # 下面保留的是旧版更平滑的关系打分逻辑，便于后续回溯实验：
        # def normalize_name(name: str) -> str:
        #     if not name:
        #         return ""
        #     return name.replace("_", "").replace(" ", "").lower()
        #
        # def build_col_map(table: Dict) -> Dict[str, str]:
        #     mapping = {}
        #     for col in table.get("table_columns", []):
        #         original = col.get("column_name", "")
        #         mapping[normalize_name(original)] = original
        #     return mapping
        #
        # def is_id_like(name: str) -> bool:
        #     return name == "id" or name.endswith("id")
        #
        # t1_col_map = build_col_map(table1)
        # t2_col_map = build_col_map(table2)
        # t1_cols = set(t1_col_map.keys())
        # t2_cols = set(t2_col_map.keys())
        #
        # t1_pk = normalize_name(table1.get("primary_key", ""))
        # t2_pk = normalize_name(table2.get("primary_key", ""))
        #
        # raw_t1_fks = {normalize_name(col) for col in table1.get("foreign_keys", []) if col}
        # raw_t2_fks = {normalize_name(col) for col in table2.get("foreign_keys", []) if col}
        #
        # t1_fks = {col for col in raw_t1_fks if col != t1_pk}
        # t2_fks = {col for col in raw_t2_fks if col != t2_pk}
        #
        # t1_is_bridge = (not t1_pk) and len(t1_fks) >= 2
        # t2_is_bridge = (not t2_pk) and len(t2_fks) >= 2
        #
        # t1_to_t2_exact = bool(t2_pk and (t2_pk in t1_fks) and (t2_pk in t1_cols) and (t2_pk in t2_cols))
        # t2_to_t1_exact = bool(t1_pk and (t1_pk in t2_fks) and (t1_pk in t1_cols) and (t1_pk in t2_cols))
        #
        # score = 0.0
        #
        # if t1_to_t2_exact and t2_to_t1_exact:
        #     score = max(score, 1.0)
        # elif t1_to_t2_exact or t2_to_t1_exact:
        #     score = max(score, 0.95)
        #
        # if (t1_is_bridge and t1_to_t2_exact) or (t2_is_bridge and t2_to_t1_exact):
        #     score = max(score, 0.9)
        #
        # shared_fks = (t1_fks & t2_fks) & t1_cols & t2_cols
        # if shared_fks:
        #     if t1_is_bridge or t2_is_bridge:
        #         score = max(score, 0.55)
        #     else:
        #         score = max(score, 0.25)
        #
        # shared_id_like_cols = {col for col in (t1_cols & t2_cols) if is_id_like(col)}
        # if shared_id_like_cols:
        #     score = max(score, 0.12)
        #
        # return score

    def compute_table_relationship_score1(self, table1: Dict, table2: Dict) -> float:
        """
        第一版的表间关系强度计算。

        说明：
        - 该版本没有显式利用主外键信息。
        - 当前主要作为对照或历史保留实现。
        """
        table1_columns = set()
        for col in table1.get("table_columns", []):
            col_name = col.get("column_name", "").lower()
            table1_columns.add(col_name)

        table2_columns = set()
        for col in table2.get("table_columns", []):
            col_name = col.get("column_name", "").lower()
            table2_columns.add(col_name)

        if len(table1_columns) == 0 or len(table2_columns) == 0:
            column_overlap = 0.0
        else:
            column_overlap = len(table1_columns & table2_columns) / max(len(table1_columns), len(table2_columns))
        table1_embedding = self._embed_text(table1.get("table_name", "").lower())
        table2_embedding = self._embed_text(table2.get("table_name", "").lower())
        name_similarity = float(np.dot(table1_embedding, table2_embedding))
        return 0.7 * column_overlap + 0.3 * name_similarity

    def compute_tables_relationships(self, tables_schemas: List[Dict]) -> Dict[Tuple[str, str], float]:
        """计算一组表中所有表对之间的关系强度。"""
        relationships = {}
        for i in range(len(tables_schemas)):
            for j in range(i + 1, len(tables_schemas)):
                table1 = tables_schemas[i]
                table2 = tables_schemas[j]
                relationships[(table1.get("table_name", ""), table2.get("table_name", ""))] = self.compute_table_relationship_score(table1, table2)
        return relationships

    def get_cache_stats(self) -> Dict:
        """返回当前 embedding 内存缓存的统计信息。"""
        return {
            "memory_cache_size": len(self._embedding_cache),
            "tablellama_cache_size": len(self._tablellama_score_cache),
            "cached_texts": list(self._embedding_cache.keys())[:10],
        }


def main():
    """单文件调试入口，用于验证问题-表与表-表打分逻辑。"""
    calculator = SemanticSimilarityCalculator()
    print("\n" + "=" * 80)
    print("语义相似度计算器测试")
    print("=" * 80)

    test_question = "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?"
    test_tables = [
        {
            "table_name": "head",
            "table_columns": [
                {"column_name": "head_ID", "column_type": "int"},
                {"column_name": "head_Name", "column_type": "varchar"},
                {"column_name": "born_state", "column_type": "varchar"},
            ],
            "primary_key": "head_ID",
            "foreign_keys": ["head_ID"],
        },
        {
            "table_name": "department",
            "table_columns": [
                {"column_name": "Department_ID", "column_type": "int"},
                {"column_name": "Department_Name", "column_type": "varchar"},
                {"column_name": "Ranking", "column_type": "int"},
            ],
            "primary_key": "Department_ID",
            "foreign_keys": ["Department_ID"],
        },
    ]

    similarities = calculator.compute_question_tables_similarity(test_question, test_tables)
    for table_name, score in similarities:
        print(f"{table_name}: {score:.4f}")


if __name__ == "__main__":
    main()
