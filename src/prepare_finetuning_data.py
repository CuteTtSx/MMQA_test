"""
准备 Qwen Text-to-SQL 微调数据。

流程：
1. 读取 QA_SQL_two_table.json 和 QA_SQL_three_table.json
2. 根据每条样本中的唯一表 id，从对应 global_table_pool 中恢复表 schema
3. 组织成 Qwen 适合的 messages 格式
4. 划分 train / val / test
5. 输出 json 与 jsonl 文件
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple


SYSTEM_PROMPT = (
    "You are an expert at text-to-SQL. Generate a SQL query based on the given "
    "multi-hop question and the provided table schemas. Use only the provided tables. "
    "Please only output valid JSON in the format: {\"SQL\": \"<generated_sql>\"}."
)


class FinetuningDataPreparer:
    def __init__(self, data_dir: str = "data", seed: int = 42):
        self.data_dir = Path(data_dir)
        self.seed = seed
        self.random = random.Random(seed)

        self.qa_two_file = self.data_dir / "QA_SQL_two_table.json"
        self.qa_three_file = self.data_dir / "QA_SQL_three_table.json"
        self.pool_two_file = self.data_dir / "global_table_pool_two.json"
        self.pool_three_file = self.data_dir / "global_table_pool_three.json"

    def _load_json(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_pool_lookup(self, pool_data: Dict) -> Dict[str, Dict]:
        """把 global_table_pool 构建成 {唯一表id: 表数据} 的索引。"""
        lookup = {}
        for unique_table_id, table_data in pool_data.items():
            lookup[unique_table_id] = table_data
        return lookup

    def _format_single_table_schema(self, table_idx: int, unique_table_id: str, table_data: Dict) -> str:
        """只保留表名和列名，去掉当前不可靠的 PK/FK 信息。"""
        table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])

        parts = [
            f"Table {table_idx}: {table_name}",
            f"Columns: {', '.join(columns)}",
        ]

        return "\n".join(parts)

    def _build_tables_text(self, table_ids: List[str], pool_lookup: Dict[str, Dict]) -> str:
        schemas = []
        for idx, table_id in enumerate(table_ids, start=1):
            if table_id not in pool_lookup:
                raise KeyError(f"表 {table_id} 不在全局表池中")
            table_data = pool_lookup[table_id]
            schemas.append(self._format_single_table_schema(idx, table_id, table_data))
        return "\n\n".join(schemas)

    def _build_user_prompt(self, question: str, tables_text: str) -> str:
        return f"[Question]\n{question}\n\n[Tables]\n{tables_text}"

    def _build_assistant_output(self, sql: str) -> str:
        return json.dumps({"SQL": sql}, ensure_ascii=False)

    def _convert_sample(self, item: Dict, pool_lookup: Dict[str, Dict], source: str) -> Dict:
        question = item.get("question", "")
        sql = item.get("sql", "")
        table_ids = item.get("table_ids", [])
        table_names = item.get("table_names", [])

        tables_text = self._build_tables_text(table_ids, pool_lookup)
        user_prompt = self._build_user_prompt(question, tables_text)
        assistant_output = self._build_assistant_output(sql)

        return {
            "id": item.get("id"),
            "source": source,
            "question": question,
            "table_names": table_names,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_output},
            ],
        }

    def load_and_convert_all(self) -> List[Dict]:
        print("[INFO] 加载 QA 数据与全局表池...")
        qa_two = self._load_json(self.qa_two_file)
        qa_three = self._load_json(self.qa_three_file)
        pool_two = self._load_json(self.pool_two_file)
        pool_three = self._load_json(self.pool_three_file)

        lookup_two = self._build_pool_lookup(pool_two)
        lookup_three = self._build_pool_lookup(pool_three)

        print(f"[OK] two-table 样本数: {len(qa_two)}")
        print(f"[OK] three-table 样本数: {len(qa_three)}")

        all_samples = []

        for item in qa_two:
            all_samples.append(self._convert_sample(item, lookup_two, "two_table"))

        for item in qa_three:
            all_samples.append(self._convert_sample(item, lookup_three, "three_table"))

        print(f"[OK] 总转换样本数: {len(all_samples)}")
        return all_samples

    def split_dataset(
        self,
        samples: List[Dict],
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-8:
            raise ValueError("train/val/test 比例之和必须为 1.0")

        shuffled = samples[:]
        self.random.shuffle(shuffled)

        total = len(shuffled)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        train_data = shuffled[:train_end]
        val_data = shuffled[train_end:val_end]
        test_data = shuffled[val_end:]

        return train_data, val_data, test_data

    def _write_json(self, path: Path, data: List[Dict]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_jsonl(self, path: Path, data: List[Dict]):
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def save_splits(self, train_data: List[Dict], val_data: List[Dict], test_data: List[Dict]):
        outputs = {
            "finetuning_train.json": train_data,
            "finetuning_val.json": val_data,
            "finetuning_test.json": test_data,
            "finetuning_train.jsonl": train_data,
            "finetuning_val.jsonl": val_data,
            "finetuning_test.jsonl": test_data,
        }

        for filename, data in outputs.items():
            output_path = self.data_dir / filename
            if filename.endswith(".jsonl"):
                self._write_jsonl(output_path, data)
            else:
                self._write_json(output_path, data)
            print(f"[OK] 已保存: {output_path}")

    def print_stats(self, train_data: List[Dict], val_data: List[Dict], test_data: List[Dict]):
        print("\n" + "=" * 80)
        print("微调数据集统计")
        print("=" * 80)
        print(f"训练集: {len(train_data)}")
        print(f"验证集: {len(val_data)}")
        print(f"测试集: {len(test_data)}")
        print(f"总计:   {len(train_data) + len(val_data) + len(test_data)}")
        print("=" * 80)

        if train_data:
            sample = train_data[0]
            print("\n训练样本示例:")
            print("-" * 80)
            print(json.dumps(sample, ensure_ascii=False, indent=2)[:2000])
            print("-" * 80)


def main():
    preparer = FinetuningDataPreparer(data_dir="data", seed=42)

    all_samples = preparer.load_and_convert_all()
    train_data, val_data, test_data = preparer.split_dataset(all_samples)
    preparer.save_splits(train_data, val_data, test_data)
    preparer.print_stats(train_data, val_data, test_data)


if __name__ == "__main__":
    main()
