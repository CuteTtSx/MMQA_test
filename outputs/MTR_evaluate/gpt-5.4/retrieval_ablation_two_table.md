# two_table 检索消融实验与错误类型分析

- 本报告实际使用的评估 Top-K：`2`

## 一、关键观察

- `E3` 相对 `E3_PAPER`：Recall +0.1249，MRR +0.1052
- `E4_HYBRID` 相对 `E3_PAPER`：Recall +0.1231，MRR +0.1064
- `E5_HYBRID_LOCAL` 相对 `E3_PAPER`：Recall +0.1249，MRR +0.1052

## 二、最佳指标

- 最佳 Recall：`E3` = 0.5535
- 最佳 MRR：`E4_HYBRID` = 0.8151
- 最佳 MAP@k：`E3` = 0.5259

## 三、消融实验对照表

| 实验 | 设置 | 问题分解 | 关系传播 | Recall | Precision | F1 | MRR | MAP@k | 平均首个命中排名 | 平均命中表数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3_PAPER | 完整 MTR（paper-like） | 是 | 是 | 0.4287 | 0.4287 | 0.4287 | 0.7087 | 0.3954 | 1.1718 | 0.8573 |
| E3 | 完整 MTR | 是 | 是 | 0.5535 | 0.5535 | 0.5535 | 0.8139 | 0.5259 | 1.1272 | 1.1070 |
| E4_HYBRID | Hybrid：不确定性门控传播 | 是 | 是 | 0.5517 | 0.5517 | 0.5517 | 0.8151 | 0.5253 | 1.1219 | 1.1034 |
| E5_HYBRID_LOCAL | Hybrid：局部扩展 + 重排 | 是 | 是 | 0.5535 | 0.5535 | 0.5535 | 0.8139 | 0.5259 | 1.1272 | 1.1070 |

## 四、逐题对比汇总

| 对比实验 | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --- | --- | --- | --- | --- | --- | --- |
| E3 vs E3_PAPER | 263 | 64 | 514 | 0.1249 | 0.1052 | 0.2497 |
| E4_HYBRID vs E3 | 14 | 17 | 810 | -0.0018 | 0.0012 | -0.0036 |
| E5_HYBRID_LOCAL vs E3 | 0 | 0 | 841 | 0.0000 | 0.0000 | 0.0000 |

## 五、E3 相对 E3_PAPER 的错误类型分析

- 改善题数：263
- 退化题数：64
- 持平题数：514
- 平均 Recall 变化：0.1249
- 平均 MRR 变化：0.1052
- 平均命中表数变化：0.2497

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 1 | 399 |
| 1 -> 2 | 135 |
| 0 -> 1 | 117 |
| 0 -> 0 | 61 |
| 2 -> 2 | 54 |
| 1 -> 0 | 49 |
| 2 -> 1 | 15 |
| 0 -> 2 | 11 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 33 |
| greater than | 21 |
| at least | 16 |
| who have | 11 |
| earliest | 5 |
| currently | 5 |
| who has | 4 |
| along with | 4 |
| less than | 4 |
| latest | 2 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 8 |
| both | 4 |
| who have | 3 |
| at least | 2 |
| along with | 1 |
| less than | 1 |
| currently | 1 |
| greater than | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| average | 38 |
| highest | 33 |
| customers | 32 |
| total | 31 |
| how | 30 |
| many | 30 |
| rating | 25 |
| number | 21 |
| greater | 21 |
| amount | 19 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| total | 15 |
| number | 13 |
| player | 13 |
| students | 9 |
| how | 9 |
| country | 9 |
| many | 8 |
| highest | 8 |
| customer | 7 |
| amount | 7 |

### 代表性改善样例

- Q81: What is the total price of all books written by Garth Ennis? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q188: What is the average age of editors who have worked on journals performing 'Photo' type tasks? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q299: Which enzymes located in the mitochondrion are inhibited by medicine with ID 2? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q303: Which enzyme located in the Cytosol is activated by medicine with ID 20? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q486: What is the Claim Header ID, status, and settlement date for the earliest Child Birth related claim having a Medical ... | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q649: What is the total amount paid using cash for bookings that are in Provisional status? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q654: What is the total value of all TMobile phones currently in stock across all markets? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q688: Which shipping agent has the most documents currently in 'working' status, and how many documents does it have? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q690: What is the shipping agent description for the agent handling the most recent 'Hard Drive' document that is marked as... | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q1134: List the names of artists from India who sang Bangla songs with ratings greater than 7. | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q14: What is the mobile number of the person whose candidate details indicate 'Alex'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q23: Which students attended both statistics and French courses? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q32: What is the state_province_county of the address where the person with person_id 141 lived? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q135: List the unique first and last names of students who are allergic to nuts and are younger than 20. | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q140: What are the first and last names of students who have a nut allergy and live in the city with the code 'PIT'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q143: List the full names and city codes of students who have allergies to both 'Nuts' and 'Soy'. | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q148: Which customer from Germany has the highest total spending amount? Provide their first name, last name, and the total... | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q149: Which customer in Germany has spent the most money and what is their total spending amount? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q151: Which customer from Germany has spent the most total, and how much have they spent? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q157: What is the total amount spent by all customers located in Germany? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000

## 五、E4_HYBRID 相对 E3 的错误类型分析

- 改善题数：14
- 退化题数：17
- 持平题数：810
- 平均 Recall 变化：-0.0018
- 平均 MRR 变化：0.0012
- 平均命中表数变化：-0.0036

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 1 | 516 |
| 2 -> 2 | 186 |
| 0 -> 0 | 108 |
| 2 -> 1 | 14 |
| 1 -> 2 | 12 |
| 1 -> 0 | 3 |
| 0 -> 1 | 2 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 3 |
| greater than | 3 |
| both | 2 |
| along with | 1 |
| at least | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 3 |
| who have | 2 |
| at least | 1 |
| currently | 1 |
| greater than | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| average | 4 |
| population | 4 |
| chip | 3 |
| highest | 3 |
| counties | 3 |
| greater | 3 |
| how | 2 |
| many | 2 |
| students | 2 |
| animal | 2 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| worked | 3 |
| highest | 3 |
| editors | 2 |
| age | 2 |
| photo | 2 |
| type | 2 |
| confirmed | 2 |
| female | 2 |
| employees | 2 |
| editor | 2 |

### 代表性改善样例

- Q802: Which reviewers gave the highest star rating to the movie with mID 108? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 0.5000
- Q845: What is the name and case burden of the county which has the city with the highest percentage of Asian population? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 0.5000
- Q1: What are the names and budgets of departments ranked in the top 10 whose current managerial positions are temporarily... | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q136: How many students have both animal and food allergies? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q137: How many students have both animal and food allergies? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q326: List the companies along with the chip model names and launch years for phones that use chip models supporting WiFi '... | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q544: What is the average ticket price of the exhibitions organized by artists from the United States who are older than 45? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q678: Which ministers belong to the party 'Convention Peoples Party' and participated in the event named 'Election Meeting'? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q829: Among directors who made films after 1980, which director has the highest average star rating? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q844: What is the average crime rate in counties that have cities with a Black population percentage greater than 10%? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q337: Which country's official native language has the highest number of midfielders playing across all seasons? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q685: What are the names of employees whose roles are described as 'Editor'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q686: What are the names of employees who have the role description 'Editor'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q187: Which editors under the age of 30 have worked on Photo assignments? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q188: What is the average age of editors who have worked on journals performing 'Photo' type tasks? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q302: Which FDA-approved medicines have an inhibitor interaction with enzyme 2? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q394: What apartment numbers have at least 2 bathrooms and a confirmed booking ending on or after November 1, 2017? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q402: How many different apartments have confirmed bookings by female guests? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q540: List the names of all males from United States who got married on or after 2015. | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q577: Who is the coach whose rank matches the club that won the most gold medals? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000

## 五、E5_HYBRID_LOCAL 相对 E3 的错误类型分析

- 改善题数：0
- 退化题数：0
- 持平题数：841
- 平均 Recall 变化：0.0000
- 平均 MRR 变化：0.0000
- 平均命中表数变化：0.0000

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 1 | 531 |
| 2 -> 2 | 200 |
| 0 -> 0 | 110 |

### 改善题中的高频短语模式

- 无

### 退化题中的高频短语模式

- 无

### 改善题中的高频关键词

- 无

### 退化题中的高频关键词

- 无

### 代表性改善样例

- 无

### 代表性退化样例

- 无
