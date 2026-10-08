# three_table 检索消融实验与错误类型分析

- 本报告实际使用的评估 Top-K：`3`

## 一、关键观察

- `E3` 相对 `E3_PAPER`：Recall +0.1318，MRR +0.1549
- `E4_HYBRID` 相对 `E3_PAPER`：Recall +0.1336，MRR +0.1639
- `E5_HYBRID_LOCAL` 相对 `E3_PAPER`：Recall +0.1253，MRR +0.1466

## 二、最佳指标

- 最佳 Recall：`E4_HYBRID` = 0.5109
- 最佳 MRR：`E4_HYBRID` = 0.7890
- 最佳 MAP@k：`E4_HYBRID` = 0.4573

## 三、消融实验对照表

| 实验 | 设置 | 问题分解 | 关系传播 | Recall | Precision | F1 | MRR | MAP@k | 平均首个命中排名 | 平均命中表数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3_PAPER | 完整 MTR（paper-like） | 是 | 是 | 0.3773 | 0.3773 | 0.3773 | 0.6251 | 0.3293 | 1.3035 | 1.1318 |
| E3 | 完整 MTR | 是 | 是 | 0.5090 | 0.5090 | 0.5090 | 0.7799 | 0.4537 | 1.2520 | 1.5270 |
| E4_HYBRID | Hybrid：不确定性门控传播 | 是 | 是 | 0.5109 | 0.5109 | 0.5109 | 0.7890 | 0.4573 | 1.2369 | 1.5326 |
| E5_HYBRID_LOCAL | Hybrid：局部扩展 + 重排 | 是 | 是 | 0.5025 | 0.5025 | 0.5025 | 0.7716 | 0.4524 | 1.2160 | 1.5076 |

## 四、逐题对比汇总

| 对比实验 | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --- | --- | --- | --- | --- | --- | --- |
| E3 vs E3_PAPER | 310 | 90 | 321 | 0.1318 | 0.1549 | 0.3953 |
| E4_HYBRID vs E3 | 24 | 21 | 676 | 0.0018 | 0.0090 | 0.0055 |
| E5_HYBRID_LOCAL vs E3 | 10 | 23 | 688 | -0.0065 | -0.0083 | -0.0194 |

## 五、E3 相对 E3_PAPER 的错误类型分析

- 改善题数：310
- 退化题数：90
- 持平题数：321
- 平均 Recall 变化：0.1318
- 平均 MRR 变化：0.1549
- 平均命中表数变化：0.3953

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 127 |
| 1 -> 1 | 113 |
| 1 -> 2 | 100 |
| 0 -> 1 | 90 |
| 0 -> 0 | 57 |
| 0 -> 2 | 51 |
| 2 -> 3 | 43 |
| 2 -> 1 | 30 |
| 1 -> 0 | 29 |
| 3 -> 3 | 24 |
| 1 -> 3 | 17 |
| 3 -> 1 | 13 |
| 3 -> 2 | 10 |
| 0 -> 3 | 9 |
| 2 -> 0 | 8 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 40 |
| greater than | 21 |
| who have | 9 |
| at least | 6 |
| along with | 6 |
| who has | 4 |
| for which | 4 |
| both | 3 |
| currently | 3 |
| earliest | 2 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| who have | 12 |
| greater than | 7 |
| at least | 7 |
| highest | 6 |
| both | 4 |
| who has | 3 |
| temporary acting | 2 |
| currently | 1 |
| earliest | 1 |
| less than | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| city | 44 |
| students | 42 |
| highest | 40 |
| average | 33 |
| located | 28 |
| number | 28 |
| how | 27 |
| many | 26 |
| total | 25 |
| code | 24 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 23 |
| customers | 15 |
| how | 14 |
| many | 14 |
| located | 14 |
| city | 11 |
| clubs | 11 |
| account | 10 |
| akw | 10 |
| distance | 9 |

### 代表性改善样例

- Q97: Who is the coach of the player named Judy Wasylycia-Leis? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q353: List the names of physicians whose training certifications expire on '2008-12-31' and who are trained in performing p... | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q355: Which physicians have valid certifications expiring on December 31, 2008, and are trained to perform procedures costi... | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q357: List the names of physicians along with procedure names and their costs, for which they hold valid certifications exp... | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q536: Which dorms have 'Air Conditioning' and a student capacity greater than the average capacity of all dormitories? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q537: How many dorms with a student capacity greater than 100 have the amenity 'Pub in Basement'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q559: What dormitory with a student capacity greater than 300 provides both 'Air Conditioning' and also 'Allows Pets'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q560: Which dorms with a student capacity greater than 100 have a 'Pub in Basement' as an amenity? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q684: Which car makers from country '4' produce models with the name containing 'corolla'? | 命中表数 0 -> 3 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q692: Which template type description has the document with the highest version number? | 命中表数 1 -> 3 | Recall 0.3333 -> 1.0000 | MRR 0.3333 -> 1.0000

### 代表性退化样例

- Q0: What are the names of heads serving as temporary acting heads in departments with rankings better than 5? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q1: Which department(s) currently have temporary acting heads who were born in California? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q2: List the names of students who have registered for both Statistics and English courses. | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q3: List the names of students who are registered for both the 'statistics' and 'French' courses. | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q8: Which employee is certified to operate the aircraft with the greatest flying distance, and what is the maximum distan... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q9: Who are the employees with salary above 200,000 certified to operate aircrafts having distance greater than 6000 miles? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q10: What are the names of the aircraft that the employee with the highest salary is certified to operate? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q12: Which employee has certificates for aircraft with the highest average flight distance, and what is this average dista... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q13: Which employee has certificates for aircrafts that have the highest average flying distance, and what is this average... | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q14: Which employee is certified to operate aircrafts having the largest combined flight distance? | 命中表数 3 -> 1 | Recall 1.0000 -> 0.3333 | MRR 1.0000 -> 1.0000

## 五、E4_HYBRID 相对 E3 的错误类型分析

- 改善题数：24
- 退化题数：21
- 持平题数：676
- 平均 Recall 变化：0.0018
- 平均 MRR 变化：0.0090
- 平均命中表数变化：0.0055

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 269 |
| 1 -> 1 | 233 |
| 0 -> 0 | 90 |
| 3 -> 3 | 84 |
| 1 -> 2 | 11 |
| 2 -> 1 | 10 |
| 2 -> 3 | 9 |
| 3 -> 2 | 9 |
| 0 -> 1 | 3 |
| 1 -> 0 | 2 |
| 0 -> 2 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 3 |
| at least | 3 |
| who have | 1 |
| along with | 1 |
| who has | 1 |
| less than | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 2 |
| ordered by | 1 |
| at least | 1 |
| highest | 1 |
| along with | 1 |
| both | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| account | 10 |
| balance | 6 |
| students | 5 |
| savings | 5 |
| checking | 5 |
| greater | 4 |
| how | 4 |
| many | 4 |
| average | 4 |
| located | 3 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| total | 4 |
| first | 3 |
| average | 3 |
| gdp | 3 |
| last | 2 |
| host | 2 |
| country | 2 |
| author | 2 |
| patient | 2 |
| prescribed | 2 |

### 代表性改善样例

- Q20: List the names of students located in 'PIT' who have an animal-related allergy. | 命中表数 0 -> 2 | Recall 0.0000 -> 0.6667 | MRR 0.0000 -> 1.0000
- Q74: What are the titles of the courses along with building names and room numbers for courses held in Fall 2005 in classr... | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q105: Who has savings account balance greater than 100000 and checking account balance greater than 5000? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q136: Which USA-headquartered company has the most gas stations according to the provided data, and how many stations does ... | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q199: What are the names of the events that were hosted by journalists with more than 10 years of working experience? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q347: Who is affiliated with the General Medicine department but doesn't have it as their primary affiliation? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q440: Which companies have office locations in buildings located in Mexico City with more than 50 stories? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q616: What is the average July temperature of cities with GDP above 500 that have hosted matches? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q659: What are the names of concerts held in 2014 that featured singers from France? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q683: How many distinct car models are produced by car makers from country 2? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q129: Which buildings host institutions that have proteins with sequence lengths exceeding 1800 and are taller than 250 feet? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q190: Which party theme had a host with Hungarian nationality serving as the main in charge? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q344: What is the name of the patient who underwent procedure 7 while staying in room 112? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q363: List the names of all patients who were prescribed the medication 'Thesisin' with a dose of 5. | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q365: What are the names of all medications prescribed to the patient living at '1100 Foobaz Avenue' and what are their res... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q491: What is the total quantity of Android devices stocked in shops opened before the year 2010? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q530: Which swimmer from a country matching the stadium hosting the 'European FINA' event had the fastest overall recorded ... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q536: Which dorms have 'Air Conditioning' and a student capacity greater than the average capacity of all dormitories? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q326: List players' first name and last name who received salary from team Washington Nationals in both 2005 and 2007. | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q244: In which country is the institution located whose author is the first author of the paper 'Functional Pearl: Modular ... | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000

## 五、E5_HYBRID_LOCAL 相对 E3 的错误类型分析

- 改善题数：10
- 退化题数：23
- 持平题数：688
- 平均 Recall 变化：-0.0065
- 平均 MRR 变化：-0.0083
- 平均命中表数变化：-0.0194

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 2 -> 2 | 277 |
| 1 -> 1 | 224 |
| 0 -> 0 | 94 |
| 3 -> 3 | 93 |
| 1 -> 0 | 15 |
| 1 -> 2 | 7 |
| 2 -> 1 | 7 |
| 2 -> 3 | 3 |
| 2 -> 0 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| both | 3 |
| who have | 3 |
| temporary acting | 2 |
| currently | 1 |
| earliest | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| along with | 2 |
| greater than | 2 |
| both | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| students | 7 |
| allergies | 5 |
| heads | 3 |
| how | 3 |
| many | 3 |
| city | 3 |
| food | 3 |
| temporary | 2 |
| acting | 2 |
| registered | 2 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| course | 10 |
| student | 9 |
| grade | 8 |
| department | 7 |
| courses | 5 |
| section | 5 |
| classes | 5 |
| credit | 5 |
| students | 5 |
| capacity | 5 |

### 代表性改善样例

- Q25: Find the first and last names of students who have both animal and food allergies. | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q26: How many students from PIT city have food-related allergies? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q27: How many unique students from the city PIT have food-related allergies? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q0: What are the names of heads serving as temporary acting heads in departments with rankings better than 5? | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q1: Which department(s) currently have temporary acting heads who were born in California? | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q2: List the names of students who have registered for both Statistics and English courses. | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q3: List the names of students who are registered for both the 'statistics' and 'French' courses. | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q4: What is the name and qualification of the candidate who was the earliest to receive a 'Pass' assessment outcome, and ... | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q22: How many students under 20 years old have allergies categorized as 'animal'? | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q24: What are the names of students younger than 20 years old from city code 'BAL' who have environmental allergies? | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q287: List the course code, class section, and room for all classes in which William Bowser is enrolled. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q275: Which courses did the student with the last name 'Smithson' take and get a grade of 'B'? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q288: What is the full name of the student who received an 'A' grade in course 'CIS-220'? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q300: What are the first and last names of professors along with class section, class time, and course description for clas... | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q64: Which courses in Cybernetics were taught during Spring 2008, and who were their instructors? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q274: List the course code, section, and classroom for the classes in which student Bowser received an 'A' grade. | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q279: What is the total number of credits for all classes conducted by the 'Computer Info. Systems' department in room 'KLR... | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q281: What is the full name of the professor and their department who teaches section 1 of course QM-362? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q291: What classroom is the section 1 of the 4-credit course offered by the Computer Info. Systems department held in? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q292: What is the class time of the courses offered by the Computer Info. Systems department that have a credit of 4.0? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
