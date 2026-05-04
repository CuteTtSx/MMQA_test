"""
检索评估模块 V2。

功能：
1. 对单个问题的检索结果进行评估。
2. 对一批问题做批量评估。
3. 支持多种常用检索指标，包括 Recall、Precision、F1、MRR、MAP。
4. 支持打印报告并保存 JSON 评估文件。

说明：
- 该版本支持不同 top_k 结果的独立评估。
- 更适合当前多轮检索、多配置对比实验的使用方式。
"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config


@dataclass
class RetrievalMetricsV2:
    """单个问题在一次检索结果下的评估指标集合。"""

    question_id: int
    question: str
    ground_truth_count: int
    top_k: int  # 实际返回的表数量
    retrieved_count: int
    matched_count: int

    # 基础指标（针对实际返回的 top_k 个表）
    recall: float  # Recall@K
    precision: float  # Precision@K
    f1: float

    # 排名指标
    mrr: float  # Mean Reciprocal Rank
    map_k: float  # Mean Average Precision@K

    # 额外指标
    first_match_rank: Optional[int]  # 第一个匹配表的排名
    all_match_ranks: List[int]  # 所有匹配表的排名


class RetrievalEvaluatorV2:
    """检索评估器 V2。"""

    def __init__(self):
        """初始化评估器。"""
        pass

    def evaluate_single(
        self,
        retrieved_tables: List[Dict],
        ground_truth_tables: Set[str],
        question_id: int = 0,
        question: str = "",
    ) -> RetrievalMetricsV2:
        """评估单个问题的检索结果。"""
        retrieved_ids = [t["table_id"] for t in retrieved_tables]  # 唯一表 id 列表
        top_k = len(retrieved_ids)
        retrieved_ids_set = set(retrieved_ids)

        # 计算基础指标。
        matched = len(retrieved_ids_set & ground_truth_tables)
        # 当实际返回数量小于真实表数量时，用较小值作为 Recall 分母，避免惩罚策略不一致。
        gt_count = len(ground_truth_tables) if top_k >= len(ground_truth_tables) else top_k

        recall = matched / gt_count if gt_count > 0 else 0.0
        precision = matched / top_k if top_k > 0 else 0.0
        f1 = self._compute_f1(precision, recall)

        mrr = self._compute_mrr(retrieved_ids, ground_truth_tables)
        map_k = self._compute_map(retrieved_ids, ground_truth_tables)

        # 记录首个命中表的排名，以及所有命中表的排名位置。
        first_match_rank = None
        all_match_ranks = []
        for rank, table_id in enumerate(retrieved_ids, 1):
            if table_id in ground_truth_tables:
                if first_match_rank is None:
                    first_match_rank = rank
                all_match_ranks.append(rank)

        return RetrievalMetricsV2(
            question_id=question_id,
            question=question,
            ground_truth_count=gt_count,
            top_k=top_k,
            retrieved_count=len(retrieved_ids),
            matched_count=matched,
            recall=recall,
            precision=precision,
            f1=f1,
            mrr=mrr,
            map_k=map_k,
            first_match_rank=first_match_rank,
            all_match_ranks=all_match_ranks,
        )

    def evaluate_batch(self, results: List[Dict]) -> Dict:
        """批量评估一组问题的检索结果。"""
        all_metrics = []

        for result in results:
            question_id = result.get("question_id", 0)
            question = result.get("question", "")
            ground_truth = set(result.get("ground_truth_tables", []))
            retrieved = result.get("retrieved_tables", [])

            metrics = self.evaluate_single(retrieved, ground_truth, question_id, question)
            all_metrics.append(metrics)

        avg_metrics = self._compute_average_metrics(all_metrics)
        analysis = self._analyze_metrics(all_metrics)

        return {
            "total_questions": len(all_metrics),
            "top_k": all_metrics[0].top_k if all_metrics else 0,
            "average_metrics": avg_metrics,
            "detailed_metrics": [asdict(m) for m in all_metrics],
            "analysis": analysis,
        }

    def _compute_f1(self, precision: float, recall: float) -> float:
        """计算 F1 分数。"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def _compute_mrr(self, retrieved_ids: List[str], ground_truth: Set[str]) -> float:
        """计算 MRR（Mean Reciprocal Rank）。"""
        for rank, table_id in enumerate(retrieved_ids, 1):
            if table_id in ground_truth:
                return 1.0 / rank
        return 0.0

    def _compute_map(self, retrieved_ids: List[str], ground_truth: Set[str]) -> float:
        """计算 MAP@K（Mean Average Precision）。"""
        if len(ground_truth) == 0:
            return 0.0

        ap = 0.0
        matched_count = 0

        for rank, table_id in enumerate(retrieved_ids, 1):
            if table_id in ground_truth:
                matched_count += 1
                precision_at_k = matched_count / rank
                ap += precision_at_k

        return ap / len(ground_truth)

    def _compute_average_metrics(self, all_metrics: List[RetrievalMetricsV2]) -> Dict:
        """对一批问题的指标取平均。"""
        if not all_metrics:
            return {}

        return {
            "recall": np.mean([m.recall for m in all_metrics]),
            "precision": np.mean([m.precision for m in all_metrics]),
            "f1": np.mean([m.f1 for m in all_metrics]),
            "mrr": np.mean([m.mrr for m in all_metrics]),
            "map_k": np.mean([m.map_k for m in all_metrics]),
            "avg_first_match_rank": np.mean([m.first_match_rank for m in all_metrics if m.first_match_rank]),
            "avg_matched_count": np.mean([m.matched_count for m in all_metrics]),
        }

    def _analyze_metrics(self, all_metrics: List[RetrievalMetricsV2]) -> Dict:
        """分析指标分布，便于快速定位检索质量区间。"""
        if not all_metrics:
            return {}

        perfect_recall = sum(1 for m in all_metrics if m.recall == 1.0)
        good_recall = sum(1 for m in all_metrics if 0.5 <= m.recall < 1.0)
        poor_recall = sum(1 for m in all_metrics if m.recall < 0.5)

        high_mrr = sum(1 for m in all_metrics if m.mrr >= 0.5)
        medium_mrr = sum(1 for m in all_metrics if 0.2 <= m.mrr < 0.5)
        low_mrr = sum(1 for m in all_metrics if m.mrr < 0.2)

        rank_1 = sum(1 for m in all_metrics if m.first_match_rank == 1)
        rank_1_k = sum(1 for m in all_metrics if m.first_match_rank and 1 <= m.first_match_rank <= m.top_k)
        rank_not_found = sum(1 for m in all_metrics if m.first_match_rank is None)

        return {
            "recall_distribution": {
                "perfect (1.0)": perfect_recall,
                "good (0.5-1.0)": good_recall,
                "poor (<0.5)": poor_recall,
            },
            "mrr_distribution": {
                "high (>=0.5)": high_mrr,
                "medium (0.2-0.5)": medium_mrr,
                "low (<0.2)": low_mrr,
            },
            "first_match_rank_distribution": {
                "rank_1": rank_1,
                "rank_1_to_k": rank_1_k,
                "not_found": rank_not_found,
            },
        }

    def print_report(self, evaluation_result: Dict, _verbose: bool = True):
        """打印评估报告。"""
        print("\n" + "=" * 120)
        print(f"检索评估报告 (Top-K={evaluation_result['top_k']})")
        print("=" * 120)

        total = evaluation_result["total_questions"]
        avg_metrics = evaluation_result["average_metrics"]
        analysis = evaluation_result["analysis"]

        print(f"\n总体统计 (共 {total} 条问题，返回Top-{evaluation_result['top_k']})")
        print("-" * 120)
        print(f"平均 Recall@{evaluation_result['top_k']:2d}:    {avg_metrics['recall']:.2%}")
        print(f"平均 Precision@{evaluation_result['top_k']:2d}: {avg_metrics['precision']:.2%}")
        print(f"平均 F1@{evaluation_result['top_k']:2d}:        {avg_metrics['f1']:.4f}")
        print(f"平均 MRR:         {avg_metrics['mrr']:.4f}")
        print(f"平均 MAP@{evaluation_result['top_k']:2d}:      {avg_metrics['map_k']:.4f}")
        print(f"平均首匹配排名:   {avg_metrics['avg_first_match_rank']:.2f}")

        print(f"\nRecall 分布:")
        print("-" * 120)
        for category, count in analysis["recall_distribution"].items():
            print(f"  {category:20s}: {count:3d} ({count/total*100:5.1f}%)")

        print(f"\nMRR 分布:")
        print("-" * 120)
        for category, count in analysis["mrr_distribution"].items():
            print(f"  {category:20s}: {count:3d} ({count/total*100:5.1f}%)")

        print(f"\n首匹配排名分布:")
        print("-" * 120)
        for category, count in analysis["first_match_rank_distribution"].items():
            print(f"  {category:20s}: {count:3d} ({count/total*100:5.1f}%)")

        print("\n" + "=" * 120)

    def save_report(self, evaluation_result: Dict, output_file: Optional[str] = None):
        """保存评估报告到 JSON 文件。"""
        if output_file is None:
            output_path = Config.get_mtr_output_path(f"retrieval_eval_top_{evaluation_result['top_k']}.json")
        else:
            output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(evaluation_result, f, indent=2, ensure_ascii=False)

        print(f"[OK] 评估报告已保存到: {output_path}")
