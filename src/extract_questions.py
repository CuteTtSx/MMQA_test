"""
提取问题数据模块
从Synthesized_three_table.json和Synthesized_two_table.json中提取问题，
分别保存到对应的JSON文件中，保持原始顺序。
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
def extract_questions_from_file(input_file: str, output_file: str) -> Dict[str, Any]:
    """
    从原始数据文件中提取问题信息
    
    Args:
        input_file: 输入的原始数据文件路径
        output_file: 输出的问题文件路径
    
    Returns:
        提取统计信息字典
    """
    print(f"开始从 {input_file} 提取问题...")
    
    try:
        # 读取原始数据
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"[ERROR] 数据格式错误：期望列表，得到 {type(data)}")
            return {"status": "error", "message": "数据格式错误"}
        
        questions = []
        
        # 提取每条问题的信息
        for item in data:
            # 先生成每个表的唯一id, 以便后续验证
            unique_table_ids = []
            table_names = item.get("table_names", [])
            tables_data = item.get('tables', [])
            for i, t_name in enumerate(table_names):
                columns = tables_data[i].get('table_columns', [])
                columns_str = ",".join(columns)
                unique_table_id = f"{t_name}_[{columns_str}]"
                unique_table_ids.append(unique_table_id)

            question_info = {
                "id": item.get("id_"),
                "question": item.get("Question"),
                "sql": item.get("SQL"),
                "table_ids": unique_table_ids, 
                "table_names": table_names,
                "ans": item.get("answer"),
            }
            questions.append(question_info)
        
        # 保存到输出文件
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] 成功提取 {len(questions)} 条问题到 {output_file}")
        
        return {
            "status": "success",
            "input_file": input_file,
            "output_file": output_file,
            "total_questions": len(questions),
        }
    
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {input_file}")
        return {"status": "error", "message": f"文件不存在: {input_file}"}
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON解析错误: {e}")
        return {"status": "error", "message": f"JSON解析错误: {e}"}
    except Exception as e:
        print(f"[ERROR] 提取过程出错: {e}")
        return {"status": "error", "message": str(e)}
        
def main():
    """主函数：提取两个数据文件的问题"""
    
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
    # 定义输入输出文件对
    file_pairs = [
        (
            str(data_dir / "Synthesized_three_table.json"),
            str(data_dir / "QA_SQL_three_table.json")
        ),
        (
            str(data_dir / "Synthesized_two_table.json"),
            str(data_dir / "QA_SQL_two_table.json")
        )
    ]
    
    print("=" * 60)
    print("开始提取问题数据")
    print("=" * 60)
    
    results = []
    total_questions = 0
    
    for input_file, output_file in file_pairs:
        result = extract_questions_from_file(input_file, output_file)
        results.append(result)
        
        if result["status"] == "success":
            total_questions += result["total_questions"]
    
    # 打印总结
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
