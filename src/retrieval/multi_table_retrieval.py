"""
多表检索（MTR）核心算法模块。

功能：
1. 读取全局表池并构造统一 schema 表示。
2. 计算问题与表的语义相似度。
3. 根据配置决定是否执行问题分解。
4. 根据配置决定是否执行表间传播。
5. 支持 current / paper / hybrid 等多种检索模式。
"""

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.semantic_similarity import SemanticSimilarityCalculator
from src.utils.config import Config

if TYPE_CHECKING:
    from src.retrieval.question_decomposer import QuestionDecomposer


class MultiTableRetriever:
    """
    多表检索器。

    该类负责串联整个检索流程：
    - 加载全局表池
    - 问题分解
    - 问题-表打分
    - 表间传播或 hybrid 重排
    - 输出最终 Top-K 表结果
    """

    def __init__(
        self,
        table_pool_file: str,
        decomposer: Optional["QuestionDecomposer"] = None,
        similarity_calculator: Optional[SemanticSimilarityCalculator] = None,
        num_iterations: Optional[int] = None,
        top_k_per_round: Optional[int] = None,
        use_decomposition: bool = True,
        use_propagation: bool = True,
        retrieval_mode: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        初始化MTR检索器

        Args:
            table_pool_file: 全局表池文件路径
            decomposer: 问题分解器实例
            similarity_calculator: 相似度计算器实例
            num_iterations: 迭代轮数
            top_k_per_round: 每轮保留的候选表数量
            use_decomposition: 是否使用问题分解
            use_propagation: 是否使用表间传播
        """
        print("[INFO] 初始化MTR检索器...")

        # 全局表池是检索阶段的候选空间。
        self.table_pool = self._load_table_pool(table_pool_file)
        self.table_pool_file = table_pool_file
        self.table_id_to_data = self._build_table_id_to_data_map()
        self.table_id_to_schema = self._build_table_id_to_schema_map()

        mtr_config = Config.MTR_CONFIG
        self.num_iterations = mtr_config["num_rounds"] if num_iterations is None else num_iterations
        self.top_k_per_round = mtr_config["top_k_per_round"] if top_k_per_round is None else top_k_per_round
        self.use_decomposition = use_decomposition
        self.use_propagation = use_propagation
        self.retrieval_mode = mtr_config["retrieval_mode"] if retrieval_mode is None else retrieval_mode

        if decomposer is None and self.use_decomposition:
            from src.retrieval.question_decomposer import QuestionDecomposer

            self.decomposer = QuestionDecomposer(model=model_name or Config.DECOMPOSER_CONFIG["model"])
        else:
            self.decomposer = decomposer

        if similarity_calculator is None:
            cache_namespace = (
                SemanticSimilarityCalculator.build_cache_namespace_from_pool_file(
                    table_pool_file
                )
            )
            self.similarity_calculator = SemanticSimilarityCalculator(
                cache_namespace=cache_namespace
            )
        else:
            self.similarity_calculator = similarity_calculator

        self._relationship_cache = {}
        # hybrid 模式相关超参数统一来自 Config，便于实验时集中调参。
        self.hybrid_gap12_threshold = mtr_config["hybrid_gap12_threshold"]
        self.hybrid_gap13_threshold = mtr_config["hybrid_gap13_threshold"]
        self.hybrid_rerank_alpha = mtr_config["hybrid_rerank_alpha"]
        self.hybrid_rerank_beta = mtr_config["hybrid_rerank_beta"]
        self.hybrid_expand_per_seed = mtr_config["hybrid_expand_per_seed"]

        print(f"[OK] MTR检索器初始化完成 (表池: {len(self.table_pool)} 张表, mode={self.retrieval_mode})")

    def _load_table_pool(self, pool_file: str) -> Dict:
        """加载全局表池文件。"""
        print(f"[INFO] 加载表池: {pool_file}")
        with open(pool_file, "r", encoding="utf-8") as f:
            table_pool = json.load(f)
        print(f"[OK] 加载了 {len(table_pool)} 张表")
        return table_pool

    def _convert_pool_table_to_schema(self, _pool_key: str, table_data: Dict) -> Dict:
        """把表池中的轻量表结构转换为相似度模块需要的统一 schema 格式。"""
        original_table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])
        # 当前全局表池没有精细列类型，这里统一填 unknown 占位。
        table_columns = [{"column_name": col, "column_type": "unknown"} for col in columns]
        return {
            "table_name": original_table_name,
            "table_columns": table_columns,
            "primary_key": table_data.get("primary_key"),
            "foreign_keys": table_data.get("foreign_keys", []),
            "pool_key": _pool_key,
        }

    def _get_table_unique_id(self, _pool_key: str, table_data: Dict) -> str:
        """根据表名和列名生成稳定的唯一表 id。"""
        table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])
        return f"{table_name}_[{','.join(columns)}]"

    def _build_table_id_to_data_map(self) -> Dict[str, Dict]:
        """预构建 table_id 到原始表数据的映射，避免后续频繁线性扫描表池。"""
        table_id_to_data = {}
        for pool_key, table_data in self.table_pool.items():
            table_id = self._get_table_unique_id(pool_key, table_data)
            table_id_to_data[table_id] = table_data
        return table_id_to_data

    def _build_table_id_to_schema_map(self) -> Dict[str, Dict]:
        """预构建 table_id 到统一 schema 的映射，避免重复做结构转换。"""
        table_id_to_schema = {}
        for pool_key, table_data in self.table_pool.items():
            table_id = self._get_table_unique_id(pool_key, table_data)
            table_id_to_schema[table_id] = self._convert_pool_table_to_schema(pool_key, table_data)
        return table_id_to_schema

    def _compute_question_table_similarities(self, question: str) -> Dict[str, float]:
        """
        计算问题与全局表池中所有表的相似度。
        
        Args:
            question: 问题文本
        
        Returns:
            {table_unique_id: similarity_score, ...}
        """
        similarities = {}
        for table_id, table_schema in self.table_id_to_schema.items():
            similarity = self.similarity_calculator.compute_question_table_similarity(question, table_schema)
            similarities[table_id] = similarity
        return similarities

    def _compute_table_relationship_score(self, table_id1: str, table_id2: str) -> float:
        """计算两张表之间的关系强度，并带缓存。"""
        cache_key = tuple(sorted([table_id1, table_id2]))
        if cache_key in self._relationship_cache:
            return self._relationship_cache[cache_key]

        schema1 = self.table_id_to_schema.get(table_id1)
        schema2 = self.table_id_to_schema.get(table_id2)

        if schema1 is None or schema2 is None:
            return 0.0

        score = self.similarity_calculator.compute_table_relationship_score(schema1, schema2)
        self._relationship_cache[cache_key] = score
        return score

    def _get_sub_questions(self, question: str, verbose: bool) -> List[str]:
        """根据配置决定是否对问题做拆解；若分解失败则回退到原问题。"""
        if not self.use_decomposition:
            if verbose:
                print("[MTR] 跳过问题分解，直接使用原问题")
            return [question]

        if self.decomposer is None:
            return [question]

        if verbose:
            print("[MTR] 步骤1: 问题分解...")

        sub_questions = self.decomposer.decompose(question)
        if not sub_questions:
            # 如果分解失败，直接退回原问题，保证检索流程不中断。
            sub_questions = [question]  # 如果分解失败，使用原问题
        
        if verbose:
            print(f"[MTR] 分解得到 {len(sub_questions)} 个子问题")
            for i, sq in enumerate(sub_questions, 1):
                print(f"      {i}. {sq[:60]}...")
        return sub_questions

    def _compute_aggregated_question_table_scores(self, questions: List[str]) -> Dict[str, float]:
        """聚合多个子问题的表分数，当前使用简单平均策略。"""
        table_scores = {}
        for sub_q in questions:
            similarities = self._compute_question_table_similarities(sub_q)
            for table_id, score in similarities.items():
                table_scores[table_id] = table_scores.get(table_id, 0.0) + score
        for table_id in table_scores:
            table_scores[table_id] /= len(questions)
        return table_scores

    def _get_table_data_by_id(self, table_id: str):
        """根据唯一表 id 从缓存映射中取回原始表结构。"""
        return self.table_id_to_data.get(table_id)

    def _format_final_results(self, table_scores: Dict[str, float], top_k: int, retrieval_round: int, verbose: bool) -> List[Dict]:
        """把最终排序结果整理成统一输出结构。"""
        final_results = []
        ranked = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        for rank, (table_id, score) in enumerate(ranked, start=1):
            table_data = self._get_table_data_by_id(table_id)
            if table_data:
                final_results.append(
                    {
                        "rank": rank,
                        "table_id": table_id,
                        "table_name": table_data.get("original_table_name", ""),
                        "columns": table_data.get("columns", []),
                        "relevance_score": float(score),
                        "retrieval_round": retrieval_round,
                    }
                )
        if verbose:
            print(f"[MTR] 检索完成，返回 {len(final_results)} 张表\n")
        return final_results

    # 改进版
    def _retrieve_current_mode(self, question: str, top_k: int, verbose: bool) -> List[Dict]:
        """E3: 当前主检索模式：问题分解 + 首轮语义排序 + 可选表间传播。"""
        # 问题分解
        sub_questions = self._get_sub_questions(question, verbose)
        if verbose:
            print("[MTR] 步骤2: 第一轮检索 (问题-表相似度)...")

        # 1. 计算问题-表相似度：将每张表在所有子问题上的得分做平均。
        table_scores = self._compute_aggregated_question_table_scores(sub_questions)
        # 选择 Top-K 候选表，作为后续传播的种子集合。
        current_tables = dict(sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[: self.top_k_per_round])
        if verbose:
            print(f"[MTR] 第一轮检索得到 {len(current_tables)} 个候选表")

        # 2. MTR 表间传播。
        if self.use_propagation and self.num_iterations > 1:
            for iteration in range(1, self.num_iterations):
                if verbose:
                    print(f"[MTR] 步骤3.{iteration}: 第{iteration + 1}轮检索 (表-表关系)...")
                new_scores = {}
                # 对每个子问题
                for sub_q in sub_questions:
                    similarities = self._compute_question_table_similarities(sub_q)
                    # 对每个候选池的表
                    for table_j_data in self.table_pool.values():
                        table_j_id = self._get_table_unique_id("", table_j_data)
                        new_scores.setdefault(table_j_id, 0.0) # 初始化分数
                        alpha = similarities.get(table_j_id, 0.0)  # α(q_i, table_j) - 问题-表相似度
                        max_beta = 0.1 # β(表,表), 基础底分0.1
                        # 对上一轮每个表
                        for table_k_id in current_tables.keys():
                            # 寻找当前表 j 与上一轮保留的表 k 之间的【最大】连通性
                            beta = self._compute_table_relationship_score(table_k_id, table_j_id)
                            if beta > max_beta:
                                max_beta = beta # 只取最强连接, 不累加得分
                        new_scores[table_j_id] += alpha * max_beta # γ += α(问题,表)*β(表-表)
                for table_id in new_scores:
                    new_scores[table_id] /= len(sub_questions)

                # 合并前一轮的分数（加权）, 不完全信新一轮传播, 保留第一轮语义排序的一部分稳定性
                for table_id in current_tables:
                    if table_id in new_scores:
                        new_scores[table_id] = 0.8 * new_scores[table_id] + 0.2 * current_tables[table_id]
                    else:
                        new_scores[table_id] = current_tables[table_id]
                current_tables = dict(sorted(new_scores.items(), key=lambda x: x[1], reverse=True)[: self.top_k_per_round])
                if verbose:
                    print(f"[MTR] 第{iteration + 1}轮检索得到 {len(current_tables)} 个候选表")
        else:
            if verbose:
                print("[MTR] 跳过表间传播，使用第一轮语义检索结果作为最终候选")

        return self._format_final_results(current_tables, top_k, self.num_iterations if self.use_propagation else 1, verbose)

    # 论文伪代码版本
    def _retrieve_paper_mode(self, question: str, top_k: int, verbose: bool) -> List[Dict]:
        """E3_PAPER: 更贴近论文伪代码的检索逻辑实现。"""
        if verbose:
            print("[MTR-paper] 使用更贴近论文伪代码的检索逻辑")

        # 论文的算法中第一轮候选表只采用q0
        q0 = question
        sub_questions = self._get_sub_questions(question, verbose) if self.use_decomposition else [question]
        gamma = self._compute_question_table_similarities(q0)
        
        # 这里保留过往尝试过的“对子问题求平均再排序”的实现，便于实验回溯。
        # table_scores = {}
        # for sub_q in sub_questions:
        #     similarities = self._compute_question_table_similarities(sub_q)
        #     for table_id, score in similarities.items():
        #         table_scores[table_id] = table_scores.get(table_id, 0.0) + score
        # for table_id in table_scores:
        #     table_scores[table_id] /= len(sub_questions)

        # gamma = table_scores

        current_tables = dict(sorted(gamma.items(), key=lambda x: x[1], reverse=True)[: self.top_k_per_round])

        if verbose:
            print(f"[MTR-paper] First round 得到 {len(current_tables)} 个候选表")

        if self.use_propagation and self.use_decomposition and sub_questions:
            # 每个子问题
            for iteration_idx, sub_q in enumerate(sub_questions, start=1):
                if verbose:
                    print(f"[MTR-paper] 第 {iteration_idx + 1} 轮，用子问题传播: {sub_q[:60]}...")
                alpha_scores = self._compute_question_table_similarities(sub_q)
                new_gamma = dict(gamma)
                # 遍历全局候选池中的每张表，尝试累加传播贡献。
                for table_j_data in self.table_pool.values():
                    table_j_id = self._get_table_unique_id("", table_j_data)
                    alpha = alpha_scores.get(table_j_id, 0.0)
                    # 上一轮每一个表
                    for table_k_id in current_tables.keys():
                        beta = self._compute_table_relationship_score(table_k_id, table_j_id)
                        new_gamma[table_j_id] = new_gamma.get(table_j_id, 0.0) + alpha * beta
                gamma = new_gamma
                current_tables = dict(sorted(gamma.items(), key=lambda x: x[1], reverse=True)[: self.top_k_per_round])
                if verbose:
                    print(f"[MTR-paper] 当前候选表数: {len(current_tables)}")
        else:
            if verbose:
                print("[MTR-paper] 跳过传播，仅使用 first-round 结果")

        retrieval_round = 1 + len(sub_questions) if (self.use_propagation and self.use_decomposition) else 1
        return self._format_final_results(current_tables, top_k, retrieval_round, verbose)

    def _retrieve_hybrid_uncertainty_mode(self, question: str, top_k: int, verbose: bool) -> List[Dict]:
        """E4: Hybrid 模式一：根据 top 分数差距判断是否需要启用传播。"""
        baseline_scores = self._compute_aggregated_question_table_scores([question])
        ranked_scores = sorted(baseline_scores.items(), key=lambda x: x[1], reverse=True)
        top_scores = [score for _, score in ranked_scores[:3]]

        should_propagate = False
        if len(top_scores) >= 3:
            gap12 = top_scores[0] - top_scores[1]
            gap13 = top_scores[0] - top_scores[2]
            # 如果 top1 与后续候选过于接近，说明首轮语义排序不够确定，可以尝试传播增强。
            should_propagate = gap12 <= self.hybrid_gap12_threshold or gap13 <= self.hybrid_gap13_threshold
            if verbose:
                print(
                    f"[MTR-hybrid-uncertainty] top1-top2={gap12:.4f}, top1-top3={gap13:.4f}, "
                    f"thresholds=({self.hybrid_gap12_threshold:.4f}, {self.hybrid_gap13_threshold:.4f})"
                )
        if not should_propagate:
            if verbose:
                print("[MTR-hybrid-uncertainty] 保持纯语义检索")
            original_use_decomposition = self.use_decomposition
            original_use_propagation = self.use_propagation
            self.use_decomposition = False
            self.use_propagation = False
            try:
                return self._retrieve_current_mode(question, top_k, verbose)
            finally:
                self.use_decomposition = original_use_decomposition
                self.use_propagation = original_use_propagation

        if verbose:
            print("[MTR-hybrid-uncertainty] 启用分解与传播")
        return self._retrieve_current_mode(question, top_k, verbose)

    def _retrieve_hybrid_local_mode(self, question: str, top_k: int, verbose: bool) -> List[Dict]:
        """E5: Hybrid 模式二：先做 E1 种子检索，再局部扩展并在候选池内传播重排。"""
        if verbose:
            print("[MTR-hybrid-local] 使用 E1 种子候选 + 局部扩展 + propagation rerank")

        baseline_scores = self._compute_aggregated_question_table_scores([question])
        seed_tables = dict(sorted(baseline_scores.items(), key=lambda x: x[1], reverse=True)[: self.top_k_per_round])

        expanded_tables = dict(seed_tables)
        for seed_table_id in seed_tables:
            neighbor_scores = []
            for candidate_table_id in baseline_scores:
                if candidate_table_id in expanded_tables:
                    continue
                rel_score = self._compute_table_relationship_score(seed_table_id, candidate_table_id)
                # 只把关系足够强的邻居表纳入扩展集合，避免候选池膨胀过快。
                if rel_score > 0.1:
                    combined_score = 0.7 * baseline_scores[candidate_table_id] + 0.3 * rel_score
                    neighbor_scores.append((candidate_table_id, combined_score))
            for neighbor_table_id, neighbor_score in sorted(neighbor_scores, key=lambda x: x[1], reverse=True)[: self.hybrid_expand_per_seed]:
                if neighbor_table_id not in expanded_tables:
                    expanded_tables[neighbor_table_id] = baseline_scores[neighbor_table_id]

        candidate_tables = dict(sorted(expanded_tables.items(), key=lambda x: x[1], reverse=True)[: self.top_k_per_round + self.hybrid_expand_per_seed])

        if verbose:
            print(f"[MTR-hybrid-local] E1 种子表数: {len(seed_tables)}，局部扩展后候选表数: {len(candidate_tables)}")

        sub_questions = self.decomposer.decompose(question) if self.use_decomposition else [question]
        if not sub_questions:
            sub_questions = [question]

        rerank_scores = dict(candidate_tables)
        if self.use_propagation and self.num_iterations > 1:
            for iteration in range(1, self.num_iterations):
                if verbose:
                    print(f"[MTR-hybrid-local] 第{iteration + 1}轮局部扩展池内传播重排")
                propagated_scores = {table_id: 0.0 for table_id in candidate_tables}
                for sub_q in sub_questions:
                    similarities = self._compute_question_table_similarities(sub_q)
                    for table_j_id in candidate_tables:
                        alpha = similarities.get(table_j_id, 0.0)
                        max_beta = 0.1
                        for table_k_id in rerank_scores:
                            beta = self._compute_table_relationship_score(table_k_id, table_j_id)
                            if beta > max_beta:
                                max_beta = beta
                        propagated_scores[table_j_id] += alpha * max_beta
                for table_id in propagated_scores:
                    propagated_scores[table_id] /= len(sub_questions)
                    # 重排时保留候选表原始语义得分，同时注入传播增益。
                    propagated_scores[table_id] = (
                        self.hybrid_rerank_alpha * candidate_tables[table_id]
                        + self.hybrid_rerank_beta * propagated_scores[table_id]
                    )
                rerank_scores = dict(sorted(propagated_scores.items(), key=lambda x: x[1], reverse=True)[: len(candidate_tables)])
        else:
            if verbose:
                print("[MTR-hybrid-local] 跳过传播，直接返回局部扩展候选")

        retrieval_round = self.num_iterations if (self.use_propagation and self.num_iterations > 1) else 1
        return self._format_final_results(rerank_scores, top_k, retrieval_round, verbose)

    def retrieve(self, question: str, top_k: int = 5, verbose: bool = False) -> List[Dict]:
        """统一检索入口，根据 retrieval_mode 分发到不同策略实现。"""
        if verbose:
            print(f"\n[MTR] 开始检索问题: {question[:60]}...")
        if self.retrieval_mode == "paper":
            return self._retrieve_paper_mode(question, top_k, verbose)
        if self.retrieval_mode == "hybrid_uncertainty":
            return self._retrieve_hybrid_uncertainty_mode(question, top_k, verbose)
        if self.retrieval_mode == "hybrid_local":
            return self._retrieve_hybrid_local_mode(question, top_k, verbose)
        return self._retrieve_current_mode(question, top_k, verbose)


def main():
    """单文件测试入口。"""
    import dotenv
    dotenv.load_dotenv()

    retriever = MultiTableRetriever(
        table_pool_file=Config.GLOBAL_TABLE_POOL_THREE_FILE,
        num_iterations=Config.MTR_CONFIG["num_rounds"],
        top_k_per_round=Config.MTR_CONFIG["top_k_per_round"],
    )

    test_questions = [
        "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?",
        "Which employee has certificates for aircrafts that have the highest average flying distance?",
        "List the names of students who have registered for both Statistics and English courses.",
    ]

    for question in test_questions:
        retriever.retrieve(question, top_k=Config.MTR_CONFIG["top_k_per_round"], verbose=True)


if __name__ == "__main__":
    main()
