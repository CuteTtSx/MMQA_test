# two_table 检索消融实验与错误类型分析

- 本报告实际使用的评估 Top-K：`2`

## 一、关键观察

- `E3` 相对 `E3_PAPER`：Recall +0.2729，MRR +0.3900
- `E4_HYBRID` 相对 `E3_PAPER`：Recall +0.2735，MRR +0.4043
- `E5_HYBRID_LOCAL` 相对 `E3_PAPER`：Recall +0.2990，MRR +0.4257

## 二、最佳指标

- 最佳 Recall：`E5_HYBRID_LOCAL` = 0.5440
- 最佳 MRR：`E5_HYBRID_LOCAL` = 0.8068
- 最佳 MAP@k：`E5_HYBRID_LOCAL` = 0.5193

## 三、消融实验对照表

| 实验 | 设置 | 问题分解 | 关系传播 | Recall | Precision | F1 | MRR | MAP@k | 平均首个命中排名 | 平均命中表数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3_PAPER | 完整 MTR（paper-like） | 是 | 是 | 0.2449 | 0.2449 | 0.2449 | 0.3811 | 0.2155 | 1.2676 | 0.4899 |
| E3 | 完整 MTR | 是 | 是 | 0.5178 | 0.5178 | 0.5178 | 0.7711 | 0.4896 | 1.1365 | 1.0357 |
| E4_HYBRID | Hybrid：不确定性门控传播 | 是 | 是 | 0.5184 | 0.5184 | 0.5184 | 0.7854 | 0.4955 | 1.1102 | 1.0369 |
| E5_HYBRID_LOCAL | Hybrid：局部扩展 + 重排 | 是 | 是 | 0.5440 | 0.5440 | 0.5440 | 0.8068 | 0.5193 | 1.1153 | 1.0880 |

## 四、逐题对比汇总

| 相对基线实验 | 改善题数 | 退化题数 | 持平题数 | 平均 Recall 变化 | 平均 MRR 变化 | 平均命中表数变化 |
| --- | --- | --- | --- | --- | --- | --- |
| E3 vs E3_PAPER | 442 | 53 | 346 | 0.2729 | 0.3900 | 0.5458 |
| E4_HYBRID vs E3 | 31 | 30 | 780 | 0.0006 | 0.0143 | 0.0012 |
| E5_HYBRID_LOCAL vs E3 | 114 | 74 | 653 | 0.0262 | 0.0357 | 0.0523 |

## 五、E3 相对 E3_PAPER 的错误类型分析

- 改善题数：442
- 退化题数：53
- 持平题数：346
- 平均 Recall 变化：0.2729
- 平均 MRR 变化：0.3900
- 平均命中表数变化：0.5458

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 0 -> 1 | 289 |
| 1 -> 1 | 215 |
| 0 -> 0 | 109 |
| 1 -> 2 | 80 |
| 0 -> 2 | 73 |
| 1 -> 0 | 33 |
| 2 -> 2 | 22 |
| 2 -> 1 | 17 |
| 2 -> 0 | 3 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 79 |
| greater than | 34 |
| at least | 27 |
| who have | 19 |
| earliest | 10 |
| currently | 8 |
| both | 7 |
| less than | 5 |
| who has | 5 |
| along with | 5 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 13 |
| greater than | 4 |
| at least | 3 |
| both | 1 |
| lowest | 1 |
| who have | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| highest | 79 |
| total | 57 |
| average | 53 |
| how | 50 |
| many | 50 |
| number | 45 |
| rating | 38 |
| greater | 34 |
| customers | 31 |
| year | 28 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| how | 13 |
| highest | 13 |
| many | 12 |
| average | 9 |
| rating | 9 |
| customer | 8 |
| customers | 8 |
| total | 7 |
| number | 7 |
| movie | 6 |

### 代表性改善样例

- Q84: What is the total price of all books with at least 5 issues that were not published by Wiley? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q89: Which actors performed in musicals that won for 'Outstanding Choreography'? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q90: Which actor performed in the musical that won the Tony Award for Best Choreography? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q91: Which actor performed in the musical that won the award for Best Choreography? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q95: Who played characters in the musical that won the Tony Award for Best Choreography? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q99: Which user has posted the most number of tweets? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q102: Which user's tweet was posted most recently among those who have less than 500,000 followers? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q105: Among users who have tweeted posts with text length of at least 50 characters, who has the highest follower count? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q106: What is the date of the latest revision for the catalog item with catalog level name 'Product'? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q107: What is the name of the catalog published by Murray Coffee shop categorized as a 'Sub-Category'? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q144: Who are the students living in city HKG that have an allergy to Soy? | 命中表数 2 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q151: Which customer from Germany has spent the most total, and how much have they spent? | 命中表数 2 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q208: How many valid debit cards are associated with customers with the last name 'Effertz'? | 命中表数 2 -> 0 | Recall 1.0000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q24: Which students attended both 'statistics' and 'English' courses? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q128: Which aircrafts with a certified pilot having employee ID 142519864 have a flying distance greater than 5000? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q146: How many students from the city coded 'PIT' have a nut allergy? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q169: Which customer from Germany has spent the highest total amount, and how many invoices did they have? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q183: How many tracks are contained in the playlist named 'Music'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q197: What is the email address of the customer who owns a VIP account named '557'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q199: How many customers residing in NH have VIP accounts? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000

## 五、E4_HYBRID 相对 E3 的错误类型分析

- 改善题数：31
- 退化题数：30
- 持平题数：780
- 平均 Recall 变化：0.0006
- 平均 MRR 变化：0.0143
- 平均命中表数变化：0.0012

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 1 | 493 |
| 2 -> 2 | 151 |
| 0 -> 0 | 136 |
| 2 -> 1 | 24 |
| 1 -> 2 | 22 |
| 0 -> 1 | 9 |
| 1 -> 0 | 6 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| at least | 6 |
| greater than | 5 |
| highest | 3 |
| who have | 1 |
| less than | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 4 |
| highest | 3 |
| who have | 2 |
| currently | 2 |
| earliest | 1 |
| at least | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| average | 7 |
| greater | 5 |
| counties | 5 |
| population | 5 |
| how | 4 |
| many | 4 |
| students | 3 |
| year | 3 |
| ticket | 3 |
| exhibitions | 3 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| number | 5 |
| greater | 4 |
| population | 3 |
| total | 3 |
| worked | 3 |
| highest | 3 |
| counties | 3 |
| hosted | 2 |
| older | 2 |
| amount | 2 |

### 代表性改善样例

- Q133: Which students with an allergy to nuts live in the city PIT? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q146: How many students from the city coded 'PIT' have a nut allergy? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q225: In which year was the track hosting 'Sahlen's Six Hours of the Glen' opened? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q230: What are the addresses of shops opened in 2010 that had a happy hour in May with at least 5 staff members in charge? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q290: How many distinct policies have received notifications of loss from customer Jay Chou? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q409: How many unique buildings have apartments with at least 2 bathrooms and facilities of either a Gym or a Swimming Pool? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q481: List the names of Democratic representatives who successfully affirmed a debate. | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q612: How many customers have more than 50,000 in their savings account and more than 5,000 in their checking account? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q633: List the names of schools that have received endowments from more than one donator and have an enrollment greater tha... | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q96: Identify the names of actors who are at least 20 years old and played roles in musicals that have won a Tony Award? | 命中表数 1 -> 2 | Recall 0.5000 -> 1.0000 | MRR 1.0000 -> 1.0000

### 代表性退化样例

- Q337: Which country's official native language has the highest number of midfielders playing across all seasons? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q157: What is the total amount spent by all customers located in Germany? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q510: How many unique regular accounts are there among customers from Mississippi? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q685: What are the names of employees whose roles are described as 'Editor'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q686: What are the names of employees who have the role description 'Editor'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q1094: What is the total number of appearances (Apps) by players who play either 'Second Row' or 'Loose Forward' position in... | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 0.5000 -> 0.0000
- Q5: Which city with a population greater than 1000 hosted the earliest farm competition? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q93: What musicals nominated for a Drama Desk Award featured actors older than 19 years? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q99: Which user has posted the most number of tweets? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000
- Q187: Which editors under the age of 30 have worked on Photo assignments? | 命中表数 2 -> 1 | Recall 1.0000 -> 0.5000 | MRR 1.0000 -> 1.0000

## 五、E5_HYBRID_LOCAL 相对 E3 的错误类型分析

- 改善题数：114
- 退化题数：74
- 持平题数：653
- 平均 Recall 变化：0.0262
- 平均 MRR 变化：0.0357
- 平均命中表数变化：0.0523

### 命中表数转移矩阵

| 命中表数转移 | 题数 |
| --- | --- |
| 1 -> 1 | 431 |
| 2 -> 2 | 141 |
| 0 -> 0 | 81 |
| 0 -> 1 | 60 |
| 1 -> 2 | 50 |
| 1 -> 0 | 40 |
| 2 -> 1 | 34 |
| 0 -> 2 | 4 |

### 改善题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 14 |
| highest | 11 |
| at least | 7 |
| who have | 6 |
| along with | 2 |
| both | 1 |
| earliest | 1 |
| currently | 1 |
| less than | 1 |
| for which | 1 |

### 退化题中的高频短语模式

| 模式 / 关键词 | 次数 |
| --- | --- |
| greater than | 6 |
| highest | 5 |
| at least | 4 |
| currently | 4 |
| who have | 2 |
| earliest | 1 |
| who has | 1 |

### 改善题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| how | 19 |
| many | 19 |
| greater | 14 |
| customer | 14 |
| average | 13 |
| number | 13 |
| customers | 13 |
| students | 12 |
| total | 11 |
| highest | 11 |

### 退化题中的高频关键词

| 模式 / 关键词 | 次数 |
| --- | --- |
| total | 10 |
| average | 9 |
| customers | 8 |
| number | 7 |
| january | 7 |
| greater | 6 |
| type | 6 |
| apartment | 6 |
| students | 5 |
| employees | 5 |

### 代表性改善样例

- Q123: What aircraft model is used for the flight from Los Angeles to Sydney? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q966: What is the name and credit score of the customer from Utah who has a loan amount greater than 2500? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q969: Which customer from Utah has taken an Auto loan? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q993: Which customer from Utah has taken an Auto loan? | 命中表数 0 -> 2 | Recall 0.0000 -> 1.0000 | MRR 0.0000 -> 1.0000
- Q36: How many students registered before November 8, 2008, have attended their courses during or after the year 2012? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q110: What is the average price in dollars of products whose parent entries are sub-categories priced above 700 dollars? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q128: Which aircrafts with a certified pilot having employee ID 142519864 have a flying distance greater than 5000? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q133: Which students with an allergy to nuts live in the city PIT? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q140: What are the first and last names of students who have a nut allergy and live in the city with the code 'PIT'? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000
- Q141: How many students from city 'HKG' have an allergy to shellfish? | 命中表数 0 -> 1 | Recall 0.0000 -> 0.5000 | MRR 0.0000 -> 1.0000

### 代表性退化样例

- Q14: What is the mobile number of the person whose candidate details indicate 'Alex'? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q16: Which students attended the course with ID 301 after January 1, 2010? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q22: How many unique students attended either the statistics or database courses? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q124: Which employee or employees hold the highest number of certificates? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q135: List the unique first and last names of students who are allergic to nuts and are younger than 20. | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q336: What player is a forward and comes from the country whose capital is Dublin? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q337: Which country's official native language has the highest number of midfielders playing across all seasons? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q483: Which customers have had 'Uniformed' policies ending between January 1st, 2018 and February 1st, 2018? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q488: List all customers who held a 'Uniformed' type policy starting anytime between January 1st, 2017, and December 31st, ... | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
- Q491: Which customers had policies of type 'Uniformed' that ended after January 1, 2018? | 命中表数 1 -> 0 | Recall 0.5000 -> 0.0000 | MRR 1.0000 -> 0.0000
