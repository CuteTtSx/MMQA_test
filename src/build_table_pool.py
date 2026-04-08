import json
import os
from typing import Dict, List, Optional, Set


def normalize_name(name: str) -> str:
    """归一化字段名，便于比较。"""
    if not name:
        return ""
    return name.replace("_", "").replace(" ", "").lower()


def build_normalized_column_map(columns: List[str]) -> Dict[str, str]:
    """构建 {归一化列名: 原始列名} 映射。"""
    mapping = {}
    for col in columns:
        mapping[normalize_name(col)] = col
    return mapping


def extract_primary_key(columns: List[str], raw_primary_keys: List[str]) -> Optional[str]:
    """
    从原始 primary_keys 中为当前表提取一个高置信度主键。

    注意：原始数据中的 primary_keys 不是按表顺序一一对应的，
    所以这里只能做列级匹配，避免使用错误的位置对齐逻辑。

    策略：
    1. 对列名和 raw_primary_keys 做归一化
    2. 找出当前表中命中的候选列
    3. 若只有一个候选，认为它是主键
    4. 若有多个候选，只在其中存在明显 ID 列时返回，否则返回 None
    """
    col_map = build_normalized_column_map(columns)
    raw_pk_set = {normalize_name(pk) for pk in raw_primary_keys if pk}

    candidates = []
    for norm_col, original_col in col_map.items():
        if norm_col in raw_pk_set:
            candidates.append(original_col)

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        id_like = [c for c in candidates if normalize_name(c).endswith("id") or normalize_name(c) == "id"]
        if len(id_like) == 1:
            return id_like[0]

    return None


def extract_foreign_keys(columns: List[str], raw_foreign_keys: List[str]) -> List[str]:
    """
    从原始 foreign_keys 中为当前表提取外键列。

    注意：原始 foreign_keys 也不是按表分组的，
    因此这里只做保守的列级归一化匹配。
    """
    col_map = build_normalized_column_map(columns)
    raw_fk_set = {normalize_name(fk) for fk in raw_foreign_keys if fk}

    matched = []
    for norm_col, original_col in col_map.items():
        if norm_col in raw_fk_set:
            matched.append(original_col)

    return matched


def merge_foreign_keys(existing: List[str], new_keys: List[str]) -> List[str]:
    seen = set(existing)
    merged = existing[:]
    for key in new_keys:
        if key not in seen:
            merged.append(key)
            seen.add(key)
    return merged


def process_and_save_table_pool(input_file, output_file):
    print(f"\n================ 开始处理: {input_file} ================")
    if not os.path.exists(input_file):
        print(f"⚠️ 找不到文件: {input_file}，请检查路径。")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    local_pool = {}

    for item in data:
        table_names = item.get('table_names', [])
        tables_data = item.get('tables', [])
        raw_primary_keys = item.get('primary_keys', [])
        raw_foreign_keys = item.get('foreign_keys', [])

        for i, t_name in enumerate(table_names):
            if i >= len(tables_data):
                continue

            columns = tables_data[i].get('table_columns', [])
            columns_str = ",".join(columns)
            unique_table_id = f"{t_name}_[{columns_str}]"

            pk = extract_primary_key(columns, raw_primary_keys)
            fks = extract_foreign_keys(columns, raw_foreign_keys)

            if unique_table_id not in local_pool:
                local_pool[unique_table_id] = {
                    "original_table_name": t_name,
                    "primary_key": pk,
                    "foreign_keys": fks,
                    "columns": columns,
                    "content": tables_data[i].get('table_content', [])
                }
            else:
                existing_fks = local_pool[unique_table_id].get("foreign_keys", [])
                local_pool[unique_table_id]["foreign_keys"] = merge_foreign_keys(existing_fks, fks)

                # 如果之前没有高置信度主键，现在有，则补上
                if local_pool[unique_table_id].get("primary_key") is None and pk is not None:
                    local_pool[unique_table_id]["primary_key"] = pk

    print(f"✅ 处理完毕！从该文件中提取到 {len(local_pool)} 张独立表格。")
    print(f"正在保存到本地: {output_file} ...")

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

    sample_keys = list(data.keys())[:3]
    for key in sample_keys:
        print(f"{key} -> PK={data[key].get('primary_key')}, FKs={data[key].get('foreign_keys')}")


if __name__ == "__main__":
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

    for task in file_tasks:
        process_and_save_table_pool(task["input"], task["output"])
        check_table_pool_integrity(task["output"])
