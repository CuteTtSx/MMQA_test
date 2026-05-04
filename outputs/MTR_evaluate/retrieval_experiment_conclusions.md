# 检索实验阶段性结论汇总

## 1. 文档目的

本文件用于汇总当前多表检索（MTR）相关实验中已经得到的稳定结论，区分不同关系分实现带来的现象，避免后续分析时混淆不同实验阶段的结果。

---

## 2. 当前实验主线回顾

本阶段主要围绕以下问题展开：

1. 纯语义 baseline 是否已经足够强。
2. 问题分解是否能提升三表检索。
3. 完整 MTR 的表间传播是否有效。
4. uncertainty gate 与 local expansion + rerank 是否能缓解全量传播带来的噪声。
5. 表间相关性分数 \beta 应该如何定义：
  - 基于主外键关系
  - 基于共享列 / 列重叠
  - 基于更细粒度的分层打分

---

## 3. 稳定实验结论（与具体关系分版本无关）

### 3.1 `E1` 是当前最稳的 retrieval baseline

在所有阶段实验中，`E1`（baseline 纯语义）始终是最稳定的参照系。

稳定结论：

- 纯语义 baseline 很强。
- 任何传播机制若无法明显提升 Recall，同时又拉低 MRR，就很难超越 `E1`。
- 后续所有 MTR 相关实验都应以 `E1` 为核心对照对象。

### 3.2 问题分解 `E2` 没有带来稳定收益

无论在哪一版结果中，`E2` 都整体弱于 `E1`。

稳定结论：

- 当前问题分解策略没有提升三表检索效果。
- 子问题拆分会削弱原问题的整体语义表达。
- 问题分解在本任务中更像噪声源，而不是稳定增益源。

### 3.3 完整全量传播 `E3` 不稳定，通常退化明显

在不同关系分版本下，`E3` 都没有成为最优方案，并且通常是退化最明显的 MTR 版本之一。

稳定结论：

- 全量传播对关系图质量和稠密度高度敏感。
- 只要传播边带入噪声，错误就会被快速放大。
- `E3` 不适合作为当前阶段的最终方案。

### 3.4 `E3_PAPER` 始终最差或接近最差

paper-like 实现始终显著弱于 `E1`，也明显弱于 `E4/E5`。

稳定结论：

- 论文伪代码不能直接照搬得到有效结果。
- paper-like 版本对当前数据和实现方式并不适配。
- 若后续写报告，可明确作为负结果保留。

### 3.5 `E5_HYBRID_LOCAL` 是当前 propagation 路线里最值得保留的版本

不论采用哪种表间相关性分数，`E5_HYBRID_LOCAL` 都表现出最强的稳定性。

稳定结论：

- 局部扩展 + rerank 比全量传播更稳。
- `E5` 能把传播约束在小候选池中，减轻噪声累积。
- 若继续保留 propagation 方向，`E5` 是最合理的主线版本。

---

## 4. 不同关系分版本下的阶段结论

### 4.1 阶段 A：较早版本（局部扩展版表现最好）

对应文件：`outputs/MTR_evaluate/retrieval_ablation_three_table_base.md`

主要结果：

- `E1`: Recall `0.5081`
- `E3`: Recall `0.4753`
- `E4_HYBRID`: Recall `0.4813`
- `E5_HYBRID_LOCAL`: Recall `0.4961`

这一阶段的结论：

- `E5` 非常接近 `E1`，是 propagation 路线中表现最好的一版。
- `E4` 比 `E3` 稳，但不如 `E5`。
- 全量传播会退化，但还没有崩得特别严重。

可归纳为：

> 在较宽松的关系传播设定下，局部扩展 + rerank 能在保留一定补表能力的同时显著减少误伤，是最接近 baseline 的传播版本。

---

### 4.2 阶段 B：改用更严格 / 分层关系打分后

这一阶段尝试让“更干净的 PK/FK”获得更高权重，并弱化共享列、共享外键等噪声关系。

现象：

- 原始表池 + 新打分：整体指标下降。
- 干净表池 + 新打分：下降更明显。
- `E3` 和 `E4` 退化尤其严重。

这一阶段的结论：

- 更干净的 PK/FK 不会自动转化成更高检索指标。
- 当前传播公式更依赖“关系图连通性”，而不是“关系图精确性”。
- 当边被削弱后，传播能力快速丧失。

可归纳为：

> 当前 MTR 框架对关系图稠密度高度敏感，严格的关系建模会让传播走不动，因此在该框架下，干净 schema 并不天然占优。

---

### 4.3 阶段 C：改用 `compute_table_relationship_score1`

对应文件：`outputs/MTR_evaluate/retrieval_ablation_three_table.md`

主要结果：

- `E1`: Recall `0.5081`
- `E3`: Recall `0.3990`
- `E4_HYBRID`: Recall `0.4457`
- `E5_HYBRID_LOCAL`: Recall `0.5021`

这一阶段的结论：

- `compute_table_relationship_score1` 用在 `E3/E4` 上会显著放大噪声。
- `score1` 更像 schema-level similarity，而不是 join-level connectivity。
- 它不适合全量传播，但在 `E5` 这种局部 rerank 框架中还能工作。

可归纳为：

> 基于列重叠/结构相似度的关系分不适合全局传播，但可以作为局部 rerank 的弱关系信号使用。

---

## 5. 关于主外键提取的结论

针对 `Synthesized_three_table.json` 与 `global_table_pool_three.json` 的对照分析，已经得到以下判断：

### 5.1 桥接表的处理最难

例如：

- `management_[Department_ID,head_ID,temporary_acting]`
- `Student_Course_Registrations_[student_id,course_id,registration_date]`
- `certificate_[eid,aid]`

这些表经常同时满足：

- 多列像主键
- 多列也像外键
- 真实结构更接近复合主键 + 多外键

因此：

- 若采用保守策略，通常会返回 `primary_key = None`
- 这在数据库建模上不完美，但在当前简化表示下是可接受的

### 5.2 带 surrogate key 的关系表容易被误判

例如：

- `People_Addresses_[person_address_id,student_id,address_id,date_from,date_to]`

这类表更合理的抽取应是：

- `primary_key = person_address_id`
- `foreign_keys = [student_id, address_id]`

但过于保守的规则会把它整体打成 `primary_key = None`。

### 5.3 原始提取法并不“更正确”，只是“更适合当前传播”

原始提取法会带来：

- 更多边
- 更多伪 FK
- 更稠密的关系图

虽然 schema 更脏，但在当前传播框架下反而可能提高 Recall。

这一点说明：

> 当前传播机制更偏好“边多”，而不偏好“边准”。

---

## 6. 关于论文中 `beta` 分数的理解

结合论文正文与现有截图，可以得到以下判断：

### 6.1 作者没有清楚给出 `beta` 的实现公式

论文只写到：

- table relevance score is computed based on the overlap of table columns
- 若表之间存在 overlap，则赋予 `1/0` 型分数

但没有明确说明：

- overlap 是完全同名还是归一化同名
- 是否只看主外键列
- 是否取二值 / 比例 / 加权交集
- 多个重叠列如何聚合

### 6.2 论文中的 `beta` 更像“共享列启发式分数”

更合理的理解是：

- `beta` 不是严格的 PK/FK 关系分数
- 更像基于共享列 / 列重叠的 heuristic table relevance score

### 6.3 因此，`compute_table_relationship_score1` 其实更接近论文的模糊原意

也就是说：

- `score1` 可以被视为较接近 paper-style beta 的实现
- PK/FK 版则更像你自己扩展出来的结构增强版本

---

## 7. 关于论文中的 `TableLlama-7B` / `SGPT-5.8B`

当前已经确认：

### 7.1 它们不是用来做表向量转换的

论文中的 `TableLlama-7B` / `SGPT-5.8B` 更可能用于计算：

\alpha(q_i, table_j)

即 question-table relevance score。

### 7.2 MTR 的结构本质上是：学得的 \alpha + 启发式 \beta

也就是说论文方法本质上是：

- 用微调后的单表检索模型来打 question-table score
- 用共享列 heuristic 来打 table-table score
- 再做多轮传播

因此当前你的实现与论文原版之间最大的差异之一在于：

- 论文的 `alpha` 是 learned retriever
- 你当前的 `alpha` 是 embedding-based similarity

---

## 8. 当前最可信的阶段性结论

综合目前全部实验，可以给出以下阶段性判断：

1. `E1` 仍然是当前三表检索任务中最稳的最终 baseline。
2. 问题分解 `E2` 没有带来稳定收益。
3. 完整全量传播 `E3` 不适合作为最终方案。
4. `E3_PAPER` 可以作为负结果保留。
5. `E5_HYBRID_LOCAL` 是 propagation 路线里最值得保留和继续分析的版本。
6. 当前传播框架更依赖关系图稠密度，而不是 schema 精确性。
7. 论文里的 `beta` 大概率是共享列启发式分数，而不是严格 PK/FK 分数。
8. 若要更接近论文原始实现，重点不只是改 `beta`，还要意识到论文里的 `alpha` 是经过微调的 single-table retrieval model。

---

## 9. 当前建议

### 9.1 如果目标是写实验结论

建议保留以下主结论：

- `E1` 为最终 baseline
- `E5` 为 propagation 路线中最优版本
- `E3/E3_PAPER` 作为失败/负结果分析
- `beta` 的定义模糊性作为复现实验中的一个重要讨论点

### 9.2 如果目标是继续优化

建议优先探索：

- 只在 `E5` 框架内继续调 `beta`
- 或改进 `alpha`，训练一个 stronger single-table scorer

不建议继续：

- 在 `E3` 上做大规模全量传播调参
- 对严格 PK/FK 图做过多结构化优化，而不同时改传播公式

---

## 10. 一句话总括

截至目前，实验最稳定的结论是：

> 在 MMQA 三表检索任务中，纯语义检索仍是最稳的 baseline；传播机制只有在局部扩展 + rerank 的受限框架中才具备可保留价值；论文中的表间相关性分数 `beta` 更像共享列启发式分数，而非严格主外键关系分数，因此复现时必须同时区分 `alpha` 与 `beta` 的来源和作用。

