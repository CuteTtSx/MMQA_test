"""
语义相似度计算器测试脚本 - 从问题检索相关表

场景：
1. 给定一个问题
2. 从global_table_pool中加载所有可用的表
3. 计算问题与每张表的相似度
4. 排序找出最相关的表
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, '.')

from src.semantic_similarity import SemanticSimilarityCalculator
import dotenv

dotenv.load_dotenv()


def load_global_table_pool(pool_file: str) -> Dict:
    """加载全局表池"""
    print(f"[INFO] 加载全局表池: {pool_file}")
    
    with open(pool_file, 'r', encoding='utf-8') as f:
        table_pool = json.load(f)
    
    print(f"[OK] 加载了 {len(table_pool)} 张表")
    return table_pool


def convert_pool_table_to_schema(table_key: str, table_data: Dict) -> Dict:
    """
    将表池中的表转换为schema格式
    
    Args:
        table_key: 表的键（包含列信息）
        table_data: 表的数据
    
    Returns:
        标准的表schema字典
    """
    original_table_name = table_data.get("original_table_name", "")
    columns = table_data.get("columns", [])
    
    # 构建列信息
    table_columns = []
    for col_name in columns:
        table_columns.append({
            "column_name": col_name,
            "column_type": "unknown"  # 表池中没有类型信息
        })
    
    return {
        "table_name": original_table_name,
        "table_columns": table_columns,
        "pool_key": table_key  # 保留原始键用于追踪
    }


def retrieve_tables_for_question(question: str, table_pool: Dict, 
                                 calculator: SemanticSimilarityCalculator,
                                 top_k: int = 5) -> List[Tuple[str, str, float]]:
    """
    为问题检索相关的表
    
    Args:
        question: 问题文本
        table_pool: 全局表池
        calculator: 相似度计算器
        top_k: 返回前K个相关表
    
    Returns:
        [(table_name, pool_key, similarity_score), ...] 按相似度降序排列
    """
    similarities = []
    
    print(f"\n[INFO] 计算问题与 {len(table_pool)} 张表的相似度...")
    
    for idx, (pool_key, table_data) in enumerate(table_pool.items(), 1):
        if idx % 100 == 0:
            print(f"  进度: {idx}/{len(table_pool)}")
        
        # 转换为schema格式
        table_schema = convert_pool_table_to_schema(pool_key, table_data)
        """
        返回的table_schema是要计算相似度用的, 所以必须用原始的表名
        "table_name": original_table_name,
        "table_columns": table_columns,
        "pool_key": table_key  # 保留原始键用于追踪
        """
        
        # 计算相似度
        similarity = calculator.compute_question_table_similarity(question, table_schema)
        
        # 计算完相似度之后, 需要将表名转换为唯一id, 为了后续验证
        t_name = table_schema["table_name"]
        columns = table_data.get('columns', [])
        columns_str = ",".join(columns)

        unique_table_id = f"{t_name}_[{columns_str}]"

        similarities.append((unique_table_id, pool_key, similarity))
    
    # 按相似度降序排列
    similarities.sort(key=lambda x: x[2], reverse=True)
    
    return similarities[:top_k]


def main():
    # 初始化计算器
    print("[INFO] 初始化语义相似度计算器...")
    calculator = SemanticSimilarityCalculator(
        model_name="BAAI/bge-base-en-v1.5",
        use_gpu=False,
        cache_dir="data/similarity_cache"
    )
    
    # 加载全局表池
    pool_file = "data/global_table_pool_three.json"
    table_pool = load_global_table_pool(pool_file)
    
    # 加载测试问题
    print("\n[INFO] 加载测试问题...")
    test_questions = []
    
    qa_file = Path("data/QA_SQL_three_table.json")
    if qa_file.exists():
        with open(qa_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data[:3]:  # 只测试前3条
                test_questions.append({
                    "id": item.get("id"),
                    "question": item.get("question"),
                    "table_ids": item.get("table_ids", [])  # 真实答案（用于验证）, 生成唯一id后的表名
                })
    
    print(f"[OK] 加载了 {len(test_questions)} 条测试问题\n")
    
    print("=" * 100)
    print("问题-表检索测试")
    print("=" * 100)
    
    for idx, item in enumerate(test_questions, 1):
        question_id = item["id"]
        question = item["question"]
        ground_truth_tables = item["table_ids"]
        
        print(f"\n[问题 {idx}] ID: {question_id}")
        print(f"问题: {question[:70]}{'...' if len(question) > 70 else ''}")
        print(f"真实表: {', '.join(ground_truth_tables)}")
        print("-" * 100)
        
        # 检索相关表
        retrieved_tables = retrieve_tables_for_question(
            question, table_pool, calculator, top_k=10
        )
        
        print("\n检索结果 (Top 10):")
        for rank, (table_name, pool_key, score) in enumerate(retrieved_tables, 1):
            is_correct = "✓" if table_name in ground_truth_tables else " "
            print(f"  {rank:2d}. [{is_correct}] {table_name:25s} (score: {score:.4f})")
        
        # 计算Recall@5 和 Recall@10
        retrieved_5 = set([t[0] for t in retrieved_tables[:5]])
        retrieved_10 = set([t[0] for t in retrieved_tables[:10]])
        ground_truth_set = set(ground_truth_tables)
        
        recall_5 = len(retrieved_5 & ground_truth_set) / len(ground_truth_set) if ground_truth_set else 0
        recall_10 = len(retrieved_10 & ground_truth_set) / len(ground_truth_set) if ground_truth_set else 0
        
        print(f"\nRecall@5: {recall_5:.2%}  |  Recall@10: {recall_10:.2%}")
        print()
    
    # 打印缓存统计
    print("=" * 100)
    print("缓存统计")
    print("=" * 100)
    stats = calculator.get_cache_stats()
    print(f"内存缓存大小: {stats['memory_cache_size']} 条")
    print("=" * 100)


if __name__ == "__main__":
    main()
