"""
完整的检索评估测试脚本

流程：
1. 加载问题数据
2. 执行MTR检索
3. 评估检索结果
4. 生成报告
"""
import sys
import json
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, '.')

from src.multi_table_retrieval import MultiTableRetriever
from src.retrieval_evaluator import RetrievalEvaluator
import dotenv

dotenv.load_dotenv()


def load_qa_data(qa_file: str, num_questions: int = None) -> List[Dict]:
    """加载QA数据"""
    with open(qa_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if num_questions:
        data = data[:num_questions]
    
    return data


def main():
    print("[INFO] 初始化MTR检索器...")
    retriever = MultiTableRetriever(
        table_pool_file="data/global_table_pool_three.json",
        num_iterations=4,
        top_k_per_round=10
    )
    
    print("[INFO] 初始化评估器...")
    evaluator = RetrievalEvaluator()
    
    print("[INFO] 加载QA数据...")
    qa_data = load_qa_data("data/QA_SQL_three_table.json", num_questions=200)
    print(f"[OK] 加载了 {len(qa_data)} 条问题\n")
    
    print("=" * 120)
    print("执行MTR检索和评估")
    print("=" * 120)
    
    evaluation_results = []
    
    for idx, item in enumerate(qa_data, 1):
        question_id = item.get("id")
        question = item.get("question")
        ground_truth_tables = item.get("table_names", [])
        
        print(f"\n[{idx}/{len(qa_data)}] 问题 ID: {question_id}")
        print(f"问题: {question[:60]}...")
        
        # 执行MTR检索
        retrieved_tables = retriever.retrieve(question, top_k=10, verbose=False)
        
        # 构建评估数据
        evaluation_results.append({
            "question_id": question_id,
            "question": question,
            "ground_truth_tables": ground_truth_tables,
            "retrieved_tables": retrieved_tables
        })
        
        print(f"检索到 {len(retrieved_tables)} 张表")
    
    print("\n" + "=" * 120)
    print("执行批量评估...")
    print("=" * 120)
    
    # 执行批量评估
    evaluation_report = evaluator.evaluate_batch(evaluation_results)
    
    # 打印报告
    evaluator.print_report(evaluation_report, verbose=True)
    
    # 保存报告
    evaluator.save_report(evaluation_report, "./data/retrieval_evaluation_report.json")
    
    print("\n[OK] 评估完成")


if __name__ == "__main__":
    main()
