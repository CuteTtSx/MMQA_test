import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

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


def rd(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def resolve_reports(table_type: str):
    reports = {}
    for name, pattern in EXPERIMENT_FILES.items():
        path = Config.get_mtr_output_path(pattern.format(table_type=table_type))
        if path.exists():
            reports[name] = path
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
    headers = ["相对基线实验", "改善题数", "退化题数", "持平题数", "平均 Recall 变化", "平均 MRR 变化", "平均命中表数变化"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for res in results:
        lines.append("| " + " | ".join([
            f"{res['target_name']} vs {res['baseline_name']}",
            str(res["improved_count"]), str(res["worsened_count"]), str(res["unchanged_count"]),
            ff(res["avg_recall_delta"]), ff(res["avg_mrr_delta"]), ff(res["avg_matched_delta"])
        ]) + " |")
    return "\n".join(lines)


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


def parse_args():
    p = argparse.ArgumentParser(description="汇总检索消融实验并输出中文分析")
    p.add_argument("--table_type", choices=["two_table", "three_table"], default="three_table")
    p.add_argument("--top_k", type=int, default=Config.MTR_CONFIG.get("top_k", 3))
    p.add_argument("--sample_limit", type=int, default=10)
    p.add_argument("--top_n", type=int, default=10)
    p.add_argument("--base_experiment", type=str, default=None, help="默认优先使用 E1，若不存在则使用首个可用实验")
    p.add_argument("--output_file", type=str, default=None)
    return p.parse_args()


def main():
    args = parse_args()
    report_paths = resolve_reports(args.table_type)
    if not report_paths:
        raise FileNotFoundError(f"在 {Config.MTR_OUTPUT_DIR} 下未找到 {args.table_type} 的评估报告文件。")

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

    output_file = args.output_file or str(Config.get_mtr_output_path(f"retrieval_ablation_{args.table_type}.md"))
    out = Path(output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary, encoding="utf-8")
    print(summary)
    print(f"[OK] 中文分析报告已保存到: {out}")


if __name__ == "__main__":
    main()
