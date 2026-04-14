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

# 新版本: 找表的主外键, 但是最终在MTR的效果却更差
# import json
# import os
# from typing import Dict, List, Optional


# SCHEMA_HINT_FILES = {
#     "Synthesized_three_table.json": "./tmp_data/three_table_only_schema.json",
#     "Synthesized_two_table.json": "./tmp_data/two_table_only_schema.json",
# }


# def normalize_name(name: str) -> str:
#     if not name:
#         return ""
#     return name.replace("_", "").replace(" ", "").lower()


# def build_normalized_column_map(columns: List[str]) -> Dict[str, str]:
#     mapping = {}
#     for col in columns:
#         mapping[normalize_name(col)] = col
#     return mapping


# def make_unique_table_id(table_name: str, columns: List[str]) -> str:
#     return f"{table_name}_[{','.join(columns)}]"


# def is_id_like(column_name: str) -> bool:
#     norm = normalize_name(column_name)
#     return norm == "id" or norm.endswith("id")


# def extract_matching_columns(columns: List[str], raw_keys: List[str]) -> List[str]:
#     col_map = build_normalized_column_map(columns)
#     raw_key_set = {normalize_name(key) for key in raw_keys if key}
#     matched = []
#     for norm_col, original_col in col_map.items():
#         if norm_col in raw_key_set:
#             matched.append(original_col)
#     return matched


# def get_schema_hint_path(input_file: str) -> Optional[str]:
#     filename = os.path.basename(input_file)
#     return SCHEMA_HINT_FILES.get(filename)


# def build_key_statistics(schema_items: List[Dict]) -> Dict[str, Dict]:
#     stats = {}

#     for item in schema_items:
#         table_names = item.get("table_names", [])
#         tables = item.get("tables", [])
#         raw_primary_keys = item.get("primary_keys", [])
#         raw_foreign_keys = item.get("foreign_keys", [])

#         for idx, table_name in enumerate(table_names):
#             if idx >= len(tables):
#                 continue

#             columns = tables[idx].get("table_columns", [])
#             unique_table_id = make_unique_table_id(table_name, columns)
#             matched_pks = extract_matching_columns(columns, raw_primary_keys)
#             matched_fks = extract_matching_columns(columns, raw_foreign_keys)

#             table_stats = stats.setdefault(
#                 unique_table_id,
#                 {
#                     "table_name": table_name,
#                     "columns": columns,
#                     "occurrences": 0,
#                     "pk_counts": {},
#                     "fk_counts": {},
#                 },
#             )
#             table_stats["occurrences"] += 1

#             for pk in matched_pks:
#                 table_stats["pk_counts"][pk] = table_stats["pk_counts"].get(pk, 0) + 1

#             for fk in matched_fks:
#                 table_stats["fk_counts"][fk] = table_stats["fk_counts"].get(fk, 0) + 1

#     return stats


# def infer_primary_key(table_stats: Dict) -> Optional[str]:
#     pk_counts = table_stats.get("pk_counts", {})
#     fk_counts = table_stats.get("fk_counts", {})

#     if not pk_counts:
#         return None

#     # 中间表/桥接表常出现多个键同时既像 PK 又像 FK，此时保守返回 None
#     overlapping_keys = [col for col in pk_counts if col in fk_counts]
#     if len(overlapping_keys) >= 2:
#         return None

#     ranked = sorted(
#         pk_counts.items(),
#         key=lambda item: (item[1], 1 if is_id_like(item[0]) else 0, len(item[0])),
#         reverse=True,
#     )

#     best_col, best_count = ranked[0]
#     if len(ranked) == 1:
#         return best_col

#     second_col, second_count = ranked[1]

#     # 若最佳候选明显更稳定，直接采用
#     if best_count > second_count:
#         return best_col

#     # 若并列，优先选择明显 ID 列；若多个都像 ID，则保守返回 None
#     id_like_cols = [col for col, count in ranked if count == best_count and is_id_like(col)]
#     if len(id_like_cols) == 1:
#         return id_like_cols[0]

#     return None


# def infer_foreign_keys(table_stats: Dict, primary_key: Optional[str]) -> List[str]:
#     fk_counts = table_stats.get("fk_counts", {})
#     pk_counts = table_stats.get("pk_counts", {})

#     ranked_fks = sorted(fk_counts.items(), key=lambda item: (-item[1], item[0]))
#     foreign_keys = []
#     for col, _ in ranked_fks:
#         if col == primary_key:
#             continue
#         foreign_keys.append(col)

#     # 如果没有显式 FK，但这是明显桥接表（多个键同时出现在 pk/fk），则保留重叠列为 FK
#     if not foreign_keys:
#         overlap = [col for col in pk_counts if col in fk_counts and col != primary_key]
#         foreign_keys.extend(sorted(set(overlap)))

#     return foreign_keys


# def load_schema_hint_data(input_file: str) -> List[Dict]:
#     schema_hint_path = get_schema_hint_path(input_file)
#     if not schema_hint_path or not os.path.exists(schema_hint_path):
#         print(f"[WARN] 未找到 schema hint 文件，将退回使用输入文件本身抽取键: {input_file}")
#         with open(input_file, "r", encoding="utf-8") as f:
#             return json.load(f)

#     print(f"[INFO] 使用 schema hint 文件增强主外键提取: {schema_hint_path}")
#     with open(schema_hint_path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def process_and_save_table_pool(input_file, output_file):
#     print(f"\n================ 开始处理: {input_file} ================")
#     if not os.path.exists(input_file):
#         print(f"找不到文件: {input_file}，请检查路径。")
#         return

#     with open(input_file, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     schema_hint_data = load_schema_hint_data(input_file)
#     key_stats = build_key_statistics(schema_hint_data)

#     local_pool = {}
#     for item in data:
#         table_names = item.get('table_names', [])
#         tables_data = item.get('tables', [])

#         for i, t_name in enumerate(table_names):
#             if i >= len(tables_data):
#                 continue

#             columns = tables_data[i].get('table_columns', [])
#             unique_table_id = make_unique_table_id(t_name, columns)

#             if unique_table_id not in local_pool:
#                 table_stats = key_stats.get(unique_table_id, {"pk_counts": {}, "fk_counts": {}})
#                 primary_key = infer_primary_key(table_stats)
#                 foreign_keys = infer_foreign_keys(table_stats, primary_key)

#                 local_pool[unique_table_id] = {
#                     "original_table_name": t_name,
#                     "primary_key": primary_key,
#                     "foreign_keys": foreign_keys,
#                     "columns": columns,
#                     "content": tables_data[i].get('table_content', [])
#                 }

#     print(f"✅ 处理完毕！从该文件中提取到 {len(local_pool)} 张独立表格。")
#     print(f"正在保存到本地: {output_file} ...")

#     os.makedirs(os.path.dirname(output_file), exist_ok=True)
#     with open(output_file, 'w', encoding='utf-8') as f:
#         json.dump(local_pool, f, ensure_ascii=False, indent=4)

#     print("🎉 保存成功！独立文件已生成。")


# def check_table_pool_integrity(file_path):
#     print(f"\n================ 检测: {file_path} ================")
#     if not os.path.exists(file_path):
#         print(f"⚠️ 找不到文件: {file_path}，请检查路径。")
#         return

#     with open(file_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     sample_keys = list(data.keys())[:5]
#     for key in sample_keys:
#         print(f"{key} -> PK={data[key].get('primary_key')}, FKs={data[key].get('foreign_keys')}")


# def main():
#     file_tasks = [
#         {
#             "input": "./data/Synthesized_three_table.json",
#             "output": "./data/global_table_pool_three.json"
#         },
#         {
#             "input": "./data/Synthesized_two_table.json",
#             "output": "./data/global_table_pool_two.json"
#         }
#     ]

#     for task in file_tasks:
#         process_and_save_table_pool(task["input"], task["output"])
#         check_table_pool_integrity(task["output"])


# if __name__ == "__main__":
#     main()
