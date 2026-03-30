"""
问题分解器测试脚本 - 从实际数据文件读取问题
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, '.')

from src.question_decomposer import QuestionDecomposer
import dotenv

dotenv.load_dotenv()

def load_test_questions():
    """从数据文件中加载测试问题"""
    test_questions = []
    
    # 从三表数据中读取前5条
    three_table_file = Path("data/QA_SQL_three_table.json")
    if three_table_file.exists():
        with open(three_table_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data[:5]:
                test_questions.append({
                    "source": "three_table",
                    "id": item.get("id"),
                    "question": item.get("question")
                })
    
    # 从二表数据中读取前5条
    two_table_file = Path("data/QA_SQL_two_table.json")
    if two_table_file.exists():
        with open(two_table_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data[:5]:
                test_questions.append({
                    "source": "two_table",
                    "id": item.get("id"),
                    "question": item.get("question")
                })
    
    return test_questions


def main():
    # 初始化分解器
    decomposer = QuestionDecomposer(model="gpt-4o-mini", cache_dir="data/decomposition_cache")
    
    # 加载测试问题
    test_questions = load_test_questions()
    
    print("=" * 80)
    print("问题分解器测试 - 从实际数据文件读取")
    print("=" * 80)
    print(f"\n总共加载 {len(test_questions)} 条测试问题\n")
    
    success_count = 0
    failed_count = 0
    
    for idx, item in enumerate(test_questions, 1):
        source = item["source"]
        question_id = item["id"]
        question = item["question"]
        
        print(f"\n[{idx}] 来源: {source.upper()} | ID: {question_id}")
        print(f"问题: {question[:70]}{'...' if len(question) > 70 else ''}")
        print("-" * 80)
        
        result = decomposer.decompose(question)
        
        if result:
            print("分解结果:")
            for i, sq in enumerate(result, 1):
                print(f"  {i}. {sq}")
            success_count += 1
        else:
            print("[ERROR] 分解失败")
            failed_count += 1
        
        print()
    
    # 打印统计信息
    print("=" * 80)
    print("测试统计")
    print("=" * 80)
    print(f"总计: {len(test_questions)} 条问题")
    print(f"成功: {success_count} 条")
    print(f"失败: {failed_count} 条")
    print(f"成功率: {success_count / len(test_questions) * 100:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
