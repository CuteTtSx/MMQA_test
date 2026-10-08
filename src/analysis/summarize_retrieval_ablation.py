"""
检索消融分析与案例汇总脚本。

支持的用法：
1. 普通消融汇总（单模型）
   - 自动读取对应模型目录下的检索评估报告，输出 `retrieval_ablation_*.md`
   - 示例：
     python src/analysis/summarize_retrieval_ablation.py --table_type three_table --model_name gpt-4o-mini

2. 问题分解器对比
   - 对比 `--model_name` 与 `--compare_model_name` 在同一组实验上的差异
   - 自动输出指标柱状图、转移热力图和中文结论
   - 示例：
     python src/analysis/summarize_retrieval_ablation.py --table_type three_table --model_name gpt-4o-mini --compare_model_name gpt-5.4

3. 案例汇总模式（指定单个 `*_cases.json` 文件）
   - 读取一个案例明细文件，按 Top3 / Top5 / Top10 分组；每个 Top 下再分为“完全命中 / 部分命中 / 完全失败”
   - 示例：
     python src/analysis/summarize_retrieval_ablation.py --cases_file outputs/MTR_evaluate/gpt-4o-mini/e3_three_table_report_cases.json --table_type three_table

4. 案例汇总模式（指定目录）
   - 自动读取目录下所有 `*_cases.json` 文件，并合并输出到一个 Markdown 文件中
   - 示例：
     python src/analysis/summarize_retrieval_ablation.py --cases_file outputs/MTR_evaluate/gpt-4o-mini --table_type three_table

5. 案例汇总模式（自动扫描当前模型目录）
   - 若不传 `--cases_file`，脚本会优先尝试扫描当前 `model_name` 对应输出目录下的 `*{table_type}*_cases.json`
   - 示例：
     python src/analysis/summarize_retrieval_ablation.py --table_type three_table --model_name gpt-4o-mini

常用参数：
- `--table_type`: `two_table` 或 `three_table`
- `--top_k`: 普通汇总 / 双模型对比模式下使用的评估 top_k
- `--cases_top_k_per_round`: 案例模式下指定读取哪个 `top_k_per_round` 档位
- `--output_file`: 指定输出 Markdown 路径

说明：
- 案例汇总文件通常会比较大，因为会完整列出 Top3 / Top5 / Top10 下的全部问题案例。
- 只有显式传入 `--cases_file` 时，才会进入案例汇总模式；否则默认执行原有的普通汇总或双模型对比模式。
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config

EXPERIMENT_FILES = {
    "E1": "e1_{table_type}_report.json",
    "E2": "e2_{table_type}_report.json",
    "E3_PAPER": "e3_paper_{table_type}_report.json",
    "E3": "e3_{table_type}_report.json",
    "E4_HYBRID": "e4_hybrid_{table_type}_report.json",
    "E5_HYBRID_LOCAL": "e5_hybrid_local_{table_type}_report.json",
}
PAIRWISE_CANDIDATES = ["E2", "E3_PAPER", "E3", "E4_HYBRID", "E5_HYBRID_LOCAL"]
BASELINE_PRIORITY = ["E3_PAPER", "E3", "E1", "E2", "E4_HYBRID", "E5_HYBRID_LOCAL"]
STOP = {"the","a","an","of","and","or","to","for","with","who","what","which","is","are","was","were","be","by","in","on","from","at","as","their","his","her","its","than","that","have","has","had","list","find","show","name","names","all","more","less","least","most","both","along","where","whose","when","after","before","into","also","only","between"}
PHRASES = ["both","along with","for which","who have","who has","greater than","less than","at least","at most","ordered by","group by","highest","lowest","earliest","latest","currently","temporary acting"]
PREFERRED_CJK_FONTS = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "WenQuanYi Zen Hei",
    "Arial Unicode MS",
]
MODEL_COMPARISON_METRICS = [
    ("Recall", "baseline_recall", "target_recall", "recall_delta"),
    ("Precision", "baseline_precision", "target_precision", "precision_delta"),
    ("F1", "baseline_f1", "target_f1", "f1_delta"),
    ("MRR", "baseline_mrr", "target_mrr", "mrr_delta"),
    ("MAP@k", "baseline_map_k", "target_map_k", "map_k_delta"),
    ("平均首个命中排名", "baseline_avg_first_match_rank", "target_avg_first_match_rank", "avg_first_match_rank_delta"),
    ("平均命中表数", "baseline_avg_matched_count", "target_avg_matched_count", "avg_matched_delta"),
]
EXPERIMENT_DISPLAY_NAMES = {
    "E3_PAPER": "E1",
    "E3": "E2",
    "E4_HYBRID": "E3",
    "E5_HYBRID_LOCAL": "E4",
}


def rd(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def display_experiment_name(name: str):
    return EXPERIMENT_DISPLAY_NAMES.get(name, name)


def configure_matplotlib_fonts():
    available_fonts = {f.name for f in font_manager.fontManager.ttflist}
    for font_name in PREFERRED_CJK_FONTS:
        if font_name in available_fonts:
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = [font_name] + [f for f in PREFERRED_CJK_FONTS if f != font_name]
            plt.rcParams["axes.unicode_minus"] = False
            sns.set_theme(style="whitegrid", font=font_name)
            return font_name

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = PREFERRED_CJK_FONTS + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    sns.set_theme(style="whitegrid")
    return None


def ff(x):
    return f"{x:.4f}"


def fb(x):
    return "是" if x else "否"


def trunc(text, n=120):
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 3] + "..."


def idx(report, top_k):
    return {item["question_id"]: item for item in report["reports"][str(top_k)]["detailed_metrics"]}


def available_top_ks(report):
    return sorted(int(k) for k in report.get("reports", {}).keys())


def resolve_top_k(reports, requested_top_k):
    common_top_ks = None
    for report in reports.values():
        report_top_ks = set(available_top_ks(report))
        common_top_ks = report_top_ks if common_top_ks is None else common_top_ks & report_top_ks

    common_top_ks = sorted(common_top_ks or [])
    if not common_top_ks:
        raise ValueError("所有报告中都没有可用的 top_k 结果。")

    if requested_top_k in common_top_ks:
        return requested_top_k, False

    lower_or_equal = [k for k in common_top_ks if k <= requested_top_k]
    if lower_or_equal:
        return max(lower_or_equal), True

    return min(common_top_ks), True


def toks(text):
    return [w for w in re.findall(r"[a-zA-Z_]+", text.lower()) if w not in STOP and len(w) >= 3]


def phs(text):
    s = text.lower()
    return [p for p in PHRASES if p in s]


def resolve_reports(table_type: str, model_name: str | None = None):
    reports = {}
    for name, pattern in EXPERIMENT_FILES.items():
        filename = pattern.format(table_type=table_type)
        candidate_paths = [Config.get_mtr_output_path(filename, model_name=model_name)]
        legacy_path = Config.get_legacy_mtr_output_path(filename)
        if legacy_path not in candidate_paths:
            candidate_paths.append(legacy_path)

        for path in candidate_paths:
            if path.exists():
                reports[name] = path
                break
    return reports


def resolve_base_experiment(reports, requested_base_experiment=None):
    if requested_base_experiment:
        if requested_base_experiment not in reports:
            raise ValueError(f"指定的 baseline `{requested_base_experiment}` 不存在于当前可用报告中。")
        return requested_base_experiment

    for name in BASELINE_PRIORITY:
        if name in reports:
            return name

    return next(iter(reports))


def resolve_pairwise_plan(reports, default_base_name):
    plan = []

    if "E2" in reports and "E2" != default_base_name:
        plan.append((default_base_name, "E2"))

    if "E3_PAPER" in reports and "E3" in reports:
        plan.append(("E3_PAPER", "E3"))

    if "E4_HYBRID" in reports and "E3" in reports:
        plan.append(("E3", "E4_HYBRID"))

    if "E5_HYBRID_LOCAL" in reports and "E3" in reports:
        plan.append(("E3", "E5_HYBRID_LOCAL"))

    seen = set()
    ordered_plan = []
    for baseline_name, target_name in plan:
        key = (baseline_name, target_name)
        if baseline_name in reports and target_name in reports and baseline_name != target_name and key not in seen:
            ordered_plan.append(key)
            seen.add(key)

    return ordered_plan


def ablation_rows(reports, top_k):
    rows = []
    for name, report in reports.items():
        metrics = report["reports"][str(top_k)]["average_metrics"]
        rows.append({
            "experiment": name,
            "label": report.get("experiment_label", name),
            "use_decomposition": report.get("use_decomposition", False),
            "use_propagation": report.get("use_propagation", False),
            **metrics,
        })
    return rows


def compare(base_report, target_report, top_k, sample_limit):
    base_items = idx(base_report, top_k)
    target_items = idx(target_report, top_k)
    cats = {"improved": [], "worsened": [], "unchanged": []}
    trans = Counter()
    phrase_counter = {"improved": Counter(), "worsened": Counter()}
    token_counter = {"improved": Counter(), "worsened": Counter()}

    for qid, base_item in base_items.items():
        target_item = target_items.get(qid)
        if not target_item:
            continue
        trans[f"{base_item['matched_count']} -> {target_item['matched_count']}"] += 1
        recall_delta = target_item["recall"] - base_item["recall"]
        mrr_delta = target_item["mrr"] - base_item["mrr"]
        matched_delta = target_item["matched_count"] - base_item["matched_count"]
        rec = {
            "question_id": qid,
            "question": target_item["question"],
            "baseline_recall": base_item["recall"],
            "target_recall": target_item["recall"],
            "recall_delta": recall_delta,
            "baseline_matched": base_item["matched_count"],
            "target_matched": target_item["matched_count"],
            "matched_delta": matched_delta,
            "baseline_mrr": base_item["mrr"],
            "target_mrr": target_item["mrr"],
            "mrr_delta": mrr_delta,
        }
        bucket = "improved" if recall_delta > 0 else "worsened" if recall_delta < 0 else "unchanged"
        cats[bucket].append(rec)
        if bucket in ("improved", "worsened"):
            for p in phs(target_item["question"]):
                phrase_counter[bucket][p] += 1
            for w in toks(target_item["question"]):
                token_counter[bucket][w] += 1

    cats["improved"].sort(key=lambda x: (x["recall_delta"], x["matched_delta"], x["mrr_delta"]), reverse=True)
    cats["worsened"].sort(key=lambda x: (x["recall_delta"], x["matched_delta"], x["mrr_delta"]))
    total = max(len(base_items), 1)
    all_records = [r for arr in cats.values() for r in arr]
    return {
        "improved_count": len(cats["improved"]),
        "worsened_count": len(cats["worsened"]),
        "unchanged_count": len(cats["unchanged"]),
        "examples_improved": cats["improved"][:sample_limit],
        "examples_worsened": cats["worsened"][:sample_limit],
        "avg_recall_delta": sum(x["recall_delta"] for x in all_records) / total,
        "avg_mrr_delta": sum(x["mrr_delta"] for x in all_records) / total,
        "avg_matched_delta": sum(x["matched_delta"] for x in all_records) / total,
        "transition_counter": trans,
        "phrase_counter": phrase_counter,
        "token_counter": token_counter,
    }


def parse_transition_key(key: str):
    left, right = [part.strip() for part in key.split("->")]
    return int(left), int(right)


def build_transition_matrix(counter):
    parsed = [(parse_transition_key(key), count) for key, count in counter.items()]
    if not parsed:
        return [0], [[0]]

    max_value = max(max(src, dst) for (src, dst), _ in parsed)
    labels = list(range(max_value + 1))
    matrix = [[0 for _ in labels] for _ in labels]
    for (src, dst), count in parsed:
        matrix[src][dst] = count
    return labels, matrix


def analyze_transition_matrix(counter):
    if not counter:
        return ["- 无可用的命中表数转移数据。", ""]

    total = sum(counter.values())
    diagonal = 0
    mild_improve = 0
    large_improve = 0
    mild_worsen = 0
    large_worsen = 0

    for key, count in counter.items():
        src, dst = parse_transition_key(key)
        delta = dst - src
        if delta == 0:
            diagonal += count
        elif delta > 0:
            if delta == 1:
                mild_improve += count
            else:
                large_improve += count
        else:
            if delta == -1:
                mild_worsen += count
            else:
                large_worsen += count

    stable_ratio = diagonal / total if total else 0.0
    improve_ratio = (mild_improve + large_improve) / total if total else 0.0
    worsen_ratio = (mild_worsen + large_worsen) / total if total else 0.0

    lines = ["### 转移矩阵幅度分析", ""]
    lines.append(f"- 主对角线（命中表数不变）共有 {diagonal} 题，占比 {stable_ratio:.2%}，说明大多数题目在更换问题分解器后保持稳定。")
    lines.append(
        f"- 改善方向共有 {mild_improve + large_improve} 题，占比 {improve_ratio:.2%}；其中小幅补表（如 0→1、1→2、2→3）为 {mild_improve} 题，大幅补表（如 0→2、0→3、1→3）为 {large_improve} 题。"
    )
    lines.append(
        f"- 退化方向共有 {mild_worsen + large_worsen} 题，占比 {worsen_ratio:.2%}；其中小幅退化（如 3→2、2→1、1→0）为 {mild_worsen} 题，大幅退化（如 3→1、3→0、2→0）为 {large_worsen} 题。"
    )

    if large_improve > large_worsen:
        lines.append("- 从幅度上看，当前转移矩阵以**大幅补表增益**更突出，说明新分解器在部分复杂题上能显著补回原本遗漏的相关表。")
    elif large_worsen > large_improve:
        lines.append("- 从幅度上看，当前转移矩阵以**大幅退化**更突出，说明虽然有题目改善，但少量严重退化样本会显著拉低总体平均指标。")
    elif mild_improve > mild_worsen:
        lines.append("- 当前变化主要表现为**小幅补表增益**，即更多题目只是多命中 1 张表，而不是从完全错误跃升到完全正确。")
    elif mild_worsen > mild_improve:
        lines.append("- 当前变化主要表现为**小幅退化**，即更多题目只是少命中 1 张表，但这类细小退化在总体上仍会侵蚀平均指标。")
    else:
        lines.append("- 改善与退化在幅度结构上较为接近，说明更换问题分解器后整体分布变化有限。")

    lines.append("")
    return lines


def render_transition_heatmap(counter, output_path: Path, title: str, base_model_name: str, target_model_name: str):
    labels, matrix = build_transition_matrix(counter)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 5))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        cbar=True,
        linewidths=0.5,
        linecolor="white",
    )
    plt.xlabel(f"{target_model_name} 命中表数")
    plt.ylabel(f"{base_model_name} 命中表数")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


def intersect_experiment_reports(table_type: str, base_model_name: str, target_model_name: str):
    base_reports = resolve_reports(table_type, base_model_name)
    target_reports = resolve_reports(table_type, target_model_name)
    common = sorted(set(base_reports) & set(target_reports))
    if not common:
        raise FileNotFoundError(
            f"模型 `{base_model_name}` 与 `{target_model_name}` 在 {table_type} 下没有可共同对比的实验报告。"
        )
    return ({name: base_reports[name] for name in common}, {name: target_reports[name] for name in common})


def md_ablation(rows):
    headers = ["实验", "设置", "问题分解", "关系传播", "Recall", "Precision", "F1", "MRR", "MAP@k", "平均首个命中排名", "平均命中表数"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join([
            r["experiment"], r["label"], fb(r["use_decomposition"]), fb(r["use_propagation"]), ff(r["recall"]),
            ff(r["precision"]), ff(r["f1"]), ff(r["mrr"]), ff(r["map_k"]), ff(r["avg_first_match_rank"]), ff(r["avg_matched_count"])
        ]) + " |")
    return "\n".join(lines)


def md_pairwise(results):
    headers = ["对比实验", "改善题数", "退化题数", "持平题数", "平均 Recall 变化", "平均 MRR 变化", "平均命中表数变化"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for res in results:
        compare_name = res.get("compare_name") or f"{res['target_name']} vs {res['baseline_name']}"
        lines.append("| " + " | ".join([
            compare_name,
            str(res["improved_count"]), str(res["worsened_count"]), str(res["unchanged_count"]),
            ff(res["avg_recall_delta"]), ff(res["avg_mrr_delta"]), ff(res["avg_matched_delta"])
        ]) + " |")
    return "\n".join(lines)


def md_model_comparison_overview(rows, base_model_name, target_model_name):
    headers = [
        "实验",
        "设置",
        f"Recall ({base_model_name})",
        f"Recall ({target_model_name})",
        "Recall 差值",
        f"Precision ({base_model_name})",
        f"Precision ({target_model_name})",
        "Precision 差值",
        f"F1 ({base_model_name})",
        f"F1 ({target_model_name})",
        "F1 差值",
        f"MRR ({base_model_name})",
        f"MRR ({target_model_name})",
        "MRR 差值",
        f"MAP@k ({base_model_name})",
        f"MAP@k ({target_model_name})",
        "MAP@k 差值",
        f"平均首个命中排名 ({base_model_name})",
        f"平均首个命中排名 ({target_model_name})",
        "首个命中排名差值",
        f"平均命中表数 ({base_model_name})",
        f"平均命中表数 ({target_model_name})",
        "命中表数差值",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join([
            r["display_experiment"],
            r["label"],
            ff(r["baseline_recall"]),
            ff(r["target_recall"]),
            ff(r["recall_delta"]),
            ff(r["baseline_precision"]),
            ff(r["target_precision"]),
            ff(r["precision_delta"]),
            ff(r["baseline_f1"]),
            ff(r["target_f1"]),
            ff(r["f1_delta"]),
            ff(r["baseline_mrr"]),
            ff(r["target_mrr"]),
            ff(r["mrr_delta"]),
            ff(r["baseline_map_k"]),
            ff(r["target_map_k"]),
            ff(r["map_k_delta"]),
            ff(r["baseline_avg_first_match_rank"]),
            ff(r["target_avg_first_match_rank"]),
            ff(r["avg_first_match_rank_delta"]),
            ff(r["baseline_avg_matched_count"]),
            ff(r["target_avg_matched_count"]),
            ff(r["avg_matched_delta"]),
        ]) + " |")
    return "\n".join(lines)


def render_experiment_metric_bar_chart(row, output_path: Path, base_model_name: str, target_model_name: str):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metric_labels = [metric_label for metric_label, _, _, _ in MODEL_COMPARISON_METRICS]
    baseline_values = [row[baseline_key] for _, baseline_key, _, _ in MODEL_COMPARISON_METRICS]
    target_values = [row[target_key] for _, _, target_key, _ in MODEL_COMPARISON_METRICS]
    delta_values = [row[delta_key] for _, _, _, delta_key in MODEL_COMPARISON_METRICS]

    spacing = 0.68
    x_positions = [idx * spacing for idx in range(len(metric_labels))]
    width = 0.17

    fig, ax = plt.subplots(figsize=(7.6, 6.0))
    left_positions = [x - width / 2 for x in x_positions]
    right_positions = [x + width / 2 for x in x_positions]

    ax.bar(left_positions, baseline_values, width=width, label=base_model_name, color="#c9e2f5")
    ax.bar(right_positions, target_values, width=width, label=target_model_name, color="#f8d9b9")

    ax.set_title(f"{row['display_experiment']}：不同问题分解器下各指标对比")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(metric_labels, rotation=18, ha="right")
    ax.set_ylabel("指标数值")
    ax.margins(x=0.015)

    for x, baseline_val, target_val, delta_val in zip(x_positions, baseline_values, target_values, delta_values):
        top = max(baseline_val, target_val)
        reference = max(abs(top), 0.1)
        offset = reference * 0.03
        ax.text(x, top + offset, f"Δ={delta_val:+.4f}", ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#333333")

    ax.legend(loc="best")
    fig.tight_layout(pad=0.6)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def summarize_model_differences(rows):
    if not rows:
        return []

    best_recall_gain = max(rows, key=lambda x: x["recall_delta"])
    worst_recall_gain = min(rows, key=lambda x: x["recall_delta"])
    best_mrr_gain = max(rows, key=lambda x: x["mrr_delta"])

    lines = ["## 一、核心结论", ""]
    lines.append(
        f"- 从 Recall 看，问题分解器替换带来的**最大正向收益**出现在 `{best_recall_gain['display_experiment']}`，"
        f"由 {ff(best_recall_gain['baseline_recall'])} 提升到 {ff(best_recall_gain['target_recall'])}，变化 {best_recall_gain['recall_delta']:+.4f}。"
    )
    lines.append(
        f"- 从 MRR 看，排序质量提升最明显的也是 `{best_mrr_gain['display_experiment']}`，"
        f"由 {ff(best_mrr_gain['baseline_mrr'])} 提升到 {ff(best_mrr_gain['target_mrr'])}，变化 {best_mrr_gain['mrr_delta']:+.4f}。"
    )
    if worst_recall_gain["recall_delta"] < 0:
        lines.append(
            f"- 并非所有检索策略都会因更换问题分解器而收益；在 `{worst_recall_gain['display_experiment']}` 中，"
            f"Recall 反而从 {ff(worst_recall_gain['baseline_recall'])} 下降到 {ff(worst_recall_gain['target_recall'])}，变化 {worst_recall_gain['recall_delta']:+.4f}。"
        )
    near_zero = [r["display_experiment"] for r in rows if abs(r["recall_delta"]) < 0.005 and abs(r["mrr_delta"]) < 0.005]
    if near_zero:
        lines.append(f"- 在 `{', '.join(near_zero)}` 中，两种问题分解器的整体表现接近，说明后续检索与传播机制对分解器差异具有一定缓冲作用。")
    lines.append("")
    return lines


def md_transition(counter):
    lines = ["| 命中表数转移 | 题数 |", "| --- | --- |"]
    for t, c in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {t} | {c} |")
    return "\n".join(lines)


def md_counter(title, counter, top_n):
    lines = [f"### {title}", ""]
    if not counter:
        return lines + ["- 无", ""]
    lines += ["| 模式 / 关键词 | 次数 |", "| --- | --- |"]
    for k, v in counter.most_common(top_n):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    return lines


def md_examples(title, records):
    lines = [f"### {title}", ""]
    if not records:
        return lines + ["- 无", ""]
    for x in records:
        lines.append(f"- Q{x['question_id']}: {trunc(x['question'])} | 命中表数 {x['baseline_matched']} -> {x['target_matched']} | Recall {ff(x['baseline_recall'])} -> {ff(x['target_recall'])} | MRR {ff(x['baseline_mrr'])} -> {ff(x['target_mrr'])}")
    lines.append("")
    return lines


def load_cases(cases_path: Path, top_k_per_round: int | None = None):
    data = rd(cases_path)
    cases_by_round = data.get("cases_by_top_k_per_round", {})
    if not cases_by_round:
        raise ValueError(f"案例文件 {cases_path} 中没有 cases_by_top_k_per_round。")

    available_rounds = sorted(int(k) for k in cases_by_round.keys())
    selected_round = top_k_per_round if top_k_per_round in available_rounds else available_rounds[0]
    return data, cases_by_round[str(selected_round)], selected_round


def discover_case_files(cases_file_arg: str | None, table_type: str, model_name: str | None):
    if cases_file_arg:
        target = Path(cases_file_arg)
        if target.is_dir():
            files = sorted(target.glob("*_cases.json"))
        else:
            files = [target]
    else:
        search_dirs = [Config.get_mtr_model_output_dir(model_name), Config.MTR_OUTPUT_DIR, Path.cwd()]
        files = []
        seen = set()
        for directory in search_dirs:
            if not directory.exists():
                continue
            for path in sorted(directory.glob(f"*{table_type}*_cases.json")):
                resolved = str(path.resolve())
                if resolved not in seen:
                    files.append(path)
                    seen.add(resolved)

    existing_files = [path for path in files if path.exists()]
    if not existing_files:
        raise FileNotFoundError("未找到可用的 *_cases.json 文件。")
    return existing_files


def group_cases_by_match_type(cases, top_k: int):
    def matched_count(case):
        retrieval_case = case.get("retrieval_cases", {}).get(str(top_k), {})
        return retrieval_case.get("matched_count", 0)

    perfect_cases = sorted(
        [case for case in cases if matched_count(case) == case.get("ground_truth_count", 0)],
        key=lambda x: x.get("question_id", 0),
    )
    partial_cases = sorted(
        [case for case in cases if 0 < matched_count(case) < case.get("ground_truth_count", 0)],
        key=lambda x: (-matched_count(x), x.get("question_id", 0)),
    )
    failed_cases = sorted(
        [case for case in cases if matched_count(case) == 0],
        key=lambda x: x.get("question_id", 0),
    )

    return {
        "perfect": perfect_cases,
        "partial": partial_cases,
        "failed": failed_cases,
    }


def md_case_table(case, top_k: int):
    retrieval_case = case.get("retrieval_cases", {}).get(str(top_k), {})
    retrieved_tables = retrieval_case.get("retrieved_tables", [])
    lines = [
        f"##### Q{case['question_id']} 案例",
        "",
        f"- 问题：{case['question']}",
        f"- 实际正确表（{case['ground_truth_count']} 张）：`{"`, `".join(case.get('ground_truth_tables', []))}`",
        f"- Top-{top_k} 候选中命中 {retrieval_case.get('matched_count', 0)} 张",
        "",
        "| 排名 | 检索表 | 是否正确 |",
        "| --- | --- | --- |",
    ]
    for table in retrieved_tables:
        lines.append(f"| {table['rank']} | `{table['table_name']}` | {table['match_mark']} |")
    lines.append("")
    return lines


def build_cases_markdown(cases_files, table_type: str, model_name: str | None, top_k_per_round: int | None = None):
    lines = [
        f"# 检索案例汇总（{table_type}）",
        "",
        f"- 检索目录：`{Config.get_mtr_model_output_dir(model_name)}`",
        f"- 案例文件数量：`{len(cases_files)}`",
        "",
        "> 文件可能较大，因为会按 Top3 / Top5 / Top10 分组，并在每个分组下完整列出完全命中、部分命中和完全失败案例。",
        "",
    ]

    for cases_path in cases_files:
        data, cases, selected_round = load_cases(cases_path, top_k_per_round)
        lines.extend([
            f"## 文件：`{cases_path.name}`",
            "",
            f"- 实验标签：`{data.get('experiment_label', '')}`",
            f"- 表类型：`{'three_table' if data.get('table_num') == 3 else 'two_table'}`",
            f"- 采用的 top_k_per_round：`{selected_round}`",
            "",
        ])

        note = data.get("cases_top_k_note")
        if note:
            lines.extend([f"> {note}", ""])

        candidate_top_ks = data.get("candidate_top_k_values", [3, 5, 10])
        for top_k in candidate_top_ks:
            grouped_cases = group_cases_by_match_type(cases, top_k)
            lines.extend([f"### Top-{top_k}", ""])

            category_titles = [
                ("perfect", "#### 完全命中案例"),
                ("partial", "#### 部分命中案例"),
                ("failed", "#### 完全失败案例"),
            ]

            for category_key, category_title in category_titles:
                category_cases = grouped_cases.get(category_key, [])
                lines.extend([category_title, ""])
                if not category_cases:
                    lines.extend(["- 无", ""])
                    continue
                for case in category_cases:
                    lines.extend(md_case_table(case, top_k))

    return "\n".join(lines)


def build_report(rows, pairwise_results, top_n, table_type, base_name, actual_top_k):
    best_recall = max(rows, key=lambda r: r["recall"])
    best_mrr = max(rows, key=lambda r: r["mrr"])
    best_map = max(rows, key=lambda r: r["map_k"])
    base = next(r for r in rows if r["experiment"] == base_name)
    lines = [f"# {table_type} 检索消融实验与错误类型分析", "", f"- 本报告实际使用的评估 Top-K：`{actual_top_k}`", ""]
    lines += ["## 一、关键观察", ""]
    for r in rows:
        if r["experiment"] == base_name:
            continue
        lines.append(f"- `{r['experiment']}` 相对 `{base_name}`：Recall {r['recall'] - base['recall']:+.4f}，MRR {r['mrr'] - base['mrr']:+.4f}")
    lines += ["", "## 二、最佳指标", ""]
    lines += [f"- 最佳 Recall：`{best_recall['experiment']}` = {ff(best_recall['recall'])}", f"- 最佳 MRR：`{best_mrr['experiment']}` = {ff(best_mrr['mrr'])}", f"- 最佳 MAP@k：`{best_map['experiment']}` = {ff(best_map['map_k'])}", ""]
    lines += ["## 三、消融实验对照表", "", md_ablation(rows), "", "## 四、逐题对比汇总", "", md_pairwise(pairwise_results), ""]
    for res in pairwise_results:
        baseline_name = res["baseline_name"]
        target_name = res["target_name"]
        lines += [f"## 五、{target_name} 相对 {baseline_name} 的错误类型分析", ""]
        lines += [f"- 改善题数：{res['improved_count']}", f"- 退化题数：{res['worsened_count']}", f"- 持平题数：{res['unchanged_count']}", f"- 平均 Recall 变化：{ff(res['avg_recall_delta'])}", f"- 平均 MRR 变化：{ff(res['avg_mrr_delta'])}", f"- 平均命中表数变化：{ff(res['avg_matched_delta'])}", ""]
        lines += ["### 命中表数转移矩阵", "", md_transition(res["transition_counter"]), ""]
        lines += md_counter("改善题中的高频短语模式", res["phrase_counter"]["improved"], top_n)
        lines += md_counter("退化题中的高频短语模式", res["phrase_counter"]["worsened"], top_n)
        lines += md_counter("改善题中的高频关键词", res["token_counter"]["improved"], top_n)
        lines += md_counter("退化题中的高频关键词", res["token_counter"]["worsened"], top_n)
        lines += md_examples("代表性改善样例", res["examples_improved"])
        lines += md_examples("代表性退化样例", res["examples_worsened"])
    return "\n".join(lines)


def build_model_comparison_report(rows, pairwise_results, top_n, table_type, base_model_name, target_model_name, actual_top_k, experiment_chart_images=None):
    lines = [
        f"# {table_type} 问题分解器模型对比分析",
        "",
        f"- 基线模型：`{base_model_name}`",
        f"- 对比模型：`{target_model_name}`",
        f"- 本报告实际使用的评估 Top-K：`{actual_top_k}`",
        "",
    ]
    lines += summarize_model_differences(rows)
    lines += [
        "## 二、按实验汇总的问题分解器差异",
        "",
        md_model_comparison_overview(rows, base_model_name, target_model_name),
        "",
    ]
    if experiment_chart_images:
        lines += ["### 各实验指标柱状图", ""]
        for experiment_name in sorted(experiment_chart_images):
            chart_path = experiment_chart_images[experiment_name]
            experiment_display_name = display_experiment_name(experiment_name)
            lines += [
                f"#### {experiment_display_name} 指标对比",
                "",
                f"![{experiment_display_name} 指标柱状图]({chart_path})",
                "",
            ]
    lines += [
        "## 三、逐题层面的差异统计",
        "",
        md_pairwise(pairwise_results),
        "",
    ]

    for res in pairwise_results:
        experiment_name = res["experiment_name"]
        experiment_display_name = display_experiment_name(experiment_name)
        lines += [f"## 四、实验 {experiment_display_name} 中 `{target_model_name}` 相对 `{base_model_name}` 的逐题差异", ""]
        lines += [
            f"- 对比实验：`{res['compare_name']}`",
            f"- 改善题数：{res['improved_count']}",
            f"- 退化题数：{res['worsened_count']}",
            f"- 持平题数：{res['unchanged_count']}",
            f"- 平均 Recall 变化：{ff(res['avg_recall_delta'])}",
            f"- 平均 MRR 变化：{ff(res['avg_mrr_delta'])}",
            f"- 平均命中表数变化：{ff(res['avg_matched_delta'])}",
            "",
        ]
        if res.get("transition_matrix_image"):
            lines += ["### 命中表数转移热力图", "", f"![{experiment_display_name} 转移热力图]({res['transition_matrix_image']})", ""]
        lines += ["### 命中表数转移矩阵", "", md_transition(res["transition_counter"]), ""]
        lines += analyze_transition_matrix(res["transition_counter"])
        lines += md_counter("改善题中的高频短语模式", res["phrase_counter"]["improved"], top_n)
        lines += md_counter("退化题中的高频短语模式", res["phrase_counter"]["worsened"], top_n)
        lines += md_counter("改善题中的高频关键词", res["token_counter"]["improved"], top_n)
        lines += md_counter("退化题中的高频关键词", res["token_counter"]["worsened"], top_n)
        lines += md_examples("代表性改善样例", res["examples_improved"])
        lines += md_examples("代表性退化样例", res["examples_worsened"])

    return "\n".join(lines)


def parse_args():
    p = argparse.ArgumentParser(description="汇总检索消融实验并输出中文分析")
    p.add_argument("--table_type", choices=["two_table", "three_table"], default="three_table")
    p.add_argument("--top_k", type=int, default=Config.MTR_CONFIG.get("top_k", 3))
    p.add_argument("--sample_limit", type=int, default=10)
    p.add_argument("--top_n", type=int, default=10)
    p.add_argument("--base_experiment", type=str, default=None, help="默认优先使用 E1，若不存在则使用首个可用实验")
    p.add_argument("--model_name", type=str, default=Config.DECOMPOSER_CONFIG["model"], help="问题分解器模型名，用于定位对应输出目录")
    p.add_argument("--compare_model_name", type=str, default=None, help="若提供，则进入双模型对比模式，比较该模型相对 --model_name 的差异")
    p.add_argument("--cases_file", type=str, default=None, help="若提供 *_cases.json 或目录，则进入案例汇总模式；为空时自动扫描当前模型输出目录下的 *_cases.json")
    p.add_argument("--cases_top_k_per_round", type=int, default=None, help="案例模式下指定使用哪个 top_k_per_round 档位")
    p.add_argument("--output_file", type=str, default=None)
    return p.parse_args()


def main():
    args = parse_args()
    selected_font = configure_matplotlib_fonts()
    if selected_font:
        print(f"[INFO] matplotlib 已启用中文字体: {selected_font}")
    else:
        print("[WARN] 未检测到常见中文字体，图中中文可能仍显示异常。")

    if args.cases_file:
        case_files = discover_case_files(args.cases_file, args.table_type, args.model_name)
        if not case_files:
            raise FileNotFoundError("未找到可用的 *_cases.json 文件。")
        summary = build_cases_markdown(case_files, args.table_type, args.model_name, args.cases_top_k_per_round)
        first_case_path = case_files[0]
        output_file = args.output_file or str(first_case_path.parent / f"cases_summary_{args.table_type}.md")
    elif args.compare_model_name:
        base_report_paths, target_report_paths = intersect_experiment_reports(
            args.table_type, args.model_name, args.compare_model_name
        )
        base_reports = {name: rd(path) for name, path in base_report_paths.items()}
        target_reports = {name: rd(path) for name, path in target_report_paths.items()}

        resolved_top_k, fallback_used = resolve_top_k({**base_reports, **target_reports}, args.top_k)
        if fallback_used:
            print(f"[WARN] 请求的 top_k={args.top_k} 在当前双模型报告中不存在，已自动回退到共同可用的 top_k={resolved_top_k}")

        output_file = args.output_file or str(
            Config.get_mtr_output_path(
                f"model_compare_{Config.normalize_model_name(args.model_name)}_vs_{Config.normalize_model_name(args.compare_model_name)}_{args.table_type}.md",
                model_name=args.compare_model_name,
            )
        )
        out = Path(output_file)
        image_dir = out.parent / f"{out.stem}_assets"

        rows = []
        pairwise_results = []
        for experiment_name in sorted(base_reports.keys()):
            base_report = base_reports[experiment_name]
            target_report = target_reports[experiment_name]
            base_metrics = base_report["reports"][str(resolved_top_k)]["average_metrics"]
            target_metrics = target_report["reports"][str(resolved_top_k)]["average_metrics"]
            rows.append({
                "experiment": experiment_name,
                "display_experiment": display_experiment_name(experiment_name),
                "label": base_report.get("experiment_label", experiment_name),
                "use_decomposition": base_report.get("use_decomposition", False),
                "use_propagation": base_report.get("use_propagation", False),
                "baseline_recall": base_metrics["recall"],
                "target_recall": target_metrics["recall"],
                "recall_delta": target_metrics["recall"] - base_metrics["recall"],
                "baseline_precision": base_metrics["precision"],
                "target_precision": target_metrics["precision"],
                "precision_delta": target_metrics["precision"] - base_metrics["precision"],
                "baseline_f1": base_metrics["f1"],
                "target_f1": target_metrics["f1"],
                "f1_delta": target_metrics["f1"] - base_metrics["f1"],
                "baseline_mrr": base_metrics["mrr"],
                "target_mrr": target_metrics["mrr"],
                "mrr_delta": target_metrics["mrr"] - base_metrics["mrr"],
                "baseline_map_k": base_metrics["map_k"],
                "target_map_k": target_metrics["map_k"],
                "map_k_delta": target_metrics["map_k"] - base_metrics["map_k"],
                "baseline_avg_first_match_rank": base_metrics["avg_first_match_rank"],
                "target_avg_first_match_rank": target_metrics["avg_first_match_rank"],
                "avg_first_match_rank_delta": target_metrics["avg_first_match_rank"] - base_metrics["avg_first_match_rank"],
                "baseline_avg_matched_count": base_metrics["avg_matched_count"],
                "target_avg_matched_count": target_metrics["avg_matched_count"],
                "avg_matched_delta": target_metrics["avg_matched_count"] - base_metrics["avg_matched_count"],
            })

            result = compare(base_report, target_report, resolved_top_k, args.sample_limit)
            result["baseline_name"] = args.model_name
            result["target_name"] = args.compare_model_name
            result["experiment_name"] = experiment_name
            result["compare_name"] = f"{display_experiment_name(experiment_name)}: {args.compare_model_name} vs {args.model_name}"

            heatmap_path = image_dir / f"{experiment_name.lower()}_transition_heatmap.png"
            render_transition_heatmap(
                result["transition_counter"],
                heatmap_path,
                f"{display_experiment_name(experiment_name)}: {args.compare_model_name} vs {args.model_name}",
                args.model_name,
                args.compare_model_name,
            )
            result["transition_matrix_image"] = heatmap_path.relative_to(out.parent).as_posix()
            pairwise_results.append(result)

        experiment_chart_images = {}
        for row in rows:
            chart_path = image_dir / f"{row['experiment'].lower()}_metric_bar_chart.png"
            render_experiment_metric_bar_chart(row, chart_path, args.model_name, args.compare_model_name)
            experiment_chart_images[row["experiment"]] = chart_path.relative_to(out.parent).as_posix()

        summary = build_model_comparison_report(
            rows, pairwise_results, args.top_n, args.table_type, args.model_name, args.compare_model_name, resolved_top_k, experiment_chart_images
        )
    else:
        report_paths = resolve_reports(args.table_type, args.model_name)
        if not report_paths:
            raise FileNotFoundError(
                f"在 {Config.get_mtr_model_output_dir(args.model_name)} 及旧版目录 {Config.MTR_OUTPUT_DIR} 下未找到 {args.table_type} 的评估报告文件。"
            )

        reports = {name: rd(path) for name, path in report_paths.items()}
        resolved_top_k, fallback_used = resolve_top_k(reports, args.top_k)
        if fallback_used:
            print(f"[WARN] 请求的 top_k={args.top_k} 在当前 {args.table_type} 报告中不存在，已自动回退到共同可用的 top_k={resolved_top_k}")

        rows = ablation_rows(reports, resolved_top_k)
        if not rows:
            raise ValueError(f"未在报告中找到 top_k={resolved_top_k} 的评估结果。")

        base_name = resolve_base_experiment(reports, args.base_experiment)
        pairwise_plan = resolve_pairwise_plan(reports, base_name)
        pairwise_results = []
        for baseline_name, target_name in pairwise_plan:
            result = compare(reports[baseline_name], reports[target_name], resolved_top_k, args.sample_limit)
            result["baseline_name"] = baseline_name
            result["target_name"] = target_name
            pairwise_results.append(result)

        summary = build_report(rows, pairwise_results, args.top_n, args.table_type, base_name, resolved_top_k)
        output_file = args.output_file or str(
            Config.get_mtr_output_path(f"retrieval_ablation_{args.table_type}.md", model_name=args.model_name)
        )

    out = Path(output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary, encoding="utf-8")
    print(summary)
    print(f"[OK] 中文分析报告已保存到: {out}")


if __name__ == "__main__":
    main()
