"""
多表检索(MTR)核心算法模块

实现论文中的MTR算法：
1. 问题分解 → 获取子问题列表
2. 第一轮检索 → 计算问题-表相似度
3. 迭代式多表检索 → 结合表-表关系强度
4. 排序与选择 → 返回Top-K表
"""

import json
from typing import Dict, List, Tuple, Optional, Set
from pathlib import Path
import numpy as np

from src.question_decomposer import QuestionDecomposer
from src.semantic_similarity import SemanticSimilarityCalculator


class MultiTableRetriever:
    """多表检索器"""
    
    def __init__(self, table_pool_file: str, 
                 decomposer: Optional[QuestionDecomposer] = None,
                 similarity_calculator: Optional[SemanticSimilarityCalculator] = None,
                 num_iterations: int = 2,
                 top_k_per_round: int = 20):
        """
        初始化MTR检索器
        
        Args:
            table_pool_file: 全局表池文件路径
            decomposer: 问题分解器实例
            similarity_calculator: 相似度计算器实例
            num_iterations: 迭代轮数
            top_k_per_round: 每轮保留的候选表数量
        """
        print("[INFO] 初始化MTR检索器...")
        
        # 加载表池
        self.table_pool = self._load_table_pool(table_pool_file)
        self.table_pool_file = table_pool_file
        
        # 初始化分解器和相似度计算器
        if decomposer is None:
            self.decomposer = QuestionDecomposer(model="gpt-4o-mini", cache_dir="data/decomposition_cache")
        else:
            self.decomposer = decomposer
        
        if similarity_calculator is None:
            self.similarity_calculator = SemanticSimilarityCalculator(
                cache_dir="data/similarity_cache"
            )
        else:
            self.similarity_calculator = similarity_calculator
        
        self.num_iterations = num_iterations
        self.top_k_per_round = top_k_per_round
        
        # 预计算表-表关系强度矩阵（缓存）
        self._relationship_cache = {}
        
        print(f"[OK] MTR检索器初始化完成 (表池: {len(self.table_pool)} 张表)")
    
    def _load_table_pool(self, pool_file: str) -> Dict:
        """加载全局表池"""
        print(f"[INFO] 加载表池: {pool_file}")
        
        with open(pool_file, 'r', encoding='utf-8') as f:
            table_pool = json.load(f)
        
        print(f"[OK] 加载了 {len(table_pool)} 张表")
        return table_pool
    
    def _convert_pool_table_to_schema(self, pool_key: str, table_data: Dict) -> Dict:
        """将表池中的表转换为schema格式"""
        original_table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])
        
        table_columns = [
            {"column_name": col, "column_type": "unknown"}
            for col in columns
        ]
        
        return {
            "table_name": original_table_name,
            "table_columns": table_columns,
            "primary_key": table_data.get("primary_key"),  # 新增：带上主键
            "foreign_keys": table_data.get("foreign_keys", []),  # 新增：带上外键
            "pool_key": pool_key
        }
    
    def _get_table_unique_id(self, pool_key: str, table_data: Dict) -> str:
        """生成表的唯一ID"""
        table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])
        columns_str = ",".join(columns)
        return f"{table_name}_[{columns_str}]"
    
    def _compute_question_table_similarities(self, question: str) -> Dict[str, float]:
        """
        计算问题与所有表的相似度
        
        Args:
            question: 问题文本
        
        Returns:
            {table_unique_id: similarity_score, ...}
        """
        similarities = {}
        
        for pool_key, table_data in self.table_pool.items():
            table_schema = self._convert_pool_table_to_schema(pool_key, table_data) # 计算相似度table_schema内要使用原始表名
            similarity = self.similarity_calculator.compute_question_table_similarity(
                question, table_schema
            )
            
            table_id = self._get_table_unique_id(pool_key, table_data)
            similarities[table_id] = similarity
        
        return similarities
    
    def _compute_table_relationship_score(self, table_id1: str, table_id2: str) -> float:
        """
        计算两张表的关系强度
        
        Args:
            table_id1: 表1的唯一ID
            table_id2: 表2的唯一ID
        
        Returns:
            关系强度 [0, 1]
        """
        # 检查缓存
        cache_key = tuple(sorted([table_id1, table_id2]))
        if cache_key in self._relationship_cache:
            return self._relationship_cache[cache_key]
        
        # 从表池中查找表数据
        table1_data = None
        table2_data = None
        
        for pool_key, table_data in self.table_pool.items():
            table_id = self._get_table_unique_id(pool_key, table_data)
            if table_id == table_id1:
                table1_data = table_data
            elif table_id == table_id2:
                table2_data = table_data
        
        if table1_data is None or table2_data is None:
            return 0.0
        
        # 转换为schema格式
        schema1 = self._convert_pool_table_to_schema("", table1_data)
        schema2 = self._convert_pool_table_to_schema("", table2_data)
        
        # 计算关系强度
        score = self.similarity_calculator.compute_table_relationship_score(schema1, schema2)
        
        # 保存到缓存
        self._relationship_cache[cache_key] = score
        
        return score
    
    def retrieve(self, question: str, top_k: int = 5, verbose: bool = False) -> List[Dict]:
        """
        MTR核心算法：多表检索
        
        Args:
            question: 输入问题
            top_k: 返回前K个相关表
            verbose: 是否打印详细信息
        
        Returns:
            [{
                "table_id": str,
                "table_name": str,
                "columns": List[str],
                "relevance_score": float,
                "retrieval_round": int,
                "related_tables": List[str]
            }, ...]
        """
        if verbose:
            print(f"\n[MTR] 开始检索问题: {question[:60]}...")
        
        # 步骤1: 问题分解
        if verbose:
            print("[MTR] 步骤1: 问题分解...")
        
        sub_questions = self.decomposer.decompose(question)
        if not sub_questions:
            sub_questions = [question]  # 如果分解失败，使用原问题
        
        if verbose:
            print(f"[MTR] 分解得到 {len(sub_questions)} 个子问题")
            for i, sq in enumerate(sub_questions, 1):
                print(f"      {i}. {sq[:60]}...")
        
        # 步骤2: 第一轮检索 - 计算问题-表相似度
        if verbose:
            print("[MTR] 步骤2: 第一轮检索 (问题-表相似度)...")
        
        # 对每个子问题计算与所有表的相似度
        table_scores = {}  # {table_id: accumulated_score}
        
        for sub_q in sub_questions:
            similarities = self._compute_question_table_similarities(sub_q)
            
            for table_id, score in similarities.items():
                if table_id not in table_scores:
                    table_scores[table_id] = 0.0
                table_scores[table_id] += score
        
        # 平均化分数
        for table_id in table_scores:
            table_scores[table_id] /= len(sub_questions)
        
        # 选择Top-K候选表
        top_candidates = sorted(
            table_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.top_k_per_round]
        
        if verbose:
            print(f"[MTR] 第一轮检索得到 {len(top_candidates)} 个候选表")
        
        # 步骤3: 迭代式多表检索
        current_tables = {table_id: score for table_id, score in top_candidates}
        
        for iteration in range(1, self.num_iterations):
            if verbose:
                print(f"[MTR] 步骤3.{iteration}: 第{iteration+1}轮检索 (表-表关系)...")
            
            new_scores = {}
            
            # 对每个子问题
            for sub_q in sub_questions:
                similarities = self._compute_question_table_similarities(sub_q)
                
                # 对每张表
                for table_j_id in self.table_pool.values():
                    table_j_unique_id = self._get_table_unique_id("", table_j_id)
                    
                    # 初始化分数
                    if table_j_unique_id not in new_scores:
                        new_scores[table_j_unique_id] = 0.0
                    
                    # α(q_i, table_j) - 问题-表相似度
                    alpha = similarities.get(table_j_unique_id, 0.0)

                    # 寻找当前表 j 与上一轮保留的表 k 之间的【最大】连通性
                    max_beta = 0.1  # 默认给个基础底分
                    # 对前一轮的每张表
                    for table_k_id in current_tables.keys():
                        beta = self._compute_table_relationship_score(table_k_id, table_j_unique_id)
                        if beta > max_beta:
                            max_beta = beta

                    # γ += α(q_i, table_j) · 最大的拓扑连接分
                    new_scores[table_j_unique_id] += alpha * max_beta
            
            # 平均化分数
            for table_id in new_scores:
                new_scores[table_id] /= len(sub_questions)
            
            # 合并前一轮的分数（加权）
            for table_id in current_tables:
                if table_id in new_scores:
                    new_scores[table_id] = 0.6 * new_scores[table_id] + 0.4 * current_tables[table_id]
                else:
                    new_scores[table_id] = current_tables[table_id]
            
            # 选择Top-K候选表
            current_tables = dict(sorted(
                new_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:self.top_k_per_round])
            
            if verbose:
                print(f"[MTR] 第{iteration+1}轮检索得到 {len(current_tables)} 个候选表")
        
        # 步骤4: 排序与选择
        if verbose:
            print(f"[MTR] 步骤4: 排序与选择 (返回Top-{top_k})...")
        
        final_results = []
        
        for rank, (table_id, score) in enumerate(sorted(
            current_tables.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]):
            # 从表池中查找表数据
            table_data = None
            for pool_key, data in self.table_pool.items():
                if self._get_table_unique_id(pool_key, data) == table_id:
                    table_data = data
                    break
            
            if table_data:
                result = {
                    "rank": rank + 1,
                    "table_id": table_id, # 表唯一id
                    "table_name": table_data.get("original_table_name", ""),
                    "columns": table_data.get("columns", []),
                    "relevance_score": float(score),
                    "retrieval_round": self.num_iterations,
                }
                final_results.append(result)
        
        if verbose:
            print(f"[MTR] 检索完成，返回 {len(final_results)} 张表\n")
        
        return final_results


def main():
    """测试MTR算法"""
    import dotenv
    dotenv.load_dotenv()
    
    # 初始化MTR检索器
    retriever = MultiTableRetriever(
        table_pool_file="../data/global_table_pool_three.json",
        num_iterations=3,
        top_k_per_round=20
    )
    
    # 测试问题
    test_questions = [
        "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?",
        "Which employee has certificates for aircrafts that have the highest average flying distance?",
        "List the names of students who have registered for both Statistics and English courses.",
    ]
    
    print("=" * 100)
    print("MTR算法测试")
    print("=" * 100)
    
    for idx, question in enumerate(test_questions, 1):
        print(f"\n[问题 {idx}]")
        print(f"问题: {question[:70]}...")
        print("-" * 100)
        
        results = retriever.retrieve(question, top_k=10, verbose=True)
        
        print("检索结果:")
        for result in results:
            print(f"  {result['rank']:2d}. {result['table_id']:50s} (score: {result['relevance_score']:.4f})")
        
        print()
    
    print("=" * 100)


if __name__ == "__main__":
    main()
