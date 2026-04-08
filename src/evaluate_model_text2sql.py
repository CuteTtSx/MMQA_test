"""
评估微调后的 Qwen Text-to-SQL LoRA 模型。

默认评估：
- data/finetuning_test.jsonl
- outputs/qwen_text2sql_lora/final_checkpoint

指标：
1. JSON 格式正确率
2. ROUGE-1（百分制，rouge-score）
3. ROUGE-L（百分制，rouge-score）
4. BLEU（百分制，sacrebleu）
5. 按 overall / two_table / three_table 分组输出
6. 预测结果明细导出
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sacrebleu
import torch
from peft import PeftModel
from rouge_score import rouge_scorer
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_ADAPTER_PATH = "outputs/qwen_text2sql_lora/final_checkpoint"
DEFAULT_TEST_FILE = "data/finetuning_test.jsonl"
DEFAULT_OUTPUT_FILE = "outputs/qwen_text2sql_lora/eval_predictions.jsonl"


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Qwen LoRA model for Text-to-SQL")
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL_NAME)
    parser.add_argument("--adapter_path", type=str, default=DEFAULT_ADAPTER_PATH)
    parser.add_argument("--test_file", type=str, default=DEFAULT_TEST_FILE)
    parser.add_argument("--output_file", type=str, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--max_new_tokens", type=int, default=256)
    parser.add_argument("--limit", type=int, default=0, help="只评估前 N 条，0 表示全部")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    return parser.parse_args()


def load_jsonl(path: str) -> List[Dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_generation_messages(messages: List[Dict]) -> List[Dict]:
    return [m for m in messages if m["role"] != "assistant"]


def apply_chat_template(messages: List[Dict], tokenizer: AutoTokenizer) -> str:
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    text_parts = []
    for message in messages:
        role = message["role"].upper()
        content = message["content"]
        text_parts.append(f"<{role}>\n{content}")
    text_parts.append("<ASSISTANT>\n")
    return "\n\n".join(text_parts)


def extract_gold_sql(item: Dict) -> str:
    assistant_msg = next(m for m in item["messages"] if m["role"] == "assistant")
    content = assistant_msg["content"]
    try:
        parsed = json.loads(content)
        return parsed.get("SQL", "")
    except json.JSONDecodeError:
        return ""


def try_parse_prediction(text: str) -> Tuple[bool, str, Optional[Dict]]:
    text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "SQL" in parsed and isinstance(parsed["SQL"], str):
            return True, parsed["SQL"].strip(), parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "SQL" in parsed and isinstance(parsed["SQL"], str):
                return True, parsed["SQL"].strip(), parsed
        except json.JSONDecodeError:
            pass

    return False, "", None


def normalize_sql(sql: str) -> str:
    sql = sql.strip().lower()
    sql = re.sub(r"\s+", " ", sql)
    sql = sql.rstrip(";")
    return sql


def generate_prediction(
    model,
    tokenizer,
    messages: List[Dict],
    max_new_tokens: int,
    device: str,
) -> str:
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


def save_predictions(path: str, rows: List[Dict]):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def init_bucket() -> Dict:
    return {
        "count": 0,
        "json_ok_count": 0,
        "pred_sqls": [],
        "gold_sqls": [],
    }


def update_bucket(bucket: Dict, json_ok: bool, pred_sql: str, gold_sql: str):
    bucket["count"] += 1
    if json_ok:
        bucket["json_ok_count"] += 1
    bucket["pred_sqls"].append(pred_sql)
    bucket["gold_sqls"].append(gold_sql)


def compute_bucket_metrics(bucket: Dict) -> Dict[str, float]:
    total = bucket["count"]
    if total == 0:
        return {
            "json_rate": 0.0,
            "avg_rouge1": 0.0,
            "avg_rouge_l": 0.0,
            "avg_bleu": 0.0,
        }

    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=False)

    rouge1_sum = 0.0
    rouge_l_sum = 0.0
    for pred_sql, gold_sql in zip(bucket["pred_sqls"], bucket["gold_sqls"]):
        scores = scorer.score(normalize_sql(gold_sql), normalize_sql(pred_sql))
        rouge1_sum += scores["rouge1"].fmeasure
        rouge_l_sum += scores["rougeL"].fmeasure

    bleu_scores = []
    for pred_sql, gold_sql in zip(bucket["pred_sqls"], bucket["gold_sqls"]):
        bleu = sacrebleu.sentence_bleu(normalize_sql(pred_sql), [normalize_sql(gold_sql)])
        bleu_scores.append(bleu.score)

    return {
        "json_rate": bucket["json_ok_count"] / total,
        "avg_rouge1": rouge1_sum / total * 100,
        "avg_rouge_l": rouge_l_sum / total * 100,
        "avg_bleu": sum(bleu_scores) / total,
    }


def print_bucket_result(name: str, bucket: Dict):
    metrics = compute_bucket_metrics(bucket)
    total = bucket["count"]

    print(f"[{name}]")
    print(f"  Total samples:         {total}")
    print(f"  JSON format accuracy:  {bucket['json_ok_count']}/{total} = {metrics['json_rate']:.4f}")
    print(f"  Average ROUGE-1:       {metrics['avg_rouge1']:.2f}")
    print(f"  Average ROUGE-L:       {metrics['avg_rouge_l']:.2f}")
    print(f"  Average BLEU:          {metrics['avg_bleu']:.2f}")


def main():
    args = parse_args()

    dtype = torch.bfloat16 if args.bf16 else (torch.float16 if args.fp16 else torch.float32)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[INFO] Loading tokenizer: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.adapter_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[INFO] Loading base model: {args.model_name}")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        dtype=dtype,
        trust_remote_code=True,
    )

    print(f"[INFO] Loading LoRA adapter: {args.adapter_path}")
    model = PeftModel.from_pretrained(base_model, args.adapter_path)
    model.to(device)
    model.eval()

    print(f"[INFO] Loading test set: {args.test_file}")
    records = load_jsonl(args.test_file)
    if args.limit > 0:
        records = records[:args.limit]
    print(f"[OK] Test samples: {len(records)}")

    buckets = {
        "overall": init_bucket(),
        "two_table": init_bucket(),
        "three_table": init_bucket(),
    }
    prediction_rows = []

    for idx, item in enumerate(records, start=1):
        generation_messages = build_generation_messages(item["messages"])
        raw_prediction = generate_prediction(
            model=model,
            tokenizer=tokenizer,
            messages=generation_messages,
            max_new_tokens=args.max_new_tokens,
            device=device,
        )

        json_ok, pred_sql, parsed_json = try_parse_prediction(raw_prediction)
        gold_sql = extract_gold_sql(item)
        pred_sql_norm = normalize_sql(pred_sql)
        gold_sql_norm = normalize_sql(gold_sql)

        update_bucket(buckets["overall"], json_ok, pred_sql_norm, gold_sql_norm)
        source = item.get("source")
        if source in buckets:
            update_bucket(buckets[source], json_ok, pred_sql_norm, gold_sql_norm)

        sample_scores = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=False).score(
            gold_sql_norm, pred_sql_norm
        )
        sample_bleu = sacrebleu.sentence_bleu(pred_sql_norm, [gold_sql_norm]).score

        prediction_rows.append(
            {
                "id": item.get("id"),
                "source": source,
                "question": item.get("question"),
                "table_names": item.get("table_names", []),
                "json_ok": json_ok,
                "gold_sql": gold_sql,
                "pred_sql": pred_sql,
                "rouge_1": sample_scores["rouge1"].fmeasure * 100,
                "rouge_l": sample_scores["rougeL"].fmeasure * 100,
                "bleu": sample_bleu,
                "raw_prediction": raw_prediction,
                "parsed_json": parsed_json,
            }
        )

        if idx % 20 == 0 or idx == len(records):
            print(f"[INFO] Evaluated {idx}/{len(records)} samples")

    print("\n" + "=" * 80)
    print("Evaluation Results")
    print("=" * 80)
    print_bucket_result("overall", buckets["overall"])
    print("-" * 80)
    print_bucket_result("two_table", buckets["two_table"])
    print("-" * 80)
    print_bucket_result("three_table", buckets["three_table"])
    print("=" * 80)

    save_predictions(args.output_file, prediction_rows)
    print(f"[OK] Prediction details saved to: {args.output_file}")


if __name__ == "__main__":
    main()
