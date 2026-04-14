"""
多表检索评估脚本（支持二表/三表实验与多 top_k_per_round 对比）。

用法示例：
- 二表 E1：python test/test_retrieval_evaluation_multi_k.py --table_num 2 --experiment_type E1
- 二表 E2：python test/test_retrieval_evaluation_multi_k.py --table_num 2 --experiment_type E2
- 三表 E3：python test/test_retrieval_evaluation_multi_k.py --table_num 3 --experiment_type E3

规则：
- 传 2：二表实验，final_top_k=2, top_k_per_round_values=[2,5,10]
- 传 3：三表实验，final_top_k=3, top_k_per_round_values=[3,5,10]
- E1：不分解，不传播
- E2：分解，不传播
- E3：分解，传播
"""

import argparse
import json
import sys
from typing import Dict, List

import dotenv

sys.path.insert(0, '.')

from src.multi_table_retrieval import MultiTableRetriever
from src.retrieval_evaluator_v2 import RetrievalEvaluatorV2


dotenv.load_dotenv()


TABLE_EXPERIMENT_CONFIG = {
    2: {
        "qa_file": "data/QA_SQL_two_table.json",
        "table_pool_file": "data/global_table_pool_two.json",
        "final_top_k": 2,
        "top_k_per_round_values": [2, 5, 10],
        "default_output_file": "outputs/MTR_evaluate/retrieval_evaluation_two_table_report.json",
        "default_num_questions": 841,
    },
    3: {
        "qa_file": "data/QA_SQL_three_table.json",
        "table_pool_file": "data/global_table_pool_three.json",
        "final_top_k": 3,
        "top_k_per_round_values": [3, 5, 10],
        "default_output_file": "outputs/MTR_evaluate/retrieval_evaluation_three_table_report.json",
        "default_num_questions": 721,
    },
}


EXPERIMENT_TYPE_CONFIG = {
    "E1": {
        "use_decomposition": False,
        "use_propagation": False,
        "label": "baseline 纯语义",
    },
    "E2": {
        "use_decomposition": True,
        "use_propagation": False,
        "label": "分解 + 纯语义",
    },
    "E3": {
        "use_decomposition": True,
        "use_propagation": True,
        "label": "完整 MTR",
    },
    "E3_PAPER": {
        "use_decomposition": True,
        "use_propagation": True,
        "label": "完整 MTR（paper-like）",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate retrieval experiments E1/E2/E3")
    parser.add_argument("--table_num", type=int, choices=[2, 3], default=3, help="2 表实验或 3 表实验")
    parser.add_argument("--experiment_type", type=str, choices=["E1", "E2", "E3", "E3_PAPER"], default="E3")
    parser.add_argument("--num_iterations", type=int, default=2, help="MTR 迭代轮数")
    parser.add_argument("--limit", type=int, default=0, help="只评估前 N 条问题，0 表示全部")
    parser.add_argument("--output_file", type=str, default="", help="输出报告路径，默认自动命名")
    parser.add_argument("--model_name", type=str, default="gpt-4o-mini", help="问题分解器的模型")
    return parser.parse_args()


def load_qa_data(qa_file: str, num_questions: int = 0) -> List[Dict]:
    with open(qa_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if num_questions and num_questions > 0:
        data = data[:num_questions]
    return data


def format_metric(value: float) -> str:
    return f"{value:.4f}"


def get_output_file(table_num: int, experiment_type: str, output_file: str) -> str:
    if output_file:
        return output_file
    suffix = "two_table" if table_num == 2 else "three_table"
    return f"outputs/MTR_evaluate/{experiment_type.lower()}_{suffix}_report.json"


def run_retrieval_experiment(
    table_num: int,
    experiment_type: str,
    num_iterations: int = 2,
    limit: int = 0,
    output_file: str = "",
    model_name: str = ""
) -> Dict:
    config = TABLE_EXPERIMENT_CONFIG[table_num]
    experiment_config = EXPERIMENT_TYPE_CONFIG[experiment_type]

    qa_file = config["qa_file"]
    table_pool_file = config["table_pool_file"]
    final_top_k = config["final_top_k"]
    top_k_per_round_values = config["top_k_per_round_values"]
    num_questions = limit if limit > 0 else config["default_num_questions"]

    print("[INFO] 加载QA数据...")
    qa_data = load_qa_data(qa_file, num_questions=num_questions)
    print(f"[OK] 加载了 {len(qa_data)} 条问题")
    print(
        f"[INFO] experiment_type={experiment_type} ({experiment_config['label']}), "
        f"table_num={table_num}, final_top_k={final_top_k}, "
        f"top_k_per_round_values={top_k_per_round_values}\n"
    )

    all_reports = {}
    evaluator = RetrievalEvaluatorV2()

    for top_k_per_round in top_k_per_round_values:
        print("=" * 120)
        print(
            f"初始化检索器 ({experiment_type}, table_num={table_num}, top_k_per_round={top_k_per_round}, "
            f"final_top_k={final_top_k}, num_iterations={num_iterations})"
        )
        print("=" * 120)

        retriever = MultiTableRetriever(
            table_pool_file=table_pool_file,
            num_iterations=num_iterations,
            top_k_per_round=top_k_per_round,
            use_decomposition=experiment_config["use_decomposition"],
            use_propagation=experiment_config["use_propagation"],
            retrieval_mode="paper" if experiment_type == "E3_PAPER" else "current",
            model_name = model_name
        )

        print("[INFO] 执行检索...")
        evaluation_results = []

        for idx, item in enumerate(qa_data, 1):
            question_id = item.get("id")
            question = item.get("question")
            ground_truth_tables = item.get("table_ids", [])

            if idx % 50 == 0:
                print(f"  [{idx}/{len(qa_data)}] 处理中...")

            retrieved_tables = retriever.retrieve(question, top_k=final_top_k, verbose=False)
            evaluation_results.append(
                {
                    "question_id": question_id,
                    "question": question,
                    "ground_truth_tables": ground_truth_tables,
                    "retrieved_tables": retrieved_tables,
                }
            )

        print(f"\n[INFO] 执行批量评估 (top_k_per_round={top_k_per_round})...")
        evaluation_report = evaluator.evaluate_batch(evaluation_results)
        all_reports[top_k_per_round] = evaluation_report
        evaluator.print_report(evaluation_report, verbose=False)

    print("\n" + "=" * 120)
    print(f"性能对比 - {experiment_type}, table_num={table_num}, final_top_k={final_top_k}")
    print("=" * 120)

    header = [f"top_k_per_round={value}" for value in top_k_per_round_values]
    print(f"\n{'Metric':<25} {header[0]:<25} {header[1]:<25} {header[2]:<25}")
    print("-" * 120)

    metrics_to_compare = ["recall", "precision", "f1", "mrr", "map_k"]
    for metric in metrics_to_compare:
        values = []
        for top_k_per_round in top_k_per_round_values:
            value = all_reports[top_k_per_round]["average_metrics"][metric]
            values.append(format_metric(value))
        print(f"{metric:<25} {values[0]:<25} {values[1]:<25} {values[2]:<25}")

    comparison_report = {
        "experiment_type": experiment_type,
        "experiment_label": experiment_config["label"],
        "use_decomposition": experiment_config["use_decomposition"],
        "use_propagation": experiment_config["use_propagation"],
        "table_num": table_num,
        "qa_file": qa_file,
        "table_pool_file": table_pool_file,
        "total_questions": len(qa_data),
        "final_top_k": final_top_k,
        "num_iterations": num_iterations,
        "top_k_per_round_values": top_k_per_round_values,
        "reports": all_reports,
    }

    final_output_file = get_output_file(table_num, experiment_type, output_file)
    evaluator.save_report(comparison_report, final_output_file)

    print("\n" + "=" * 120)
    print(f"[OK] {experiment_type} 评估完成，报告已保存到: {final_output_file}")
    print("=" * 120)
    return comparison_report


def main():
    args = parse_args()
    run_retrieval_experiment(
        table_num=args.table_num,
        experiment_type=args.experiment_type,
        num_iterations=args.num_iterations,
        limit=args.limit,
        output_file=args.output_file,
        model_name=args.model_name
    )


if __name__ == "__main__":
    main()
