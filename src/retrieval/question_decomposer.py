"""
问题分解器模块。

功能：
1. 将复杂的多跳问题拆解为多个可独立回答的子问题。
2. 通过 few-shot 示例约束大模型输出风格。
3. 提供缓存、重试和批量处理能力。
4. 为多表检索中的“先分解后检索”流程提供输入。

说明：
- 该模块默认依赖 OpenAI 兼容接口。
- 输出格式被约束为 JSON，字段名固定为 sub_questions。
"""

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.utils.config import Config


class SubQuestions(BaseModel):
    """定义问题分解后的标准输出结构。"""

    sub_questions: List[str] = Field(..., description="拆解后的一系列子问题列表")


# few-shot 示例用于稳定模型输出格式，并引导其按多跳推理顺序拆解问题。
FEW_SHOT_EXAMPLES = [
    {
        "question": "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?",
        "sub_questions": [
            "Which departments have rankings better than 5?",
            "Who are the temporary acting heads in these departments?",
            "What are the names of these heads?",
        ],
    },
    {
        "question": "Which employee has certificates for aircrafts that have the highest average flying distance, and what is this average flying distance?",
        "sub_questions": [
            "For each employee, calculate the average flying distance of aircrafts they are certified for",
            "Which employee has the highest average flying distance?",
            "What is this average flying distance value?",
        ],
    },
    {
        "question": "List the names of students who have registered for both Statistics and English courses.",
        "sub_questions": [
            "Which students are registered for Statistics course?",
            "Which students are registered for English course?",
            "Which students appear in both lists?",
        ],
    },
    {
        "question": "What country did the student John live in?",
        "sub_questions": [
            "Find the address information for student John",
            "What country is this address located in?",
        ],
    },
    {
        "question": "Who are the employees with salary above 200,000 certified to operate aircrafts having distance greater than 6000 miles?",
        "sub_questions": [
            "Which employees have salary above 200,000?",
            "Which aircrafts have distance greater than 6000 miles?",
            "Which employees are certified to operate these aircrafts?",
            "Find the intersection of these two employee sets",
        ],
    },
]


class QuestionDecomposer:
    """基于大模型的问题分解器。"""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None,
        cache_dir: Optional[str] = None,
    ):
        """初始化分解器，并绑定模型、重试策略和缓存目录。"""
        config = Config.DECOMPOSER_CONFIG
        self.model = model or config["model"]
        self.temperature = config["temperature"] if temperature is None else temperature
        self.max_retries = config["max_retries"] if max_retries is None else max_retries
        self.retry_delay = config["retry_delay"]

        cache_enabled = config.get("cache_enabled", True)
        resolved_cache_dir = Path(cache_dir) if cache_dir else Path(config["cache_dir"])
        self.cache_dir = resolved_cache_dir / self.model if cache_enabled else None

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
        )

        self.parser = JsonOutputParser(pydantic_object=SubQuestions)
        self.chain = self._build_chain()

    def _build_chain(self):
        """构造 LangChain 调用链：提示词 -> 模型 -> JSON 解析器。"""
        # 系统提示词
        system_prompt = """You are an expert at multi-hop question decomposition. Your task is to decompose complex multi-hop questions into simpler sub-questions that can be answered sequentially.

Key principles:
1. Break down complex questions into 2-5 simpler sub-questions
2. Each sub-question should be answerable independently
3. The sub-questions should logically lead to answering the original question
4. Maintain the semantic meaning and intent of the original question

Please decompose the given question into sub-questions. Output ONLY valid JSON in the format: {{"sub_questions": [...]}}"""

        template = ChatPromptTemplate.from_messages(
            [
                # few-shot 示例直接拼到 system prompt 中，能提高格式稳定性。
                ("system", system_prompt + "\n\n" + self._format_examples()),
                ("human", "[Question] {question}"),
            ]
        )

        return template | self.llm | self.parser

    def _format_examples(self) -> str:
        """把 few-shot 示例格式化为可拼接进提示词的文本。"""
        examples_text = "[Examples]\n"
        for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Question: {example['question']}\n"
            examples_text += "Sub-questions:\n"
            for j, sub_question in enumerate(example["sub_questions"], 1):
                examples_text += f"  {j}. {sub_question}\n"
        return examples_text

    def _get_cache_key(self, question: str) -> str:
        """为原问题生成稳定缓存键。"""
        return hashlib.md5(question.encode()).hexdigest()

    def _normalize_sub_questions(self, sub_questions) -> List[str]:
        """把模型输出或缓存输出统一清洗为字符串列表。"""
        normalized = []
        if not isinstance(sub_questions, list):
            return normalized

        for item in sub_questions:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                # 兼容历史缓存或模型偶发返回对象结构的情况。
                text = str(item.get("question") or item.get("sub_question") or item.get("text") or "").strip()
            else:
                text = str(item).strip()

            if text:
                normalized.append(text)

        return normalized

    def _load_from_cache(self, question: str) -> Optional[List[str]]:
        """尝试从本地缓存读取问题分解结果。"""
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{self._get_cache_key(question)}.json"
        if cache_file.exists():
            try:
                with cache_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    return self._normalize_sub_questions(data.get("sub_questions"))
            except Exception:
                return None
        return None

    def _save_to_cache(self, question: str, sub_questions: List[str]):
        """将分解结果写入本地缓存。"""
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{self._get_cache_key(question)}.json"
        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(
                    {
                        "question": question,
                        "sub_questions": sub_questions,
                        "timestamp": time.time(),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            print(f"[WARNING] Failed to save cache: {e}")

    def decompose(self, question: str) -> Optional[List[str]]:
        """分解单个问题；若失败则在限定次数内重试。"""
        cached_result = self._load_from_cache(question)
        if cached_result:
            return cached_result

        for attempt in range(self.max_retries):
            try:
                result = self.chain.invoke({"question": question})
                sub_questions = self._normalize_sub_questions(result.get("sub_questions", []))

                if len(sub_questions) == 0:
                    raise ValueError("Invalid sub_questions format")

                # 过长的子问题链往往会引入噪声，因此做一个上限裁剪。
                if len(sub_questions) > 5:
                    print(f"[WARNING] Too many sub-questions ({len(sub_questions)}), truncating to 5")
                    sub_questions = sub_questions[:5]

                self._save_to_cache(question, sub_questions)
                return sub_questions

            except json.JSONDecodeError as e:
                print(f"[RETRY {attempt + 1}/{self.max_retries}] JSON parsing error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))
                continue

            except Exception as e:
                print(f"[RETRY {attempt + 1}/{self.max_retries}] Error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))
                continue

        print(f"[ERROR] Failed to decompose question after {self.max_retries} attempts")
        return None

    def decompose_batch(self, questions: List[str], verbose: bool = False) -> Dict[str, Any]:
        """批量分解问题，并统计成功率。"""
        results = []
        success_count = 0
        failed_count = 0

        for i, question in enumerate(questions, 1):
            if verbose:
                print(f"[{i}/{len(questions)}] Decomposing: {question[:60]}...")

            sub_questions = self.decompose(question)

            if sub_questions:
                results.append({"question": question, "sub_questions": sub_questions, "status": "success"})
                success_count += 1
            else:
                results.append({"question": question, "sub_questions": None, "status": "failed"})
                failed_count += 1

        return {
            "total": len(questions),
            "success": success_count,
            "failed": failed_count,
            "success_rate": success_count / len(questions) if questions else 0,
            "results": results,
        }


def main():
    """简单的单文件测试入口。"""
    decomposer = QuestionDecomposer()

    test_questions = [
        "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?",
        "Which employee has certificates for aircrafts that have the highest average flying distance, and what is this average flying distance?",
        "List the names of students who have registered for both Statistics and English courses.",
    ]

    print("=" * 70)
    print("问题分解器测试")
    print("=" * 70)

    for i, question in enumerate(test_questions, 1):
        print(f"\n[问题 {i}]")
        print(f"原始问题: {question}")
        print("-" * 70)

        sub_questions = decomposer.decompose(question)

        if sub_questions:
            print("分解结果:")
            for j, sub_question in enumerate(sub_questions, 1):
                print(f"  {j}. {sub_question}")
        else:
            print("[ERROR] 分解失败")

        print()

    print("=" * 70)


if __name__ == "__main__":
    main()
