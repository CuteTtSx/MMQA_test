# three_table 检索消融实验与错误类型分析

- 本报告实际使用的评估 Top-K：`3`

## 一、关键观察

- `E3` 相对 `E3_PAPER`：Recall +0.2011，MRR +0.2249
- `E4_HYBRID` 相对 `E3_PAPER`：Recall +0.2196，MRR +0.2670
- `E5_HYBRID_LOCAL` 相对 `E3_PAPER`：Recall +0.2219，MRR +0.2681

## 二、最佳指标

- 最佳 Recall：`E5_HYBRID_LOCAL` = 0.4961
- 最佳 MRR：`E5_HYBRID_LOCAL` = 0.7457
- 最佳 MAP@k：`E5_HYBRID_LOCAL` = 0.4458

## 三、消融实验对照表

| 实验 | 设置 | 问题分解 | 关系传播 | Recall | Precision | F1 | MRR | MAP@k | 平均首个命中排名 | 平均命中表数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3_PAPER | 完整 MTR（paper-like） | 是 | 是 | 0.2742 | 0.2742 | 0.2742 | 0.4776 | 0.2294 | 1.4145 | 0.8225 |
| E3 | 完整 MTR | 是 | 是 | 0.4753 | 0.4753 | 0.4753 | 0.7025 | 0.4227 | 1.3038 | 1.4258 |
| E4_HYBRID | Hybrid：不确定性门控传播 | 是 | 是 | 0.4938 | 0.4938 | 0.4938 | 0.7446 | 0.4429 | 1.2437 | 1.4813 |
| E5_HYBRID_LOCAL | Hybrid：局部扩展 + 重排 | 是 | 是 | 0.4961 | 0.4961 | 0.4961 | 0.7457 | 0.4458 | 1.2383 | 1.4882 |

## 四、逐题对比汇总

| 相对基线实验 | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --- | --- | --- | --- | --- | --- | --- |
| E3 vs E3_PAPER | 375 | 63 | 283 | 0.2011 | 0.2249 | 0.6033 |
| E4_HYBRID vs E3 | 59 | 30 | 632 | 0.0185 | 0.0421 | 0.0555 |
| E5_HYBRID_LOCAL vs E3 | 152 | 107 | 462 | 0.0208 | 0.0432 | 0.0624 |

## 五、E3 相对 E3_PAPER 的错误类型分析

- 改善题数：375
- 退化题数：63
- 持平题数：283
- 平均 Recall 变化：0.2011
- 平均 MRR 变化：0.2249
- 平均命中表数变化：0.6033

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 2 | 116 |
| 0 -> 1 | 112 |
| 0 -> 0 | 110 |
| 1 -> 1 | 86 |
| 2 -> 2 | 78 |
| 0 -> 2 | 67 |
| 2 -> 3 | 36 |
| 1 -> 0 | 31 |
| 1 -> 3 | 27 |
| 0 -> 3 | 17 |
| 2 -> 1 | 15 |
| 3 -> 2 | 13 |
| 3 -> 3 | 9 |
| 2 -> 0 | 3 |
| 3 -> 0 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 45 |
| greater than | 22 |
| at least | 14 |
| who have | 11 |
| both | 8 |
| along with | 7 |
| currently | 6 |
| who has | 5 |
| less than | 4 |
| for which | 3 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 8 |
| greater than | 4 |
| who have | 4 |
| at least | 3 |
| who has | 2 |
| temporary acting | 1 |
| both | 1 |
| lowest | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 45 |
| number | 41 |
| how | 38 |
| many | 37 |
| located | 37 |
| average | 33 |
| students | 29 |
| total | 26 |
| first | 25 |
| department | 24 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 25 |
| city | 16 |
| average | 12 |
| code | 10 |
| baltimore | 10 |
| distance | 9 |
| first | 9 |
| last | 9 |
| members | 9 |
| club | 9 |

### 代表性改善样例

- Q109: What is the total combined balance from both savings and checking accounts of customers named Brown, Wang, and Granger? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q145: How many distinct aircraft, ordered after 1996, have been piloted by pilots in the 'Center Team' position? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q248: Who are the authors of the paper titled 'An Equivalence-Preserving CPS Translation via Multi-Language Semantics'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q264: Which chargeable parts have had faults that required skill ID 3 to fix? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q350: Which physicians have valid certifications as of December 31, 2008 for procedures that cost over $5000? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q477: Which store has the largest area size among the stores that are located in districts with a city population higher th... | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q534: Which dormitories that have both 'Air Conditioning' and 'Working Fireplaces' have a student capacity greater than 200? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q536: Which dorms have 'Air Conditioning' and a student capacity greater than the average capacity of all dormitories? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q539: Which dorms have both 'Study Room' and 'Ethernet Ports' amenities, and among those, what is the maximum student capac... | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q552: Which dorms with a student capacity of more than 300 have a pub in the basement? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q14: Which employee is certified to operate aircrafts having the largest combined flight distance? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q19: Find the first and last names of students who live in PIT and have allergies to animals. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q25: Find the first and last names of students who have both animal and food allergies. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q668: Who among the students in the city code 'HKG' has the highest total number of pets, and how many pets do they have? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q0: What are the names of heads serving as temporary acting heads in departments with rankings better than 5? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q8: Which employee is certified to operate the aircraft with the greatest flying distance, and what is the maximum distan... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q9: Who are the employees with salary above 200,000 certified to operate aircrafts having distance greater than 6000 miles? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q10: What are the names of the aircraft that the employee with the highest salary is certified to operate? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q11: Who has the highest salary among the employees certified to fly the Airbus A340-300 aircraft, and what is their salary? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q12: Which employee has certificates for aircraft with the highest average flight distance, and what is this average dista... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000

## 五、E4_HYBRID 相对 E3 的错误类型分析

- 改善题数：59
- 退化题数：30
- 持平题数：632
- 平均 Recall 变化：0.0185
- 平均 MRR 变化：0.0421
- 平均命中表数变化：0.0555

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 241 |
| 1 -> 1 | 191 |
| 0 -> 0 | 126 |
| 3 -> 3 | 74 |
| 1 -> 2 | 22 |
| 2 -> 3 | 18 |
| 2 -> 1 | 15 |
| 3 -> 2 | 14 |
| 0 -> 2 | 12 |
| 0 -> 1 | 7 |
| 3 -> 1 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 11 |
| at least | 5 |
| less than | 3 |
| highest | 3 |
| both | 2 |
| who has | 2 |
| currently | 2 |
| along with | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 3 |
| temporary acting | 2 |
| highest | 2 |
| both | 2 |
| currently | 1 |
| earliest | 1 |
| who has | 1 |
| who have | 1 |
| at least | 1 |
| along with | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| account | 23 |
| greater | 15 |
| savings | 15 |
| checking | 15 |
| balance | 13 |
| customers | 11 |
| balances | 8 |
| student | 8 |
| capacity | 7 |
| how | 6 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| located | 4 |
| maximum | 4 |
| heads | 3 |
| named | 3 |
| march | 3 |
| distinct | 3 |
| hosted | 3 |
| cities | 3 |
| capacity | 3 |
| greater | 3 |

### 代表性改善样例

- Q98: Which customers have savings account balances over 100000 and checking account balances of at least 5000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q99: Which customers have both savings balances greater than 50000 and checking balances greater than 5000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q103: Which customer(s) have savings account balance greater than 50000 and checking account balance of at least 10000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q106: Which customers have savings account balances greater than 50,000 and checking account balances greater than 5,000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q110: Which customers have a savings account balance greater than 100000 and a checking account balance less than 5000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q113: Which customers have a savings account balance greater than 190,000 and a checking account balance greater than 2,500? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q121: Which customers have savings account balances greater than 50,000 and checking account balances above 5,000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q188: Who were the main hosts responsible for parties held at the Heineken Music Hall Amsterdam? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q227: List all paper titles authored by individuals from institutions in Japan. | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q389: What is the name of the club that the youngest student from BAL city is a member of? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q1: Which department(s) currently have temporary acting heads who were born in California? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q20: List the names of students located in 'PIT' who have an animal-related allergy. | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q54: How many different phone companies manufactured devices using a chip model that supports WiFi '802.11b' and utilizing... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q109: What is the total combined balance from both savings and checking accounts of customers named Brown, Wang, and Granger? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q124: Which web client accelerators compatible with Firefox since 2007 or earlier support wireless connections? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q189: How many distinct hosts from the United States have hosted parties located at Heineken Music Hall Amsterdam? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q196: Which regions have been affected by storms with a maximum speed below 980 and had more than 20 cities affected? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q264: Which chargeable parts have had faults that required skill ID 3 to fix? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q344: What is the name of the patient who underwent procedure 7 while staying in room 112? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q365: What are the names of all medications prescribed to the patient living at '1100 Foobaz Avenue' and what are their res... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000

## 五、E5_HYBRID_LOCAL 相对 E3 的错误类型分析

- 改善题数：152
- 退化题数：107
- 持平题数：462
- 平均 Recall 变化：0.0208
- 平均 MRR 变化：0.0432
- 平均命中表数变化：0.0624

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 186 |
| 1 -> 1 | 135 |
| 0 -> 0 | 83 |
| 3 -> 3 | 58 |
| 1 -> 2 | 47 |
| 0 -> 1 | 44 |
| 2 -> 3 | 40 |
| 2 -> 1 | 39 |
| 1 -> 0 | 28 |
| 3 -> 2 | 23 |
| 0 -> 2 | 17 |
| 2 -> 0 | 9 |
| 3 -> 0 | 5 |
| 1 -> 3 | 3 |
| 3 -> 1 | 3 |
| 0 -> 3 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 14 |
| highest | 9 |
| who have | 8 |
| at least | 8 |
| both | 6 |
| who has | 3 |
| less than | 3 |
| along with | 3 |
| ordered by | 2 |
| currently | 2 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 10 |
| greater than | 8 |
| at least | 3 |
| both | 3 |
| along with | 3 |
| currently | 2 |
| who have | 1 |
| earliest | 1 |
| for which | 1 |
| who has | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 36 |
| city | 28 |
| account | 28 |
| first | 18 |
| greater | 18 |
| savings | 18 |
| last | 17 |
| checking | 17 |
| code | 16 |
| located | 14 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| located | 12 |
| paper | 12 |
| students | 12 |
| titled | 11 |
| highest | 10 |
| average | 10 |
| author | 10 |
| number | 10 |
| student | 9 |
| city | 9 |

### 代表性改善样例

- Q25: Find the first and last names of students who have both animal and food allergies. | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q537: How many dorms with a student capacity greater than 100 have the amenity 'Pub in Basement'? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.3333 -> 1.0000
- Q18: How many distinct students older than 18 have allergies classified as animal-related? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q357: List the names of physicians along with procedure names and their costs, for which they hold valid certifications exp... | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q14: Which employee is certified to operate aircrafts having the largest combined flight distance? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q19: Find the first and last names of students who live in PIT and have allergies to animals. | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q98: Which customers have savings account balances over 100000 and checking account balances of at least 5000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q99: Which customers have both savings balances greater than 50000 and checking balances greater than 5000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q103: Which customer(s) have savings account balance greater than 50000 and checking account balance of at least 10000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q106: Which customers have savings account balances greater than 50,000 and checking account balances greater than 5,000? | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q210: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q211: Who is the first-listed author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q213: Who is the primary author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q534: Which dormitories that have both 'Air Conditioning' and 'Working Fireplaces' have a student capacity greater than 200? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q552: Which dorms with a student capacity of more than 300 have a pub in the basement? | 命中表数 3 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q536: Which dorms have 'Air Conditioning' and a student capacity greater than the average capacity of all dormitories? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q539: Which dorms have both 'Study Room' and 'Ethernet Ports' amenities, and among those, what is the maximum student capac... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 0.3333
- Q37: Who was the editor responsible for the photo work in the journal issue with the highest sales? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q17: List the names of the employees who are certified to fly aircraft capable of traveling more than 8000 miles and who h... | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q34: Who was responsible for the photo work type in the journal themed 'at Minnesota Vikings'? | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 1.0000 -> 0.0000
