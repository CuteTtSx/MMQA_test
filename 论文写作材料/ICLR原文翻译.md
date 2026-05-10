**MMQA****：使用多表多跳复杂问题评估大语言模型**

**吴建****1****∗** **杨林怡****2****∗** **李东元****4****∗** **季雨良****5** **奥库村满博****1** **张越****3†**

1东京科学研究所2伦敦大学学院3西湖大学工程学院4东京大学5南京科技大学

 

摘要

虽然大语言模型（LLMs）在理解表格数据方面取得了进展，但当前的表格评估基准测试，如WikiTableQuestions和WikiSQL，主要关注单表场景，这并不能完全反映实际应用的复杂性。为了弥补这一差距，我们提出了一个多表和多跳问答（MMQA）数据集，用于评估大语言模型在处理多表任务时的理解和推理能力。MMQA数据集要求模型通过从不同表格中提取证据进行多次推理，这些表格被设计为相互连接，并需要模型识别和使用外键和主键等关系。然后，我们引入了一个全面的评估框架，用于评估大语言模型在多表检索、文本到SQL生成、多表问答、主键选择和外键选择等多个方面的能力。最后，我们提出了一种新的多表检索方法，在MMQA数据集上相比几个强大的基线实现了最先进（SOTA）的性能。我们的实验结果表明，与人类表现相比，开源和商业大语言模型在多表理解和推理任务方面仍有显著的性能提升空间。我们相信，MMQA基准测试将增强和促进大语言模型在实际场景中的多表能力。完整的MMQA数据集可在https://anonymous.4open.science/r/MMQA‑34B1获取。

 

1 引言

*表*是实际场景中一种基本的结构化数据类型，其广泛应用包括关系数据库和电子表格形式（Raffel等人，2019）。近期研究表明，大语言模型在表格相关任务上表现出强大的能力（Zhu等人，2021； Zhao等人，2023；Hegselmann等人，2022；李等人，2023；张等人，2024b；Lu等人，2024）。然而，大语言模型的多表理解和推理性能仍有待深入探索。之前的表格相关研究，如表问答（Chen等人，2020b；Zhu等人，2021；Pasupat和李，2015；Zhong等人，2017；Yu等人，2018a； Cheng等人，2021；Katsis等人，2021；Nan等人，2022；Jauhar等人，2016；李等人，2021； Chen等人，2020a）、表格事实验证（Chen等人，2019；Günther等人，2021）、表格到文本生成（Moosavi等人，2021；Suadaa等人，2021；Lebret等人，2016）以及列类型与关系分类（Iida等人，2021；Deng等人，2020）都专注于单表任务。然而，在实际场景中，连接、并集、交集和外键识别等操作在多表推理中频繁使用，但针对这些任务的全面评估基准却非常少（Pal等人，2023；张等人，2024a）。

为填补这一空白，我们构建了一个多表和多跳问答评估数据集（MMQA），旨在评估大语言模型在多表数据上的理解和推理能力。为了全面了解大语言模型在多表任务上的表现，我们提出了一个涵盖不同方面的评估框架（多表检索、文本到SQL生成、多表问答、外键选择和主键选择），综合考虑表格的粗粒度和细粒度信息，包括表格、列和单元格级别。

![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image002.gif)

![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image004.gif)

图1：我们MMQA基准测试的一个示例。MMQA中的典型挑战包括：1）确定推理顺序；2）识别主键和外键；3）从不同表中检索证据进行多跳推理。表格中深蓝色的文字是用于推理答案的证据。

 

图1展示了我们MMQA的一个示例，一个涉及三个表格的问题。问题是*“**一位出生于阿拉巴马州的秘书所管理的部门的独特创建年份是什么？**”*，三个输入表格分别是*“**负责人**”**、**“**管理”*和*“**部门**”*。蓝色字体是跨表推理的关键词。大语言模型需要首先理解问题以及输入表格，以确定推理顺序。从特定的表格和列开始推理，然后定位用于跳转到另一个表格的关键列。例如，在**负责人**表格中，列包括*负责人**ID**、姓名*和*出生州*，其中*负责人**ID*既是该表的外键也是主键，这有助于大语言模型跳转到**管理**表。在**负责人**表格中，我们可以根据州*“**阿拉巴马州**”*确定*负责人**ID*是*“1”*。然后，从*负责人**ID*到**管理**表中的*部门**ID*，大语言模型可以确定数字*“7”*的部门。最后，根据**部门**表中的部门*“7”*，我们可以找到候选答案*“1903”*。因此，在这个示例中，大语言模型需要在列级别和单元格级别进行表内和表间推理，这比单表推理复杂得多。多表问答和单表问答之间的区别，类似于多跳问答（Yang等人，2018年）和单跳问答（Rajpurkar等人， 2016年）之间的区别。

我们对LLMs在我们MMQA数据集上的多表和多跳理解及推理能力进行了广泛的实验。结果表明，人类表现优于当前的SOTA LLMs，揭示了现有模型在执行多表任务时遇到的挑战。基于此，我们提出了一种新的多表检索方法，命名为**MTR**，该方法结合了问题分解模块，将多跳问题分解为一系列子问题，并将多表检索任务转换为多轮单表检索任务。在每一轮中，MTR联合考虑了问题‑表相关性和表‑表相关性进行单表检索。据我们所知，我们的研究是首个引入多表和多跳问答基准的，用于评估LLM的多表复杂推理能力。在MMQA数据集上，MTR在一系列先前的强基线模型中取得了最佳结果。

 

2 相关工作

**单表问答。**表格问答（TQA）涉及从给定表格的一个或多个表格单元中检索答案，例如WikiTableQuestions（Pasupat&Liang，2015）、WikiSQL（Zhong等人，2017）、SPIDER （Yu等人，2018a）、TABFACT（Chen等人，2019）。然而，这些数据集主要关注对表格进行推理，而忽略了存储在文本语料库中的重要知识。因此，涵盖表格和文本知识的问答正获得越来越多的关注。Chen等人（2020b）开创了一个passage‑table QA基准测试，HybridQA，该测试将维基百科表格链接到相关的自由文本段落（例如，维基百科实体定义页面）。OTT‑QA（Chen等人，2020a）基准测试将HybridQA扩展到开放域设置，其中系统需要首先检索相关的表格和段落，然后再尝试回答问题。此外，表格和段落之间的链接并未明确提供。FinQA（Chen等人，2021）和AIT‑QA（Katsis等人，2021）主要针对金融和航空表格，这表明需要复杂的推理挑战，要求模型不仅要解释，还要计算并精确提取细微信息。TableBench （Wu等人，2024b）是一个全面且复杂的表格基准测试，包括四个主要类别中的18个字段，用于评估大语言模型在表格问答方面的能力。尽管大语言模型在表格问答方面取得了显著进展（李等人，2022;Singha等人，2023;李等人，2023），但仍然迫切需要能够反映实际场景中多表格推理复杂性的基准测试。我们的工作与这一领域的工作不同，将其现实世界的复杂性纳入评估场景中。

**用于表格推理的大语言模型。**尽管大语言模型在文本推理方面表现出色，但它们在表格任务上的推理能力仍然有限。Zhu等人（2021）提出了一种TAT‑LLM，用于对表格和文本数据的混合进行推理，并在FinQA（Chen等人，2021）、TAT‑QA（Zhu等人，2021）和TAT‑DQA Zhu等人（2022）基准测试上进行评估。Chen等人（2022）和Chen（2022）专注于利用大语言模型在零样本设置下对单表数据进行推理。TableLLM（张等人，2024b）和TableLlama（张等人，2023）是两个与表格相关的大语言模型，它们在单表数据集上进行预训练和评估。TAT‑LLM（Zhu等人，2024）通过提出一个包括提取器、推理器和执行器的逐步流程，来处理问答任务（QA），以协助大语言模型在表格和文本数据的混合上进行更好的离散推理。Ye等人（2023）利用大语言模型的多步推理能力，首先通过为表格数据生成中间SQL查询来将复杂问题分解为子问题。TAP4LLM（Sui等人，2023）是一个通用的预处理工具箱，用于生成表格提示，以增强大语言模型在表格数据上的复杂推理能力。然而，所有基于大语言模型的表格推理方法都专注于单表推理。多结构理解和推理问题仍然有待探索。

**多表格任务。**Pal等人（2023）开创了一种多表格预训练任务，该任务旨在从输入的多表格中生成子表格来回答跨多个表格的问题。刘等人（2023）进一步提出了一种文档级摘要数据集，该数据集联合考虑了文档中的文本信息以及多表格内容。然而，这两种方法都集中在子表格级别，属于粗粒度。相比之下，考虑多跳和多表格任务。Chen等人（2024）提出了一种多表格检索方法，该方法考虑了列和子问题之间的相关性，而无需对整个表格标题进行对齐。我们的工作与先前工作的主要区别在于两个方面：1）全面的、多表格理解和推理评估；以及2）在不同粒度上的评估，即表格、列和单元格级别。

 

3 MMQA

如图2所示，评估框架包含两个主要步骤：1）多表格检索；以及2）多表格评估。评估任务分为四类：多表格检索、文本到SQL生成、表格问答和关键选择（主键和外键）。

![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image006.gif)

图2：我们的多表格评估框架，首先需要让大语言模型从给定的表语料库中检索表格。然后，我们在MMQA上评估大语言模型的推理和理解能力。多表格评估涉及文本到SQL生成、多表格问答、主键选择和外键选择。

 

3.1 MMQA构建

本节详细介绍了数据集构建过程，包括数据标注和质量验证，以及与先前表格QA基准相比的推理步骤。

**数据收集与标注** 我们在Spider数据库（Yu等人，2018a）上开发了MMQA基准，Spider是一个跨领域的复杂语义解析数据集，用于文本到SQL生成。Spider包含5，693个SQL查询和超过200个多表数据库，涵盖138个不同的领域。我们从Spider中随机选择了总共5，000个样本，每个样本包含两个或三个表。

**问答标注** 然后，我们遵循Pal等人（2023）的范式，通过Spider数据库上的45个手动设计的模板和操作类型的自定义规则，合成多表SQL查询。获取SQL查询后，我们将表和SQL查询提示给GPT‑4‑turbo等大语言模型，以生成自然语言问题。最后，我们邀请了两位具有计算机科学背景的人类专家，对每个表的外键和主键进行标注。一个表的主键是用于唯一标识表中每条记录的列或约束。外键是用于在两个表的数据之间建立并强制执行链接的列或列组合，以控制可以存储在外键表中的数据。对于问答标注，需要两位人类专家根据表和生成的问题给出答案。

![文本框: 表1： MMQA和人机一致性的统计摘要  属性	2表	3表 总表数	2591	721 每表平均行数	1833.31	1369.01 每表平均列数	6.04	4.78 每表平均外键 	2.81	1.95 每张表的主键数量	3.35	2.41 人机一致性	86%	82% 问题长度	77.11	85.38  问题类别 数值	889	289 List	214	44 计数	200	42 选择 	1289	346   ](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image007.gif)**质量验证** 在获得标注结果后，若存在差异，会邀请第三方专家对两位专家的标注进行复核，作为提升一致性的参考，最终结果通过多数投票确定。为确保标注数据的质量，我们舍弃了无法从给定表格中提取正确答案或存在语法问题的题目。一致性是根据三位专家的复核结果计算出的平均分。我们将专家的结果作为人类表现，与大语言模型进行比较。我们在表1中列出了我们基准测试的属性。

**问题类别** 基于实际场景和用户对多表数据的需求，我们设计了四个主要问题类别：*数值*（数值运算、求和、平均值等）、*列表*（列表操作，展示所有满足条件的答案）、*计数*（统计满足条件的答案数量）和*选择*（选择一个满足条件的特定答案）。我们在表3中展示了不同类别问题的几个示例。

**推理步骤** 我们通过计算解决多跳问题所需的推理步骤数量来比较不同数据集的数据复杂度。图3表明，MMQA的平均推理步骤显著高于现有数据集。

最后，在获得MMQA后，构建了一个包含3312张表的综合复杂基准测试，其中包含相应的自然语言问题、SQL查询、标准答案、外键和主键标注。

 

3.2 多表检索（MTR）

与单表检索任务不同，多表检索任务可以定义如下。具体来说，给定一个问题*Q*和一个表语料库![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image009.gif)，检索一个表![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image011.gif)，该表包含*Q*的答案。单表检索任务是从*C*中选择与问题最相关的表。然而，在多表检索任务中，我们的问题是检索一系列与问题相关的表，这些表可以通过外键的连接进行联合推理。这里，我们将检索到的表表示为![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image013.gif)，其中 ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image015.gif) 和 ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image017.gif) 必须能够与另一个 ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image019.gif) 进行连接。例如，在图1中，表Head可以与表Management进行

 

表2：我们MMQA与先前问答基准QAbenchmarks之间的差异。我们在此处将自然语言缩写为“NL”。我们的基准测试可以更全面地评估大语言模型在多表理解和推理方面的能力。

| Benchmarks                     | Question  format         | Data  size                            | Data  source                  | Task                                                         | Multi-table |
| ------------------------------ | ------------------------ | ------------------------------------- | ----------------------------- | ------------------------------------------------------------ | ----------- |
| WTQ  (Pasupat & Liang, 2015)   | NL  question             | 20,000  table-question pairs          | Wikipedia                     | Single-table  QA                                             |             |
| WikiSQL  (Zhong et al., 2017)  | SQL  query               | 24241  tables                         | Wikipedia                     | Single-table  QA                                             |             |
| HybridQA  (Chen et al., 2020b) | NL  question             | 70k  table-question pairs             | Wikipedia                     | Table-text  QA                                               |             |
| SQA  (Iyyer et al., 2017)      | NL  question             | 6,066  unique questions               | Wikipedia                     | Single-table  QA                                             |             |
| FeTaQA  (Nan et al., 2022)     | NL  question             | 10,330  tables                        | Wikipedia                     | Single-table                                                 |             |
| Spider  (Yu et al., 2018b)     | NL  question & SQL query | 8000  questions and SQL query pairs   | Crowdsourcing                 | Text-to-SQL                                                  |             |
| BIRD  (Li et al., 2024)        | NL  question & SQL query | 12,751  questions and SQL query pairs | Kaggle                        | Text-to-SQL                                                  |             |
| SPINACH  (Liu et al., 2024)    | NL  question & SQL query | 320  questions and SQL query pairs    | Crowdsourcing                 | Text-to-SQL                                                  |             |
| Tablebench  (Wu et al., 2024b) | NL                       | 3681  tables                          | WTQ/SQA/FeTaQA  /FinQA/AIT-QA | Single-table                                                 |             |
| **MMQA**(Ours)                 | NL  question & SQL query | 3,312  tables                         | Wikipedia                     | Multi-table  retrieval, Text-to-SQL, Multi-table QAPrimary Key & Foreign Key Selection |             |

 

表3：MMQA问题类型和表格的示例。我们强调与相关表格列的关键词。

| Table  Type | Question  Type                                               | Multi-hop  Question                                          |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 2 table     | Numerical                                                    | What  are the *ids of all stations*  that have a *latitude*  above 37.4 and have never had less than 7 *bikes* available? |
| List        | List  the  *customers’ first and last name* of 10 least expensive *invoices.* |                                                              |
| Count       | How  many *departments*  are led by *heads* who  are not mentioned? |                                                              |
| Select      | What  are the *ids of the courses* that  are *registered* or  *attended* by the *student* whose id is 121? |                                                              |
| 3  table    | Numerical                                                    | What is the *salary* and *name* of  the *employee* who has the most number of *certificates* on *aircraft* with *distance* of more than  5000? |
| List        | Find the *cell mobile  number* of the *candidates* whose *assessment  code* is Fail? |                                                              |
| Count       | For each *course id*, how many *students* are  registered and what are the *course names* ? |                                                              |
| Select      | What are the distinct *creation years*  of the *departments* managed by a  secretary born in *state ’Alabama’?* |                                                              |

 

连接，因为它们具有相同的列Head ID。因此，为了在表语料库中识别最相关的表，我们需要考虑两个方面：检索与问题相关的表，以及检索与表相关的表。受先前多跳问题分解工作（Wu等人，2024a）的启发，该工作生成式地分解多跳问题以增强与问题相关的证据检索性能。

我们提出了一种新颖的多表检索方法（MTR），该方法迭代检索与问题相关和与表格相关的表格。给定一个多跳问题*Q*，我们首先使用GPT‑4‑turbo作为问题分解器，通过一组提示（附录B）直接将多跳问题输入分解器，采用单样本设置，得到一系列子问题![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image021.gif)。然后，我们在现成的单表QA数据集上微调TableLlama‑7b（张等人，2023）以及SGPT‑5.8B（Muennighoff，2022），作为单表检索模型，数据集包括Chen等人（2019；2021）；Katsis等人（2021）；Zhu等人（2021）。

 

| **Algorithm  1** Multi-Table Retrieval                       |                                                       |
| ------------------------------------------------------------ | ----------------------------------------------------- |
| **Initialize:** **Input:**  Multi-hop Question ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image023.gif), **LLM:**  GPT-4-turbo. |                                                       |
| **Output:**  Retrieved Tables                                |                                                       |
| **First  Round:** ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image025.gif) | ▹only  compute question-relevance scores in 1st round |
| **for** ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image027.gif) **do** |                                                       |
| **for** ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image029.gif) **do** |                                                       |
| **for** ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image031.gif) **do** | ▹Compute  Relevance Scores                            |
| ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image033.gif) |                                                       |
| **end for**                                                  |                                                       |
| **end  for**                                                 |                                                       |
| **end  for**                                                 |                                                       |
| **for** ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image035.gif) **do** |                                                       |
| ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image037.gif) | ▹Select  top K relevant tables                        |
| **end  for**                                                 |                                                       |
| **Return**  tables                                           |                                                       |

 

我们将多表检索任务分解为多轮单表检索任务。对于分解后的子问题，我们迭代 *n* 轮，从表语料库中检索与子问题相关的TopK（K==2, 5,10）表格。在第一轮中，我们仅考虑问题‑表格相关性分数，并为每个检索到的表格分配表格相关性分数。然后我们根据分数排序，获取TopK表格。从第二轮到最后一轮，先前检索到的表格被视为种子。我们根据问题相关性分数和表格相关性分数对TopK表格进行排序。问题相关性分数通过单表检索模型计算，表格相关性分数基于表格列的交集计算。如果检索到的表格与上一轮检索到的表格存在列交集，则分配分数1和0。当分配0时，停止迭代。每一轮的分数是问题相关性分数与表格相关性分数的乘积。所有子问题都用于检索表格后，我们求和所有分数：

![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image039.gif)

其中 ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image041.gif) 是单表检索模型计算出的表格相关性分数，表示第 *i*个子问题与第 *j*个检索到的表格在第 ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image043.gif)轮推理中的相关性；*k*‑th检索到的表格在第 *i -* 1 轮与第 *j*个检索到的表格在第 *i*轮推理中的表格相关性分数。具体实现细节请参见附录C。

 

3.3 子任务

![文本框: 图3：推理步骤中与现有数据集的数据复杂度对比](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image044.gif)![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image046.gif)多表评估是指从给定表格中多次推理以回答复杂问题的任务。我们为多表检索、多表问答、文本到SQL生成和键选择任务采用一个多维度指标集。

 

**多表检索。**我们在MMQA数据集上评估了大语言模型在多表格检索任务上的表现，该数据集的问题需要跨多个表格进行推理才能回答。目标是回答以下问题：LLMs的检索多表能力在多大程度上能同时考虑问题‑表相关性和表‑表相关性？我们构建了一个包含MMQA所有表的表池，并将输入的多跳问题输入LLMs，以从池中检索所有与问题相关的表。这项任务至关重要，因为在现实场景中，推理和回答性能的后继步骤基于检索到的表的质量。

 

**文本到****SQL****生成。**在遵循文本生成评估任务后，我们利用Rouge‑1、Rouge‑L（Lin，2004）和BLEU （Papineni等人，2002）来评估大语言模型生成的SQL查询质量与真实值。与单表问答推理任务不同，多表SQL查询要复杂得多，包含更多操作。

 

表4：多表检索（MTR）的主要实验结果，我们的MTR表现优于所有先前强基线模型。

|                                    | Top-2   | Top-5   | Top-10  |         |         |         |      |      |      |      |      |      |      |      |       |      |      |      |
| ---------------------------------- | ------- | ------- | ------- | ------- | ------- | ------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----- | ---- | ---- | ---- |
|                                    | 2-table | 3-table | 2-table | 3-table | 2-table | 3-table |      |      |      |      |      |      |      |      |       |      |      |      |
|                                    | P       | R       | F1      | P       | R       | F1      | P    | R    | F1   | P    | R    | F1   | P    | R    | F1    | P    | R    | F1   |
| *Baselines*                        |         |         |         |         |         |         |      |      |      |      |      |      |      |      |       |      |      |      |
| BM25                               | 6.2     | 4.3     | 5.1     | 4.4     | 5.2     | 4.8     | 9.8  | 8.7  | 9.2  | 6.3  | 7.5  | 6.8  | 10.9 | 9.2  | 9.9   | 8.6  | 8.2  | 8.4  |
| Tfidf                              | 4.6     | 5.1     | 4.8     | 4.5     | 5.1     | 4.8     | 10.6 | 9.3  | 9.9  | 8.5  | 9.2  | 8.8  | 11.4 | 10.8 | 11.1  | 9.3  | 8.9  | 9.1  |
| DTR(  (Herzig  et al., 2021  )     | 31.4    | 35.4    | 33.3    | 29.9    | 30.9    | 30.4    | 34.0 | 35.8 | 34.9 | 33.2 | 32.9 | 33.0 | 39.3 | 37.2 | 38.2  | 38.5 | 35.4 | 36.9 |
| SGPT‑125M  (Muennighoff, 2022)     | 39.5    | 41.7    | 30.6    | 37.4    | 39.1    | 38.2    | 40.4 | 42.2 | 41.3 | 38.6 | 39.4 | 39.0 | 41.7 | 42.5 | 42.1  | 40.2 | 40.6 | 40.4 |
| SGPT‑5.8B  (Muennighoff, 2022)     | 45.7    | 48.1    | 46.9    | 44.2    | 45.3    | 44.7    | 45.1 | 44.9 | 46.9 | 43.9 | 45.3 | 44.6 | 47.7 | 48.8 | 48．2 | 46.2 | 47.3 | 46.7 |
| TableLlama‑7b(Zhang  et al., 2023) | 56.7    | 58.2    | 57.4    | 53.6    | 52.8    | 53.2    | 59.2 | 63.1 | 60.1 | 57.7 | 58.1 | 57.9 | 60.8 | 64.2 | 62.5  | 59.6 | 59.3 | 59.4 |
| *Our methods —MTR*                 |         |         |         |         |         |         |      |      |      |      |      |      |      |      |       |      |      |      |
| MTR  (SGPT-5.8B)                   | 58.1    | 53.9    | 55.9    | 51.4    | 49.3    | 50.3    | 62.3 | 59.5 | 60.9 | 60.2 | 64.7 | 62.4 | 61.7 | 65.6 | 63.6  | 61.8 | 63.5 | 62.6 |
| MTR  (TableLlama-7b)               | 72.3    | 64.7    | 68.3    | 69.5    | 66.2    | 67.8    | 74.3 | 71.8 | 73.0 | 72.9 | 70.6 | 71.7 | 74.5 | 73.3 | 74.9  | 73.6 | 71.9 | 72.7 |
| w/o  QD                            | 65.3    | 62.3    | 63.8    | 64.7    | 63.6    | 64.1    | 70.2 | 68.3 | 74.6 | 68.6 | 67.5 | 68.0 | 70.8 | 68.5 | 69.6  | 69.5 | 67.7 | 68.6 |

 

**多表问答。**多表问答评估的主要目标是衡量大语言模型在理解复杂查询、导航各种表格以及生成正确且连贯答案方面的能力。这项评估对于确定大语言模型在现实世界应用中的有效性至关重要，因为它们通常需要同时与多个数据源交互并提取信息。

**主键和外键选择。**与表示数据库中记录的行不同，列表示列头为值提供语义含义的属性。此外主键和外键是多表数据的重要列特征。因此正确的键选择表现了LLM跨多个表的列级理解能力。主键和外键选择是所有目标中正确选择的列的百分比评估集中的列。

 

4 实验

我们基于MMQA基准设计了一系列实验，旨在回答三个问题：1）与人类表现相比，大语言模型在多表问答任务上的表现如何？2）大语言模型在主键选择和外键选择等多表相关任务上的表现如何？3）MMQA的平均行数超过1,000行。大语言模型在长表上的表现如何？

4.1 实验设置

**数据集。**具体来说，我们将我们的MMQA基准分为两部分：2表（2,591个样本，平均1,833.31行和6.04列）和3表（721个样本，平均1,369.01行和4.78列）子集。

**模型。**我们在实验中使用了专有和开源大语言模型，为了提高可复现性，我们将专有模型的温度设置为0.7，所有实验结果都是三次实验结果的平均分数。对于专有模型，我们采用GPT‑4 （Achiam等人，2023年）、GPT‑3.5（Ouyang等人，2022年）、Gemini‑pro（团队等人， 2023年）和O1‑preview。对于开源大语言模型，我们在TableLlama‑7b（张等人，2023年）和Mistral‑7b（姜等人，2023年）上进行评估。不同评估任务的提示在附录B中显示。

**评估指标。**对于表检索任务，我们使用精确率、召回率和F1分数来衡量多表检索的性能。对于多表推理，我们结合多种指标对大语言模型进行评估，包括用于多表问答的精确匹配（EM）和部分匹配（PM），用于文本到SQL任务的Rouge‑1、Rouge‑L（Lin，2004）、BLEU（Papineni et al.，2002），以及用于主键选择（PKS）和外键选择（FKS）的准确率。部分匹配表示大语言模型生成的答案与标准答案之间的部分语义匹配分数。我们使用GPT‑4‑turbo作为答案评估器来给出分数，提示语见附录。

表5：不同基线在2表数据集上的主要结果。我们将基准测试分为一个3表子集和一个2表子集。我们使用 *∗* 表示零样本设置，†表示单样本设置。在此，我们将主键选择缩写为“ PKS”，外键选择缩写为“FKS”。PM表示使用GPT‑4‑turbo和附录B中的提示对LL Ms生成结果进行部分语义匹配评估。

| Dataset                  | 2  table  |             |           |           |          |           |           |
| ------------------------ | --------- | ----------- | --------- | --------- | -------- | --------- | --------- |
| Evaluation Methods       | Table  QA | Text-to-SQL | PKS       | FKS       |          |           |           |
| Metrics                  | EM        | PM          | Rouge1    | RougeL    | BLEU     | Acc       | Acc       |
| ***Open  Source LLMs\*** |           |             |           |           |          |           |           |
| TableLlama 7b∗           | 7.58±0.3  | 8.06±0.1    | 9.12±0.2  | 7.89±0.2  | 1.82±0.1 | 17.86±0.2 | 13.75±0.2 |
| TableLlama 7b†           | 8.23±0.1  | 8.57±0.1    | 10.34±0.3 | 9.53±0.2  | 2.92±0.2 | 20.25±0.2 | 15.89±0.2 |
| Mistral-7b ∗             | 5.36±0.1  | 5.89±0.1    | 7.25±0.2  | 6.36±0.1  | 1.79±0.1 | 14.15±0.1 | 13.98±0.2 |
| Mistral-7b †             | 6.26±0.2  | 6.72±0.1    | 9.55±0.1  | 8.45±0.1  | 2.49±0.1 | 17.65±0.2 | 16.17±0.2 |
| LlaMA-2-13b ∗            | 9.45±0.2  | 10.13±0.1   | 17.34±0.2 | 15.81±0.3 | 5.44±0.1 | 25.34±0.1 | 22.78±0.1 |
| LlaMA-2-13b †            | 11.28±0.2 | 13.04±0.2   | 20.45±0.1 | 18.17±0.1 | 7.59±0.2 | 28.89±0.2 | 25.27±0.1 |
| ***Proprietary  LLMs\*** |           |             |           |           |          |           |           |
| GPT-3.5∗                 | 25.56±0.2 | 29.34±0.1   | 31.75±0.1 | 27.89±0.2 | 2.71±0.3 | 28.06±0.1 | 19.25±0.1 |
| GPT-3.5†                 | 26.79±0.1 | 29.78±0.1   | 33.96±0.2 | 29.74±0.1 | 4.82±0.2 | 38.75±0.1 | 28.83±0.1 |
| GPT-4∗                   | 25.17±0.2 | 31.35±0.2   | 32.51±0.2 | 28.39±0.3 | 2.53±0.1 | 31.59±0.2 | 21.27±0.2 |
| GPT-4†                   | 28.88±0.1 | 34.57±0.1   | 39.64±0.2 | 35.07±0.2 | 5,77±0.2 | 42.78±0.2 | 26.88±0.1 |
| Gemini-pro∗              | 27.16±0.2 | 32.72±0.2   | 33.13±0.2 | 29.28±0.1 | 2.69±0.1 | 32.77±0.1 | 22.06±0.2 |
| Gemini-pro†              | 28.58±0.2 | 33.89±0.1   | 35.26±0.1 | 30.15±0.2 | 5.34±0.2 | 44.19±0.2 | 28.38±0.2 |
| O1-preview∗              | 46.25±0.2 | 49.72±0.2   | 38.41±0.2 | 37.75±0.3 | 6.79±0.3 | 42.81±0.1 | 30.53±0.1 |
| O1-preview⋆              | 50.78±0.2 | 43.85±0.2   | 43.62±0.2 | 39.52±0.3 | 7.58±0.2 | 49.53±0.2 | 34.17±0.2 |
| Human7.58+               | **89.8**  | **82.7**    | **96.5**  | **95.3**  |          |           |           |

 

B. 这些指标提供了模型性能的综合视图，从其生成准确SQL查询（文本到SQL）的能力到其理解和推理表格数据的能力

 

4.2 多表检索评估

表4展示了在不同K值（K=2,5,10）下，针对MMQA多表检索任务评估不同基线的实验结果。在不同的K值下，我们的MTR相比于之前的强检索方法（BM25、TF‑IDF、DTR和开源大语言模型）均取得了SOTA性能。值得注意的是，基于小模型构建的BM25、TF‑IDF和Table Dense检索在检索多个相互关联的表时表现较差。虽然SGPT‑5.8B和TableLlama‑7b可以处理长结构输入，但MTR在问题相关性得分和表相关性得分中全面考虑了内部和外部连接。多表检索实验结果表明，在评估的大语言模型之间存在明显的性能差异。具体而言，我们的MTR优于开源大语言模型、SGPT和TableLlama，并展现出更高的精确率，达到了72.3%的得分，这表明在识别给定问题最相关的表方面具有很高的准确率。这种性能归因于MTR先进的问题理解和辨别多表关系复杂性的能力。相比之下，与TableLlama‑7b结合的MTR虽然以64.7%的得分展现出可称赞的召回率，但在精确率方面有所落后，表明其倾向于检索更广泛的表集，其中偶尔包含不太相关的表。F1得分（协调精确率和召回率）在MTR中最高，达到68.3%，反映了在识别相关表和最小化假阳性的平衡性能。这些结果强调了理解表关系在多表检索任务中的重要性，这是MTR优于开源模型的一个领域。我们还消融了问题分解（QD）模块，我们发现QD在MTR中起着至关重要的作用。QD在多表检索任务上为MTR提供了显著的改进，例如，在Top‑2检索中，精确率从65.3提高到72.3，召回率从62.3提高到64.7（在2表子集上）

 

表6：大语言模型在3表子集上的主要结果

| Dataset                  | 3  table  |             |           |           |          |           |           |
| ------------------------ | --------- | ----------- | --------- | --------- | -------- | --------- | --------- |
| Evaluation Methods       | Table QA  | Text-to-SQL | PKS       | FKS       |          |           |           |
| Metrics                  | EM        | PM          | Rouge1    | RougeL    | BLEU     | Acc       | Acc       |
| ***Open  Source LLMs\*** |           |             |           |           |          |           |           |
| TableLlama 7b∗           | 7.42±0.1  | 8.12±0.1    | 8.96±0.2  | 7.58±0.3  | 1.77±0.1 | 16.17±0.2 | 11.75±0.2 |
| TableLlama 7b†           | 7.82±0.1  | 8.38±0.1    | 9.36±0.1  | 7.92±0.3  | 2.15±0.1 | 18.05±0.1 | 13.57±0.2 |
| Mistral-7b ∗             | 5.27±0.1  | 5.91±0.1    | 3.72±0.1  | 2.46±0.2  | 1.68±0.1 | 16.86±0.1 | 12.58±0.2 |
| Mistral-7b †             | 5.88±0.2  | 6.26±0.1    | 4.33±0.2  | 3.08±0.2  | 2.58±0.1 | 18.24±0.1 | 15.06±0.2 |
| LlaMA-2-13b ∗            | 8.62±0.1  | 9.24±0.2    | 14.22±0.2 | 12.75±0.1 | 4.79±0.1 | 21.27±0.1 | 20.09±0.1 |
| LlaMA-2-13b †            | 9.65±0.1  | 11.74±0.1   | 18.66±0.2 | 15.73±0.2 | 6.29±0.2 | 24.37±0.2 | 22.58±0.1 |
| ***Proprietary  LLMs\*** |           |             |           |           |          |           |           |
| GPT-3.5∗                 | 20.66±0.2 | 24.29±0.1   | 31.48±0.3 | 27.39±0.3 | 2.67±0.1 | 27.36±0.2 | 18.18±0.3 |
| GPT-3.5†                 | 24.64±0.2 | 28.55±0.2   | 39.25±0.2 | 33.26±0.3 | 5.26±0.1 | 40.16±0.1 | 25.01±0.2 |
| GPT-4∗                   | 27.16±0.2 | 31.48±0.2   | 33.13±0.2 | 29.28±0.1 | 2.69±0.1 | 32.77±0.1 | 22.06±0.2 |
| GPT-4†                   | 28.58±0.2 | 33.21±0.1   | 35.26±0.1 | 30.15±0.2 | 5.34±0.2 | 44.19±0.2 | 28.38±0.2 |
| Gemini-pro∗              | 24.25±0.1 | 28.59±0.1   | 29.78±0.2 | 27.17±0.2 | 3.02±0.1 | 30.31±0.1 | 21.92±0.2 |
| Gemini-pro†              | 26.38±0.1 | 30.88±0.1   | 33.44±0.1 | 29.25±0.2 | 4.88±0.2 | 38.85±0.2 | 31.52±0.2 |
| O1-preview∗              | 42.37±0.1 | 45.97±0.2   | 36.29±0.2 | 35.73±0.3 | 5.28±0.1 | 41.89±0.2 | 32.32±0.2 |
| O1-preview⋆              | 48.28±0.2 | 52.95±0.2   | 42.41±0.2 | 36.29±0.1 | 7.08±0.1 | 46.84±0.1 | 40.78±0.1 |
| Human7.58+               | **92.3**  | **86.9**    | **98.7**  | **97.5**  |          |           |           |

 

4.3 多表格推理评估

各种大语言模型的主要结果展示在表5和表6中。以表5为例，O1‑preview在我们的MMQA基准测试中优于众多多表任务，在复杂的推理场景中表现出卓越的性能。特别是在表QA任务（50.78 EM得分）、主键选择（49.53准确率）和外键选择（34.17准确率）中，O1‑preview保持了一个显著的性能水平，显著超越了GPT‑4（表QA中的28.88 EM得分、主键选择中的42.78准确率和外键选择中的26.88）。尽管取得了这些进步，专有和开源大语言模型在多表理解和推理任务上仍然显著落后于人类表现（89.8、82.7、96.5和95.3）。然而，某些先进的大语言模型，尤其是与表格相关的大语言模型，在这些场景中展现出潜力。

 

**文本到****SQL****。**在文本到SQL生成任务中，评估大语言模型将自然语言问题翻译成准确SQL查询的能力。O1‑preview在单样本设置下表现最佳，表5中Rouge1、Rouge‑L和BLEU得分分别为43.62、39.52和7.58。这一高分可归因于O1‑preview复杂的语言解析和结构化输出生成能力，这对于理解问题的语义差异并将其映射到相应的SQL语法至关重要。GPT‑4虽然取得了不错的BLEU得分，但Rouge‑L和Rouge‑1得分较低，表明尽管它能捕捉SQL查询的整体结构，但在查询语法的细节上存在不足。文本到SQL的结果显示，虽然大语言模型在这一领域取得了进展，但仍存在相当大的改进空间，尤其是在生成不仅语法正确而且与原始问题语义一致的查询方面。

 

**多表问答。**多表问答任务评估模型检索证据、跨多张表导航并最终提取正确答案的能力。O1‑preview_在单样本设置下展现了令人印象深刻的精确匹配得分，在表5和表6中分别为50.78和48.28，展示了其理解复杂、跨表关系的专业能力以检索准确答案。这一表现可能归因于模型E能够有效利用外键和主键在表之间导航并识别相关数据点。相反，尽管GPT‑4在其他任务中表现稳健，但在表5和表6中的精确匹配得分分别仅为28.88和28.58，表明其在整合多表信息以形成连贯答案方面遇到了困难。

 

**主键选择和外键选择。**主键和外键选择的准确率对于建立正确的表关系至关重要，这一点在本任务中得到了验证。O1‑preview在主键选择上达到了46.84%的准确率，在外键选择上达到了40.78%，在6个测试中表现突出，这表明其具备强大的表模式理解能力，并能准确识别关键列以促进跨表数据关联。这些高分反映了O1‑preview先进的功能工程能力和对数据库结构的深刻把握。另一方面，虽然GPT‑4在其他任务中表现尚可，但在主键选择和外键选择上分别只达到了42.78%和26.88%的准确率。这种性能差异可能源于GPT‑4在识别表关系背景下某些列重要性的能力上不够精细。本任务的结果强调了精确的关键列识别对于有效的多表数据处理的重要性，而这一点对许多大语言模型来说仍然是一个挑战，需要进一步的研究和改进。

 

**表长的影响。**我们随机选择具有500、600、700、800、900和1,000个平均表长的数据，每种数据类型采样50个样本，以评估LLM在不同长度表下的性能。图4和图5展示了多表问答和文本到SQL生成任务在不同表长度下的性能评估结果。图4揭示多表问答任务存在一个拐点。当表长不超过800行时，随着表长的增加，LLM的性能逐渐下降。但当表长超过800行时，出现拐点，LLM的性能迅速下降到极低水平。而，在文本到SQL生成任务中，无论表长如何变化，LLM的性能都保持缓慢下降的速率。这可能是因为在文本到SQL任务中， LLM只关注表头而不是表内容本身。

![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image050.gif)

图 4：不同输入表长度在多表问答任务上的评估。我们将 MMQA 分为 6 个子集：表长度为500、600、700、800、900和1000。所有大语言模型均在零样本设置下进行评估。

![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image052.gif)

图5：不同输入表长度的评估结果，针对文本到SQL生成任务。我们将MMQA分为四个子集：表长度在500（400‑600）、700（600‑800）、900（800‑1000）和1100（1000‑1200）附近的表格。所有大语言模型均在零样本设置下进行评估。

 

5 结论

我们介绍了一个新的MMQA基准，用于评估大语言模型在处理多表格任务方面的能力。广泛的实验表明，当前的大语言模型在处理复杂、相互关联的数据时，既展现了潜力也存在局限性。尽管现有的强有力的大语言模型（如GPT‑4和O1‑preview）在复杂任务上表现出色，但大语言模型仍然缺乏全面理解和推理表格的能力，尤其是在多表格任务中，并且在表格问答任务和外键选择任务中，其表现显著落后于人类表现。随着该领域的进步，MMQA数据集及其相关挑战无疑将作为创新的关键催化剂，推动开发出能够更有效地跨多个表格进行推理、应对现实世界数据复杂性的大语言模型。



|      |                                                              |      |                                                              |
| ---- | ------------------------------------------------------------ | ---- | ------------------------------------------------------------ |
|      | ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image053.gif) |      | ![img](file:///C:/Users/Lenovo/AppData/Local/Temp/msohtmlclip1/01/clip_image053.gif) |

 



参考文献

Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al. Gpt-4 technical report. *arXiv preprint arXiv:2303.08774*, 2023.

Simran Arora, Avanika Narayan, Mayee F Chen, Laurel J Orr, Neel Guha, Kush Bhatia, Ines Chami, Frederic Sala, and Christopher Ré. Ask me anything: A simple strategy for prompting language models. *arXiv preprint arXiv:2210.02441*, 2022.

Peter Baile Chen, Yi Zhang, and Dan Roth. Is table retrieval a solved problem? exploring join-aware multi-table retrieval. In *Annual Meeting of the Association for Computational Linguistics*, 2024. URL https://api.semanticscholar.org/CorpusID:269148607.

Wenhu Chen. Large language models are few(1)-shot table reasoners. *ArXiv*, abs/2210.06710, 2022. URL https://api.semanticscholar.org/CorpusID:252872943.

Wenhu Chen, Hongmin Wang, Jianshu Chen, Yunkai Zhang, Hong Wang, SHIYANG LI, Xiyou Zhou, and William Yang Wang. Tabfact: A large-scale dataset for table-based fact verification. *ArXiv*, abs/1909.02164, 2019. URL https://api.semanticscholar.org/CorpusID:198917339.

Wenhu Chen, Ming-Wei Chang, Eva Schlinger, William Yang Wang, and William W. Cohen. Open question answering over tables and text. *ArXiv*, abs/2010.10439, 2020a. URL https://api. semanticscholar.org/CorpusID:224803601.

Wenhu Chen, Hanwen Zha, Zhiyu Chen, Wenhan Xiong, Hong Wang, and William Wang. Hybridqa: A dataset of multi-hop question answering over tabular and textual data. *Findings of EMNLP 2020*, 2020b.

Zhiyu Chen, Wenhu Chen, Charese Smiley, Sameena Shah, Iana Borova, Dylan Langdon, Reema N Moussa, Matthew I. Beane, Ting-Hao ’Kenneth’ Huang, Bryan R. Routledge, and William Yang Wang. Finqa: A dataset of numerical reasoning over financial data. *ArXiv*, abs/2109.00122, 2021. URL https://api.semanticscholar.org/CorpusID:235399966.

Z Cheng, Tianbao Xie, Peng Shi, Chengzu Li, Rahul Nadkarni, Yushi Hu, Caiming Xiong, Dragomir R. Radev, Marilyn Ostendorf, Luke Zettlemoyer, Noah A. Smith, and Tao Yu. Binding language models in symbolic languages. *ArXiv*, abs/2210.02875, 2022. URL https: //api.semanticscholar.org/CorpusID:252734772.

Zhoujun Cheng, Haoyu Dong, Zhiruo Wang, Ran Jia, Jiaqi Guo, Yan Gao, Shi Han, Jian-Guang Lou, and Dongmei Zhang. Hitab: A hierarchical table dataset for question answering and natural language generation. *arXiv preprint arXiv:2108.06712*, 2021.

Xiang Deng, Huan Sun, Alyssa Lees, You Wu, and Cong Yu. Turl. *ACM SIGMOD Record*, 51:33 – 40, 2020. URL https://api.semanticscholar.org/CorpusID:220128303.

Shizhe Diao, Pengcheng Wang, Yong Lin, and Tong Zhang. Active prompting with chain-of-thought for large language models. *arXiv preprint arXiv:2302.12246*, 2023.

Michael Günther, Maik Thiele, Julius Gonsior, and Wolfgang Lehner. Pre-trained web table embeddings for table discovery. In *Proceedings of the Fourth International Workshop on Exploiting Artificial Intelligence Techniques for Data Management*, aiDM ’21, pp. 24–31, New York, NY, USA, 2021. Association for Computing Machinery. ISBN 9781450385350. doi: 10.1145/3464509.3464892. URL https://doi.org/10.1145/3464509.3464892.

Stefan Hegselmann, Alejandro Buendia, Hunter Lang, Monica Agrawal, Xiaoyi Jiang, and David A. Sontag. Tabllm: Few-shot classification of tabular data with large language models. *ArXiv*, abs/2210.10723, 2022. URL https://api.semanticscholar.org/CorpusID:252992811.

Jonathan Herzig, Thomas Müller, Syrine Krichene, and Julian Eisenschlos. Open domain question answering over tables via dense retrieval. In Kristina Toutanova, Anna Rumshisky, Luke Zettlemoyer, Dilek Hakkani-Tur, Iz Beltagy, Steven Bethard, Ryan Cotterell, Tanmoy Chakraborty, and Yichao Zhou (eds.), *Proceedings of the 2021 Conference of the North American Chapter of the*

11

*Association for Computational Linguistics: Human Language Technologies*, pp. 512–519, Online, June 2021. Association for Computational Linguistics. doi: 10.18653/v1/2021.naacl-main.43. URL https://aclanthology.org/2021.naacl-main.43.

Hiroshi Iida, Dung Ngoc Thai, Varun Manjunatha, and Mohit Iyyer. Tabbie: Pretrained representations of tabular data. In *North American Chapter of the Association for Computational Linguistics*, 2021. URL https://api.semanticscholar.org/CorpusID:233864627.

Mohit Iyyer, Wen-tau Yih, and Ming-Wei Chang. Search-based neural structured learning for sequential question answering. In Regina Barzilay and Min-Yen Kan (eds.), *Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pp. 1821–1831, Vancouver, Canada, July 2017. Association for Computational Linguistics. doi: 10.18653/v1/P17-1167. URL https://aclanthology.org/P17-1167.

Sujay Kumar Jauhar, Peter D. Turney, and Eduard H. Hovy. Tabmcq: A dataset of general knowledge tables and multiple-choice questions. *ArXiv*, abs/1602.03960, 2016. URL https://api.semanticscholar.org/CorpusID:17380649.

Albert Qiaochu Jiang, Alexandre Sablayrolles, Arthur Mensch, Chris Bamford, Devendra Singh Chaplot, Diego de Las Casas, Florian Bressand, Gianna Lengyel, Guillaume Lample, Lucile Saulnier, L’elio Renard Lavaud, Marie-Anne Lachaux, Pierre Stock, Teven Le Scao, Thibaut Lavril, Thomas Wang, Timothée Lacroix, and William El Sayed. Mistral 7b. *ArXiv*, abs/2310.06825, 2023. URL https://api.semanticscholar.org/CorpusID:263830494.

Yannis Katsis, Saneem A. Chemmengath, Vishwajeet Kumar, Samarth Bharadwaj, Mustafa Canim, Michael R. Glass, A. Gliozzo, Feifei Pan, Jaydeep Sen, Karthik Sankaranarayanan, and Soumen Chakrabarti. Ait-qa: Question answering dataset over complex tables in the airline industry. *ArXiv*, abs/2106.12944, 2021. URL https://api.semanticscholar.org/CorpusID:235623770.

Rémi Lebret, David Grangier, and Michael Auli. Neural text generation from structured data with application to the biography domain. In Jian Su, Kevin Duh, and Xavier Carreras (eds.), *Proceedings of the 2016 Conference on Empirical Methods in Natural Language Processing*, pp. 1203–1213, Austin, Texas, November 2016. Association for Computational Linguistics. doi: 10.18653/v1/D16-1128. URL https://aclanthology.org/D16-1128.

Jinyang Li, Binyuan Hui, Ge Qu, Jiaxi Yang, Binhua Li, Bowen Li, Bailin Wang, Bowen Qin, Ruiying Geng, Nan Huo, et al. Can llm already serve as a database interface? a big bench for large-scale database grounded text-to-sqls. *Advances in Neural Information Processing Systems*, 36, 2024.

Peng Li, Yeye He, Dror Yashar, Weiwei Cui, Song Ge, Haidong Zhang, Danielle Rifinski Fainman, Dongmei Zhang, and Surajit Chaudhuri. Table-gpt: Table-tuned gpt for diverse table tasks. *ArXiv*, abs/2310.09263, 2023. URL https://api.semanticscholar.org/CorpusID:264127877.

Xiao Li, Yawei Sun, and Gong Cheng. Tsqa: Tabular scenario based question answering. *ArXiv*, abs/2101.11429, 2021. URL https://api.semanticscholar.org/CorpusID:231719096.

Yinghui Li, Qingyu Zhou, Yangning Li, Zhongli Li, Ruiyang Liu, Rongyi Sun, Zizhen Wang, Chao Li, Yunbo Cao, and Hai-Tao Zheng. The past mistake is the future wisdom: Error-driven contrastive probability optimization for Chinese spell checking. In Smaranda Muresan, Preslav Nakov, and Aline Villavicencio (eds.), *Findings of the Association for Computational Linguistics: ACL 2022*, pp. 3202–3213, Dublin, Ireland, May 2022. Association for Computational Linguistics. doi: 10. 18653/v1/2022.findings-acl.252. URL https://aclanthology.org/2022.findings-acl.252.

Chin-Yew Lin. ROUGE: A package for automatic evaluation of summaries. In *Text Summarization Branches Out*, pp. 74–81, Barcelona, Spain, July 2004. Association for Computational Linguistics. URL https://aclanthology.org/W04-1013.

Shicheng Liu, Sina J. Semnani, Harold Triedman, Jialiang Xu, Isaac Dan Zhao, and Monica S. Lam. Spinach: Sparql-based information navigation for challenging real-world questions. *ArXiv*, abs/2407.11417, 2024. URL https://api.semanticscholar.org/CorpusID:271218638.

Shuaiqi Liu, Jiannong Cao, Ruosong Yang, and Zhiyuan Wen. Long text and multi-table summarization: Dataset and method. *ArXiv*, abs/2302.03815, 2023. URL https://api.semanticscholar. org/CorpusID:256631057.

12

Weizheng Lu, Jiaming Zhang, Jing Zhang, and Yueguo Chen. Large language model for table processing: A survey. *ArXiv*, abs/2402.05121, 2024. URL https://api.semanticscholar. org/CorpusID:267548080.

Nafise Sadat Moosavi, Andreas Ruckl’e, Dan Roth, and Iryna Gurevych. Learning to reason for text generation from scientific tables. *ArXiv*, abs/2104.08296, 2021. URL https://api. semanticscholar.org/CorpusID:233296604.

Niklas Muennighoff. Sgpt: Gpt sentence embeddings for semantic search. *arXiv preprint arXiv:2202.08904*, 2022.

Linyong Nan, Chiachun Hsieh, Ziming Mao, Xi Victoria Lin, Neha Verma, Rui Zhang, Wojciech Krys´cin´ski, Hailey Schoelkopf, Riley Kong, Xiangru Tang, Mutethia Mutuma, Ben Rosand, Isabel Trindade, Renusree Bandaru, Jacob Cunningham, Caiming Xiong, Dragomir Radev, and Dragomir Radev. FeTaQA: Free-form table question answering. *Transactions of the Association for Computational Linguistics*, 10:35–49, 2022. doi: 10.1162/tacl_a_00446. URL https:// aclanthology.org/2022.tacl-1.3.

Long Ouyang, Jeff Wu, Xu Jiang, Diogo Almeida, Carroll L. Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, John Schulman, Jacob Hilton, Fraser Kelton, Luke E. Miller, Maddie Simens, Amanda Askell, Peter Welinder, Paul Francis Christiano, Jan Leike, and Ryan J. Lowe. Training language models to follow instructions with human feedback. *ArXiv*, abs/2203.02155, 2022. URL https://api.semanticscholar.org/CorpusID:246426909.

Vaishali Pal, Andrew Yates, Evangelos Kanoulas, and Maarten de Rijke. MultiTabQA: Generating tabular answers for multi-table question answering. In Anna Rogers, Jordan Boyd-Graber, and Naoaki Okazaki (eds.), *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pp. 6322–6334, Toronto, Canada, July 2023. Association for Computational Linguistics. doi: 10.18653/v1/2023.acl-long.348. URL https://aclanthology.org/2023.acl-long.348.

Kishore Papineni, Salim Roukos, Todd Ward, and Wei-Jing Zhu. Bleu: a method for automatic evaluation of machine translation. In Pierre Isabelle, Eugene Charniak, and Dekang Lin (eds.), *Proceedings of the 40th Annual Meeting of the Association for Computational Linguistics*, pp. 311–318, Philadelphia, Pennsylvania, USA, July 2002. Association for Computational Linguistics. doi: 10.3115/1073083.1073135. URL https://aclanthology.org/P02-1040.

Panupong Pasupat and Percy Liang. Compositional semantic parsing on semi-structured tables. In *Annual Meeting of the Association for Computational Linguistics*, 2015. URL https://api. semanticscholar.org/CorpusID:9027681.

Colin Raffel, Noam M. Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and Peter J. Liu. Exploring the limits of transfer learning with a unified text-to-text transformer. *J. Mach. Learn. Res.*, 21:140:1–140:67, 2019. URL https://api. semanticscholar.org/CorpusID:204838007.

Pranav Rajpurkar, Jian Zhang, Konstantin Lopyrev, and Percy Liang. SQuAD: 100,000+ questions for machine comprehension of text. In Jian Su, Kevin Duh, and Xavier Carreras (eds.), *Proceedings of the 2016 Conference on Empirical Methods in Natural Language Processing*, pp. 2383–2392, Austin, Texas, November 2016. Association for Computational Linguistics. doi: 10.18653/v1/ D16-1264. URL https://aclanthology.org/D16-1264.

Ananya Singha, José Pablo Cambronero, Sumit Gulwani, Vu Le, and Chris Parnin. Tabular representation, noisy operators, and impacts on table structure understanding tasks in llms. *ArXiv*, abs/2310.10358, 2023. URL https://api.semanticscholar.org/CorpusID:264146587.

Lya Hulliyyatus Suadaa, Hidetaka Kamigaito, Kotaro Funakoshi, Manabu Okumura, and Hiroya Takamura. Towards table-to-text generation with numerical reasoning. In Chengqing Zong, Fei Xia, Wenjie Li, and Roberto Navigli (eds.), *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)*, pp. 1451–1465, Online, August 2021. Association for Computational Linguistics. doi: 10.18653/v1/2021.acl-long.115. URL https: //aclanthology.org/2021.acl-long.115.

13

发表于ICLR2025会议论文集

Yuan Sui, Jiaru Zou, Mengyu Zhou, Xinyi He, Lun Du, Shi Han, and Dongmei Zhang. Tap4llm: Table provider on sampling, augmenting, and packing semi-structured data for large language model reasoning. *ArXiv*, abs/2312.09039, 2023. URL https://api.semanticscholar.org/CorpusID: 266210509.

Gemini Team, Rohan Anil, Sebastian Borgeaud, Yonghui Wu, Jean-Baptiste Alayrac, Jiahui Yu, Radu Soricut, Johan Schalkwyk, Andrew M Dai, Anja Hauth, et al. Gemini: a family of highly capable multimodal models. *arXiv preprint arXiv:2312.11805*, 2023.

Jian Wu, Linyi Yang, Yuliang Ji, Wenhao Huang, Börje F. Karlsson, and Manabu Okumura. Gendec: A robust generative question-decomposition method for multi-hop reasoning. *ArXiv*, abs/2402.11166, 2024a. URL https://api.semanticscholar.org/CorpusID:267750855.

Xianjie Wu, Jian Yang, Linzheng Chai, Ge Zhang, Jiaheng Liu, Xinrun Du, Di Liang, Daixin Shu, Xianfu Cheng, Tianzhen Sun, et al. Tablebench: A comprehensive and complex benchmark for table question answering. *arXiv preprint arXiv:2408.09174*, 2024b.

Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William W. Cohen, Ruslan Salakhutdinov, and Christopher D. Manning. HotpotQA: A dataset for diverse, explainable multi-hop question answering. In *Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 2018.

Yunhu Ye, Binyuan Hui, Min Yang, Binhua Li, Fei Huang, and Yongbin Li. Large language models are versatile decomposers: Decomposing evidence and questions for table-based reasoning.

*Proceedings of the 46th International ACM SIGIR Conference on Research and Development in Information Retrieval*, 2023. URL https://api.semanticscholar.org/CorpusID:256416408.

Tao Yu, Rui Zhang, Kai Yang, Michihiro Yasunaga, Dongxu Wang, Zifan Li, James Ma, Irene Li, Qingning Yao, Shanelle Roman, Zilin Zhang, and Dragomir Radev. Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task. In Ellen Riloff, David Chiang, Julia Hockenmaier, and Jun’ichi Tsujii (eds.), *Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing*, pp. 3911–3921, Brussels, Belgium, October-November 2018a. Association for Computational Linguistics. doi: 10.18653/v1/D18-1425. URL https://aclanthology.org/D18-1425.

Tao Yu, Rui Zhang, Kai-Chou Yang, Michihiro Yasunaga, Dongxu Wang, Zifan Li, James Ma, Irene Z Li, Qingning Yao, Shanelle Roman, Zilin Zhang, and Dragomir R. Radev. Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-sql task. *ArXiv*, abs/1809.08887, 2018b. URL https://api.semanticscholar.org/CorpusID:52815560.

Tianshu Zhang, Xiang Yue, Yifei Li, and Huan Sun. Tablellama: Towards open large generalist models for tables. *ArXiv*, abs/2311.09206, 2023. URL https://api.semanticscholar.org/CorpusID: 265213406.

Weijia Zhang, Vaishali Pal, Jia-Hong Huang, E. Kanoulas, and Maarten de Rijke. Qfmts: Generating query-focused summaries over multi-table inputs. *ArXiv*, abs/2405.05109, 2024a. URL https: //api.semanticscholar.org/CorpusID:269626608.

Xiaokang Zhang, Jing Zhang, Zeyao Ma, Yang Li, Bohan Zhang, Guanlin Li, Zijun Yao, Kangli Xu, Jinchang Zhou, Daniel Zhang-Li, et al. Tablellm: Enabling tabular data manipulation by llms in real office usage scenarios. *arXiv preprint arXiv:2403.19318*, 2024b.

Bowen Zhao, Changkai Ji, Yuejie Zhang, Wen He, Yingwen Wang, Qing Wang, Rui Feng, and Xiaobo Zhang. Large language models are complex table parsers. In *Conference on Empirical Methods in Natural Language Processing*, 2023. URL https://api.semanticscholar.org/CorpusID: 266163842.

Ruiqi Zhong, Tao Yu, and Dan Klein. Semantic evaluation for text-to-SQL with distilled test suites. In Bonnie Webber, Trevor Cohn, Yulan He, and Yang Liu (eds.), *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pp. 396–411, Online, November 2020. Association for Computational Linguistics. doi: 10.18653/v1/2020.emnlp-main.29. URL https://aclanthology.org/2020.emnlp-main.29.

14

Victor Zhong, Caiming Xiong, and Richard Socher. Seq2sql: Generating structured queries from natural language using reinforcement learning. *CoRR*, abs/1709.00103, 2017.

Fengbin Zhu, Wenqiang Lei, Youcheng Huang, Chao Wang, Shuo Zhang, Jiancheng Lv, Fuli Feng, and Tat-Seng Chua. TAT-QA: A question answering benchmark on a hybrid of tabular and textual content in finance. In Chengqing Zong, Fei Xia, Wenjie Li, and Roberto Navigli (eds.), *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)*, pp. 3277–3287, Online, August 2021. Association for Computational Linguistics. doi: 10.18653/v1/2021.acl-long.254. URL https://aclanthology.org/2021.acl-long.254.

Fengbin Zhu, Wenqiang Lei, Fuli Feng, Chao Wang, Haozhou Zhang, and Tat seng Chua. Towards complex document understanding by discrete reasoning. *Proceedings of the 30th ACM International Conference on Multimedia*, 2022. URL https://api.semanticscholar.org/CorpusID: 251041071.

Fengbin Zhu, Ziyang Liu, Fuli Feng, Chao Wang, Moxin Li, and Tat seng Chua. Tat-llm: A specialized language model for discrete reasoning over tabular and textual data. *ArXiv*, abs/2401.13223, 2024. URL https://api.semanticscholar.org/CorpusID:267200238.

 

A 可复现性声明

为了使结果和模型可复现和验证，我们提供了完整的数据标注指南、数据链接、实现细节和提示：我们在第3.1节详细说明了数据标注过程，实现代码在附录C中。所有用于复现结果的提示都已在附录B中说明。

 

B 提示

在评估大语言模型时，设计提示是一个脆弱的过程，提示词的微小修改可能导致模型预测产生巨大变化，因此需要投入大量精力为给定任务精心设计完美的提示词（Arora等人，2022年； Diao等人，2023年）。在本研究中，我们调查了零样本在我们的基准测试上的性能。为了消除随机性，我们为每个任务手动选择一个示例，确保所有任务都得到覆盖。

我们将设计的输入示例分别用于三个不同的任务，以帮助读者理解我们的实现，如表7所示。

表7：与表格相关的任务的提示模板。我们这里以2表数据为例.[WORDS]表示我们应该提供的信息

| ***Prompts of Question Decomposition\***                     |
| ------------------------------------------------------------ |
| ***Prompt\*** You are an expert at  multi-hop question decomposition, you need to decompose the given multi-hop  question [Question] based on the given example. Please only output the  results without any other words in the JSON format of:  {"Sub-questions": List}."  ***[Question]\*** The given multi-hop question.  ***[Example]\*** The given  example of question and sub-questions. |
| ***Prompts of Text-to-SQL\***                                |
| ***Prompt\*** You  are an expert at text-to-SQL, you need to generate a SQL query based on the  given multihop question [Question] and given two tables [TABLE1], [TABLE2].  Please only output the results without any other words in the JSON format of:  {"SQL": String}. "  ***[Question]\*** The given  multi-hop question.   ***[TABLE1]\*** The given table 1.  ***[TABLE2]\*** The given table 2. |
| ***Prompts of Multi-table QA\***                             |
| ***Prompt\*** "You are an expert at  multi-table question answering, you need to extract answers based on the  given multi-hop question [Question] and given two tables [TABLE1], and  [TABLE2]. Please only output the results without any other words in the  format of: {"Answers": List}. ***[Question]\***  The given multi-hop question.  ***[TABLE1]\*** The given table 1.  ***[TABLE2]\*** The given  table 2. |
| ***Prompts of Foreign Key Selection\***                      |
| ***Prompt\*** "You  are an expert at foreign key selection, you need to select foreign keys based  on the given two tables [TABLE1], and [TABLE2]. Please only output the  results without any other words in the JSON format of:  {"foreign keys": List}.   ***[TABLE1]\*** The given table 1.   ***[TABLE2]\*** The given table 2. |
| ***Prompts of Primary Key Selection\***                      |
| ***Prompt\*** "You are an expert at  primary key selection, you need to select primary keys based on the given two  tables [TABLE1], and [TABLE2]. Please only output the results without any  other words in the JSON format of:  {"primary keys": List}.  ***[TABLE1]\*** The given  table 1.   ***[TABLE2]\*** The given  table 2. |
| ***Prompts of Partial Match Evalutaion\***                   |
| ***Prompt\*** You  are an Answer evaluator, you need to measure the semantic similarity between  [Generated Answer] and [Gold Answer], and give the score, 1 means equal, 0  means not. Some answers may have abbreviations or alias, for example, Lionel  Messi is equal to Messi, Donald Trump is equal to Trump. Please only output  the score 1 or 0 without any other words. |
| ***[Generated Answer]\*** The LLM generated answer.  ***[Gold Answer]\*** The  ground truth. |

 

C 实现细节

对于专有模型，我们使用官方API与专属大语言模型交互，提示词定义良好。对于开源模型，所有实验均在8块A100 GPU上进行。对于微调单表检索模型，我们在单表问答数据集上对TableLlama‑7B和SGPT‑5.8B进行监督微调。我们将初始学习率设置为2e‑5，并进行了三个epoch的训练。优化使用Adam优化器，批大小为4，最大输入序列长度为4,096。

 

D GPT‑4与人工检查的部分匹配相关性

我们还检查了GPT‑4部分匹配分数和人工检查分数之间的人得分。我们从MMQA中随机选择了100个数据（50个来自2表子集，50个来自3表子集），并手动检查了部分匹配分数。对于由O1‑preview生成的答案，GPT‑4给出了53个部分匹配分数，这表明有53个答案可以与真实情况对齐。人工检查给出了59个部分分数，这表明有59个答案可以与真实情况对齐。我们收集了两个包含100个元素的列表，元素是“0”或“1”。一个列表是GPT‑4部分匹配分数列表，另一个是人工检查部分匹配分数列表。我们计算了这两个列表之间的皮尔逊相关性。结果如表8所示，我们发现人工检查部分匹配分数与GPT‑4部分匹配分数高度相关。例如，给定问题“找出有食物类型过敏的男性（性别为‘M’）学生的数量。”答案是“10”，而生成答案是“ten”。GPT‑4 PM可以将“ten”视为正确答案。然而，人工部分匹配比GPT‑4 PM更好。例如，问题是“所有员工ID以及他们工作的国家的名称是什么？”其中一个答案是“CA”，而LLM生成的答案是“Canada”。GPT‑4 PM分配的分数是0。

 

表8：GPT‑4部分匹配分数与人工检查部分分数之间的皮尔逊相关性

| Model      | EM   | GPT-4 PM | Human Check PM | Pearson Correlation |
| ---------- | ---- | -------- | -------------- | ------------------- |
| O1-preview | 45.7 | 53       | 59             | 0.8852              |
| GPT-4      | 31.6 | 41       | 45             | 0.8273              |
| GPT-3.5    | 26.7 | 38       | 41             | 0.7784              |

 

E 原始问题与释义问题之间的差异

我们随机选择了100个问题（50个来自2表子集，50个来自3表子集），这些问题经过人工释义，并将问题及其对应的表格发送给大语言模型，使用EM分数评估了表格问答任务。结果如表9所示。释义后，表格列相关信息减少，大语言模型的性能也随之下降。例如，原始问题是：“显示由临时代理值为'是'的负责人管理的部门的员工姓名和数量？”；释义后的问题是：“现在担任部门负责人的员工的姓名和数量是什么？”；其中“临时”和“管理”等列相关信息被删除了。

 

表9：原始SQL查询生成的问题与释义问题的性能对比

| **Models**     | **2-Table**  | **3-Table**     |              |                 |
| -------------- | ------------ | --------------- | ------------ | --------------- |
| **Settings**   | **Original** | **Paraphrased** | **Original** | **Paraphrased** |
| **O1-preview** | **43.5**     | **40.7**        | **39.8**     | **34.4**        |
| **GPT-4**      | **29.6**     | **25.8**        | **26.2**     | **23.6**        |
| **GPT-3.5**    | **26.3**     | **23.1**        | **24.5**     | **21.9**        |

 

F 文本到SQL的F测试套件准确度评估

我们使用ESM（Zhong等人，2020）来评估大语言模型在2表和3表子集上的文本到SQL性能。表10表明，尽管大语言模型在ESM得分上获得了相对较高的通过率，但仍有大量假阳性SQL查询。

表10：ESM指标的假阳性/假阴性率。

| Models     | 2-Table   | 3-Table   |
| ---------- | --------- | --------- |
| GPT-4      | 11.5/24.7 | 13.6/27.8 |
| GPT-3.5    | 15.4/28.1 | 17.9/31.2 |
| O1-preview | 8.7/19.4  | 11.3/22.6 |

 

G 限制

在本文中，我们专注于评估大语言模型在我们的标注反事实MMQA数据集上的多表理解推理能力。尽管大语言模型在人类之间表现出明显的性能差距，但评估方法仍在改进中，例如，精确匹配不足以回复真实结果。其次，尽管大语言模型可以生成质量相对较好的SQL查询，但生成的SQL查询是否可以执行以获得正确答案仍然未知。