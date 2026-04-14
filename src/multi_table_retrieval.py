"""多表检索(MTR)核心算法模块。"""

import json
from typing import Dict, List, Optional

from src.question_decomposer import QuestionDecomposer
from src.semantic_similarity import SemanticSimilarityCalculator


class MultiTableRetriever:
    """多表检索器。"""

    def __init__(
        self,
        table_pool_file: str,
        decomposer: Optional[QuestionDecomposer] = None,
        similarity_calculator: Optional[SemanticSimilarityCalculator] = None,
        num_iterations: int = 2,
        top_k_per_round: int = 20,
        use_decomposition: bool = True,
        use_propagation: bool = True,
        retrieval_mode: str = "current",
        model_name : str = "gpt-4o-mini"
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

        self.table_pool = self._load_table_pool(table_pool_file)
        self.table_pool_file = table_pool_file

        if decomposer is None:
            self.decomposer = QuestionDecomposer(model=model_name, cache_dir="data/decomposition_cache")
        else:
            self.decomposer = decomposer

        if similarity_calculator is None:
            self.similarity_calculator = SemanticSimilarityCalculator(cache_dir="data/similarity_cache")
        else:
            self.similarity_calculator = similarity_calculator

        self.num_iterations = num_iterations
        self.top_k_per_round = top_k_per_round
        self.use_decomposition = use_decomposition
        self.use_propagation = use_propagation
        self.retrieval_mode = retrieval_mode
        self._relationship_cache = {}
        self.hybrid_uncertainty_top_k = 3
        self.hybrid_gap12_threshold = 0.015
        self.hybrid_gap13_threshold = 0.03

        print(f"[OK] MTR检索器初始化完成 (表池: {len(self.table_pool)} 张表, mode={self.retrieval_mode})")

    def _load_table_pool(self, pool_file: str) -> Dict:
        print(f"[INFO] 加载表池: {pool_file}")
        with open(pool_file, "r", encoding="utf-8") as f:
            table_pool = json.load(f)
        print(f"[OK] 加载了 {len(table_pool)} 张表")
        return table_pool

    def _convert_pool_table_to_schema(self, pool_key: str, table_data: Dict) -> Dict:
        original_table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])
        table_columns = [{"column_name": col, "column_type": "unknown"} for col in columns]
        return {
            "table_name": original_table_name,
            "table_columns": table_columns,
            "primary_key": table_data.get("primary_key"),
            "foreign_keys": table_data.get("foreign_keys", []),
            "pool_key": pool_key,
        }

    def _get_table_unique_id(self, pool_key: str, table_data: Dict) -> str:
        """生成表的唯一ID"""
        table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])
        return f"{table_name}_[{','.join(columns)}]"

    def _compute_question_table_similarities(self, question: str) -> Dict[str, float]:
        """
        计算问题与所有表的相似度
        
        Args:
            question: 问题文本
        
        Returns:
            {table_unique_id: similarity_score, ...}
        """
        similarities = {}
        for pool_key, table_data in self.table_pool.items():
            table_schema = self._convert_pool_table_to_schema(pool_key, table_data)
            similarity = self.similarity_calculator.compute_question_table_similarity(question, table_schema)
            table_id = self._get_table_unique_id(pool_key, table_data)
            similarities[table_id] = similarity
        return similarities

    def _compute_table_relationship_score(self, table_id1: str, table_id2: str) -> float:
        cache_key = tuple(sorted([table_id1, table_id2]))
        if cache_key in self._relationship_cache:
            return self._relationship_cache[cache_key]

        table1_data = None
        table2_data = None
        for pool_key, table_data in self.table_pool.items():
            table_id = self._get_table_unique_id(pool_key, table_data)
            if table_id == table_id1:
                table1_data = table_data
            elif table_id == table_id2:
                table2_data = table_data

        if table1_data is None or table2_data is None:
            return 0.0

        schema1 = self._convert_pool_table_to_schema("", table1_data)
        schema2 = self._convert_pool_table_to_schema("", table2_data)
        score = self.similarity_calculator.compute_table_relationship_score(schema1, schema2)
        self._relationship_cache[cache_key] = score
        return score

    def _get_sub_questions(self, question: str, verbose: bool) -> List[str]:
        if not self.use_decomposition:
            if verbose:
                print("[MTR] 跳过问题分解，直接使用原问题")
            return [question]

        if verbose:
            print("[MTR] 步骤1: 问题分解...")

        sub_questions = self.decomposer.decompose(question)
        if not sub_questions:
            sub_questions = [question]  # 如果分解失败，使用原问题
        
        if verbose:
            print(f"[MTR] 分解得到 {len(sub_questions)} 个子问题")
            for i, sq in enumerate(sub_questions, 1):
                print(f"      {i}. {sq[:60]}...")
        return sub_questions

    def _compute_aggregated_question_table_scores(self, questions: List[str]) -> Dict[str, float]:
        table_scores = {}
        for sub_q in questions:
            similarities = self._compute_question_table_similarities(sub_q)
            for table_id, score in similarities.items():
                table_scores[table_id] = table_scores.get(table_id, 0.0) + score
        for table_id in table_scores:
            table_scores[table_id] /= len(questions)
        return table_scores

    def _should_use_hybrid_propagation(self, question: str, verbose: bool) -> bool:
        semantic_scores = self._compute_aggregated_question_table_scores([question])
        ranked_scores = sorted(semantic_scores.items(), key=lambda x: x[1], reverse=True)
        top_scores = [score for _, score in ranked_scores[: self.hybrid_uncertainty_top_k]]

        if len(top_scores) < 3:
            if verbose:
                print("[MTR-hybrid] 候选表不足，退回纯语义检索")
            return False

        gap12 = top_scores[0] - top_scores[1]
        gap13 = top_scores[0] - top_scores[2]
        should_propagate = gap12 <= self.hybrid_gap12_threshold or gap13 <= self.hybrid_gap13_threshold

        if verbose:
            print(
                f"[MTR-hybrid] 纯语义不确定性: top1-top2={gap12:.4f}, top1-top3={gap13:.4f}, "
                f"thresholds=({self.hybrid_gap12_threshold:.4f}, {self.hybrid_gap13_threshold:.4f})"
            )
            print("[MTR-hybrid] 判定: 启用关系传播" if should_propagate else "[MTR-hybrid] 判定: 保持纯语义检索")

        return should_propagate

    def _get_table_data_by_id(self, table_id: str):
        for pool_key, data in self.table_pool.items():
            if self._get_table_unique_id(pool_key, data) == table_id:
                return data
        return None

    def _format_final_results(self, table_scores: Dict[str, float], top_k: int, retrieval_round: int, verbose: bool) -> List[Dict]:
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
        # 问题分解
        sub_questions = self._get_sub_questions(question, verbose)
        if verbose:
            print("[MTR] 步骤2: 第一轮检索 (问题-表相似度)...")

        # 1. 计算问题-表相似度: 计算每个表在所有子问题上的平均得分
        table_scores = self._compute_aggregated_question_table_scores(sub_questions)
        # 选择Top-K候选表
        current_tables = dict(sorted(table_scores.items(), key=lambda x: x[1], reverse=True)[: self.top_k_per_round])
        if verbose:
            print(f"[MTR] 第一轮检索得到 {len(current_tables)} 个候选表")

        # 2. MTR表间传播
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
        if verbose:
            print("[MTR-paper] 使用更贴近论文伪代码的检索逻辑")

        q0 = question
        sub_questions = self._get_sub_questions(question, verbose) if self.use_decomposition else [question]
        gamma = self._compute_question_table_similarities(q0)
        
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
            # 每一个子问题
            for iteration_idx, sub_q in enumerate(sub_questions, start=1):
                if verbose:
                    print(f"[MTR-paper] 第 {iteration_idx + 1} 轮，用子问题传播: {sub_q[:60]}...")
                alpha_scores = self._compute_question_table_similarities(sub_q)
                new_gamma = dict(gamma)
                # 候选池每一个子表
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

    def _retrieve_hybrid_mode(self, question: str, top_k: int, verbose: bool) -> List[Dict]:
        original_use_decomposition = self.use_decomposition
        original_use_propagation = self.use_propagation

        should_propagate = self._should_use_hybrid_propagation(question, verbose)
        self.use_decomposition = should_propagate
        self.use_propagation = should_propagate

        try:
            return self._retrieve_current_mode(question, top_k, verbose)
        finally:
            self.use_decomposition = original_use_decomposition
            self.use_propagation = original_use_propagation

    def retrieve(self, question: str, top_k: int = 5, verbose: bool = False) -> List[Dict]:
        if verbose:
            print(f"\n[MTR] 开始检索问题: {question[:60]}...")
        if self.retrieval_mode == "paper":
            return self._retrieve_paper_mode(question, top_k, verbose)
        if self.retrieval_mode == "hybrid":
            return self._retrieve_hybrid_mode(question, top_k, verbose)
        return self._retrieve_current_mode(question, top_k, verbose)


def main():
    import dotenv
    dotenv.load_dotenv()

    retriever = MultiTableRetriever(
        table_pool_file="../data/global_table_pool_three.json",
        num_iterations=2,
        top_k_per_round=10,
        retrieval_mode="paper",
    )

    test_questions = [
        "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?",
        "Which employee has certificates for aircrafts that have the highest average flying distance?",
        "List the names of students who have registered for both Statistics and English courses.",
    ]

    for question in test_questions:
        retriever.retrieve(question, top_k=10, verbose=True)


if __name__ == "__main__":
    main()
