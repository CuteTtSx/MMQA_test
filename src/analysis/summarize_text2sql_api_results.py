import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config

MODEL_OUTPUT_DIRS = {
    "deepseek_v4_flash": Config.OUTPUTS_DIR / "deepseek_v4_flash_text2sql_api",
    "glm5": Config.OUTPUTS_DIR / "glm5_text2sql_api",
    "kimi_k26": Config.OUTPUTS_DIR / "kimi_k26_text2sql_api",
    "minimax_m25": Config.OUTPUTS_DIR / "minimax_m25_text2sql_api",
    "qwen36": Config.OUTPUTS_DIR / "qwen36_flash_text2sql_api",
}
BUCKETS = ["overall", "two_table", "three_table"]
METRICS = ["json_rate", "avg_rouge1", "avg_rouge_l", "avg_bleu"]
METRIC_LABELS = {
    "json_rate": "JSON格式正确率",
    "avg_rouge1": "ROUGE-1",
    "avg_rouge_l": "ROUGE-L",
    "avg_bleu": "BLEU",
}
BUCKET_LABELS = {
    "overall": "总体",
    "two_table": "双表",
    "three_table": "三表",
}
DEFAULT_OUTPUT_FILE = Config.OUTPUTS_DIR / "text2sql_api_final_report.md"


def parse_args():
    parser = argparse.ArgumentParser(description="汇总多个 Text-to-SQL API 模型评估结果并生成实验展示报告")
    parser.add_argument(
        "--output_file",
        default=str(DEFAULT_OUTPUT_FILE),
        help="输出 Markdown 报告路径",
    )
    parser.add_argument(
        "--model_keys",
        nargs="*",
        default=list(MODEL_OUTPUT_DIRS.keys()),
        choices=sorted(MODEL_OUTPUT_DIRS.keys()),
        help="需要纳入汇总的模型键",
    )
    return parser.parse_args()


def load_metrics(metrics_file: Path):
    with metrics_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def format_rate(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_score(value: float) -> str:
    return f"{value:.2f}"


def metric_sort_value(metric_name: str, value: float) -> float:
    return value


def collect_results(model_keys):
    results = []
    for model_key in model_keys:
        metrics_file = MODEL_OUTPUT_DIRS[model_key] / "eval_metrics.json"
        if not metrics_file.exists():
            raise FileNotFoundError(f"未找到评估结果文件: {metrics_file}")
        metrics = load_metrics(metrics_file)
        results.append(metrics)
    return results


def build_summary_table(results, bucket_name: str):
    lines = [
        "| 模型 | 样本数 | JSON格式正确率 | ROUGE-1 | ROUGE-L | BLEU |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    sorted_results = sorted(
        results,
        key=lambda x: (
            metric_sort_value("avg_rouge1", x["buckets"][bucket_name]["avg_rouge1"]),
            metric_sort_value("avg_bleu", x["buckets"][bucket_name]["avg_bleu"]),
        ),
        reverse=True,
    )
    for item in sorted_results:
        bucket = item["buckets"][bucket_name]
        lines.append(
            "| "
            + " | ".join(
                [
                    item["model_name"],
                    str(bucket["count"]),
                    format_rate(bucket["json_rate"]),
                    format_score(bucket["avg_rouge1"]),
                    format_score(bucket["avg_rouge_l"]),
                    format_score(bucket["avg_bleu"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def get_best_model(results, bucket_name: str, metric_name: str):
    return max(results, key=lambda x: metric_sort_value(metric_name, x["buckets"][bucket_name][metric_name]))


def build_best_observations(results):
    lines = ["## 一、关键结论", ""]
    overall_best_rouge1 = get_best_model(results, "overall", "avg_rouge1")
    overall_best_bleu = get_best_model(results, "overall", "avg_bleu")
    overall_best_json = get_best_model(results, "overall", "json_rate")
    two_best = get_best_model(results, "two_table", "avg_rouge1")
    three_best = get_best_model(results, "three_table", "avg_rouge1")

    lines.append(
        f"- 总体表现上，`{overall_best_rouge1['model_name']}` 的 ROUGE-1 最高，为 {format_score(overall_best_rouge1['buckets']['overall']['avg_rouge1'])}；"
        f"`{overall_best_bleu['model_name']}` 的 BLEU 最高，为 {format_score(overall_best_bleu['buckets']['overall']['avg_bleu'])}。"
    )
    lines.append(
        f"- 在输出格式约束方面，`{overall_best_json['model_name']}` 的 JSON 格式正确率最高，为 {format_rate(overall_best_json['buckets']['overall']['json_rate'])}。"
    )
    lines.append(
        f"- 双表场景中，ROUGE-1 最优模型为 `{two_best['model_name']}`，得分为 {format_score(two_best['buckets']['two_table']['avg_rouge1'])}。"
    )
    lines.append(
        f"- 三表场景中，ROUGE-1 最优模型为 `{three_best['model_name']}`，得分为 {format_score(three_best['buckets']['three_table']['avg_rouge1'])}。"
    )

    gap_lines = []
    for item in results:
        two_score = item["buckets"]["two_table"]["avg_rouge1"]
        three_score = item["buckets"]["three_table"]["avg_rouge1"]
        gap_lines.append((item["model_name"], three_score - two_score))
    gap_lines.sort(key=lambda x: x[1], reverse=True)
    best_gap_model, best_gap_value = gap_lines[0]
    worst_gap_model, worst_gap_value = gap_lines[-1]
    lines.append(
        f"- 从双表到三表的 ROUGE-1 变化看，`{best_gap_model}` 提升最明显（{best_gap_value:+.2f}），而 `{worst_gap_model}` 变化最弱（{worst_gap_value:+.2f}）。"
    )
    lines.append("")
    return lines


def build_metric_winners(results):
    lines = ["## 二、分指标最优模型", ""]
    for bucket_name in BUCKETS:
        lines.append(f"### {BUCKET_LABELS[bucket_name]}")
        lines.append("")
        lines.append("| 指标 | 最优模型 | 数值 |")
        lines.append("| --- | --- | ---: |")
        for metric_name in METRICS:
            best_item = get_best_model(results, bucket_name, metric_name)
            best_value = best_item["buckets"][bucket_name][metric_name]
            formatted = format_rate(best_value) if metric_name == "json_rate" else format_score(best_value)
            lines.append(f"| {METRIC_LABELS[metric_name]} | {best_item['model_name']} | {formatted} |")
        lines.append("")
    return lines


def build_bucket_tables(results):
    lines = ["## 三、分场景结果对比", ""]
    for bucket_name in BUCKETS:
        lines.append(f"### {BUCKET_LABELS[bucket_name]}")
        lines.append("")
        lines.append(build_summary_table(results, bucket_name))
        lines.append("")
    return lines


def build_model_analysis(results):
    lines = ["## 四、模型结果解读", ""]
    for item in sorted(results, key=lambda x: x["buckets"]["overall"]["avg_rouge1"], reverse=True):
        overall = item["buckets"]["overall"]
        two_table = item["buckets"]["two_table"]
        three_table = item["buckets"]["three_table"]
        lines.append(f"### {item['model_name']}")
        lines.append("")
        lines.append(
            f"- 总体结果：JSON格式正确率 {format_rate(overall['json_rate'])}，ROUGE-1 {format_score(overall['avg_rouge1'])}，"
            f"ROUGE-L {format_score(overall['avg_rouge_l'])}，BLEU {format_score(overall['avg_bleu'])}。"
        )
        lines.append(
            f"- 双表到三表变化：ROUGE-1 {format_score(two_table['avg_rouge1'])} -> {format_score(three_table['avg_rouge1'])}，"
            f"ROUGE-L {format_score(two_table['avg_rouge_l'])} -> {format_score(three_table['avg_rouge_l'])}，"
            f"BLEU {format_score(two_table['avg_bleu'])} -> {format_score(three_table['avg_bleu'])}。"
        )
        if three_table["avg_rouge1"] >= two_table["avg_rouge1"]:
            lines.append("- 现象分析：该模型在三表样本上的文本匹配表现不低于双表样本，说明其在复杂 Schema 条件下仍保持了较好的结构生成稳定性。")
        else:
            lines.append("- 现象分析：该模型在三表样本上的文本匹配表现低于双表样本，说明随着表结构复杂度上升，其 SQL 组织能力出现了一定下降。")
        lines.append("")
    return lines


def build_final_report(results):
    lines = ["# Text-to-SQL API 模型最终实验报告", ""]
    lines.append("本文基于统一的测试集、统一的提示词格式和统一的阿里百炼 API 调用方式，对多个原始大语言模型的 Text-to-SQL 生成能力进行了横向对比。评价指标包括 JSON 格式正确率、ROUGE-1、ROUGE-L 和 BLEU，并分别从总体、双表和三表三个层面进行统计。")
    lines.append("")
    lines.extend(build_best_observations(results))
    lines.extend(build_metric_winners(results))
    lines.extend(build_bucket_tables(results))
    lines.extend(build_model_analysis(results))
    return "\n".join(lines)


def main():
    args = parse_args()
    results = collect_results(args.model_keys)
    report = build_final_report(results)

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding="utf-8")

    print(report)
    print(f"[OK] Text-to-SQL 最终实验报告已保存到: {output_file}")


if __name__ == "__main__":
    main()
