"""
MTR算法测试脚本 - 从实际数据文件读取问题
"""
import sys
import json
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, '.')

from src.multi_table_retrieval import MultiTableRetriever
import dotenv

dotenv.load_dotenv()

def load_test_questions(num_questions: int = 5) -> List[Dict]:
    """从QA数据中加载测试问题"""
    test_questions = []
    
    qa_file = Path("data/QA_SQL_three_table.json")
    if qa_file.exists():
        with open(qa_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data[:num_questions]:
                test_questions.append({
                    "id": item.get("id"),
                    "question": item.get("question"),
                    "ground_truth_tables": item.get("table_ids", [])
                })
    
    return test_questions


def evaluate_retrieval(retrieved_tables: List[Dict], ground_truth_tables: List[str]) -> Dict:
    """
    评估检索结果
    
    Args:
        retrieved_tables: 检索到的表列表
        ground_truth_tables: 真实表列表
    
    Returns:
        评估指标字典
    """
    retrieved_ids = set([t["table_id"] for t in retrieved_tables])
    ground_truth_set = set(ground_truth_tables)
    
    # 计算Recall@K
    recall_5 = len(retrieved_ids & ground_truth_set) / len(ground_truth_set) if ground_truth_set else 0
    recall_10 = len(retrieved_ids & ground_truth_set) / len(ground_truth_set) if ground_truth_set else 0
    
    # 计算Precision@K
    precision_5 = len(retrieved_ids & ground_truth_set) / len(retrieved_ids) if retrieved_ids else 0
    precision_10 = len(retrieved_ids & ground_truth_set) / len(retrieved_ids) if retrieved_ids else 0
    
    # 计算MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for rank, table in enumerate(retrieved_tables, 1):
        if table["table_id"] in ground_truth_set:
            mrr = 1.0 / rank
            break
    
    return {
        "recall_5": recall_5,
        "recall_10": recall_10,
        "precision_5": precision_5,
        "precision_10": precision_10,
        "mrr": mrr,
        "retrieved_count": len(retrieved_ids),
        "ground_truth_count": len(ground_truth_set),
        "matched_count": len(retrieved_ids & ground_truth_set)
    }


def main():
    print("[INFO] 初始化MTR检索器...")
    retriever = MultiTableRetriever(
        table_pool_file="data/global_table_pool_three.json",
        num_iterations=4,
        top_k_per_round=10
    )
    
    print("[INFO] 加载测试问题...")
    test_questions = load_test_questions(num_questions=100)
    
    print(f"[OK] 加载了 {len(test_questions)} 条测试问题\n")
    
    print("=" * 120)
    print("MTR算法测试 - 从实际数据读取")
    print("=" * 120)
    
    all_metrics = []
    
    for idx, item in enumerate(test_questions, 1):
        question_id = item["id"]
        question = item["question"]
        ground_truth_tables = item["ground_truth_tables"]
        
        print(f"\n[问题 {idx}] ID: {question_id}")
        print(f"问题: {question[:70]}{'...' if len(question) > 70 else ''}")
        print(f"真实表: {', '.join(ground_truth_tables)}")
        print("-" * 120)
        
        # 执行MTR检索
        results = retriever.retrieve(question, top_k=10, verbose=True)
        
        # 评估结果
        metrics = evaluate_retrieval(results, ground_truth_tables)
        all_metrics.append(metrics)
        
        # 打印检索结果
        print("检索结果 (Top 10):")
        for result in results:
            is_correct = "✓" if result["table_id"] in ground_truth_tables else " "
            print(f"  {result['rank']:2d}. [{is_correct}] {result['table_id']:50s} (score: {result['relevance_score']:.4f})")
        
        # 打印评估指标
        print(f"\n评估指标:")
        print(f"  Recall@5: {metrics['recall_5']:.2%}  |  Recall@10: {metrics['recall_10']:.2%}")
        print(f"  Precision@5: {metrics['precision_5']:.2%}  |  Precision@10: {metrics['precision_10']:.2%}")
        print(f"  MRR: {metrics['mrr']:.4f}")
        print()
    
    # 打印总体统计
    print("=" * 120)
    print("总体统计")
    print("=" * 120)
    
    avg_recall_5 = sum(m["recall_5"] for m in all_metrics) / len(all_metrics)
    avg_recall_10 = sum(m["recall_10"] for m in all_metrics) / len(all_metrics)
    avg_precision_5 = sum(m["precision_5"] for m in all_metrics) / len(all_metrics)
    avg_precision_10 = sum(m["precision_10"] for m in all_metrics) / len(all_metrics)
    avg_mrr = sum(m["mrr"] for m in all_metrics) / len(all_metrics)
    
    print(f"平均 Recall@5: {avg_recall_5:.2%}")
    print(f"平均 Recall@10: {avg_recall_10:.2%}")
    print(f"平均 Precision@5: {avg_precision_5:.2%}")
    print(f"平均 Precision@10: {avg_precision_10:.2%}")
    print(f"平均 MRR: {avg_mrr:.4f}")
    print("=" * 120)


if __name__ == "__main__":
    main()
