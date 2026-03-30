"""
检索评估模块

功能：
1. 评估MTR算法的检索质量
2. 计算多种评估指标（Recall、Precision、F1、MRR等）
3. 支持批量评估和详细分析
4. 生成评估报告
"""

import json
from typing import Dict, List, Tuple, Set, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class RetrievalMetrics:
    """检索评估指标"""
    question_id: int
    question: str
    ground_truth_count: int
    retrieved_count: int
    matched_count: int
    
    # 基础指标 (TOP2, TOP5, TOP10)
    recall_2: float
    recall_5: float
    recall_10: float
    precision_2: float
    precision_5: float
    precision_10: float
    f1_2: float
    f1_5: float
    f1_10: float
    
    # 排名指标
    mrr: float  # Mean Reciprocal Rank
    map_2: float  # Mean Average Precision@2
    map_10: float  # Mean Average Precision@10
    
    # 额外指标
    first_match_rank: Optional[int]  # 第一个匹配表的排名
    all_match_ranks: List[int]  # 所有匹配表的排名


class RetrievalEvaluator:
    """检索评估器"""
    
    def __init__(self):
        """初始化评估器"""
        pass
    
    def evaluate_single(self, retrieved_tables: List[Dict], 
                       ground_truth_tables: Set[str],
                       question_id: int = 0,
                       question: str = "") -> RetrievalMetrics:
        """
        评估单个问题的检索结果
        
        Args:
            retrieved_tables: 检索到的表列表 [{"table_id": str, "relevance_score": float}, ...]
            ground_truth_tables: 真实表集合
            question_id: 问题ID
            question: 问题文本
        
        Returns:
            RetrievalMetrics对象
        """
        retrieved_ids = [t["table_id"] for t in retrieved_tables]
        retrieved_ids_2 = set(retrieved_ids[:2])
        retrieved_ids_5 = set(retrieved_ids[:5])
        retrieved_ids_10 = set(retrieved_ids[:10])
        
        # 计算基础指标
        matched_2 = len(retrieved_ids_2 & ground_truth_tables)
        matched_5 = len(retrieved_ids_5 & ground_truth_tables)
        matched_10 = len(retrieved_ids_10 & ground_truth_tables)
        matched_all = len(set(retrieved_ids) & ground_truth_tables)
        
        gt_count = len(ground_truth_tables)
        
        # Recall@K
        recall_2 = matched_2 / gt_count if gt_count > 0 else 0.0
        recall_5 = matched_5 / gt_count if gt_count > 0 else 0.0
        recall_10 = matched_10 / gt_count if gt_count > 0 else 0.0
        
        # Precision@K
        precision_2 = matched_2 / 2 if len(retrieved_ids_2) > 0 else 0.0
        precision_5 = matched_5 / 5 if len(retrieved_ids_5) > 0 else 0.0
        precision_10 = matched_10 / 10 if len(retrieved_ids_10) > 0 else 0.0
        
        # F1@K
        f1_2 = self._compute_f1(precision_2, recall_2)
        f1_5 = self._compute_f1(precision_5, recall_5)
        f1_10 = self._compute_f1(precision_10, recall_10)
        
        # MRR (Mean Reciprocal Rank)
        mrr = self._compute_mrr(retrieved_ids, ground_truth_tables)
        
        # MAP@K (Mean Average Precision)
        map_2 = self._compute_map(retrieved_ids[:2], ground_truth_tables)
        map_10 = self._compute_map(retrieved_ids[:10], ground_truth_tables)
        
        # 第一个匹配表的排名
        first_match_rank = None
        all_match_ranks = []
        for rank, table_id in enumerate(retrieved_ids, 1):
            if table_id in ground_truth_tables:
                if first_match_rank is None:
                    first_match_rank = rank
                all_match_ranks.append(rank)
        
        return RetrievalMetrics(
            question_id=question_id,
            question=question,
            ground_truth_count=gt_count,
            retrieved_count=len(retrieved_ids),
            matched_count=matched_all,
            recall_2=recall_2,
            recall_5=recall_5,
            recall_10=recall_10,
            precision_2=precision_2,
            precision_5=precision_5,
            precision_10=precision_10,
            f1_2=f1_2,
            f1_5=f1_5,
            f1_10=f1_10,
            mrr=mrr,
            map_2=map_2,
            map_10=map_10,
            first_match_rank=first_match_rank,
            all_match_ranks=all_match_ranks
        )
    
    def evaluate_batch(self, results: List[Dict]) -> Dict:
        """
        批量评估检索结果
        
        Args:
            results: 检索结果列表，每个元素包含：
                {
                    "question_id": int,
                    "question": str,
                    "ground_truth_tables": List[str],
                    "retrieved_tables": List[Dict]
                }
        
        Returns:
            包含详细指标和统计信息的字典
        """
        all_metrics = []
        
        for result in results:
            question_id = result.get("question_id", 0)
            question = result.get("question", "")
            ground_truth = set(result.get("ground_truth_tables", []))
            retrieved = result.get("retrieved_tables", [])
            
            metrics = self.evaluate_single(retrieved, ground_truth, question_id, question)
            all_metrics.append(metrics)
        
        # 计算平均指标
        avg_metrics = self._compute_average_metrics(all_metrics)
        
        # 按不同维度分析
        analysis = self._analyze_metrics(all_metrics)
        
        return {
            "total_questions": len(all_metrics),
            "average_metrics": avg_metrics,
            "detailed_metrics": [asdict(m) for m in all_metrics],
            "analysis": analysis
        }
    
    def _compute_f1(self, precision: float, recall: float) -> float:
        """计算F1分数"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def _compute_mrr(self, retrieved_ids: List[str], ground_truth: Set[str]) -> float:
        """计算MRR (Mean Reciprocal Rank)"""
        for rank, table_id in enumerate(retrieved_ids, 1):
            if table_id in ground_truth:
                return 1.0 / rank
        return 0.0
    
    def _compute_map(self, retrieved_ids: List[str], ground_truth: Set[str]) -> float:
        """计算MAP@K (Mean Average Precision)"""
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
    
    def _compute_average_metrics(self, all_metrics: List[RetrievalMetrics]) -> Dict:
        """计算平均指标"""
        if not all_metrics:
            return {}
        
        return {
            "recall_2": np.mean([m.recall_2 for m in all_metrics]),
            "recall_5": np.mean([m.recall_5 for m in all_metrics]),
            "recall_10": np.mean([m.recall_10 for m in all_metrics]),
            "precision_2": np.mean([m.precision_2 for m in all_metrics]),
            "precision_5": np.mean([m.precision_5 for m in all_metrics]),
            "precision_10": np.mean([m.precision_10 for m in all_metrics]),
            "f1_2": np.mean([m.f1_2 for m in all_metrics]),
            "f1_5": np.mean([m.f1_5 for m in all_metrics]),
            "f1_10": np.mean([m.f1_10 for m in all_metrics]),
            "mrr": np.mean([m.mrr for m in all_metrics]),
            "map_2": np.mean([m.map_2 for m in all_metrics]),
            "map_10": np.mean([m.map_10 for m in all_metrics]),
            "avg_first_match_rank": np.mean([m.first_match_rank for m in all_metrics if m.first_match_rank]),
            "avg_matched_count": np.mean([m.matched_count for m in all_metrics]),
        }
    
    def _analyze_metrics(self, all_metrics: List[RetrievalMetrics]) -> Dict:
        """分析指标分布"""
        if not all_metrics:
            return {}
        
        # 按Recall@2分类
        perfect_recall_2 = sum(1 for m in all_metrics if m.recall_2 == 1.0)
        good_recall_2 = sum(1 for m in all_metrics if 0.5 <= m.recall_2 < 1.0)
        poor_recall_2 = sum(1 for m in all_metrics if m.recall_2 < 0.5)
        
        # 按Recall@5分类
        perfect_recall_5 = sum(1 for m in all_metrics if m.recall_5 == 1.0)
        good_recall_5 = sum(1 for m in all_metrics if 0.5 <= m.recall_5 < 1.0)
        poor_recall_5 = sum(1 for m in all_metrics if m.recall_5 < 0.5)
        
        # 按MRR分类
        high_mrr = sum(1 for m in all_metrics if m.mrr >= 0.5)
        medium_mrr = sum(1 for m in all_metrics if 0.2 <= m.mrr < 0.5)
        low_mrr = sum(1 for m in all_metrics if m.mrr < 0.2)
        
        # 按first_match_rank分类
        rank_1 = sum(1 for m in all_metrics if m.first_match_rank == 1)
        rank_1_2 = sum(1 for m in all_metrics if m.first_match_rank and 1 <= m.first_match_rank <= 2)
        rank_1_5 = sum(1 for m in all_metrics if m.first_match_rank and 1 <= m.first_match_rank <= 5)
        rank_1_10 = sum(1 for m in all_metrics if m.first_match_rank and 1 <= m.first_match_rank <= 10)
        rank_not_found = sum(1 for m in all_metrics if m.first_match_rank is None)
        
        return {
            "recall_2_distribution": {
                "perfect (1.0)": perfect_recall_2,
                "good (0.5-1.0)": good_recall_2,
                "poor (<0.5)": poor_recall_2
            },
            "recall_5_distribution": {
                "perfect (1.0)": perfect_recall_5,
                "good (0.5-1.0)": good_recall_5,
                "poor (<0.5)": poor_recall_5
            },
            "mrr_distribution": {
                "high (>=0.5)": high_mrr,
                "medium (0.2-0.5)": medium_mrr,
                "low (<0.2)": low_mrr
            },
            "first_match_rank_distribution": {
                "rank_1": rank_1,
                "rank_1_2": rank_1_2,
                "rank_1_5": rank_1_5,
                "rank_1_10": rank_1_10,
                "not_found": rank_not_found
            }
        }
    
    def print_report(self, evaluation_result: Dict, verbose: bool = True):
        """打印评估报告"""
        print("\n" + "=" * 120)
        print("检索评估报告")
        print("=" * 120)
        
        total = evaluation_result["total_questions"]
        avg_metrics = evaluation_result["average_metrics"]
        analysis = evaluation_result["analysis"]
        
        # 打印平均指标
        print(f"\n总体统计 (共 {total} 条问题)")
        print("-" * 120)
        print(f"平均 Recall@2:    {avg_metrics['recall_2']:.2%}  |  Precision@2: {avg_metrics['precision_2']:.2%}  |  F1@2: {avg_metrics['f1_2']:.4f}")
        print(f"平均 Recall@5:    {avg_metrics['recall_5']:.2%}  |  Precision@5: {avg_metrics['precision_5']:.2%}  |  F1@5: {avg_metrics['f1_5']:.4f}")
        print(f"平均 Recall@10:   {avg_metrics['recall_10']:.2%}  |  Precision@10:{avg_metrics['precision_10']:.2%}  |  F1@10:{avg_metrics['f1_10']:.4f}")
        print(f"平均 MRR:         {avg_metrics['mrr']:.4f}")
        print(f"平均 MAP@2:       {avg_metrics['map_2']:.4f}  |  MAP@10: {avg_metrics['map_10']:.4f}")
        print(f"平均首匹配排名:   {avg_metrics['avg_first_match_rank']:.2f}")
        
        # 打印分布分析
        print(f"\nRecall@2 分布:")
        print("-" * 120)
        for category, count in analysis["recall_2_distribution"].items():
            print(f"  {category:20s}: {count:3d} ({count/total*100:5.1f}%)")
        
        print(f"\nRecall@5 分布:")
        print("-" * 120)
        for category, count in analysis["recall_5_distribution"].items():
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
    
    def save_report(self, evaluation_result: Dict, output_file: str):
        """保存评估报告到JSON文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] 评估报告已保存到: {output_file}")
