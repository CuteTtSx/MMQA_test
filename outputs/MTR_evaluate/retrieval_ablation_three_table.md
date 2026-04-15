# 检索消融实验与错误类型分析

## 一、关键观察

- `E2` 相对 `E1`：Recall -0.0240，MRR -0.0268
- `E3` 相对 `E1`：Recall -0.1091，MRR -0.2087
- `E3_PAPER` 相对 `E1`：Recall -0.2224，MRR -0.3641
- `E4_HYBRID` 相对 `E1`：Recall -0.0624，MRR -0.1117
- `E5_HYBRID_LOCAL` 相对 `E1`：Recall -0.0060，MRR -0.0728

## 二、最佳指标

- 最佳 Recall：`E1` = 0.5081
- 最佳 MRR：`E1` = 0.7732
- 最佳 MAP@k：`E1` = 0.4483

## 三、消融实验对照表

| 实验 | 设置 | 问题分解 | 关系传播 | Recall | Precision | F1 | MRR | MAP@k | 平均首个命中排名 | 平均命中表数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | baseline 纯语义 | 否 | 否 | 0.5081 | 0.5081 | 0.5081 | 0.7732 | 0.4483 | 1.2778 | 1.5243 |
| E2 | 分解 + 纯语义 | 是 | 否 | 0.4840 | 0.4840 | 0.4840 | 0.7464 | 0.4319 | 1.2666 | 1.4521 |
| E3 | 完整 MTR | 是 | 是 | 0.3990 | 0.3990 | 0.3990 | 0.5645 | 0.3350 | 1.4533 | 1.1969 |
| E3_PAPER | 完整 MTR（paper-like） | 是 | 是 | 0.2857 | 0.2857 | 0.2857 | 0.4092 | 0.2310 | 1.5459 | 0.8571 |
| E4_HYBRID | Hybrid：不确定性门控传播 | 是 | 是 | 0.4457 | 0.4457 | 0.4457 | 0.6616 | 0.3934 | 1.2904 | 1.3370 |
| E5_HYBRID_LOCAL | Hybrid：局部扩展 + 重排 | 是 | 是 | 0.5021 | 0.5021 | 0.5021 | 0.7004 | 0.4371 | 1.4378 | 1.5062 |

## 四、逐题对比汇总（相对 E1）

| 相对 E1 的实验 | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --- | --- | --- | --- | --- | --- | --- |
| E2 | 97 | 147 | 477 | -0.0240 | -0.0268 | -0.0721 |
| E3 | 87 | 279 | 355 | -0.1091 | -0.2087 | -0.3273 |
| E3_PAPER | 57 | 407 | 257 | -0.2224 | -0.3641 | -0.6671 |
| E4_HYBRID | 53 | 174 | 494 | -0.0624 | -0.1117 | -0.1872 |
| E5_HYBRID_LOCAL | 95 | 106 | 520 | -0.0060 | -0.0728 | -0.0180 |

## 五、E2 相对 E1 的错误类型分析

- 改善题数：97
- 退化题数：147
- 持平题数：477
- 平均 Recall 变化：-0.0240
- 平均 MRR 变化：-0.0268
- 平均命中表数变化：-0.0721

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 190 |
| 1 -> 1 | 170 |
| 0 -> 0 | 61 |
| 3 -> 3 | 56 |
| 2 -> 1 | 55 |
| 1 -> 0 | 42 |
| 1 -> 2 | 40 |
| 3 -> 2 | 35 |
| 2 -> 3 | 26 |
| 0 -> 1 | 21 |
| 2 -> 0 | 14 |
| 0 -> 2 | 6 |
| 0 -> 3 | 3 |
| 1 -> 3 | 1 |
| 3 -> 1 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 7 |
| highest | 7 |
| both | 3 |
| along with | 3 |
| earliest | 2 |
| at least | 2 |
| currently | 2 |
| who have | 1 |
| for which | 1 |
| who has | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 15 |
| at least | 8 |
| highest | 8 |
| who have | 7 |
| both | 4 |
| along with | 4 |
| who has | 3 |
| less than | 3 |
| currently | 2 |
| ordered by | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| located | 12 |
| paper | 12 |
| titled | 11 |
| students | 11 |
| how | 10 |
| many | 10 |
| author | 10 |
| orders | 8 |
| average | 8 |
| functional | 8 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 33 |
| account | 28 |
| city | 24 |
| greater | 19 |
| savings | 18 |
| checking | 17 |
| average | 16 |
| how | 15 |
| many | 15 |
| customers | 14 |

### 代表性改善样例

- Q210: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q211: Who is the first-listed author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q213: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q37: Who was the editor responsible for the photo work in the journal issue with the highest sales? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q34: Who was responsible for the photo work type in the journal themed 'at Minnesota Vikings'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q232: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q233: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q241: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q378: What are the full names and ages of students who are members of clubs located at 'AKW'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q615: Which city hosted the match in 2011 and what was its GDP? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 0.5000

### 代表性退化样例

- Q357: List the names of physicians along with procedure names and their costs, for which they hold valid certifications exp... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q19: Find the first and last names of students who live in PIT and have allergies to animals. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q25: Find the first and last names of students who have both animal and food allergies. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q98: Which customers have savings account balances over 100000 and checking account balances of at least 5000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q99: Which customers have both savings balances greater than 50000 and checking balances greater than 5000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q103: Which customer(s) have savings account balance greater than 50000 and checking account balance of at least 10000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q106: Which customers have savings account balances greater than 50,000 and checking account balances greater than 5,000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q110: Which customers have a savings account balance greater than 100000 and a checking account balance less than 5000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q113: Which customers have a savings account balance greater than 190,000 and a checking account balance greater than 2,500? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q121: Which customers have savings account balances greater than 50,000 and checking account balances above 5,000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000

## 五、E3 相对 E1 的错误类型分析

- 改善题数：87
- 退化题数：279
- 持平题数：355
- 平均 Recall 变化：-0.1091
- 平均 MRR 变化：-0.2087
- 平均命中表数变化：-0.3273

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 136 |
| 1 -> 1 | 114 |
| 1 -> 0 | 107 |
| 2 -> 1 | 76 |
| 0 -> 0 | 67 |
| 2 -> 0 | 42 |
| 3 -> 2 | 38 |
| 3 -> 3 | 38 |
| 1 -> 2 | 31 |
| 2 -> 3 | 31 |
| 0 -> 1 | 15 |
| 3 -> 1 | 14 |
| 0 -> 3 | 6 |
| 0 -> 2 | 3 |
| 3 -> 0 | 2 |
| 1 -> 3 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 10 |
| highest | 7 |
| who have | 4 |
| both | 3 |
| temporary acting | 2 |
| earliest | 2 |
| less than | 2 |
| at least | 2 |
| currently | 1 |
| for which | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 29 |
| greater than | 20 |
| who have | 11 |
| along with | 8 |
| at least | 8 |
| currently | 6 |
| both | 3 |
| who has | 3 |
| for which | 3 |
| ordered by | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| average | 14 |
| how | 12 |
| many | 12 |
| student | 12 |
| paper | 11 |
| capacity | 11 |
| greater | 10 |
| total | 10 |
| titled | 10 |
| students | 9 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 47 |
| city | 39 |
| highest | 29 |
| number | 29 |
| average | 28 |
| first | 26 |
| located | 24 |
| last | 24 |
| greater | 23 |
| customers | 21 |

### 代表性改善样例

- Q210: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q211: Who is the first-listed author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q213: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q232: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q233: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q241: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q37: Who was the editor responsible for the photo work in the journal issue with the highest sales? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q34: Who was responsible for the photo work type in the journal themed 'at Minnesota Vikings'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q79: In which building is located the department where the student with the highest total credits belongs to? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q378: What are the full names and ages of students who are members of clubs located at 'AKW'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 0.5000

### 代表性退化样例

- Q74: What are the titles of the courses along with building names and room numbers for courses held in Fall 2005 in classr... | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q357: List the names of physicians along with procedure names and their costs, for which they hold valid certifications exp... | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q199: What are the names of the events that were hosted by journalists with more than 10 years of working experience? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q355: Which physicians have valid certifications expiring on December 31, 2008, and are trained to perform procedures costi... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q520: What is the color of the product named 'cumin', if its product description matches the characteristic type code of a ... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q627: What is the total number of project hours assigned to the scientists Michael Rogers and Eric Goldsmith? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q692: Which template type description has the document with the highest version number? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q24: What are the names of students younger than 20 years old from city code 'BAL' who have environmental allergies? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.5000
- Q711: Which high school students have friends who like Kris? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.5000
- Q136: Which USA-headquartered company has the most gas stations according to the provided data, and how many stations does ... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000

## 五、E3_PAPER 相对 E1 的错误类型分析

- 改善题数：57
- 退化题数：407
- 持平题数：257
- 平均 Recall 变化：-0.2224
- 平均 MRR 变化：-0.3641
- 平均命中表数变化：-0.6671

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 0 | 157 |
| 2 -> 1 | 92 |
| 2 -> 0 | 90 |
| 0 -> 0 | 85 |
| 1 -> 1 | 75 |
| 2 -> 2 | 73 |
| 3 -> 1 | 32 |
| 2 -> 3 | 30 |
| 3 -> 2 | 28 |
| 3 -> 3 | 24 |
| 1 -> 2 | 14 |
| 3 -> 0 | 8 |
| 1 -> 3 | 7 |
| 0 -> 1 | 6 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 15 |
| at least | 10 |
| who have | 5 |
| less than | 4 |
| both | 3 |
| temporary acting | 2 |
| highest | 2 |
| who has | 2 |
| currently | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 46 |
| greater than | 19 |
| who have | 13 |
| along with | 11 |
| at least | 10 |
| both | 7 |
| who has | 6 |
| currently | 6 |
| for which | 4 |
| earliest | 2 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| account | 28 |
| savings | 24 |
| checking | 22 |
| customers | 19 |
| balance | 19 |
| greater | 18 |
| balances | 14 |
| average | 12 |
| student | 9 |
| capacity | 9 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 51 |
| city | 48 |
| highest | 46 |
| number | 41 |
| average | 40 |
| first | 38 |
| how | 37 |
| last | 36 |
| located | 36 |
| many | 36 |

### 代表性改善样例

- Q562: How many students from PIT city have an advisor who also advises students living in dorms that have a kitchen in ever... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.3333 -> 1.0000
- Q100: List the names of customers who have more than 50,000 in their savings account and more than 5,000 in their checking ... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q101: Which customers have at least $100,000 in their savings account and at least $5,000 in their checking account? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q102: Which customers have more than $100,000 in their savings accounts and at least $5,000 in their checking accounts? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q107: Find the name of the customer who has a balance in the checking account but has no savings account. | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q112: What are the names of the customers who have savings accounts with balances greater than 50000 and checking accounts ... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q119: Which customers have more than $50,000 in savings and more than $8,000 in checking accounts? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q563: How many different amenities are available in dorms that allow pets? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q564: Which students with major 600 coming from cities 'PIT' or 'BAL' could potentially reside in a dormitory which has mor... | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q98: Which customers have savings account balances over 100000 and checking account balances of at least 5000? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q47: Which FDA-approved medicines activate enzymes that are located in the mitochondrion? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q520: What is the color of the product named 'cumin', if its product description matches the characteristic type code of a ... | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q616: What is the average July temperature of cities with GDP above 500 that have hosted matches? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q709: What is the name of the city with the largest population among the countries whose official or spoken language is Por... | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q148: Give me a list of names and years of races that had any driver whose forename is Lewis? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q156: Find the id, forename and number of races of all drivers who have at least participated in two races? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q157: What is the id, forename, and number of races for all drivers that have participated in at least 2 races? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q158: Find the driver id and number of races of all drivers who have at most participated in 30 races? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q138: Which company with the highest rank was associated with a gas station managed by Colin Denman? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q162: Which machine team has the highest average value points among machines serviced by technicians older than 40 years? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333

## 五、E4_HYBRID 相对 E1 的错误类型分析

- 改善题数：53
- 退化题数：174
- 持平题数：494
- 平均 Recall 变化：-0.0624
- 平均 MRR 变化：-0.1117
- 平均命中表数变化：-0.1872

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 209 |
| 1 -> 1 | 150 |
| 1 -> 0 | 86 |
| 0 -> 0 | 68 |
| 3 -> 3 | 67 |
| 2 -> 1 | 41 |
| 2 -> 0 | 22 |
| 3 -> 2 | 18 |
| 1 -> 2 | 16 |
| 0 -> 1 | 14 |
| 2 -> 3 | 13 |
| 0 -> 3 | 6 |
| 3 -> 1 | 6 |
| 0 -> 2 | 3 |
| 1 -> 3 | 1 |
| 3 -> 0 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 4 |
| greater than | 3 |
| who have | 2 |
| earliest | 1 |
| for which | 1 |
| both | 1 |
| along with | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 20 |
| greater than | 10 |
| who have | 10 |
| along with | 6 |
| at least | 4 |
| who has | 2 |
| for which | 2 |
| currently | 2 |
| both | 1 |
| ordered by | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| paper | 11 |
| titled | 10 |
| how | 9 |
| many | 9 |
| author | 9 |
| functional | 8 |
| pearl | 8 |
| modular | 8 |
| rollback | 8 |
| through | 8 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 41 |
| city | 30 |
| first | 24 |
| last | 23 |
| average | 23 |
| highest | 20 |
| code | 18 |
| number | 18 |
| grade | 18 |
| located | 15 |

### 代表性改善样例

- Q210: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q211: Who is the first-listed author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q213: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q232: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q233: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q241: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q37: Who was the editor responsible for the photo work in the journal issue with the highest sales? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q34: Who was responsible for the photo work type in the journal themed 'at Minnesota Vikings'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q79: In which building is located the department where the student with the highest total credits belongs to? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q378: What are the full names and ages of students who are members of clubs located at 'AKW'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 0.5000

### 代表性退化样例

- Q357: List the names of physicians along with procedure names and their costs, for which they hold valid certifications exp... | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q520: What is the color of the product named 'cumin', if its product description matches the characteristic type code of a ... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q24: What are the names of students younger than 20 years old from city code 'BAL' who have environmental allergies? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.5000
- Q711: Which high school students have friends who like Kris? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.5000
- Q183: What is the average age of main hosts who have hosted parties located at Heineken Music Hall Amsterdam? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q352: Which physicians have valid certifications after January 1, 2008, to perform procedures costing more than $3000? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q575: List names of visitors who visited a tourist attraction located at location id 417 and got there by shuttle. | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q18: How many distinct students older than 18 have allergies classified as animal-related? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q19: Find the first and last names of students who live in PIT and have allergies to animals. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q21: List the first and last names of students who live in NYC and have animal-type allergies. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000

## 五、E5_HYBRID_LOCAL 相对 E1 的错误类型分析

- 改善题数：95
- 退化题数：106
- 持平题数：520
- 平均 Recall 变化：-0.0060
- 平均 MRR 变化：-0.0728
- 平均命中表数变化：-0.0180

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 188 |
| 1 -> 1 | 177 |
| 3 -> 3 | 80 |
| 0 -> 0 | 75 |
| 2 -> 1 | 51 |
| 2 -> 3 | 43 |
| 1 -> 0 | 40 |
| 1 -> 2 | 35 |
| 0 -> 1 | 16 |
| 3 -> 2 | 12 |
| 2 -> 0 | 3 |
| 1 -> 3 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 10 |
| highest | 5 |
| who have | 4 |
| both | 4 |
| at least | 3 |
| who has | 2 |
| for which | 2 |
| lowest | 1 |
| less than | 1 |
| along with | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 10 |
| who have | 5 |
| greater than | 5 |
| along with | 3 |
| currently | 2 |
| both | 2 |
| ordered by | 1 |
| at least | 1 |
| for which | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 13 |
| total | 13 |
| student | 12 |
| greater | 10 |
| capacity | 10 |
| customers | 10 |
| number | 10 |
| how | 9 |
| many | 9 |
| first | 7 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| average | 18 |
| students | 16 |
| city | 16 |
| code | 13 |
| highest | 10 |
| course | 10 |
| grade | 10 |
| characteristic | 10 |
| last | 9 |
| located | 8 |

### 代表性改善样例

- Q112: What are the names of the customers who have savings accounts with balances greater than 50000 and checking accounts ... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q143: Which aircraft manufacturer had flights operated by the highest number of different pilots? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q18: How many distinct students older than 18 have allergies classified as animal-related? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q21: List the first and last names of students who live in NYC and have animal-type allergies. | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q22: How many students under 20 years old have allergies categorized as 'animal'? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q23: List the first and last names of students from NYC who have animal-related allergies. | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q109: What is the total combined balance from both savings and checking accounts of customers named Brown, Wang, and Granger? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q121: Which customers have savings account balances greater than 50,000 and checking account balances above 5,000? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q124: Which web client accelerators compatible with Firefox since 2007 or earlier support wireless connections? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q144: Which pilots from the United States have operated aircraft that use diesel fuel propulsion? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q662: What is the average age of pets owned by students who live in city code 'HKG'? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q664: What is the average age of pets owned by students living in the city coded 'HKG'? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q670: What is the average age of pets owned by students who are from the city with code 'HKG'? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q24: What are the names of students younger than 20 years old from city code 'BAL' who have environmental allergies? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q51: List the names of FDA-approved medicines that inhibit enzymes located in the mitochondrion. | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q74: What are the titles of the courses along with building names and room numbers for courses held in Fall 2005 in classr... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q135: Who is the manager of the gas station associated with the highest ranked company headquartered in the UK? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q136: Which USA-headquartered company has the most gas stations according to the provided data, and how many stations does ... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q223: Who is the first author (full name) of the paper titled 'Binders Unbound'? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q240: Who is the first author of the paper titled 'Binders Unbound'? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
