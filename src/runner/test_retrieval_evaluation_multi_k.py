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
from pathlib import Path
from typing import Dict, List

import dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.multi_table_retrieval import MultiTableRetriever
from src.retrieval.retrieval_evaluator_v2 import RetrievalEvaluatorV2
from src.utils.config import Config

dotenv.load_dotenv()


# two-table和three-table的实验配置
TABLE_EXPERIMENT_CONFIG = {
    2: {
        "qa_file": str(Config.QA_SQL_TWO_TABLE_FILE), # QA_SQL_two_table.json
        "table_pool_file": str(Config.GLOBAL_TABLE_POOL_TWO_FILE), # Synthesized_two_table.json
        "final_top_k": 2, # 最终返回表的个数
        "top_k_per_round_values": [2, 5, 10], # 候选池大小依次2,5,10
        "default_num_questions": 872, # 样本数量
    },
    3: {
        "qa_file": str(Config.QA_SQL_THREE_TABLE_FILE), # QA_SQL_three_table.json
        "table_pool_file": str(Config.GLOBAL_TABLE_POOL_THREE_FILE), # Synthesized_three_table.json
        "final_top_k": 3, # 最终返回表的个数
        "top_k_per_round_values": [3, 5, 10], # 候选池大小依次2,5,10
        "default_num_questions": 721, # 样本数量
    },
}

# 实验配置
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
    "E4_HYBRID": {
        "use_decomposition": True,
        "use_propagation": True,
        "label": "Hybrid：不确定性门控传播",
    },
    "E5_HYBRID_LOCAL": {
        "use_decomposition": True,
        "use_propagation": True,
        "label": "Hybrid：局部扩展 + 重排",
    },
}

# 传参
def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate retrieval experiments E1/E2/E3")
    parser.add_argument("--table_num", type=int, choices=[2, 3], default=3, help="2 表实验或 3 表实验")
    parser.add_argument("--experiment_type", type=str, choices=["E1", "E2", "E3", "E3_PAPER", "E4_HYBRID", "E5_HYBRID_LOCAL"], default="E3")
    parser.add_argument("--limit", type=int, default=0, help="只评估前 N 条问题，0 表示全部")
    parser.add_argument("--output_file", type=str, default="", help="输出报告路径，默认自动命名")
    parser.add_argument("--model_name", type=str, default=Config.DECOMPOSER_CONFIG["model"], help="问题分解器的模型")
    return parser.parse_args()

# 加载数据集
def load_qa_data(qa_file: str, num_questions: int = 0) -> List[Dict]:
    with open(qa_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if num_questions and num_questions > 0:
        data = data[:num_questions]
    return data


def format_metric(value: float) -> str:
    return f"{value:.4f}"

# 规定输出文件路径
def get_output_file(table_num: int, experiment_type: str, output_file: str, model_name:str) -> str:
    if output_file:
        return output_file
    suffix = "two_table" if table_num == 2 else "three_table"
    # return f"{experiment_type.lower()}_{suffix}_report.json"
    return str(Config.get_mtr_output_path(f"{experiment_type.lower()}_{suffix}_report.json", model_name=model_name))

# 
def get_cases_output_file(report_output_file: str) -> str:
    output_path = Path(report_output_file)
    return str(output_path.with_name(f"{output_path.stem}_cases.json"))

# 每一个样本的具体表命中情况
def build_case_detail(_question_id, _question, ground_truth_tables, top_k, candidate_tables, round_traces=None):
    ground_truth_set = set(ground_truth_tables)

    def mark_tables(tables):
        return [
            {
                **table,
                "is_correct": table["table_id"] in ground_truth_set,
                "match_mark": "√" if table["table_id"] in ground_truth_set else "×",
            }
            for table in tables
        ]

    marked_round_traces = []
    for trace in round_traces or []:
        marked_round_traces.append(
            {
                **trace,
                "candidate_tables": mark_tables(trace.get("candidate_tables", [])),
            }
        )

    return {
            str(top_k): {
                "top_k": top_k,
                "retrieved_count": len(candidate_tables),
                "matched_count": sum(1 for table in candidate_tables if table["table_id"] in ground_truth_set),
                "retrieved_tables": mark_tables(candidate_tables),
                "round_traces": marked_round_traces,
            }
    }

def build_retrieved_tables(question_id, question, ground_truth_tables, retrieved_tables, candidate_tables, top_k_per_round):
    ground_truth_set = set(ground_truth_tables)
    return {
        "question_id": question_id,
        "question": question,
        "ground_truth_tables": ground_truth_tables,
        "retrieved_tables": retrieved_tables,
        "matched_count": sum(1 for table in candidate_tables if table["table_id"] in ground_truth_set),
        "top_k_per_round": top_k_per_round
    }


# 程序主入口
def run_retrieval_experiment(
    table_num: int,
    experiment_type: str,
    limit: int = 0,
    output_file: str = "",
    model_name: str = ""
) -> Dict:
    # 1. 加载实验配置
    config = TABLE_EXPERIMENT_CONFIG[table_num]
    experiment_config = EXPERIMENT_TYPE_CONFIG[experiment_type]
    # 2. 初始化配置
    qa_file = config["qa_file"]
    table_pool_file = config["table_pool_file"]
    final_top_k = config["final_top_k"]
    top_k_per_round_values = config["top_k_per_round_values"]
    num_questions = limit if limit > 0 else config["default_num_questions"]
    # 3. 加载数据集
    print("[INFO] 加载QA数据...")
    qa_data = load_qa_data(qa_file, num_questions=num_questions)
    print(f"[OK] 加载了 {len(qa_data)} 条问题")
    print(
        f"[INFO] experiment_type={experiment_type} ({experiment_config['label']}), "
        f"table_num={table_num}, final_top_k={final_top_k}, "
        f"top_k_per_round_values={top_k_per_round_values}\n"
    )

    # 4. 初始化相关信息
    # 如果是三表, 就是top3, top5, top10的报告 
    all_reports = {top_k: [] for top_k in top_k_per_round_values}
    all_case_details = {str(top_k): [] for top_k in top_k_per_round_values}

    # 5. 初始化评估器: 所有检索结果, 共享一个评估器
    evaluator = RetrievalEvaluatorV2() 

    # 6. 正式开启检索
    for top_k_per_round in top_k_per_round_values:
        # 6.1 初始化检索器
        print("=" * 120)
        print(
            f"初始化检索器 ({experiment_type}, table_num={table_num}, top_k_per_round={top_k_per_round}, "
            f"final_top_k={final_top_k})"
        )
        print("=" * 120)
        # 6.1.2 检索模式
        retrieval_mode = (
            "paper" if experiment_type == "E3_PAPER"
            else "hybrid_uncertainty" if experiment_type == "E4_HYBRID"
            else "hybrid_local" if experiment_type == "E5_HYBRID_LOCAL"
            else "current"
        )
        # 6.1.3 初始化
        retriever = MultiTableRetriever(
            table_pool_file=table_pool_file,
            top_k_per_round=top_k_per_round,
            use_decomposition=experiment_config["use_decomposition"],
            use_propagation=experiment_config["use_propagation"],
            retrieval_mode=retrieval_mode,
            model_name=model_name,
        )

        # 6.2 保存每一轮的检索内容
        print("[INFO] 执行检索...")
        evaluation_results = []
        case_details = []

        # 6.3 对每一个样本进行检索
        for idx, item in enumerate(qa_data, 1):
            question_id = item.get("id")
            question = item.get("question")
            ground_truth_tables = item.get("table_ids", [])

            if idx % 50 == 0:
                print(f"  [{idx}/{len(qa_data)}] 处理中...")

            # 开始检索
            retrieved_tables, candidate_tables, round_traces = retriever.retrieve(question, top_k=final_top_k, verbose=False)

            # a. 仅保存final_top_k个需要的表
            evaluation_results.append(
                build_retrieved_tables(
                    question_id,
                    question,
                    ground_truth_tables,
                    retrieved_tables,
                    candidate_tables,
                    top_k_per_round
                )
            )
            
            # b. 保存TopK长度个候选表
            case_details.append(
                {
                    "question_id": question_id,
                    "question": question,
                    "ground_truth_tables": list(ground_truth_tables),
                    "ground_truth_count": len(ground_truth_tables),
                    "retrieval_cases": build_case_detail(
                        question_id,
                        question,
                        ground_truth_tables,
                        top_k_per_round,
                        candidate_tables,
                        round_traces,
                    )
                }
            )

        print(f"\n[INFO] 执行批量评估 (top_k_per_round={top_k_per_round})...")
        # 6.4 根据检索结果进行指标计算, 并保存
        evaluation_report = evaluator.evaluate_batch(evaluation_results) # 计算指标
        all_reports[top_k_per_round] = evaluation_report # 添加指标
        evaluator.print_report(evaluation_report, verbose=False) # 打印结果

        # 6.5 保存样例具体检索细节
        all_case_details[str(top_k_per_round)] = case_details

    # 7. 最终Top3-5-10进行一个统计打印对比
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

    # 8. 保存报告
    # 最终指标报告
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
        "top_k_per_round_values": top_k_per_round_values,
        "reports": all_reports,
    }

    # 最终案例细节报告
    cases_report = {
        "experiment_type": experiment_type,
        "experiment_label": experiment_config["label"],
        "table_num": table_num,
        "qa_file": qa_file,
        "table_pool_file": table_pool_file,
        "total_questions": len(qa_data),
        "top_k_per_round_values": top_k_per_round_values,
        "cases_top_k_note": "案例明细中的各个 Top-K 由当前实验配置下保留下来的候选池结果切片得到；仅当候选池长度足够时才会写入对应 Top-K。",
        "cases_by_top_k_per_round": all_case_details,
    }

    # 保存指标报告
    final_output_file = get_output_file(table_num, experiment_type, output_file, model_name)
    evaluator.save_report(comparison_report, final_output_file)
    # 保存样本细节报告
    cases_output_file = get_cases_output_file(final_output_file)
    evaluator.save_report(cases_report, cases_output_file)

    print("\n" + "=" * 120)
    print(f"[OK] {experiment_type} 评估完成，报告已保存到: {final_output_file}")
    print(f"[OK] 案例明细已保存到: {cases_output_file}")
    print("=" * 120)
    return comparison_report


def main():
    args = parse_args()
    run_retrieval_experiment(
        table_num=args.table_num,
        experiment_type=args.experiment_type,
        limit=args.limit,
        output_file=args.output_file,
        model_name=args.model_name
    )


if __name__ == "__main__":
    main()
