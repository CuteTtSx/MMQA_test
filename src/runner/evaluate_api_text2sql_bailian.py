"""
使用阿里百炼 OpenAI 兼容接口评估 Text-to-SQL。

输入输出与 evaluate_model_text2sql.py 保持一致：
- 输入：data/finetuning_test.jsonl
- 明细：eval_predictions.jsonl
- 指标：eval_metrics.json

设置环境变量 DASHSCOPE_API_KEY，或通过 --api_key 传入。
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sacrebleu
from openai import OpenAI
from rouge_score import rouge_scorer
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config

DEFAULT_TEST_FILE = str(Config.FINETUNING_TEST_JSONL)
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ALL_MODEL_KEY = "all"
MODEL_PRESETS = {
    "qwen36": {"model_name": "qwen3.6-flash", "output_dir": str(Config.OUTPUTS_DIR / "qwen36_flash_text2sql_api")},
    "deepseek_v4_flash": {"model_name": "deepseek-v4-flash", "output_dir": str(Config.OUTPUTS_DIR / "deepseek_v4_flash_text2sql_api")},
    "kimi_k26": {"model_name": "kimi-k2.6", "output_dir": str(Config.OUTPUTS_DIR / "kimi_k26_text2sql_api")},
    "minimax_m25": {"model_name": "MiniMax-M2.5", "output_dir": str(Config.OUTPUTS_DIR / "minimax_m25_text2sql_api")},
    "glm5": {"model_name": "glm-5", "output_dir": str(Config.OUTPUTS_DIR / "glm5_text2sql_api")},
}


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Text-to-SQL through Alibaba Bailian API")
    parser.add_argument("--model_key", default="qwen35", choices=[ALL_MODEL_KEY, *sorted(MODEL_PRESETS.keys())])
    parser.add_argument("--model_name", default=None, help="只在非 all 模式下覆盖预设模型名")
    parser.add_argument("--api_key", default=None)
    parser.add_argument("--base_url", default=DEFAULT_BASE_URL)
    parser.add_argument("--test_file", default=DEFAULT_TEST_FILE)
    parser.add_argument("--output_file", default=None, help="只在非 all 模式下生效")
    parser.add_argument("--metrics_file", default=None, help="只在非 all 模式下生效")
    parser.add_argument("--max_new_tokens", type=int, default=Config.FINETUNING_CONFIG["max_new_tokens"])
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0, help="只评估前 N 条，0 表示全部")
    parser.add_argument("--request_timeout", type=float, default=120.0)
    parser.add_argument("--max_retries", type=int, default=3)
    parser.add_argument("--retry_sleep", type=float, default=2.0)
    return parser.parse_args()


def load_jsonl(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_generation_messages(messages: List[Dict]) -> List[Dict]:
    return [m for m in messages if m["role"] != "assistant"]


def extract_gold_sql(item: Dict) -> str:
    assistant_msg = next(m for m in item["messages"] if m["role"] == "assistant")
    try:
        return json.loads(assistant_msg["content"]).get("SQL", "")
    except json.JSONDecodeError:
        return ""


def try_parse_prediction(text: str) -> Tuple[bool, str, Optional[Dict]]:
    text = text.strip()
    candidates = [text]
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and isinstance(parsed.get("SQL"), str):
                return True, parsed["SQL"].strip(), parsed
        except json.JSONDecodeError:
            continue
    return False, "", None


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower()).rstrip(";")


def get_api_key(cli_api_key: Optional[str]) -> str:
    api_key = (
        cli_api_key
        or Config.DASHSCOPE_API_KEY
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("BAILIAN_API_KEY")
        or os.getenv("ALIBABA_CLOUD_API_KEY")
    )
    if not api_key:
        raise ValueError("请在 src/utils/config.py、环境变量或 --api_key 中设置阿里百炼 API Key。")
    return api_key


def call_api(client: OpenAI, args, model_name: str, messages: List[Dict]) -> str:
    last_error = None
    for attempt in range(1, args.max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=args.temperature,
                max_tokens=args.max_new_tokens,
                timeout=args.request_timeout,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:
            last_error = exc
            if attempt < args.max_retries:
                wait = args.retry_sleep * attempt
                print(f"[WARN] API 调用失败 {attempt}/{args.max_retries}: {exc}; {wait:.1f}s 后重试")
                time.sleep(wait)
    raise RuntimeError(f"API 调用失败，已重试 {args.max_retries} 次: {last_error}")


def save_json(path: str, data: Dict):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_jsonl(path: str, rows: List[Dict]):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def init_bucket() -> Dict:
    return {"count": 0, "json_ok_count": 0, "pred_sqls": [], "gold_sqls": []}


def update_bucket(bucket: Dict, json_ok: bool, pred_sql: str, gold_sql: str):
    bucket["count"] += 1
    bucket["json_ok_count"] += int(json_ok)
    bucket["pred_sqls"].append(pred_sql)
    bucket["gold_sqls"].append(gold_sql)


def compute_bucket_metrics(bucket: Dict) -> Dict[str, float]:
    total = bucket["count"]
    if total == 0:
        return {"json_rate": 0.0, "avg_rouge1": 0.0, "avg_rouge_l": 0.0, "avg_bleu": 0.0}
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=False)
    rouge1_sum, rouge_l_sum, bleu_scores = 0.0, 0.0, []
    for pred_sql, gold_sql in zip(bucket["pred_sqls"], bucket["gold_sqls"]):
        scores = scorer.score(normalize_sql(gold_sql), normalize_sql(pred_sql))
        rouge1_sum += scores["rouge1"].fmeasure
        rouge_l_sum += scores["rougeL"].fmeasure
        bleu_scores.append(sacrebleu.sentence_bleu(normalize_sql(pred_sql), [normalize_sql(gold_sql)]).score)
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
    return {"count": total, "json_ok_count": bucket["json_ok_count"], **metrics}


def resolve_paths(args, model_key: str) -> Tuple[str, str]:
    out_dir = Path(MODEL_PRESETS[model_key]["output_dir"])
    return args.output_file or str(out_dir / "eval_predictions.jsonl"), args.metrics_file or str(out_dir / "eval_metrics.json")


def evaluate_model(args, client: OpenAI, model_key: str, records: List[Dict]) -> Dict:
    preset = MODEL_PRESETS[model_key]
    model_name = args.model_name if args.model_name and args.model_key != ALL_MODEL_KEY else preset["model_name"]
    output_file, metrics_file = resolve_paths(args, model_key)
    buckets = {"overall": init_bucket(), "two_table": init_bucket(), "three_table": init_bucket()}
    prediction_rows = []

    print("\n" + "=" * 80)
    print(f"[INFO] Evaluating {model_key}: {model_name}")
    print("=" * 80)
    for item in tqdm(records, desc=f"Evaluating {model_key}", unit="sample"):
        raw_prediction = call_api(client, args, model_name, build_generation_messages(item["messages"]))
        json_ok, pred_sql, parsed_json = try_parse_prediction(raw_prediction)
        gold_sql = extract_gold_sql(item)
        pred_sql_norm, gold_sql_norm = normalize_sql(pred_sql), normalize_sql(gold_sql)
        source = item.get("source")
        update_bucket(buckets["overall"], json_ok, pred_sql_norm, gold_sql_norm)
        if source in buckets:
            update_bucket(buckets[source], json_ok, pred_sql_norm, gold_sql_norm)
        scores = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=False).score(gold_sql_norm, pred_sql_norm)
        prediction_rows.append({
            "eval_mode": "api",
            "api_provider": "aliyun_bailian",
            "model_key": model_key,
            "model_name": model_name,
            "id": item.get("id"),
            "source": source,
            "question": item.get("question"),
            "table_names": item.get("table_names", []),
            "json_ok": json_ok,
            "gold_sql": gold_sql,
            "pred_sql": pred_sql,
            "rouge_1": scores["rouge1"].fmeasure * 100,
            "rouge_l": scores["rougeL"].fmeasure * 100,
            "bleu": sacrebleu.sentence_bleu(pred_sql_norm, [gold_sql_norm]).score,
            "raw_prediction": raw_prediction,
            "parsed_json": parsed_json,
        })

    print("\n" + "=" * 80)
    print(f"Evaluation Results\nModel: {model_key} | Name: {model_name} | Mode: api")
    print("=" * 80)
    bucket_metrics = {"overall": print_bucket_result("overall", buckets["overall"])}
    print("-" * 80)
    bucket_metrics["two_table"] = print_bucket_result("two_table", buckets["two_table"])
    print("-" * 80)
    bucket_metrics["three_table"] = print_bucket_result("three_table", buckets["three_table"])
    print("=" * 80)
    metrics = {
        "model_key": model_key,
        "model_name": model_name,
        "eval_mode": "api",
        "api_provider": "aliyun_bailian",
        "base_url": args.base_url,
        "test_file": args.test_file,
        "limit": args.limit,
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "prediction_file": output_file,
        "buckets": bucket_metrics,
    }
    save_jsonl(output_file, prediction_rows)
    save_json(metrics_file, metrics)
    print(f"[OK] Prediction details saved to: {output_file}")
    print(f"[OK] Evaluation metrics saved to: {metrics_file}")
    return metrics


def main():
    args = parse_args()
    client = OpenAI(api_key=get_api_key(args.api_key), base_url=args.base_url)
    records = load_jsonl(args.test_file)
    if args.limit > 0:
        records = records[:args.limit]
    print(f"[OK] Test samples: {len(records)}")
    if args.model_key == ALL_MODEL_KEY:
        if args.model_name or args.output_file or args.metrics_file:
            print("[WARN] all 模式会忽略 --model_name / --output_file / --metrics_file")
        metrics = [evaluate_model(args, client, key, records) for key in MODEL_PRESETS]
        save_json(str(Config.OUTPUTS_DIR / "text2sql_api_bailian_all_metrics.json"), {"api_provider": "aliyun_bailian", "models": metrics})
    else:
        evaluate_model(args, client, args.model_key, records)


if __name__ == "__main__":
    main()
