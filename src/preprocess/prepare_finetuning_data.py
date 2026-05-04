"""
准备 Qwen Text-to-SQL 微调数据。

流程：
1. 读取 QA_SQL_two_table.json 和 QA_SQL_three_table.json。
2. 根据每条样本中的唯一表 id，从对应 global_table_pool 中恢复表 schema。
3. 组织成 Qwen 适合的 messages 格式。
4. 划分 train / val / test。
5. 同时输出 json 与 jsonl 文件。

说明：
- 当前 schema 文本仅保留表名和列名。
- 之所以不直接加入 PK/FK，是因为当前抽取质量还不稳定，避免把噪声注入训练数据。
"""

import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config


SYSTEM_PROMPT = (
    "You are an expert at text-to-SQL. Generate a SQL query based on the given "
    "multi-hop question and the provided table schemas. Use only the provided tables. "
    "Please only output valid JSON in the format: {\"SQL\": \"<generated_sql>\"}."
)


class FinetuningDataPreparer:
    """将 QA 数据与全局表池转换为 Qwen LoRA 微调数据格式。"""

    def __init__(self, data_dir: str = "", seed: Optional[int] = None):
        """初始化数据准备器，并绑定输入文件路径与随机种子。"""
        self.data_dir = Path(data_dir) if data_dir else Config.DATA_DIR
        self.seed = Config.DATASET_CONFIG["seed"] if seed is None else seed
        self.random = random.Random(self.seed)

        self.qa_two_file = Config.QA_SQL_TWO_TABLE_FILE
        self.qa_three_file = Config.QA_SQL_THREE_TABLE_FILE
        self.pool_two_file = Config.GLOBAL_TABLE_POOL_TWO_FILE
        self.pool_three_file = Config.GLOBAL_TABLE_POOL_THREE_FILE

    def _load_json(self, path: Path):
        """读取单个 JSON 文件。"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_pool_lookup(self, pool_data: Dict) -> Dict[str, Dict]:
        """把 global_table_pool 构建成 {唯一表id: 表数据} 的索引。"""
        lookup = {}
        for unique_table_id, table_data in pool_data.items():
            lookup[unique_table_id] = table_data
        return lookup

    def _format_single_table_schema(self, table_idx: int, _unique_table_id: str, table_data: Dict) -> str:
        """把单张表格式化为训练时使用的 schema 文本。"""
        table_name = table_data.get("original_table_name", "")
        columns = table_data.get("columns", [])

        parts = [
            f"Table {table_idx}: {table_name}",
            # 当前训练主要依赖列级线索，因此这里只保留列名。
            f"Columns: {', '.join(columns)}",
        ]

        return "\n".join(parts)

    def _build_tables_text(self, table_ids: List[str], pool_lookup: Dict[str, Dict]) -> str:
        """根据样本中的 table_ids 拼接完整的多表 schema 文本。"""
        schemas = []
        for idx, table_id in enumerate(table_ids, start=1):
            if table_id not in pool_lookup:
                raise KeyError(f"表 {table_id} 不在全局表池中")
            table_data = pool_lookup[table_id]
            schemas.append(self._format_single_table_schema(idx, table_id, table_data))
        return "\n\n".join(schemas)

    def _build_user_prompt(self, question: str, tables_text: str) -> str:
        """构造训练样本中的 user 提示词。"""
        return f"[Question]\n{question}\n\n[Tables]\n{tables_text}"

    def _build_assistant_output(self, sql: str) -> str:
        """把标准答案 SQL 包装成模型训练目标 JSON。"""
        return json.dumps({"SQL": sql}, ensure_ascii=False)

    def _convert_sample(self, item: Dict, pool_lookup: Dict[str, Dict], source: str) -> Dict:
        """把单条 QA 样本转换成 Qwen chat 格式样本。"""
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
        """加载二表和三表 QA 数据，并统一转换为训练样本。"""
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
        train_ratio: Optional[float] = None,
        val_ratio: Optional[float] = None,
        test_ratio: Optional[float] = None,
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """按给定比例切分训练、验证和测试集。"""
        train_ratio = Config.DATASET_CONFIG["train_ratio"] if train_ratio is None else train_ratio
        val_ratio = Config.DATASET_CONFIG["val_ratio"] if val_ratio is None else val_ratio
        test_ratio = Config.DATASET_CONFIG["test_ratio"] if test_ratio is None else test_ratio

        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-8:
            raise ValueError("train/val/test 比例之和必须为 1.0")

        shuffled = samples[:]
        # 使用固定随机种子打乱，保证多次运行切分结果可复现。
        self.random.shuffle(shuffled)

        total = len(shuffled)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        train_data = shuffled[:train_end]
        val_data = shuffled[train_end:val_end]
        test_data = shuffled[val_end:]

        return train_data, val_data, test_data

    def _write_json(self, path: Path, data: List[Dict]):
        """以 JSON 格式保存样本列表。"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_jsonl(self, path: Path, data: List[Dict]):
        """以 JSONL 格式逐行保存样本列表。"""
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def save_splits(self, train_data: List[Dict], val_data: List[Dict], test_data: List[Dict]):
        """把数据切分结果同时保存为 JSON 和 JSONL 两种格式。"""
        outputs = {
            Config.FINETUNING_TRAIN_JSON: train_data,
            Config.FINETUNING_VAL_JSON: val_data,
            Config.FINETUNING_TEST_JSON: test_data,
            Config.FINETUNING_TRAIN_JSONL: train_data,
            Config.FINETUNING_VAL_JSONL: val_data,
            Config.FINETUNING_TEST_JSONL: test_data,
        }

        for output_path, data in outputs.items():
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # 根据扩展名自动选择 JSON 或 JSONL 写法。
            if output_path.suffix == ".jsonl":
                self._write_jsonl(output_path, data)
            else:
                self._write_json(output_path, data)
            print(f"[OK] 已保存: {output_path}")

    def print_stats(self, train_data: List[Dict], val_data: List[Dict], test_data: List[Dict]):
        """打印切分后的数据集规模和一条训练样本示例。"""
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
            # 仅截断显示前 2000 个字符，避免样本过长刷屏。
            print(json.dumps(sample, ensure_ascii=False, indent=2)[:2000])
            print("-" * 80)


def main():
    """执行完整的微调数据准备流程。"""
    preparer = FinetuningDataPreparer()

    all_samples = preparer.load_and_convert_all()
    train_data, val_data, test_data = preparer.split_dataset(all_samples)
    preparer.save_splits(train_data, val_data, test_data)
    preparer.print_stats(train_data, val_data, test_data)


if __name__ == "__main__":
    main()
