"""
构建全局表池数据。

功能：
1. 读取原始多表样本文件。
2. 将每条样本中的表结构抽取出来。
3. 按“表名 + 列名集合”构造稳定的唯一表 id。
4. 去重后保存为全局表池，供检索阶段复用。

说明：
- 当前主键/外键信息来自原始样本中的字段抽取。
- 如果同一张表在不同样本中重复出现，会合并其外键信息。
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config


def process_and_save_table_pool(input_file, output_file):
    """从原始样本文件中提取全局唯一表池并保存到本地。"""
    input_path = Path(input_file)
    output_path = Path(output_file)

    print(f"\n================ 开始处理: {input_path} ================")
    if not input_path.exists():
        print(f"找不到文件: {input_path}，请检查路径。")
        return

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # local_pool 的键是唯一表 id，值是该表的结构信息。
    local_pool = {}

    for item in data:
        table_names = item.get("table_names", [])
        tables_data = item.get("tables", [])
        pks = item.get("primary_keys", [])
        fks = item.get("foreign_keys", [])

        for i, table_name in enumerate(table_names):
            # 防御性处理：若 table_names 与 tables 数量不一致，则跳过越界项。
            if i >= len(tables_data):
                continue

            columns = tables_data[i].get("table_columns", [])
            # 只保留当前表真实包含的外键列，避免把其它表的列误加进来。
            table_fks = [fk for fk in fks if fk in columns]
            unique_table_id = make_unique_table_id(table_name, columns)

            if unique_table_id not in local_pool:
                pk = pks[i] if i < len(pks) else None
                local_pool[unique_table_id] = {
                    "original_table_name": table_name,
                    "primary_key": pk,
                    "foreign_keys": sorted(set(table_fks)),
                    "columns": columns,
                }
            else:
                # 同一张表可能在不同样本里反复出现，这里把外键信息做并集。
                existing_fks = local_pool[unique_table_id].get("foreign_keys", [])
                local_pool[unique_table_id]["foreign_keys"] = sorted(set(existing_fks + table_fks))

    print(f"处理完毕！从该文件中提取到 {len(local_pool)} 张独立表格。")
    print(f"正在保存到本地: {output_path} ...")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(local_pool, f, ensure_ascii=False, indent=4)

    print("保存成功！独立文件已生成。")


def make_unique_table_id(table_name: str, columns) -> str:
    """根据表名和列名生成稳定的唯一表 id。"""
    return f"{table_name}_[{','.join(columns)}]"


def check_table_pool_integrity(file_path):
    """打印表池中的若干样例，便于人工检查主键和外键抽取结果。"""
    path = Path(file_path)
    print(f"\n================ 检测: {path} ================")
    if not path.exists():
        print(f"找不到文件: {path}，请检查路径。")
        return

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 仅抽样打印前几项，避免大文件输出过长。
    sample_keys = list(data.keys())[:5]
    for key in sample_keys:
        print(f"{key} -> PK={data[key].get('primary_key')}, FKs={data[key].get('foreign_keys')}")


def main():
    """按配置中的任务列表依次构建二表和三表全局表池。"""
    for input_file, output_file in Config.get_table_pool_tasks():
        process_and_save_table_pool(input_file, output_file)
        check_table_pool_integrity(output_file)


if __name__ == "__main__":
    main()
