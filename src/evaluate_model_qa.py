"""
多表问答评估脚本：将完整表内容放入 prompt，直接让模型回答。

功能：
1. 从 QA_SQL_two_table.json / QA_SQL_three_table.json 读取样本
2. 通过 global_table_pool 恢复完整表内容（包含所有 rows）
3. 构造多表问答 prompt
4. 调用模型生成答案
5. 计算 EM / PM
6. 输出按 overall / two_table / three_table 的结果
7. 输出按表长分桶的准确率分析
"""

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_OUTPUT_FILE = "outputs/qwen_qa/evaluate_model_qa_predictions.jsonl"

SYSTEM_PROMPT = (
    "You are an expert at multi-table question answering. "
    "Read the question and tables carefully, then output only the final answers. "
    "Please only output valid JSON in the format: {\"Answers\": [\"answer1\", \"answer2\"]}. "
    "Rules: "
    "(1) Answers must be a flat list of final answer strings. "
    "(2) Do not output nested lists. "
    "(3) Do not output dictionaries or key-value objects. "
    "(4) Do not output field names, explanations, reasoning steps, or intermediate results. "
    "(5) If there is only one answer, still return a list with one string."
)


class MultiTableQAPipeline:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.qa_two_file = self.data_dir / "QA_SQL_two_table.json"
        self.qa_three_file = self.data_dir / "QA_SQL_three_table.json"
        self.pool_two_file = self.data_dir / "global_table_pool_two.json"
        self.pool_three_file = self.data_dir / "global_table_pool_three.json"

    def _load_json(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_pool_lookup(self, pool_data: Dict) -> Dict[str, Dict]:
        return dict(pool_data)

    def load_all_samples(self) -> List[Dict]:
        qa_two = self._load_json(self.qa_two_file)
        qa_three = self._load_json(self.qa_three_file)
        pool_two = self._load_json(self.pool_two_file)
        pool_three = self._load_json(self.pool_three_file)

        lookup_two = self._build_pool_lookup(pool_two)
        lookup_three = self._build_pool_lookup(pool_three)

        all_samples = []
        for item in qa_two:
            all_samples.append(self._convert_sample(item, lookup_two, "two_table"))
        for item in qa_three:
            all_samples.append(self._convert_sample(item, lookup_three, "three_table"))
        return all_samples

    def _convert_sample(self, item: Dict, pool_lookup: Dict[str, Dict], source: str) -> Dict:
        table_ids = item.get("table_ids", [])
        tables = []
        total_rows = 0

        for table_id in table_ids:
            if table_id not in pool_lookup:
                raise KeyError(f"表 {table_id} 不在全局表池中")
            table_data = pool_lookup[table_id]
            content = table_data.get("content", [])
            total_rows += len(content)
            tables.append(
                {
                    "table_id": table_id,
                    "table_name": table_data.get("original_table_name", ""),
                    "columns": table_data.get("columns", []),
                    "rows": content,
                }
            )

        answers = self._parse_answers(item.get("ans", ""))

        return {
            "id": item.get("id"),
            "source": source,
            "question": item.get("question", ""),
            "answers": answers,
            "raw_answer": item.get("ans", ""),
            "table_names": item.get("table_names", []),
            "tables": tables,
            "table_count": len(tables),
            "total_rows": total_rows,
        }

    def _parse_answers(self, ans: str) -> List[str]:
        if ans is None:
            return []
        text = str(ans).strip()
        if not text:
            return []
        return [part.strip() for part in text.split(",") if part.strip()]


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate multi-table QA with full rows in prompt")
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL_NAME)
    parser.add_argument("--data_dir", type=str, default="data")
    parser.add_argument("--output_file", type=str, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument("--max_rows", type=int, default=50) # 每个表最大取多少行
    parser.add_argument("--limit", type=int, default=0, help="只评估前 N 条，0 表示全部")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_answer_list(answers: List[str]) -> List[str]:
    normalized = [normalize_text(a) for a in answers if normalize_text(a)]
    normalized = sorted(set(normalized))
    return normalized


def compute_em(pred_answers: List[str], gold_answers: List[str]) -> float:
    return 1.0 if normalize_answer_list(pred_answers) == normalize_answer_list(gold_answers) else 0.0


def compute_pm(pred_answers: List[str], gold_answers: List[str]) -> float:
    pred_set = set(normalize_answer_list(pred_answers))
    gold_set = set(normalize_answer_list(gold_answers))

    if not pred_set and not gold_set:
        return 1.0
    if not pred_set or not gold_set:
        return 0.0

    overlap = len(pred_set & gold_set)
    precision = overlap / len(pred_set)
    recall = overlap / len(gold_set)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def format_table(table_idx: int, table: Dict, max_rows: int = 100) -> str:
    header = f"[TABLE{table_idx}]\n"
    header += f"Table Name: {table['table_name']}\n"
    header += f"Columns: {', '.join(table['columns'])}\n"
    header += "Rows:\n"

    row_lines = []
    # 只取前max_rows行
    for row_id, row in enumerate(table["rows"][:max_rows], start=1):
        row_values = [str(x) for x in row]
        row_lines.append(f"Row {row_id}: {', '.join(row_values)}")

    # 如果原表行数超过了最大行数，加一句提示，让大模型知道数据被截断了
    if len(table["rows"]) > max_rows:
        row_lines.append(f"... [TRUNCATED, ONLY SHOWING TOP {max_rows} ROWS] ...")

    if not row_lines:
        row_lines.append("<EMPTY>")

    return header + "\n".join(row_lines)


def build_user_prompt(question: str, tables: List[Dict], max_rows: int) -> str:
    parts = [f"[Question]\n{question}"]
    for idx, table in enumerate(tables, start=1):
        parts.append(format_table(idx, table, max_rows))
    return "\n\n".join(parts)


def apply_chat_template(messages: List[Dict], tokenizer: AutoTokenizer) -> str:
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    text_parts = []
    for message in messages:
        text_parts.append(f"<{message['role'].upper()}>\n{message['content']}")
    text_parts.append("<ASSISTANT>\n")
    return "\n\n".join(text_parts)


def flatten_answer_item(item) -> List[str]:
    if item is None:
        return []
    if isinstance(item, str):
        text = item.strip()
        return [text] if text else []
    if isinstance(item, (int, float, bool)):
        return [str(item)]
    if isinstance(item, list):
        results = []
        for sub_item in item:
            results.extend(flatten_answer_item(sub_item))
        return results
    if isinstance(item, dict):
        results = []
        for value in item.values():
            results.extend(flatten_answer_item(value))
        return results
    return [str(item).strip()]


def try_parse_answers(text: str) -> Tuple[bool, List[str], Optional[Dict]]:
    text = text.strip()

    def extract_answers(parsed_obj):
        if isinstance(parsed_obj, dict):
            answers = parsed_obj.get("Answers")
            if isinstance(answers, list):
                return True, flatten_answer_item(answers), parsed_obj
        if isinstance(parsed_obj, list):
            return True, flatten_answer_item(parsed_obj), {"Answers": parsed_obj}
        return False, [], None

    try:
        parsed = json.loads(text)
        ok, flattened, parsed_json = extract_answers(parsed)
        if ok:
            return True, flattened, parsed_json
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
    if match:
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            ok, flattened, parsed_json = extract_answers(parsed)
            if ok:
                return True, flattened, parsed_json
        except json.JSONDecodeError:
            pass

    return False, [], None


def generate_answers(model, tokenizer, question: str, tables: List[Dict], max_new_tokens: int, device: str, max_rows: int) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(question, tables, max_rows)},
    ]

    prompt = apply_chat_template(messages, tokenizer)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def init_bucket() -> Dict:
    return {"count": 0, "json_ok": 0, "em_sum": 0.0, "pm_sum": 0.0}


def update_bucket(bucket: Dict, json_ok: bool, em: float, pm: float):
    bucket["count"] += 1
    if json_ok:
        bucket["json_ok"] += 1
    bucket["em_sum"] += em
    bucket["pm_sum"] += pm


def print_bucket_result(name: str, bucket: Dict):
    total = bucket["count"]
    json_rate = bucket["json_ok"] / total if total else 0.0
    avg_em = bucket["em_sum"] / total * 100 if total else 0.0
    avg_pm = bucket["pm_sum"] / total * 100 if total else 0.0

    print(f"[{name}]")
    print(f"  Total samples:         {total}")
    print(f"  JSON format accuracy:  {bucket['json_ok']}/{total} = {json_rate:.4f}")
    print(f"  EM:                    {avg_em:.2f}")
    print(f"  PM:                    {avg_pm:.2f}")


def get_row_bucket(total_rows: int) -> str:
    if total_rows <= 20:
        return "rows_0_20"
    if total_rows <= 50:
        return "rows_21_50"
    if total_rows <= 100:
        return "rows_51_100"
    return "rows_100_plus"


def save_jsonl(path: str, rows: List[Dict]):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    args = parse_args()

    dtype = torch.bfloat16 if args.bf16 else (torch.float16 if args.fp16 else torch.float32)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipeline = MultiTableQAPipeline(data_dir=args.data_dir)
    samples = pipeline.load_all_samples()
    if args.limit > 0:
        samples = samples[:args.limit]

    print(f"[INFO] Total QA samples: {len(samples)}")
    print(f"[INFO] Loading tokenizer: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[INFO] Loading model: {args.model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        dtype=dtype,
        trust_remote_code=True,
    )
    model.to(device)
    model.eval()

    buckets = {
        "overall": init_bucket(),
        "two_table": init_bucket(),
        "three_table": init_bucket(),
    }
    row_buckets = {}
    prediction_rows = []

    for idx, sample in enumerate(samples, start=1):
        raw_prediction = generate_answers(
            model=model,
            tokenizer=tokenizer,
            question=sample["question"],
            tables=sample["tables"],
            max_new_tokens=args.max_new_tokens,
            device=device,
            max_rows=args.max_rows,
        )

        json_ok, pred_answers, parsed_json = try_parse_answers(raw_prediction)
        gold_answers = sample["answers"]
        em = compute_em(pred_answers, gold_answers)
        pm = compute_pm(pred_answers, gold_answers)

        update_bucket(buckets["overall"], json_ok, em, pm)
        if sample["source"] in buckets:
            update_bucket(buckets[sample["source"]], json_ok, em, pm)

        row_bucket_name = get_row_bucket(sample["total_rows"])
        if row_bucket_name not in row_buckets:
            row_buckets[row_bucket_name] = init_bucket()
        update_bucket(row_buckets[row_bucket_name], json_ok, em, pm)

        prediction_rows.append(
            {
                "id": sample["id"],
                "source": sample["source"],
                "question": sample["question"],
                "table_names": sample["table_names"],
                "table_count": sample["table_count"],
                "total_rows": sample["total_rows"],
                "gold_answers": gold_answers,
                "pred_answers": pred_answers,
                "json_ok": json_ok,
                "em": em * 100,
                "pm": pm * 100,
                "raw_prediction": raw_prediction,
                "parsed_json": parsed_json,
            }
        )

        if idx % 20 == 0 or idx == len(samples):
            print(f"[INFO] Evaluated {idx}/{len(samples)} samples")

    print("\n" + "=" * 80)
    print("Multi-table QA Evaluation Results")
    print("=" * 80)
    print_bucket_result("overall", buckets["overall"])
    print("-" * 80)
    print_bucket_result("two_table", buckets["two_table"])
    print("-" * 80)
    print_bucket_result("three_table", buckets["three_table"])
    print("=" * 80)
    print("Table Length Analysis")
    print("=" * 80)
    for bucket_name in ["rows_0_20", "rows_21_50", "rows_51_100", "rows_100_plus"]:
        if bucket_name in row_buckets:
            print_bucket_result(bucket_name, row_buckets[bucket_name])
            print("-" * 80)

    save_jsonl(args.output_file, prediction_rows)
    print(f"[OK] Prediction details saved to: {args.output_file}")


if __name__ == "__main__":
    main()
