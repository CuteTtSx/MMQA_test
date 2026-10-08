# three_table 检索消融实验与错误类型分析

- 本报告实际使用的评估 Top-K：`3`

## 一、关键观察

- `E1` 相对 `E3`：Recall +0.0000，MRR -0.0046
- `E2` 相对 `E3`：Recall +0.0000，MRR +0.0012
- `E4_HYBRID` 相对 `E3`：Recall +0.0060，MRR +0.0129
- `E5_HYBRID_LOCAL` 相对 `E3`：Recall -0.0060，MRR -0.0025

## 二、最佳指标

- 最佳 Recall：`E4_HYBRID` = 0.5141
- 最佳 MRR：`E4_HYBRID` = 0.7908
- 最佳 MAP@k：`E4_HYBRID` = 0.4585

## 三、消融实验对照表


| 实验              | 设置               | 问题分解 | 关系传播 | Recall | Precision | F1     | MRR    | MAP@k  | 平均首个命中排名 | 平均命中表数 |
| --------------- | ---------------- | ---- | ---- | ------ | --------- | ------ | ------ | ------ | -------- | ------ |
| E1              | baseline 纯语义     | 否    | 否    | 0.5081 | 0.5081    | 0.5081 | 0.7732 | 0.4483 | 1.2778   | 1.5243 |
| E2              | 分解 + 纯语义         | 是    | 否    | 0.5081 | 0.5081    | 0.5081 | 0.7790 | 0.4513 | 1.2862   | 1.5243 |
| E3              | 完整 MTR           | 是    | 是    | 0.5081 | 0.5081    | 0.5081 | 0.7779 | 0.4500 | 1.2846   | 1.5243 |
| E4_HYBRID       | Hybrid：不确定性门控传播  | 是    | 是    | 0.5141 | 0.5141    | 0.5141 | 0.7908 | 0.4585 | 1.2590   | 1.5423 |
| E5_HYBRID_LOCAL | Hybrid：局部扩展 + 重排 | 是    | 是    | 0.5021 | 0.5021    | 0.5021 | 0.7753 | 0.4530 | 1.2237   | 1.5062 |


## 四、逐题对比汇总


| 对比实验                  | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --------------------- | ---- | ---- | ---- | ------------ | --------- | -------- |
| E2 vs E3              | 0    | 0    | 721  | 0.0000       | 0.0012    | 0.0000   |
| E4_HYBRID vs E3       | 29   | 16   | 676  | 0.0060       | 0.0129    | 0.0180   |
| E5_HYBRID_LOCAL vs E3 | 13   | 24   | 684  | -0.0060      | -0.0025   | -0.0180  |


## 五、E2 相对 E3 的错误类型分析

- 改善题数：0
- 退化题数：0
- 持平题数：721
- 平均 Recall 变化：0.0000
- 平均 MRR 变化：0.0012
- 平均命中表数变化：0.0000

### 命中表数转移矩阵


| 命中表数转移 | 题数  |
| ------ | --- |
| 1 -> 1 | 270 |
| 2 -> 2 | 269 |
| 3 -> 3 | 97  |
| 0 -> 0 | 85  |


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

## 五、E4_HYBRID 相对 E3 的错误类型分析

- 改善题数：29
- 退化题数：16
- 持平题数：676
- 平均 Recall 变化：0.0060
- 平均 MRR 变化：0.0129
- 平均命中表数变化：0.0180

### 命中表数转移矩阵


| 命中表数转移 | 题数  |
| ------ | --- |
| 2 -> 2 | 252 |
| 1 -> 1 | 251 |
| 3 -> 3 | 90  |
| 0 -> 0 | 83  |
| 1 -> 2 | 18  |
| 2 -> 3 | 9   |
| 2 -> 1 | 8   |
| 3 -> 2 | 7   |
| 0 -> 1 | 2   |
| 1 -> 0 | 1   |


### 改善题中的高频短语模式


| 模式 / 关键词     | 次数  |
| ------------ | --- |
| greater than | 8   |
| at least     | 2   |
| who has      | 2   |
| less than    | 2   |
| along with   | 1   |
| highest      | 1   |
| currently    | 1   |


### 退化题中的高频短语模式


| 模式 / 关键词     | 次数  |
| ------------ | --- |
| greater than | 2   |
| at least     | 1   |
| along with   | 1   |


### 改善题中的高频关键词


| 模式 / 关键词  | 次数  |
| --------- | --- |
| account   | 17  |
| greater   | 11  |
| balance   | 10  |
| savings   | 9   |
| checking  | 9   |
| customers | 6   |
| balances  | 6   |
| student   | 3   |
| city      | 3   |
| how       | 3   |


### 退化题中的高频关键词


| 模式 / 关键词 | 次数  |
| -------- | --- |
| march    | 3   |
| policies | 2   |
| named    | 2   |
| how      | 2   |
| many     | 2   |
| been     | 2   |
| affected | 2   |
| cities   | 2   |
| hosted   | 2   |
| classes  | 2   |


### 代表性改善样例

- Q74: What are the titles of the courses along with building names and room numbers for courses held in Fall 2005 in classr... | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q104: Who has more than 100000 in savings and also more than 5000 in checking account? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q105: Who has savings account balance greater than 100000 and checking account balance greater than 5000? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q114: Which account holders have savings balance greater than 50000 but checking account balance less than 5000? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q199: What are the names of the events that were hosted by journalists with more than 10 years of working experience? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q347: Who is affiliated with the General Medicine department but doesn't have it as their primary affiliation? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q353: List the names of physicians whose training certifications expire on '2008-12-31' and who are trained in performing p... | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q659: What are the names of concerts held in 2014 that featured singers from France? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q683: How many distinct car models are produced by car makers from country 2? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q418: How many unique documents are associated with grants provided by organisations that have awarded grants with amounts ... | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 0.5000 -> 1.0000

### 代表性退化样例

- Q54: How many different phone companies manufactured devices using a chip model that supports WiFi '802.11b' and utilizing... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q124: Which web client accelerators compatible with Firefox since 2007 or earlier support wireless connections? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q196: Which regions have been affected by storms with a maximum speed below 980 and had more than 20 cities affected? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q202: What events were hosted by English journalists? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q344: What is the name of the patient who underwent procedure 7 while staying in room 112? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q365: What are the names of all medications prescribed to the patient living at '1100 Foobaz Avenue' and what are their res... | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q536: Which dorms have 'Air Conditioning' and a student capacity greater than the average capacity of all dormitories? | 命中表数 3 -> 2 | Recall 1.0000 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q301: Which department within the BUS school offers the most classes, and how many classes does it offer? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q41: What type of insurance policies did the customer named Jay Chou have, whose policies were closed between March 15, 20... | 命中表数 2 -> 1 | Recall 0.6667 -> 0.3333 | MRR 1.0000 -> 1.0000
- Q424: List all distinct organisation IDs that have at least one project resulting in a patent. | 命中表数 2 -> 1 | Recall 0.6667 -> 0.3333 | MRR 1.0000 -> 1.0000

## 五、E5_HYBRID_LOCAL 相对 E3 的错误类型分析

- 改善题数：13
- 退化题数：24
- 持平题数：684
- 平均 Recall 变化：-0.0060
- 平均 MRR 变化：-0.0025
- 平均命中表数变化：-0.0180

### 命中表数转移矩阵


| 命中表数转移 | 题数  |
| ------ | --- |
| 2 -> 2 | 258 |
| 1 -> 1 | 244 |
| 3 -> 3 | 97  |
| 0 -> 0 | 85  |
| 1 -> 0 | 17  |
| 1 -> 2 | 9   |
| 2 -> 1 | 5   |
| 2 -> 3 | 4   |
| 2 -> 0 | 2   |


### 改善题中的高频短语模式


| 模式 / 关键词         | 次数  |
| ---------------- | --- |
| who have         | 4   |
| both             | 3   |
| temporary acting | 2   |
| currently        | 1   |
| earliest         | 1   |
| who has          | 1   |
| highest          | 1   |


### 退化题中的高频短语模式


| 模式 / 关键词     | 次数  |
| ------------ | --- |
| along with   | 2   |
| greater than | 2   |
| both         | 1   |


### 改善题中的高频关键词


| 模式 / 关键词  | 次数  |
| --------- | --- |
| students  | 9   |
| allergies | 6   |
| animal    | 5   |
| related   | 5   |
| heads     | 3   |
| how       | 3   |
| many      | 3   |
| pit       | 3   |
| first     | 3   |
| last      | 3   |


### 退化题中的高频关键词


| 模式 / 关键词   | 次数  |
| ---------- | --- |
| course     | 10  |
| student    | 9   |
| classes    | 8   |
| grade      | 8   |
| department | 8   |
| section    | 6   |
| class      | 6   |
| credit     | 6   |
| capacity   | 6   |
| courses    | 5   |


### 代表性改善样例

- Q18: How many distinct students older than 18 have allergies classified as animal-related? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q20: List the names of students located in 'PIT' who have an animal-related allergy. | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q26: How many students from PIT city have food-related allergies? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q27: How many unique students from the city PIT have food-related allergies? | 命中表数 2 -> 3 | Recall 0.6667 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q0: What are the names of heads serving as temporary acting heads in departments with rankings better than 5? | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q1: Which department(s) currently have temporary acting heads who were born in California? | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q2: List the names of students who have registered for both Statistics and English courses. | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q3: List the names of students who are registered for both the 'statistics' and 'French' courses. | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q4: What is the name and qualification of the candidate who was the earliest to receive a 'Pass' assessment outcome, and ... | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000
- Q11: Who has the highest salary among the employees certified to fly the Airbus A340-300 aircraft, and what is their salary? | 命中表数 1 -> 2 | Recall 0.3333 -> 0.6667 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q280: Which classes, along with their times and rooms, belong to the 'Computer Info. Systems' department and have a course ... | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q287: List the course code, class section, and room for all classes in which William Bowser is enrolled. | 命中表数 2 -> 0 | Recall 0.6667 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q271: Which classes (course code, section, class time, and professor number) offered by the Business school have a credit v... | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q275: Which courses did the student with the last name 'Smithson' take and get a grade of 'B'? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q288: What is the full name of the student who received an 'A' grade in course 'CIS-220'? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q303: Which students earned a grade of 'A' in courses having exactly 3 credit hours? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q64: Which courses in Cybernetics were taught during Spring 2008, and who were their instructors? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q279: What is the total number of credits for all classes conducted by the 'Computer Info. Systems' department in room 'KLR... | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q281: What is the full name of the professor and their department who teaches section 1 of course QM-362? | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000
- Q289: List the course descriptions and their credits for the classes where student number 321452 received a grade of 'C'. | 命中表数 1 -> 0 | Recall 0.3333 -> 0.0000 | MRR 0.3333 -> 0.0000

