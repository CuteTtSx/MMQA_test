# 检索消融实验与错误类型分析

## 一、关键观察

- `E2` 相对 `E1`：Recall -0.0240，MRR -0.0268
- `E3` 相对 `E1`：Recall -0.0328，MRR -0.0707
- `E3_PAPER` 相对 `E1`：Recall -0.2339，MRR -0.2957
- `E4_HYBRID` 相对 `E1`：Recall -0.0143，MRR -0.0287

## 二、最佳指标

- 最佳 Recall：`E1` = 0.5081
- 最佳 MRR：`E1` = 0.7732
- 最佳 MAP@k：`E1` = 0.4483

## 三、消融实验对照表

| 实验 | 设置 | 问题分解 | 关系传播 | Recall | Precision | F1 | MRR | MAP@k | 平均首个命中排名 | 平均命中表数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | baseline 纯语义 | 否 | 否 | 0.5081 | 0.5081 | 0.5081 | 0.7732 | 0.4483 | 1.2778 | 1.5243 |
| E2 | 分解 + 纯语义 | 是 | 否 | 0.4840 | 0.4840 | 0.4840 | 0.7464 | 0.4319 | 1.2666 | 1.4521 |
| E3 | 完整 MTR | 是 | 是 | 0.4753 | 0.4753 | 0.4753 | 0.7025 | 0.4227 | 1.3038 | 1.4258 |
| E3_PAPER | 完整 MTR（paper-like） | 是 | 是 | 0.2742 | 0.2742 | 0.2742 | 0.4776 | 0.2294 | 1.4145 | 0.8225 |
| E4_HYBRID | Hybrid：选择性关系传播 | 是 | 是 | 0.4938 | 0.4938 | 0.4938 | 0.7446 | 0.4429 | 1.2437 | 1.4813 |

## 四、逐题对比汇总（相对 E1）

| 相对 E1 的实验 | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --- | --- | --- | --- | --- | --- | --- |
| E2 | 97 | 147 | 477 | -0.0240 | -0.0268 | -0.0721 |
| E3 | 105 | 167 | 449 | -0.0328 | -0.0707 | -0.0985 |
| E3_PAPER | 59 | 429 | 233 | -0.2339 | -0.2957 | -0.7018 |
| E4_HYBRID | 75 | 108 | 538 | -0.0143 | -0.0287 | -0.0430 |

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

- 改善题数：105
- 退化题数：167
- 持平题数：449
- 平均 Recall 变化：-0.0328
- 平均 MRR 变化：-0.0707
- 平均命中表数变化：-0.0985

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 184 |
| 1 -> 1 | 144 |
| 0 -> 0 | 65 |
| 1 -> 0 | 58 |
| 3 -> 3 | 56 |
| 2 -> 1 | 51 |
| 1 -> 2 | 49 |
| 3 -> 2 | 34 |
| 2 -> 3 | 28 |
| 2 -> 0 | 22 |
| 0 -> 1 | 16 |
| 0 -> 2 | 7 |
| 0 -> 3 | 3 |
| 1 -> 3 | 2 |
| 3 -> 1 | 2 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 12 |
| greater than | 9 |
| both | 5 |
| who have | 4 |
| currently | 3 |
| along with | 3 |
| temporary acting | 2 |
| earliest | 2 |
| who has | 2 |
| at least | 2 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 16 |
| highest | 9 |
| at least | 8 |
| who have | 7 |
| along with | 6 |
| both | 4 |
| who has | 3 |
| less than | 3 |
| currently | 2 |
| ordered by | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 12 |
| average | 12 |
| paper | 12 |
| students | 11 |
| titled | 11 |
| greater | 10 |
| located | 10 |
| author | 10 |
| aircraft | 8 |
| orders | 8 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 39 |
| city | 29 |
| account | 28 |
| greater | 20 |
| code | 19 |
| average | 19 |
| first | 18 |
| last | 18 |
| savings | 18 |
| checking | 17 |

### 代表性改善样例

- Q210: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q211: Who is the first-listed author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q213: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q1: Which department(s) currently have temporary acting heads who were born in California? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q37: Who was the editor responsible for the photo work in the journal issue with the highest sales? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q17: List the names of the employees who are certified to fly aircraft capable of traveling more than 8000 miles and who h... | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q34: Who was responsible for the photo work type in the journal themed 'at Minnesota Vikings'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q232: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q233: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q241: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q537: How many dorms with a student capacity greater than 100 have the amenity 'Pub in Basement'? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q357: List the names of physicians along with procedure names and their costs, for which they hold valid certifications exp... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q19: Find the first and last names of students who live in PIT and have allergies to animals. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q25: Find the first and last names of students who have both animal and food allergies. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q98: Which customers have savings account balances over 100000 and checking account balances of at least 5000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q99: Which customers have both savings balances greater than 50000 and checking balances greater than 5000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q103: Which customer(s) have savings account balance greater than 50000 and checking account balance of at least 10000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q106: Which customers have savings account balances greater than 50,000 and checking account balances greater than 5,000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q110: Which customers have a savings account balance greater than 100000 and a checking account balance less than 5000? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q113: Which customers have a savings account balance greater than 190,000 and a checking account balance greater than 2,500? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000

## 五、E3_PAPER 相对 E1 的错误类型分析

- 改善题数：59
- 退化题数：429
- 持平题数：233
- 平均 Recall 变化：-0.2339
- 平均 MRR 变化：-0.2957
- 平均命中表数变化：-0.7018

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 0 | 141 |
| 2 -> 1 | 121 |
| 2 -> 0 | 83 |
| 1 -> 1 | 82 |
| 2 -> 2 | 76 |
| 0 -> 0 | 67 |
| 3 -> 1 | 36 |
| 3 -> 2 | 33 |
| 0 -> 1 | 21 |
| 1 -> 2 | 20 |
| 3 -> 0 | 15 |
| 1 -> 3 | 10 |
| 3 -> 3 | 8 |
| 2 -> 3 | 5 |
| 0 -> 2 | 3 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 7 |
| highest | 7 |
| who have | 4 |
| temporary acting | 2 |
| both | 2 |
| who has | 2 |
| at least | 2 |
| currently | 1 |
| earliest | 1 |
| lowest | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 43 |
| greater than | 29 |
| at least | 18 |
| who have | 12 |
| along with | 10 |
| both | 10 |
| currently | 8 |
| who has | 7 |
| less than | 5 |
| for which | 4 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 12 |
| distance | 9 |
| greater | 8 |
| baltimore | 8 |
| aircraft | 7 |
| salary | 7 |
| highest | 7 |
| city | 7 |
| orders | 7 |
| located | 6 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| number | 47 |
| students | 44 |
| highest | 43 |
| located | 41 |
| average | 41 |
| how | 40 |
| many | 39 |
| city | 36 |
| greater | 33 |
| student | 31 |

### 代表性改善样例

- Q15: List all the employees who have a certificate for an aircraft with a flight distance greater than 6000 miles and have... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.3333 -> 1.0000
- Q8: Which employee is certified to operate the aircraft with the greatest flying distance, and what is the maximum distan... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q10: What are the names of the aircraft that the employee with the highest salary is certified to operate? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q13: Which employee has certificates for aircrafts that have the highest average flying distance, and what is this average... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q14: Which employee is certified to operate aircrafts having the largest combined flight distance? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q16: List the names of employees whose salary is greater than $200,000 and who hold certificates for aircrafts capable of ... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.5000 -> 1.0000
- Q0: What are the names of heads serving as temporary acting heads in departments with rankings better than 5? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q1: Which department(s) currently have temporary acting heads who were born in California? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q11: Who has the highest salary among the employees certified to fly the Airbus A340-300 aircraft, and what is their salary? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q12: Which employee has certificates for aircraft with the highest average flight distance, and what is this average dista... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q114: Which account holders have savings balance greater than 50000 but checking account balance less than 5000? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q136: Which USA-headquartered company has the most gas stations according to the provided data, and how many stations does ... | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q350: Which physicians have valid certifications as of December 31, 2008 for procedures that cost over $5000? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q352: Which physicians have valid certifications after January 1, 2008, to perform procedures costing more than $3000? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q440: Which companies have office locations in buildings located in Mexico City with more than 50 stories? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q477: Which store has the largest area size among the stores that are located in districts with a city population higher th... | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q537: How many dorms with a student capacity greater than 100 have the amenity 'Pub in Basement'? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q554: Which gender-neutral dorm has a 'Pub in Basement' amenity and can accommodate more than 300 students? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q559: What dormitory with a student capacity greater than 300 provides both 'Air Conditioning' and also 'Allows Pets'? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q573: What is the total amount of purchase transactions involving lots owned by the investor with investor_id 7? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000

## 五、E4_HYBRID 相对 E1 的错误类型分析

- 改善题数：75
- 退化题数：108
- 持平题数：538
- 平均 Recall 变化：-0.0143
- 平均 MRR 变化：-0.0287
- 平均命中表数变化：-0.0430

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 232 |
| 1 -> 1 | 167 |
| 3 -> 3 | 74 |
| 0 -> 0 | 65 |
| 1 -> 0 | 51 |
| 1 -> 2 | 34 |
| 2 -> 1 | 29 |
| 0 -> 1 | 16 |
| 3 -> 2 | 16 |
| 2 -> 3 | 14 |
| 2 -> 0 | 10 |
| 0 -> 2 | 7 |
| 0 -> 3 | 3 |
| 3 -> 1 | 2 |
| 1 -> 3 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 10 |
| greater than | 6 |
| both | 3 |
| who have | 3 |
| along with | 2 |
| currently | 2 |
| earliest | 1 |
| for which | 1 |
| at least | 1 |
| who has | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| who have | 7 |
| highest | 6 |
| greater than | 5 |
| along with | 5 |
| at least | 3 |
| both | 2 |
| ordered by | 1 |
| who has | 1 |
| for which | 1 |
| at most | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| paper | 12 |
| titled | 11 |
| highest | 10 |
| average | 10 |
| author | 10 |
| students | 9 |
| orders | 8 |
| functional | 8 |
| pearl | 8 |
| modular | 8 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 36 |
| city | 24 |
| code | 18 |
| first | 17 |
| last | 17 |
| grade | 14 |
| number | 13 |
| average | 13 |
| course | 13 |
| bal | 11 |

### 代表性改善样例

- Q210: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q211: Who is the first-listed author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q213: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q37: Who was the editor responsible for the photo work in the journal issue with the highest sales? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q17: List the names of the employees who are certified to fly aircraft capable of traveling more than 8000 miles and who h... | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q34: Who was responsible for the photo work type in the journal themed 'at Minnesota Vikings'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q232: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q233: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q241: Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q378: What are the full names and ages of students who are members of clubs located at 'AKW'? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q537: How many dorms with a student capacity greater than 100 have the amenity 'Pub in Basement'? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q357: List the names of physicians along with procedure names and their costs, for which they hold valid certifications exp... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q19: Find the first and last names of students who live in PIT and have allergies to animals. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q25: Find the first and last names of students who have both animal and food allergies. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q696: What course scheduled on 9 May is taught by a teacher from Little Lever Urban District? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q699: Who is the teacher teaching the Math course to students in grade 3? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q64: Which courses in Cybernetics were taught during Spring 2008, and who were their instructors? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q228: Which country has the institution with the highest number of distinct published papers? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q280: Which classes, along with their times and rooms, belong to the 'Computer Info. Systems' department and have a course ... | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q403: How many unique clubs have at least one member who is a student from the city with the city_code 'BAL'? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
