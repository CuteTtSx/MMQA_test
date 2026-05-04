"""
提取问题数据模块。

功能：
1. 从原始 Synthesized_two_table / Synthesized_three_table 数据中提取问题级样本。
2. 为每条样本生成统一字段，包括问题、SQL、答案和关联表 id。
3. 保持原始样本顺序输出，供检索与 Text-to-SQL 共用。
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config



def make_unique_table_id(table_name: str, columns) -> str:
    """根据表名和列名生成稳定的唯一表 id。"""
    return f"{table_name}_[{','.join(columns)}]"


def extract_questions_from_file(input_file, output_file) -> Dict[str, Any]:
    """从单个原始数据文件中提取问题样本并保存为标准化 QA 文件。"""
    input_path = Path(input_file)
    output_path = Path(output_file)

    print(f"开始从 {input_path} 提取问题...")

    try:
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"[ERROR] 数据格式错误：期望列表，得到 {type(data)}")
            return {"status": "error", "message": "数据格式错误"}

        questions = []

        for item in data:
            unique_table_ids = []
            table_names = item.get("table_names", [])
            tables_data = item.get("tables", [])

            for i, table_name in enumerate(table_names):
                # 防止 table_names 与 tables 长度不一致导致越界。
                if i >= len(tables_data):
                    continue
                columns = tables_data[i].get("table_columns", [])
                unique_table_ids.append(make_unique_table_id(table_name, columns))

            # 这里输出的是项目内部统一使用的 QA 样本结构。
            questions.append(
                {
                    "id": item.get("id_"),
                    "question": item.get("Question"),
                    "sql": item.get("SQL"),
                    "table_ids": unique_table_ids,
                    "table_names": table_names,
                    "ans": item.get("answer"),
                }
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        print(f"[OK] 成功提取 {len(questions)} 条问题到 {output_path}")

        return {
            "status": "success",
            "input_file": str(input_path),
            "output_file": str(output_path),
            "total_questions": len(questions),
        }

    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {input_path}")
        return {"status": "error", "input_file": str(input_path), "message": f"文件不存在: {input_path}"}
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON解析错误: {e}")
        return {"status": "error", "input_file": str(input_path), "message": f"JSON解析错误: {e}"}
    except Exception as e:
        print(f"[ERROR] 提取过程出错: {e}")
        return {"status": "error", "input_file": str(input_path), "message": str(e)}


def main():
    """按配置依次提取二表和三表问题数据，并打印汇总信息。"""
    print("=" * 60)
    print("开始提取问题数据")
    print("=" * 60)

    results = []
    total_questions = 0

    for input_file, output_file in Config.get_question_extraction_tasks():
        result = extract_questions_from_file(input_file, output_file)
        results.append(result)

        if result["status"] == "success":
            total_questions += result["total_questions"]

    print("=" * 60)
    print("提取完成总结")
    print("=" * 60)
    for result in results:
        if result["status"] == "success":
            print(f"[OK] {result['output_file']}: {result['total_questions']} 条问题")
        else:
            print(f"[ERROR] {result.get('input_file', 'Unknown')}: {result['message']}")

    print(f"总计提取: {total_questions} 条问题")
    print("=" * 60)


if __name__ == "__main__":
    main()
