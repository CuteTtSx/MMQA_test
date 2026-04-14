import argparse, json, re
from collections import Counter
from pathlib import Path

REPORTS={"E1":"outputs/MTR_evaluate/e1_three_table_report.json","E2":"outputs/MTR_evaluate/e2_three_table_report.json","E3":"outputs/MTR_evaluate/e3_three_table_report.json","E3_PAPER":"outputs/MTR_evaluate/e3_paper_three_table_report.json"}
PAIRWISE=["E2","E3","E3_PAPER"]
STOP={"the","a","an","of","and","or","to","for","with","who","what","which","is","are","was","were","be","by","in","on","from","at","as","their","his","her","its","than","that","have","has","had","list","find","show","name","names","all","more","less","least","most","both","along","where","whose","when","after","before","into","also","only","between"}
PHRASES=["both","along with","for which","who have","who has","greater than","less than","at least","at most","ordered by","group by","highest","lowest","earliest","latest","currently","temporary acting"]


def rd(p):
    with Path(p).open("r",encoding="utf-8") as f:return json.load(f)

def ff(x): return f"{x:.4f}"
def fb(x): return "是" if x else "否"
def trunc(t,n=120): t=" ".join(t.split()); return t if len(t)<=n else t[:n-3]+"..."
def idx(rep,k): return {x["question_id"]:x for x in rep["reports"][str(k)]["detailed_metrics"]}

def toks(t):
    return [w for w in re.findall(r"[a-zA-Z_]+",t.lower()) if w not in STOP and len(w)>=3]

def phs(t):
    s=t.lower(); return [p for p in PHRASES if p in s]

def ablation_rows(reports,k):
    rows=[]
    for name,rep in reports.items():
        m=rep["reports"][str(k)]["average_metrics"]
        rows.append({"experiment":name,"label":rep.get("experiment_label",name),"use_decomposition":rep.get("use_decomposition",False),"use_propagation":rep.get("use_propagation",False),**m})
    return rows

def compare(base_rep,target_rep,k,sample_limit):
    b=idx(base_rep,k); t=idx(target_rep,k)
    cats={"improved":[],"worsened":[],"unchanged":[]}; trans=Counter(); phr={"improved":Counter(),"worsened":Counter()}; tok={"improved":Counter(),"worsened":Counter()}
    for qid,bi in b.items():
        ti=t.get(qid)
        if not ti: continue
        trans[f"{bi['matched_count']} -> {ti['matched_count']}"]+=1
        rdlt=ti["recall"]-bi["recall"]; mdlt=ti["mrr"]-bi["mrr"]; cdlt=ti["matched_count"]-bi["matched_count"]
        rec={"question_id":qid,"question":ti["question"],"baseline_recall":bi["recall"],"target_recall":ti["recall"],"recall_delta":rdlt,"baseline_matched":bi["matched_count"],"target_matched":ti["matched_count"],"matched_delta":cdlt,"baseline_mrr":bi["mrr"],"target_mrr":ti["mrr"],"mrr_delta":mdlt}
        bucket="improved" if rdlt>0 else "worsened" if rdlt<0 else "unchanged"
        cats[bucket].append(rec)
        if bucket in ("improved","worsened"):
            for p in phs(ti["question"]): phr[bucket][p]+=1
            for w in toks(ti["question"]): tok[bucket][w]+=1
    cats["improved"].sort(key=lambda x:(x["recall_delta"],x["matched_delta"],x["mrr_delta"]),reverse=True)
    cats["worsened"].sort(key=lambda x:(x["recall_delta"],x["matched_delta"],x["mrr_delta"]))
    total=len(b); allrecs=[r for arr in cats.values() for r in arr]
    return {"improved_count":len(cats["improved"]),"worsened_count":len(cats["worsened"]),"unchanged_count":len(cats["unchanged"]),"examples_improved":cats["improved"][:sample_limit],"examples_worsened":cats["worsened"][:sample_limit],"avg_recall_delta":sum(x["recall_delta"] for x in allrecs)/total,"avg_mrr_delta":sum(x["mrr_delta"] for x in allrecs)/total,"avg_matched_delta":sum(x["matched_delta"] for x in allrecs)/total,"transition_counter":trans,"phrase_counter":phr,"token_counter":tok}

def md_ablation(rows):
    hs=["实验","设置","问题分解","关系传播","Recall","Precision","F1","MRR","MAP@k","平均首个命中排名","平均命中表数"]
    lines=["| "+" | ".join(hs)+" |","| "+" | ".join(["---"]*len(hs))+" |"]
    for r in rows:
        lines.append("| "+" | ".join([r["experiment"],r["label"],fb(r["use_decomposition"]),fb(r["use_propagation"]),ff(r["recall"]),ff(r["precision"]),ff(r["f1"]),ff(r["mrr"]),ff(r["map_k"]),ff(r["avg_first_match_rank"]),ff(r["avg_matched_count"] )])+" |")
    return "\n".join(lines)

def md_pairwise(results):
    hs=["相对 E1 的实验","改善题数","退化题数","持平题数","平均 Recall 变化","平均 MRR 变化","平均命中表数变化"]
    lines=["| "+" | ".join(hs)+" |","| "+" | ".join(["---"]*len(hs))+" |"]
    for name,res in results.items():
        lines.append("| "+" | ".join([name,str(res["improved_count"]),str(res["worsened_count"]),str(res["unchanged_count"]),ff(res["avg_recall_delta"]),ff(res["avg_mrr_delta"]),ff(res["avg_matched_delta"])])+" |")
    return "\n".join(lines)

def md_transition(counter):
    lines=["| 命中表数转移 | 题数 |","| --- | --- |"]
    for t,c in sorted(counter.items(),key=lambda x:(-x[1],x[0])): lines.append(f"| {t} | {c} |")
    return "\n".join(lines)

def md_counter(title,counter,top_n):
    lines=[f"### {title}",""]
    if not counter: return lines+["- 无",""]
    lines += ["| 模式 / 关键词 | 次数 |","| --- | --- |"]
    for k,v in counter.most_common(top_n): lines.append(f"| {k} | {v} |")
    lines.append(""); return lines

def md_examples(title,records):
    lines=[f"### {title}",""]
    if not records: return lines+["- 无",""]
    for x in records:
        lines.append(f"- Q{x['question_id']}: {trunc(x['question'])} | 命中表数 {x['baseline_matched']} -> {x['target_matched']} | Recall {ff(x['baseline_recall'])} -> {ff(x['target_recall'])} | MRR {ff(x['baseline_mrr'])} -> {ff(x['target_mrr'])}")
    lines.append(""); return lines

def build_report(rows,pairwise,top_n):
    best_r=max(rows,key=lambda r:r["recall"]); best_m=max(rows,key=lambda r:r["mrr"]); best_map=max(rows,key=lambda r:r["map_k"]); base=next(r for r in rows if r["experiment"]=="E1")
    lines=["# 检索消融实验与错误类型分析",""]
    lines += ["## 一、关键观察",""]
    for r in rows:
        if r["experiment"]=="E1": continue
        lines.append(f"- `{r['experiment']}` 相对 `E1`：Recall {r['recall']-base['recall']:+.4f}，MRR {r['mrr']-base['mrr']:+.4f}")
    lines += ["","## 二、最佳指标",""]
    lines += [f"- 最佳 Recall：`{best_r['experiment']}` = {ff(best_r['recall'])}",f"- 最佳 MRR：`{best_m['experiment']}` = {ff(best_m['mrr'])}",f"- 最佳 MAP@k：`{best_map['experiment']}` = {ff(best_map['map_k'])}",""]
    lines += ["## 三、消融实验对照表", "", md_ablation(rows), "", "## 四、逐题对比汇总（相对 E1）", "", md_pairwise(pairwise), ""]
    for name in PAIRWISE:
        r=pairwise[name]
        lines += [f"## 五、{name} 相对 E1 的错误类型分析",""]
        lines += [f"- 改善题数：{r['improved_count']}",f"- 退化题数：{r['worsened_count']}",f"- 持平题数：{r['unchanged_count']}",f"- 平均 Recall 变化：{ff(r['avg_recall_delta'])}",f"- 平均 MRR 变化：{ff(r['avg_mrr_delta'])}",f"- 平均命中表数变化：{ff(r['avg_matched_delta'])}",""]
        lines += ["### 命中表数转移矩阵", "", md_transition(r["transition_counter"]), ""]
        lines += md_counter("改善题中的高频短语模式",r["phrase_counter"]["improved"],top_n)
        lines += md_counter("退化题中的高频短语模式",r["phrase_counter"]["worsened"],top_n)
        lines += md_counter("改善题中的高频关键词",r["token_counter"]["improved"],top_n)
        lines += md_counter("退化题中的高频关键词",r["token_counter"]["worsened"],top_n)
        lines += md_examples("代表性改善样例",r["examples_improved"])
        lines += md_examples("代表性退化样例",r["examples_worsened"])
    return "\n".join(lines)

def parse_args():
    p=argparse.ArgumentParser(description="汇总检索消融实验并输出中文分析")
    p.add_argument("--top_k",type=int,default=3)
    p.add_argument("--sample_limit",type=int,default=10)
    p.add_argument("--top_n",type=int,default=10)
    p.add_argument("--output_file",type=str,default="outputs/MTR_evaluate/retrieval_ablation_three_table.md")
    p.add_argument("--e1",type=str,default=REPORTS["E1"])
    p.add_argument("--e2",type=str,default=REPORTS["E2"])
    p.add_argument("--e3",type=str,default=REPORTS["E3"])
    p.add_argument("--e3_paper",type=str,default=REPORTS["E3_PAPER"])
    return p.parse_args()

def main():
    a=parse_args()
    reports={"E1":rd(a.e1),"E2":rd(a.e2),"E3":rd(a.e3),"E3_PAPER":rd(a.e3_paper)}
    rows=ablation_rows(reports,a.top_k)
    base=reports["E1"]
    pairwise={name:compare(base,reports[name],a.top_k,a.sample_limit) for name in PAIRWISE}
    summary=build_report(rows,pairwise,a.top_n)
    out=Path(a.output_file); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(summary,encoding="utf-8")
    print(summary); print(f"[OK] 中文分析报告已保存到: {out}")

if __name__=="__main__":
    main()
