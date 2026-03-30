"""
语义相似度计算模块

功能：
1. 计算问题与表的语义相关性
2. 计算表与表的关系强度
3. 支持缓存和批量计算
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import hashlib
from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings


class SemanticSimilarityCalculator:
    """语义相似度计算器"""
    
    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5",
                 use_gpu: bool = False, cache_dir: Optional[str] = None):
        """
        初始化相似度计算器
        
        Args:
            model_name: HuggingFace embedding模型名称
            use_gpu: 是否使用GPU加速
            cache_dir: 缓存目录路径
        """
        print(f"[INFO] 初始化embedding模型: {model_name}")
        
        model_kwargs = {}
        if use_gpu:
            model_kwargs['device'] = 'cuda'
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={'normalize_embeddings': True},
            model_kwargs=model_kwargs
        )
        
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._embedding_cache = {}
        
        print("[OK] Embedding模型加载完成")
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _embed_text(self, text: str) -> np.ndarray:
        """
        获取文本的embedding向量
        
        Args:
            text: 输入文本
        
        Returns:
            embedding向量
        """
        # 检查内存缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # 计算embedding
        embedding = np.array(self.embeddings.embed_query(text))
        
        # 保存到内存缓存
        self._embedding_cache[cache_key] = embedding
        
        return embedding
    
    def _format_table_description(self, table_schema: Dict) -> str:
        """
        格式化表结构为文本描述
        
        Args:
            table_schema: 表结构字典
        
        Returns:
            格式化的表描述文本
        """
        table_name = table_schema.get("table_name", "")
        columns = table_schema.get("table_columns", [])
        
        # 提取列名和类型
        column_info = []
        for col in columns:
            col_name = col.get("column_name", "")
            col_type = col.get("column_type", "")
            column_info.append(f"{col_name}({col_type})")
        
        # 组合成描述文本
        description = f"Table: {table_name}. Columns: {', '.join(column_info)}"
        return description
    
    def compute_question_table_similarity(self, question: str, table_schema: Dict) -> float:
        """
        计算问题与表的相似度
        
        Args:
            question: 问题文本
            table_schema: 表结构字典
        
        Returns:
            相似度分数 [0, 1]
        """
        # 获取问题的embedding
        question_embedding = self._embed_text(question)
        
        # 格式化表描述
        table_description = self._format_table_description(table_schema)
        
        # 获取表描述的embedding
        table_embedding = self._embed_text(table_description)
        
        # 计算余弦相似度（由于已归一化，直接点积即可）
        similarity = float(np.dot(question_embedding, table_embedding))
        
        return similarity
    
    def compute_question_tables_similarity(self, question: str, 
                                         tables_schemas: List[Dict]) -> List[Tuple[str, float]]:
        """
        计算问题与多张表的相似度
        
        Args:
            question: 问题文本
            tables_schemas: 表结构列表
        
        Returns:
            [(table_name, similarity_score), ...] 按相似度降序排列
        """
        similarities = []
        
        for table_schema in tables_schemas:
            table_name = table_schema.get("table_name", "unknown")
            similarity = self.compute_question_table_similarity(question, table_schema)
            similarities.append((table_name, similarity))
        
        # 按相似度降序排列
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities

    def compute_table_relationship_score(self, table1: Dict, table2: Dict) -> float:
        """
            计算两张表的拓扑关系强度（严格基于主键和外键）
        """
        # 获取表1的列名
        t1_cols = set()
        for col in table1.get("table_columns", []):
            col_name = col.get("column_name", "")
            t1_cols.add(col_name)
        # print("table1_columns:", t1_cols)

        # 获取表2的列名
        t2_cols = set()
        for col in table2.get("table_columns", []):
            col_name = col.get("column_name", "")
            t2_cols.add(col_name)
        # print("table2_columns:", t2_cols)

        t1_pk = table1.get("primary_key")
        t2_pk = table2.get("primary_key")
        # print("primary_key:", t1_pk, t2_pk)

        t1_fks = set(table1.get("foreign_keys", []))
        t2_fks = set(table2.get("foreign_keys", []))
        # print("foreign_keys:", t1_fks, t2_fks)

        has_strong_link = False

        # 1. 表1的外键连了表2的主键 (且字段真实存在)
        if t2_pk and (t2_pk in t1_fks) and (t2_pk in t1_cols) and (t2_pk in t2_cols):
            has_strong_link = True

        # 2. 表2的外键连了表1的主键
        if t1_pk and (t1_pk in t2_fks) and (t1_pk in t2_cols) and (t1_pk in t1_cols):
            has_strong_link = True

        # 3. 共享外键（针对中间表，如 management 表同时包涵 department 和 head 的 FK）
        shared_fks = (t1_fks & t2_fks) & t1_cols & t2_cols
        if shared_fks:
            has_strong_link = True

        # 【评分策略】如果主外键严丝合缝，给予极高的权重 1.0。如果是孤岛表，直接惩罚到 0.1
        return 1.0 if has_strong_link else 0.1

    def compute_table_relationship_score1(self, table1: Dict, table2: Dict) -> float:
        """
        (第一版的表间相似度计算, 没有考虑主外键关系, 废弃掉)
        计算两张表的关系强度
        
        基于以下因素：
        1. 列名相似度（可能存在FK关系）
        2. 表名相似度
        
        Args:
            table1: 表1的结构字典
            table2: 表2的结构字典
        
        Returns:
            关系强度 [0, 1]
        """
        # 获取表1的列名
        table1_columns = set()
        for col in table1.get("table_columns", []):
            col_name = col.get("column_name", "").lower()
            table1_columns.add(col_name)

        # 获取表2的列名
        table2_columns = set()
        for col in table2.get("table_columns", []):
            col_name = col.get("column_name", "").lower()
            table2_columns.add(col_name)

        # 计算列名重叠度（可能的FK关系）
        if len(table1_columns) == 0 or len(table2_columns) == 0:
            column_overlap = 0.0
        else:
            overlap_count = len(table1_columns & table2_columns)
            column_overlap = overlap_count / max(len(table1_columns), len(table2_columns))
        
        # 计算表名相似度
        table1_name = table1.get("table_name", "").lower()
        table2_name = table2.get("table_name", "").lower()
        
        table1_embedding = self._embed_text(table1_name)
        table2_embedding = self._embed_text(table2_name)
        name_similarity = float(np.dot(table1_embedding, table2_embedding))
        
        # 综合关系强度（列重叠权重更高）
        relationship_score = 0.7 * column_overlap + 0.3 * name_similarity
        
        return relationship_score
    
    def compute_tables_relationships(self, tables_schemas: List[Dict]) -> Dict[Tuple[str, str], float]:
        """
        计算所有表对之间的关系强度
        
        Args:
            tables_schemas: 表结构列表
        
        Returns:
            {(table1_name, table2_name): relationship_score, ...}
        """
        relationships = {}
        
        for i in range(len(tables_schemas)):
            for j in range(i + 1, len(tables_schemas)):
                table1 = tables_schemas[i]
                table2 = tables_schemas[j]
                
                table1_name = table1.get("table_name", "")
                table2_name = table2.get("table_name", "")
                
                score = self.compute_table_relationship_score(table1, table2)
                relationships[(table1_name, table2_name)] = score
        
        return relationships
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            "memory_cache_size": len(self._embedding_cache),
            "cached_texts": list(self._embedding_cache.keys())[:10]  # 显示前10个
        }


def main():
    """测试语义相似度计算"""
    
    # 初始化计算器
    calculator = SemanticSimilarityCalculator(
        model_name="BAAI/bge-base-en-v1.5",
        use_gpu=False,
        cache_dir="data/similarity_cache"
    )
    
    print("\n" + "=" * 80)
    print("语义相似度计算器测试")
    print("=" * 80)
    
    # 测试问题
    test_question = "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?"
    
    # 测试表结构（从实际数据中提取）
    test_tables = [
        {
            "table_name": "head",
            "table_columns": [
                {"column_name": "head_ID", "column_type": "int"},
                {"column_name": "head_Name", "column_type": "varchar"},
                {"column_name": "born_state", "column_type": "varchar"}
            ],
            "primary_key": "head_ID",
            "foreign_keys": ["head_ID"]
        },
        {
            "table_name": "department",
            "table_columns": [
                {"column_name": "Department_ID", "column_type": "int"},
                {"column_name": "Department_Name", "column_type": "varchar"},
                {"column_name": "Ranking", "column_type": "int"}
            ],
            "primary_key": "Department_ID",
            "foreign_keys": ["Department_ID"]
        },
        {
            "table_name": "management",
            "table_columns": [
                {"column_name": "head_ID", "column_type": "int"},
                {"column_name": "Department_ID", "column_type": "int"},
                {"column_name": "temporary_acting", "column_type": "varchar"}
            ],
            "primary_key": "head_ID",
            "foreign_keys": ["head_ID", "Department_ID"]
        },
        {
            "table_name": "student",
            "table_columns": [
                {"column_name": "student_id", "column_type": "int"},
                {"column_name": "student_name", "column_type": "varchar"},
                {"column_name": "age", "column_type": "int"}
            ],
            "primary_key": "student_id",
            "foreign_keys": ["student_id"]
        }
    ]
    
    # 测试1: 问题-表相似度
    print(f"\n[测试1] 问题与表的相似度")
    print(f"问题: {test_question[:60]}...")
    print("-" * 80)
    
    similarities = calculator.compute_question_tables_similarity(test_question, test_tables)
    
    for table_name, score in similarities:
        print(f"  {table_name:20s}: {score:.4f}")
    
    # 测试2: 表-表关系强度
    print(f"\n[测试2] 表与表的关系强度")
    print("-" * 80)
    
    relationships = calculator.compute_tables_relationships(test_tables)
    
    for (table1, table2), score in sorted(relationships.items(), key=lambda x: x[1], reverse=True):
        print(f"  {table1:15s} <-> {table2:15s}: {score:.4f}")
    
    # 测试3: 缓存统计
    print(f"\n[测试3] 缓存统计")
    print("-" * 80)
    
    stats = calculator.get_cache_stats()
    print(f"  内存缓存大小: {stats['memory_cache_size']} 条")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
