import json
import os


def process_and_save_table_pool(input_file, output_file):
    print(f"\n================ 开始处理: {input_file} ================")
    if not os.path.exists(input_file):
        print(f"⚠️ 找不到文件: {input_file}，请检查路径。")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 针对当前文件，创建一个独立的本地字典
    local_pool = {}

    # 遍历每一条问答数据
    for item in data:
        table_names = item.get('table_names', [])
        tables_data = item.get('tables', [])
        pks = item.get('primary_keys', [])
        fks = item.get('foreign_keys', [])

        # 遍历当前问题用到的每一张表
        for i, t_name in enumerate(table_names):
            if i >= len(tables_data):
                continue

            columns = tables_data[i].get('table_columns', [])

            # 找出真正属于这张表的外键
            table_fks = [fk for fk in fks if fk in columns]

            # 【修复核心】：生成唯一指纹，格式如 "department_[Department_ID,Ranking...]"
            # 即使表名相同，只要列结构不同，就会被识别为两张不同的表
            columns_str = ",".join(columns)
            unique_table_id = f"{t_name}_[{columns_str}]"

            # 如果这张具有特定结构的表还没被加进当前库
            if unique_table_id not in local_pool:
                pk = pks[i] if i < len(pks) else None
                local_pool[unique_table_id] = {
                    "original_table_name": t_name,  # 保留原始表名，供后续大模型生成 SQL 时使用
                    "primary_key": pk,
                    "foreign_keys": list(set(table_fks)),
                    "columns": columns,
                    "content": tables_data[i].get('table_content', [])
                }
            else:
                # 补充新外键（针对真正的同一张表）
                existing_fks = local_pool[unique_table_id].get("foreign_keys", [])
                local_pool[unique_table_id]["foreign_keys"] = list(set(existing_fks + table_fks))

    print(f"✅ 处理完毕！从该文件中提取到 {len(local_pool)} 张独立表格。")

    # 将当前文件的结果保存为独立的 JSON 文件
    print(f"正在保存到本地: {output_file} ...")

    # 确保保存的目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(local_pool, f, ensure_ascii=False, indent=4)

    print(f"🎉 保存成功！独立文件已生成。")

def check_table_pool_integrity(file_path):
    print(f"\n================ 检测: {file_path} ================")
    if not os.path.exists(file_path):
        print(f"⚠️ 找不到文件: {file_path}，请检查路径。")
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 随便抽查一张表看看l


if __name__ == "__main__":
    # 定义输入文件和对应输出文件的映射关系
    file_tasks = [
        {
            "input": "./data/Synthesized_three_table.json",
            "output": "./data/global_table_pool_three.json"
        },
        {
            "input": "./data/Synthesized_two_table.json",
            "output": "./data/global_table_pool_two.json"
        }
    ]

    # 循环执行任务，互不干扰
    for task in file_tasks:
        process_and_save_table_pool(task["input"], task["output"])