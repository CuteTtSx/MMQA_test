"""
优化的问题分解器模块

功能：
1. 将多跳问题分解为子问题
2. 包含few-shot示例提高分解质量
3. 实现错误处理和重试机制
4. 支持缓存和批量处理
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import dotenv

# 定义输出结构
class SubQuestions(BaseModel):
    sub_questions: List[str] = Field(..., description="拆解后的一系列子问题列表")


# Few-shot示例
FEW_SHOT_EXAMPLES = [
    {
        "question": "What are the names of heads serving as temporary acting heads in departments with rankings better than 5?",
        "sub_questions": [
            "Which departments have rankings better than 5?",
            "Who are the temporary acting heads in these departments?",
            "What are the names of these heads?"
        ]
    },
    {
        "question": "Which employee has certificates for aircrafts that have the highest average flying distance, and what is this average flying distance?",
        "sub_questions": [
            "For each employee, calculate the average flying distance of aircrafts they are certified for",
            "Which employee has the highest average flying distance?",
            "What is this average flying distance value?"
        ]
    },
    {
        "question": "List the names of students who have registered for both Statistics and English courses.",
        "sub_questions": [
            "Which students are registered for Statistics course?",
            "Which students are registered for English course?",
            "Which students appear in both lists?"
        ]
    },
    {
        "question": "What country did the student John live in?",
        "sub_questions": [
            "Find the address information for student John",
            "What country is this address located in?"
        ]
    },
    {
        "question": "Who are the employees with salary above 200,000 certified to operate aircrafts having distance greater than 6000 miles?",
        "sub_questions": [
            "Which employees have salary above 200,000?",
            "Which aircrafts have distance greater than 6000 miles?",
            "Which employees are certified to operate these aircrafts?",
            "Find the intersection of these two employee sets"
        ]
    }
]


class QuestionDecomposer:
    """问题分解器类"""
    
    def __init__(self, model: str, temperature: float = 0.0, 
                 max_retries: int = 3, cache_dir: Optional[str] = None):
        """
        初始化分解器
        
        Args:
            model: 使用的模型名称
            temperature: 温度参数（0表示确定性）
            max_retries: 最大重试次数
            cache_dir: 缓存目录路径
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
        )
        
        self.parser = JsonOutputParser(pydantic_object=SubQuestions)
        self.chain = self._build_chain()
    
    def _build_chain(self):
        """构建LangChain链"""
        
        # 构建few-shot示例部分
        examples_text = self._format_examples()
        
        system_prompt = """You are an expert at multi-hop question decomposition. Your task is to decompose complex multi-hop questions into simpler sub-questions that can be answered sequentially.

Key principles:
1. Break down complex questions into 2-5 simpler sub-questions
2. Each sub-question should be answerable independently
3. The sub-questions should logically lead to answering the original question
4. Maintain the semantic meaning and intent of the original question

Please decompose the given question into sub-questions. Output ONLY valid JSON in the format: {{"sub_questions": [...]}}"""

        human_prompt = "[Question] {question}"
        
        template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        return template | self.llm | self.parser
    
    def _format_examples(self) -> str:
        """格式化few-shot示例"""
        examples_text = "[Examples]\n"
        for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Question: {example['question']}\n"
            examples_text += f"Sub-questions:\n"
            for j, sq in enumerate(example['sub_questions'], 1):
                examples_text += f"  {j}. {sq}\n"
        return examples_text
    
    def _get_cache_key(self, question: str) -> str:
        """生成缓存键"""
        return hashlib.md5(question.encode()).hexdigest()
    
    def _load_from_cache(self, question: str) -> Optional[List[str]]:
        """从缓存加载结果"""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{self._get_cache_key(question)}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('sub_questions')
            except Exception:
                return None
        return None
    
    def _save_to_cache(self, question: str, sub_questions: List[str]):
        """保存结果到缓存"""
        if not self.cache_dir:
            return
        
        cache_file = self.cache_dir / f"{self._get_cache_key(question)}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'question': question,
                    'sub_questions': sub_questions,
                    'timestamp': time.time()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save cache: {e}")
    
    def decompose(self, question: str) -> Optional[List[str]]:
        """
        分解单个问题
        
        Args:
            question: 输入问题
        
        Returns:
            子问题列表，或None（失败时）
        """
        # 检查缓存
        cached_result = self._load_from_cache(question)
        if cached_result:
            # print(f"[CACHE HIT] Loaded from cache")
            return cached_result
        
        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                result = self.chain.invoke({"question": question})
                sub_questions = result.get('sub_questions', [])
                
                # 验证结果
                if not isinstance(sub_questions, list) or len(sub_questions) == 0:
                    raise ValueError("Invalid sub_questions format")
                
                if len(sub_questions) > 5:
                    print(f"[WARNING] Too many sub-questions ({len(sub_questions)}), truncating to 5")
                    sub_questions = sub_questions[:5]
                
                # 保存到缓存
                self._save_to_cache(question, sub_questions)
                
                return sub_questions
            
            except json.JSONDecodeError as e:
                print(f"[RETRY {attempt + 1}/{self.max_retries}] JSON parsing error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                continue
            
            except Exception as e:
                print(f"[RETRY {attempt + 1}/{self.max_retries}] Error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                continue
        
        print(f"[ERROR] Failed to decompose question after {self.max_retries} attempts")
        return None
    
    def decompose_batch(self, questions: List[str], verbose: bool = False) -> Dict[str, Any]:
        """
        批量分解问题
        
        Args:
            questions: 问题列表
            verbose: 是否打印详细信息
        
        Returns:
            包含结果和统计信息的字典
        """
        results = []
        success_count = 0
        failed_count = 0
        
        for i, question in enumerate(questions, 1):
            if verbose:
                print(f"[{i}/{len(questions)}] Decomposing: {question[:60]}...")
            
            sub_questions = self.decompose(question)
            
            if sub_questions:
                results.append({
                    "question": question,
                    "sub_questions": sub_questions,
                    "status": "success"
                })
                success_count += 1
            else:
                results.append({
                    "question": question,
                    "sub_questions": None,
                    "status": "failed"
                })
                failed_count += 1
        
        return {
            "total": len(questions),
            "success": success_count,
            "failed": failed_count,
            "success_rate": success_count / len(questions) if questions else 0,
            "results": results
        }


def main():
    """主函数：测试问题分解器"""
    dotenv.load_dotenv()
    
    # 初始化分解器（启用缓存）
    decomposer = QuestionDecomposer(
        model = "gpt-4o-mini",
        cache_dir="data/decomposition_cache"
    )
    
    # 测试问题
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
            for j, sq in enumerate(sub_questions, 1):
                print(f"  {j}. {sq}")
        else:
            print("[ERROR] 分解失败")
        
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    main()
