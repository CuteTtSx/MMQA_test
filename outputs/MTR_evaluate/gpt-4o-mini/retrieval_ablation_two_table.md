# two_table 检索消融实验与错误类型分析

- 本报告实际使用的评估 Top-K：`2`

## 一、关键观察

- `E3` 相对 `E3_PAPER`：Recall +0.0987，MRR +0.0850
- `E4_HYBRID` 相对 `E3_PAPER`：Recall +0.0969，MRR +0.0838
- `E5_HYBRID_LOCAL` 相对 `E3_PAPER`：Recall +0.0987，MRR +0.0850

## 二、最佳指标

- 最佳 Recall：`E3` = 0.5458
- 最佳 MRR：`E3` = 0.8098
- 最佳 MAP@k：`E3` = 0.5184

## 三、消融实验对照表

| 实验 | 设置 | 问题分解 | 关系传播 | Recall | Precision | F1 | MRR | MAP@k | 平均首个命中排名 | 平均命中表数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3_PAPER | 完整 MTR（paper-like） | 是 | 是 | 0.4471 | 0.4471 | 0.4471 | 0.7247 | 0.4177 | 1.1502 | 0.8942 |
| E3 | 完整 MTR | 是 | 是 | 0.5458 | 0.5458 | 0.5458 | 0.8098 | 0.5184 | 1.1265 | 1.0916 |
| E4_HYBRID | Hybrid：不确定性门控传播 | 是 | 是 | 0.5440 | 0.5440 | 0.5440 | 0.8086 | 0.5178 | 1.1215 | 1.0880 |
| E5_HYBRID_LOCAL | Hybrid：局部扩展 + 重排 | 是 | 是 | 0.5458 | 0.5458 | 0.5458 | 0.8098 | 0.5184 | 1.1265 | 1.0916 |

## 四、逐题对比汇总

| 对比实验 | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --- | --- | --- | --- | --- | --- | --- |
| E3 vs E3_PAPER | 230 | 66 | 545 | 0.0987 | 0.0850 | 0.1974 |
| E4_HYBRID vs E3 | 12 | 15 | 814 | -0.0018 | -0.0012 | -0.0036 |
| E5_HYBRID_LOCAL vs E3 | 0 | 0 | 841 | 0.0000 | 0.0000 | 0.0000 |

## 五、E3 相对 E3_PAPER 的错误类型分析

- 改善题数：230
- 退化题数：66
- 持平题数：545
- 平均 Recall 变化：0.0987
- 平均 MRR 变化：0.0850
- 平均命中表数变化：0.1974

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 1 | 404 |
| 1 -> 2 | 121 |
| 0 -> 1 | 107 |
| 0 -> 0 | 73 |
| 2 -> 2 | 68 |
| 1 -> 0 | 41 |
| 2 -> 1 | 25 |
| 0 -> 2 | 2 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 30 |
| greater than | 22 |
| at least | 13 |
| who have | 10 |
| along with | 5 |
| less than | 5 |
| who has | 4 |
| earliest | 4 |
| latest | 2 |
| for which | 2 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 7 |
| who have | 4 |
| both | 3 |
| greater than | 3 |
| at least | 3 |
| along with | 1 |
| less than | 1 |
| currently | 1 |
| latest | 1 |
| ordered by | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| total | 32 |
| customers | 32 |
| highest | 30 |
| how | 29 |
| many | 29 |
| number | 28 |
| average | 26 |
| greater | 22 |
| amount | 21 |
| customer | 18 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| total | 14 |
| player | 14 |
| number | 12 |
| country | 9 |
| team | 8 |
| students | 7 |
| customer | 7 |
| highest | 7 |
| amount | 6 |
| season | 6 |

### 代表性改善样例

- Q81: What is the total price of all books written by Garth Ennis? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q183: How many tracks are contained in the playlist named 'Music'? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q98: Who does Iron Man follow that has more than 1 million followers? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q100: What are the names of the users followed by the user that Natalie Portman is following? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q130: Who is the employee with the highest salary among those who have received certificate number 15? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q132: Which students from Pittsburgh (PIT) have an allergy to nuts? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q134: How many distinct students from city code 'PHL' have an allergy to either 'Nuts' or 'Soy'? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q141: How many students from city 'HKG' have an allergy to shellfish? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q142: How many distinct students from PIT city have an allergy to either Shellfish or Nuts? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q144: Who are the students living in city HKG that have an allergy to Soy? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q23: Which students attended both statistics and French courses? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q32: What is the state_province_county of the address where the person with person_id 141 lived? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q109: List the product names and their prices in dollars from the catalog entries that have an attribute ID 3 set as '1' an... | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q140: What are the first and last names of students who have a nut allergy and live in the city with the code 'PIT'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q143: List the full names and city codes of students who have allergies to both 'Nuts' and 'Soy'. | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q148: Which customer from Germany has the highest total spending amount? Provide their first name, last name, and the total... | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q149: Which customer in Germany has spent the most money and what is their total spending amount? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q151: Which customer from Germany has spent the most total, and how much have they spent? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q329: Which team selected the player from the 2007 MLS SuperDraft, and what was their playing position? Also, provide detai... | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q334: What was the name, position, and native language of the player, along with his country name, who played during the 20... | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000

## 五、E4_HYBRID 相对 E3 的错误类型分析

- 改善题数：12
- 退化题数：15
- 持平题数：814
- 平均 Recall 变化：-0.0018
- 平均 MRR 变化：-0.0012
- 平均命中表数变化：-0.0036

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 1 | 521 |
| 2 -> 2 | 180 |
| 0 -> 0 | 113 |
| 1 -> 2 | 11 |
| 2 -> 1 | 11 |
| 1 -> 0 | 4 |
| 0 -> 1 | 1 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 4 |
| highest | 2 |
| who have | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 2 |
| greater than | 2 |
| at least | 1 |
| who have | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater | 4 |
| population | 4 |
| percentage | 3 |
| average | 3 |
| counties | 3 |
| first | 2 |
| party | 2 |
| participated | 2 |
| directors | 2 |
| highest | 2 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| total | 2 |
| amount | 2 |
| located | 2 |
| models | 2 |
| country | 2 |
| highest | 2 |
| employees | 2 |
| editor | 2 |
| population | 2 |
| greater | 2 |

### 代表性改善样例

- Q845: What is the name and case burden of the county which has the city with the highest percentage of Asian population? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 0.5000
- Q314: Which university's basketball team had an ACC road record of 6–2 and an overall game winning percentage greater than ... | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q405: What are the first and last names of the guests who have confirmed apartment bookings ending before October 1, 2017? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q678: Which ministers belong to the party 'Convention Peoples Party' and participated in the event named 'Election Meeting'? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q701: Which organizers have participated in the same events as participant Justyn Lebsack? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q813: What movies have directors that are also listed as reviewers? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q829: Among directors who made films after 1980, which director has the highest average star rating? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q844: What is the average crime rate in counties that have cities with a Black population percentage greater than 10%? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q851: What is the average crime rate in counties that contain cities with a Black population greater than 20%? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000
- Q904: Which counties with population greater than 20,000 are represented by delegates first elected before the year 2000, a... | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q157: What is the total amount spent by all customers located in Germany? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q337: Which country's official native language has the highest number of midfielders playing across all seasons? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q685: What are the names of employees whose roles are described as 'Editor'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q686: What are the names of employees who have the role description 'Editor'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q302: Which FDA-approved medicines have an inhibitor interaction with enzyme 2? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q322: Which companies have phone models using chip models launched by 2004 that support WiFi standard 802.11b? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q394: What apartment numbers have at least 2 bathrooms and a confirmed booking ending on or after November 1, 2017? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q430: What is the name of the league in the country whose name is Portugal? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q540: List the names of all males from United States who got married on or after 2015. | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q849: Which cities have a Black population greater than 10% and are located in counties that use RCMP as their police force? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000

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
| 1 -> 1 | 536 |
| 2 -> 2 | 191 |
| 0 -> 0 | 114 |

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
