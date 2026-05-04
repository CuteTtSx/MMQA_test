"""
探索并精简原始多表数据。

功能：
1. 读取原始 Synthesized 数据文件。
2. 删除问题、SQL、答案和表内容等大字段。
3. 仅保留后续分析表结构所需的 schema 信息。
4. 将精简结果保存到 tmp_data 目录。

用途：
- 方便人工查看原始数据结构。
- 为后续主键、外键、列结构分析提供更轻量的中间文件。
"""

import copy
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config


def save_tables_info(input_file_path, output_file_path):
    """删除原始样本中的大字段，只保留精简后的 schema 信息。"""
    input_path = Path(input_file_path)
    output_path = Path(output_file_path)

    print(f"正在加载大文件: {input_path} ...")
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"加载成功, 数据集中共有 {len(data)} 条多表查询样本。\n")

    for item in data:
        # 这些字段与结构探索无关，删除后更便于观察 schema。
        item.pop("Question", None)
        item.pop("SQL", None)
        item.pop("answer", None)

        if "tables" in item:
            for table in item["tables"]:
                # 表内容通常体积较大，这里只保留列结构等元信息。
                table.pop("table_content", None)
                table.pop("table_contents", None)

    print(f"正在将精简后的 Schema 数据保存至: {output_path} ...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("保存完成！")
    # 深拷贝后打印，避免后续若扩展调试逻辑时误修改原数据。
    first_item_display = copy.deepcopy(data[0])
    print("================ 第一条数据的精简 Schema 结构 ================")
    print(json.dumps(first_item_display, indent=4, ensure_ascii=False))


def get_table_nums(file_path):
    """统计某个数据文件中按“表名+列名”去重后的唯一表数量。"""
    path = Path(file_path)
    print(f"正在加载大文件: {path} ...")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 兼容某些可能带最外层字典包装的数据格式。
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                data = value
                break

    if not isinstance(data, list):
        print("数据格式异常，无法找到数据列表。")
        return

    print(f"加载成功！数据集中共有 {len(data)} 条多表查询样本")
    print("================ 全局表格统计 ================")
    unique_tables = set()

    for item in data:
        if not isinstance(item, dict):
            continue

        table_names = item.get("table_names", [])
        tables_data = item.get("tables", [])

        for i, table_name in enumerate(table_names):
            if i >= len(tables_data):
                continue

            columns = tables_data[i].get("table_columns", [])
            unique_table_id = f"{table_name}_[{','.join(columns)}]"
            unique_tables.add(unique_table_id)

    print(f"统计完毕：在【{path.name}】中，一共包含 {len(unique_tables)} 张真正独特的表！\n")


def main():
    """按配置依次生成二表和三表数据的精简 schema 文件。"""
    for input_file, output_file in Config.get_schema_extraction_tasks():
        save_tables_info(input_file, output_file)
        # get_table_nums(input_file)


if __name__ == "__main__":
    main()
