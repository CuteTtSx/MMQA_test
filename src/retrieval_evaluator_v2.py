"""
检索评估模块 V2 - 支持多K值独立评估

改进点：
1. 支持为不同的top_k值分别评估
2. 每个top_k对应一个独立的Recall/Precision计算
3. 更符合实际应用场景
4. 原版本保留为 retrieval_evaluator_v1.py
"""

import json
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class RetrievalMetricsV2:
    """检索评估指标 V2"""
    question_id: int
    question: str
    ground_truth_count: int
    top_k: int  # 实际返回的表数量
    retrieved_count: int
    matched_count: int
    
    # 基础指标（针对实际返回的top_k个表）
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
    """检索评估器 V2 - 支持多K值独立评估"""
    
    def __init__(self):
        """初始化评估器"""
        pass
    
    def evaluate_single(self, retrieved_tables: List[Dict], 
                       ground_truth_tables: Set[str],
                       question_id: int = 0,
                       question: str = "") -> RetrievalMetricsV2:
        """
        评估单个问题的检索结果
        
        Args:
            retrieved_tables: 检索到的表列表 [{"table_id": str, "relevance_score": float}, ...]
            ground_truth_tables: 真实表集合
            question_id: 问题ID
            question: 问题文本
        
        Returns:
            RetrievalMetricsV2对象
        """
        retrieved_ids = [t["table_id"] for t in retrieved_tables] # 唯一表id
        top_k = len(retrieved_ids)
        retrieved_ids_set = set(retrieved_ids)
        
        # 计算基础指标
        matched = len(retrieved_ids_set & ground_truth_tables)
        gt_count = len(ground_truth_tables) if top_k >= len(ground_truth_tables) else top_k
        
        # Recall@K
        recall = matched / gt_count if gt_count > 0 else 0.0
        
        # Precision@K
        precision = matched / top_k if top_k > 0 else 0.0
        
        # F1@K
        f1 = self._compute_f1(precision, recall)
        
        # MRR (Mean Reciprocal Rank)
        mrr = self._compute_mrr(retrieved_ids, ground_truth_tables)
        
        # MAP@K (Mean Average Precision)
        map_k = self._compute_map(retrieved_ids, ground_truth_tables)
        
        # 第一个匹配表的排名
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
            "top_k": all_metrics[0].top_k if all_metrics else 0,
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
    
    def _compute_average_metrics(self, all_metrics: List[RetrievalMetricsV2]) -> Dict:
        """计算平均指标"""
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
        """分析指标分布"""
        if not all_metrics:
            return {}
        
        # 按Recall分类
        perfect_recall = sum(1 for m in all_metrics if m.recall == 1.0)
        good_recall = sum(1 for m in all_metrics if 0.5 <= m.recall < 1.0)
        poor_recall = sum(1 for m in all_metrics if m.recall < 0.5)
        
        # 按MRR分类
        high_mrr = sum(1 for m in all_metrics if m.mrr >= 0.5)
        medium_mrr = sum(1 for m in all_metrics if 0.2 <= m.mrr < 0.5)
        low_mrr = sum(1 for m in all_metrics if m.mrr < 0.2)
        
        # 按first_match_rank分类
        rank_1 = sum(1 for m in all_metrics if m.first_match_rank == 1)
        rank_1_k = sum(1 for m in all_metrics if m.first_match_rank and 1 <= m.first_match_rank <= m.top_k)
        rank_not_found = sum(1 for m in all_metrics if m.first_match_rank is None)
        
        return {
            "recall_distribution": {
                "perfect (1.0)": perfect_recall,
                "good (0.5-1.0)": good_recall,
                "poor (<0.5)": poor_recall
            },
            "mrr_distribution": {
                "high (>=0.5)": high_mrr,
                "medium (0.2-0.5)": medium_mrr,
                "low (<0.2)": low_mrr
            },
            "first_match_rank_distribution": {
                "rank_1": rank_1,
                "rank_1_to_k": rank_1_k,
                "not_found": rank_not_found
            }
        }
    
    def print_report(self, evaluation_result: Dict, verbose: bool = True):
        """打印评估报告"""
        print("\n" + "=" * 120)
        print(f"检索评估报告 (Top-K={evaluation_result['top_k']})")
        print("=" * 120)
        
        total = evaluation_result["total_questions"]
        avg_metrics = evaluation_result["average_metrics"]
        analysis = evaluation_result["analysis"]
        
        # 打印平均指标
        print(f"\n总体统计 (共 {total} 条问题，返回Top-{evaluation_result['top_k']})")
        print("-" * 120)
        print(f"平均 Recall@{evaluation_result['top_k']:2d}:    {avg_metrics['recall']:.2%}")
        print(f"平均 Precision@{evaluation_result['top_k']:2d}: {avg_metrics['precision']:.2%}")
        print(f"平均 F1@{evaluation_result['top_k']:2d}:        {avg_metrics['f1']:.4f}")
        print(f"平均 MRR:         {avg_metrics['mrr']:.4f}")
        print(f"平均 MAP@{evaluation_result['top_k']:2d}:      {avg_metrics['map_k']:.4f}")
        print(f"平均首匹配排名:   {avg_metrics['avg_first_match_rank']:.2f}")
        
        # 打印分布分析
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
    
    def save_report(self, evaluation_result: Dict, output_file: str):
        """保存评估报告到JSON文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] 评估报告已保存到: {output_file}")
