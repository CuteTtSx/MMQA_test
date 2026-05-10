"""
评估 Text-to-SQL 模型。

支持两种评估模式：
- base: 直接评估原始开源大模型，不加载 LoRA adapter
- lora: 评估微调后的 LoRA adapter

默认评估：
- data/finetuning_test.jsonl

支持的模型预设：
- qwen: Qwen/Qwen2.5-1.5B-Instruct 或 FINETUNING_BASE_MODEL
- deepseek_coder: deepseek-ai/deepseek-coder-1.3b-instruct
- kimi: moonshotai/Kimi-K2-Instruct

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
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sacrebleu
import torch
from peft import PeftModel
from rouge_score import rouge_scorer
from transformers import AutoModelForCausalLM, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config


DEFAULT_TEST_FILE = str(Config.FINETUNING_TEST_JSONL)

MODEL_PRESETS = {
    "qwen": {
        "model_name": Config.FINETUNING_BASE_MODEL,
        "adapter_path": str(Config.OUTPUTS_DIR / "qwen_text2sql_lora" / "final_checkpoint"),
        "lora_output_file": str(Config.OUTPUTS_DIR / "qwen_text2sql_lora" / "eval_predictions.jsonl"),
        "base_output_file": str(Config.OUTPUTS_DIR / "qwen_text2sql_base" / "eval_predictions.jsonl"),
    },
    "deepseek_coder": {
        "model_name": "deepseek-ai/deepseek-coder-1.3b-instruct",
        "adapter_path": str(Config.OUTPUTS_DIR / "deepseek_coder_text2sql_lora" / "final_checkpoint"),
        "lora_output_file": str(Config.OUTPUTS_DIR / "deepseek_coder_text2sql_lora" / "eval_predictions.jsonl"),
        "base_output_file": str(Config.OUTPUTS_DIR / "deepseek_coder_text2sql_base" / "eval_predictions.jsonl"),
    },
    "kimi": {
        "model_name": "moonshotai/Kimi-K2-Instruct",
        "adapter_path": str(Config.OUTPUTS_DIR / "kimi_text2sql_lora" / "final_checkpoint"),
        "lora_output_file": str(Config.OUTPUTS_DIR / "kimi_text2sql_lora" / "eval_predictions.jsonl"),
        "base_output_file": str(Config.OUTPUTS_DIR / "kimi_text2sql_base" / "eval_predictions.jsonl"),
    },
}

DEFAULT_MODEL_KEY = "qwen"


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate LoRA model for Text-to-SQL")
    parser.add_argument(
        "--model_key",
        type=str,
        default=DEFAULT_MODEL_KEY,
        choices=sorted(MODEL_PRESETS.keys()),
        help="预设模型：qwen / deepseek_coder / kimi。若传入 --model_name 或 --adapter_path，则手动参数优先。",
    )
    parser.add_argument(
        "--eval_mode",
        type=str,
        default="lora",
        choices=["base", "lora"],
        help="base 表示直接评估原始模型；lora 表示加载 LoRA adapter 后评估。",
    )
    parser.add_argument("--model_name", type=str, default=None)
    parser.add_argument("--adapter_path", type=str, default=None)
    parser.add_argument("--test_file", type=str, default=DEFAULT_TEST_FILE)
    parser.add_argument("--output_file", type=str, default=None)
    parser.add_argument("--metrics_file", type=str, default=None, help="汇总指标输出 JSON 文件；默认与 output_file 同目录。")
    parser.add_argument("--max_new_tokens", type=int, default=Config.FINETUNING_CONFIG["max_new_tokens"])
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


def save_metrics(path: str, metrics: Dict):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)


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


def print_bucket_result(name: str, bucket: Dict) -> Dict[str, float]:
    metrics = compute_bucket_metrics(bucket)
    total = bucket["count"]

    print(f"[{name}]")
    print(f"  Total samples:         {total}")
    print(f"  JSON format accuracy:  {bucket['json_ok_count']}/{total} = {metrics['json_rate']:.4f}")
    print(f"  Average ROUGE-1:       {metrics['avg_rouge1']:.2f}")
    print(f"  Average ROUGE-L:       {metrics['avg_rouge_l']:.2f}")
    print(f"  Average BLEU:          {metrics['avg_bleu']:.2f}")
    return {
        "count": total,
        "json_ok_count": bucket["json_ok_count"],
        **metrics,
    }


def resolve_model_args(args) -> Tuple[str, Optional[str], str]:
    preset = MODEL_PRESETS[args.model_key]
    model_name = args.model_name or preset["model_name"]
    adapter_path = args.adapter_path or preset["adapter_path"]
    default_output_file = preset["lora_output_file"] if args.eval_mode == "lora" else preset["base_output_file"]
    output_file = args.output_file or default_output_file
    return model_name, adapter_path, output_file


def main():
    args = parse_args()
    model_name, adapter_path, output_file = resolve_model_args(args)

    dtype = torch.bfloat16 if args.bf16 else (torch.float16 if args.fp16 else torch.float32)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[INFO] Model preset: {args.model_key}")
    print(f"[INFO] Evaluation mode: {args.eval_mode}")
    tokenizer_source = adapter_path if args.eval_mode == "lora" else model_name
    print(f"[INFO] Loading tokenizer: {tokenizer_source}")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[INFO] Loading base model: {model_name}")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=dtype,
        trust_remote_code=True,
    )

    if args.eval_mode == "lora":
        print(f"[INFO] Loading LoRA adapter: {adapter_path}")
        model = PeftModel.from_pretrained(base_model, adapter_path)
    else:
        if args.adapter_path:
            print("[WARN] --adapter_path is ignored when --eval_mode base")
        model = base_model

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
                "eval_mode": args.eval_mode,
                "model_key": args.model_key,
                "model_name": model_name,
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
    print(f"Model: {args.model_key} | Mode: {args.eval_mode}")
    print("=" * 80)
    bucket_metrics = {
        "overall": print_bucket_result("overall", buckets["overall"]),
    }
    print("-" * 80)
    bucket_metrics["two_table"] = print_bucket_result("two_table", buckets["two_table"])
    print("-" * 80)
    bucket_metrics["three_table"] = print_bucket_result("three_table", buckets["three_table"])
    print("=" * 80)

    metrics_output = {
        "model_key": args.model_key,
        "model_name": model_name,
        "eval_mode": args.eval_mode,
        "test_file": args.test_file,
        "limit": args.limit,
        "max_new_tokens": args.max_new_tokens,
        "dtype": "bf16" if args.bf16 else ("fp16" if args.fp16 else "fp32"),
        "prediction_file": output_file,
        "buckets": bucket_metrics,
    }
    metrics_file = args.metrics_file or str(Path(output_file).with_name("eval_metrics.json"))

    save_predictions(output_file, prediction_rows)
    save_metrics(metrics_file, metrics_output)
    print(f"[OK] Prediction details saved to: {output_file}")
    print(f"[OK] Evaluation metrics saved to: {metrics_file}")


if __name__ == "__main__":
    main()
