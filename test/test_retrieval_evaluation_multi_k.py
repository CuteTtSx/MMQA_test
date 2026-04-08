"""
多top_k_per_round评估测试脚本

流程：
1. 加载问题数据
2. 分别用 top_k_per_round=2, 5, 10 初始化MTR检索器
3. 都返回 top_k=3 的表
4. 用V2评估器独立评估每个配置
5. 对比不同top_k_per_round的性能
"""
import sys
import json
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, '.')

from src.multi_table_retrieval import MultiTableRetriever
from src.retrieval_evaluator_v2 import RetrievalEvaluatorV2
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
    print("[INFO] 加载QA数据...")
    qa_data = load_qa_data("data/QA_SQL_three_table.json", num_questions=721)
    print(f"[OK] 加载了 {len(qa_data)} 条问题\n")
    
    # 测试不同的top_k_per_round值
    top_k_per_round_values = [2, 3, 5, 10]
    final_top_k = 3  # 最终返回的表数量
    all_reports = {}
    
    for top_k_per_round in top_k_per_round_values:
        print("=" * 120)
        print(f"初始化MTR检索器 (top_k_per_round={top_k_per_round}, 最终返回top_k={final_top_k})")
        print("=" * 120)
        
        retriever = MultiTableRetriever(
            table_pool_file="data/global_table_pool_three.json",
            num_iterations=4,
            top_k_per_round=top_k_per_round
        )
        
        print(f"[INFO] 执行MTR检索...")
        
        evaluator = RetrievalEvaluatorV2()
        evaluation_results = []
        
        for idx, item in enumerate(qa_data, 1):
            question_id = item.get("id")
            question = item.get("question")
            ground_truth_tables = item.get("table_ids", [])
            
            if idx % 50 == 0:
                print(f"  [{idx}/{len(qa_data)}] 处理中...")
            
            # 执行MTR检索，最终返回top_k=3张表
            retrieved_tables = retriever.retrieve(question, top_k=final_top_k, verbose=False)
            
            # 构建评估数据
            evaluation_results.append({
                "question_id": question_id,
                "question": question,
                "ground_truth_tables": ground_truth_tables,
                "retrieved_tables": retrieved_tables
            })
        
        print(f"\n[INFO] 执行批量评估 (top_k_per_round={top_k_per_round})...")
        
        # 执行批量评估
        evaluation_report = evaluator.evaluate_batch(evaluation_results)
        all_reports[top_k_per_round] = evaluation_report
        
        # 打印报告
        evaluator.print_report(evaluation_report, verbose=False)
    
    # 对比不同top_k_per_round的性能
    print("\n" + "=" * 120)
    print(f"性能对比 - 不同top_k_per_round值 (最终返回top_k={final_top_k})")
    print("=" * 120)
    print(f"\n{'Metric':<25} {'top_k_per_round=2':<25} {'top_k_per_round=5':<25} {'top_k_per_round=10':<25}")
    print("-" * 120)
    
    metrics_to_compare = ['recall', 'precision', 'f1', 'mrr', 'map_k']
    
    for metric in metrics_to_compare:
        values = []
        for top_k_per_round in top_k_per_round_values:
            value = all_reports[top_k_per_round]['average_metrics'][metric]
            values.append(f"{value:.4f}")
        
        print(f"{metric:<25} {values[0]:<25} {values[1]:<25} {values[2]:<25}")
    
    # 保存对比报告
    comparison_report = {
        "total_questions": len(qa_data),
        "final_top_k": final_top_k,
        "top_k_per_round_values": top_k_per_round_values,
        "reports": all_reports
    }
    
    output_file = "./data/retrieval_evaluation_top_k_per_round_report.json"
    evaluator.save_report(comparison_report, output_file)
    
    print("\n" + "=" * 120)
    print(f"[OK] 多top_k_per_round评估完成，报告已保存到: {output_file}")
    print("=" * 120)


if __name__ == "__main__":
    main()
