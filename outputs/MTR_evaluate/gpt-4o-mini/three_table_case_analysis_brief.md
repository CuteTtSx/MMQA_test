### 4.4.3 典型错题案例分析

本节以E2实验在 three-table 场景下的检索结果为例，对几类有代表性的案例进行简要分析。相比前文的平均指标和逐题统计，这类案例更适合直观观察系统在真实问题上的检索表现，包括哪些问题能够完整召回目标表、哪些问题只能部分召回，以及哪些问题会出现完全召回失败的情况。

#### 1. Top-3 下的完全召回情况

从 Top-3 的结果来看，系统在一部分问题上已经可以完整召回 3 张目标表，说明当前检索模块在语义线索较明确、表间关系较直接的问题上已经具备较好的效果。

例如，Q22 问题 *“How many students under 20 years old have allergies categorized as 'animal'?”* 对应的真实目标表为 `Has_Allergy`、`Student` 和 `Allergy_Type`，系统返回的 Top-3 恰好为这三张表。又如 Q54 问题 *“How many different phone companies manufactured devices using a chip model that supports WiFi '802.11b' and utilizing a screen mode classified as 'Graphics'?”*，真实目标表为 `chip_model`、`screen_mode` 和 `phone`，系统同样在 Top-3 中全部命中。

表 1 给出了两个完全命中案例。


| 题号  | 问题概述                                     | 真实目标表                                  | Top-3 检索结果                                |
| --- | ---------------------------------------- | -------------------------------------- | ----------------------------------------- |
| Q22 | 统计 20 岁以下且过敏类型为 animal 的学生人数             | `Has_Allergy`、`Student`、`Allergy_Type` | `Has_Allergy`√、`Student`√、`Allergy_Type`√ |
| Q54 | 查询使用支持 802.11b 芯片且图形模式为 Graphics 的手机公司数量 | `chip_model`、`screen_mode`、`phone`     | `chip_model`√、`screen_mode`√、`phone`√     |


这些案例说明，当问题中的核心实体表、条件表和连接关系都比较明确时，当前方法已经能够在 Top-3 范围内形成较完整的召回结果。

#### 2. Top-3 下的部分召回情况

相比完全命中案例，更值得分析的是部分召回情况。此时系统通常能够找回一部分关键表，但仍会遗漏某一张真实目标表，并用语义上相近、结构上相关但并不正确的表替代。

第一类比较常见的情况是：桥接表和一张实体表被召回了，但另一张实体表被语义相近的表替代。例如 Q216 问题 *“Which institutions are affiliated with the author whose last name is Hinze?”* 的真实目标表为 `Inst`、`Authors` 和 `Authorship`。其中 `Authors` 与 `Authorship` 被成功召回，但第三张表却变成了 `Scientists`，而不是真实所需的 `Inst`。这说明系统已经识别出了“作者”以及“作者—机构关联”这两个关键线索，但在“机构表”的判别上，仍容易受到同主题域相近表的干扰。

与之相似的还有 Q661 问题 *“What is the average weight of pets owned by students who are from the city with the code 'HKG'?”*。该题的真实目标表为 `Student`、`Has_Pet` 和 `Pets`。Top-3 中系统成功召回了 `Pets`，同时也识别出了与学生相关的方向，但返回结果为 `Dogs`、`Pets` 和 `Students`。其中 `Students` 与真实目标表 `Student` 在命名和语义上都十分接近，而真正承担连接作用的 `Has_Pet` 没有进入前三。这类情况说明，系统有时能够同时感知到两个实体方向，但对中间关系表的重要性建模仍然不足，因此近名实体表更容易挤占桥接表的位置。

第二类情况是：桥接表被正确召回，但其余实体表没有进入前三。例如 Q232 问题 *“Who is the second author of the paper titled 'Functional Pearl: Modular Rollback through Control Logging'?”* 的真实目标表为 `Authors`、`Papers` 和 `Authorship`。其中 `Authorship` 被召回，说明系统已经一定程度上抓住了 authorship order 这一连接关系；但 Top-3 中另外两张表却是 `Fault_Log` 和 `Transactions`，直到 Top-5 时 `Authors` 才进入候选集合，到 Top-10 时 `Papers` 才出现。这说明在复杂论文标题、作者顺序等约束下，系统虽然能够较早定位桥接关系表，但实体表排序仍不够稳定。

第三类情况是：真实关系表与错误关系表在功能上比较接近，系统难以细致区分。例如 Q467 问题 *“How many unique products were ordered by customers paying with a credit card whose orders have a pending status?”* 的真实目标表为 `Customers`、`Customer_Orders` 和 `Order_Items`，而 Top-3 返回的是 `Orders`、`Customer_Orders` 和 `Customer_Orders`。可以看出，系统已经抓住了“订单”这一主题，也找到了其中一张正确关系表，但在 `Orders`、`Customer_Orders` 与 `Order_Items` 之间没有稳定区分开。对于同一业务链条中的多个中间关系表，当前方法仍然容易发生结构角色层面的混淆。

表 2 给出了四个部分召回案例。


| 题号   | 真实目标表                                       | Top-3 检索结果                                      | 现象分析                                                                         |
| ---- | ------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------- |
| Q216 | `Inst`、`Authors`、`Authorship`               | `Authors`√、`Scientists`×、`Authorship`√          | 作者表和桥接表被召回，但机构表 `Inst` 漏召回，取而代之的是语义相近的 `Scientists`                          |
| Q661 | `Student`、`Has_Pet`、`Pets`                  | `Dogs`×、`Pets`√、`Students`×                     | 系统已经识别出宠物和学生两个实体方向，但真正承担连接作用的 `Has_Pet` 未进入前三，且 `Student` 被近名表 `Students` 替代 |
| Q232 | `Authors`、`Papers`、`Authorship`             | `Fault_Log`×、`Authorship`√、`Transactions`×      | 桥接表 `Authorship` 被召回，但作者表和论文表未进入 Top-3，说明复杂约束下实体表排序不稳定                       |
| Q467 | `Customers`、`Customer_Orders`、`Order_Items` | `Orders`×、`Customer_Orders`√、`Customer_Orders`× | 系统已识别出订单关系主题，但在多个功能相近的关系表之间发生混淆                                              |


综合来看，Top-3 下的部分召回错误主要表现为三种模式：一是实体表与相似表混淆，二是桥接表虽然被找回，但其余实体表没有同时进入最终截断结果，三是多个关系表在业务语义上较为接近，导致系统难以准确判断哪一张才是真正承担连接作用的目标表。这说明当前方法对局部语义线索已有一定把握，但在多表路径的完整覆盖和结构角色判别上仍然不够稳定。

#### 3. Top-3 下的完全失败情况

除了部分召回外，three-table 场景中也存在 Top-3 完全失败的情况，即前三张候选表中没有任何一张真实目标表。这类问题通常更能反映当前检索框架的薄弱点。

例如 Q671 问题 *“List the last name and first name of students who live in city code 'HKG' and own dogs.”* 的真实目标表为 `Student`、`Has_Pet` 和 `Pets`。但系统的 Top-3 结果却是 `Students`、`Students` 和 `STUDENT`，三张都不属于真实答案集合。这里可以看出，系统强烈受到了“student”相关表名的语义吸引，重复召回了多个名字相近但结构并不匹配的表，而真正涉及“养宠关系”的 `Has_Pet` 和 `Pets` 没有进入前三。进一步结合该题的问题分解结果可以发现，分解后的子问题几乎都围绕 `students` 展开，如“哪些学生住在 HKG”“这些学生中哪些人养狗”“这些学生的姓和名是什么”等，这会使检索阶段持续强化对学生相关表的关注，而与宠物关系相关的表更容易被边缘化。因此，这个例子也说明，问题分解质量同样会影响后续检索效果：如果子问题过度集中在某一实体上，而没有充分突出另一实体或关系线索，就可能放大检索排序的偏置。

再如 Q603 问题 *“Which customer was the first to have a cancelled order containing product with product_id 2?”* 的真实目标表为 `Customers`、`Customer_Orders` 和 `Order_Items`。Top-3 返回的是 `Order_Items`、`Customer_Orders` 和 `Customer_Orders`，表面上看与问题语义十分接近，但实际上这几张返回表都不是数据集中定义的真实目标表标识，因此在严格匹配下记为 0 命中。这个案例说明，系统有时并不是完全没有抓住问题主题，而是会在同域近名表、重复表或非标准对应表之间发生偏移。

表 3 给出了两个完全失败案例。


| 题号   | 真实目标表                                       | Top-3 检索结果                                           | 现象分析                                  |
| ---- | ------------------------------------------- | ---------------------------------------------------- | ------------------------------------- |
| Q671 | `Student`、`Has_Pet`、`Pets`                  | `Students`×、`Students`×、`STUDENT`×                   | 被学生相关近名表强烈干扰，真实的宠物关系表完全未进入前三          |
| Q603 | `Customers`、`Customer_Orders`、`Order_Items` | `Order_Items`×、`Customer_Orders`×、`Customer_Orders`× | 返回结果与问题主题接近，但与真实答案表标识不一致，导致严格评估下 0 命中 |


这类案例说明，当前检索模块在复杂问题下不仅会漏召回桥接表，也可能在同域近义表、重复候选表和表名变体之间发生明显混淆。换言之，系统在主题级别已经捕捉到了“学生”“订单”“客户”等大致方向，但还不能稳定地区分真实目标表与跨库中大量形式近似、命名相近的干扰表。

#### 4. Top-5 与 Top-10 的补充观察

在前面的 three-table 实验中，最终指标统计采用的是 Top-3，即系统返回排名最高的 3 张候选表，并据此计算 Recall、MRR 等结果。这里继续观察 Top-5 和 Top-10，并不是因为最终评估改成了返回 5 张或 10 张表，而是希望借助更大的候选范围判断：某些真实目标表究竟是完全没有被检索到，还是实际上已经进入了候选集合，只是排序没有进入前三。换句话说，Top-5 和 Top-10 更适合用来辅助分析排序问题和候选覆盖情况。

Q232 就是一个比较典型的例子。该题在 Top-3 时只命中 `Authorship` 1 张表；到了 Top-5，`Authors` 被补召回，命中数上升为 2；到了 Top-10，`Papers` 也进入候选集合，最终 3 张真实目标表全部出现。说明该题的问题并不完全在于“找不到相关表”，而更在于“相关表排序不够靠前”。

Q671 也有类似现象。该题在 Top-3 时 0 命中，但到了 Top-5 时 `Student` 已经进入候选集合，只是 `Has_Pet` 和 `Pets` 仍未被有效提升到靠前位置。这说明扩大候选池能够在一定程度上缓解严格截断带来的损失，但并不能从根本上解决桥接表或关系表难以进入前列的问题。

表 4 给出了两个 Top-K 扩大后的例子。


| 题号   | Top-3  | Top-5  | Top-10 | 说明                              |
| ---- | ------ | ------ | ------ | ------------------------------- |
| Q232 | 命中 1 张 | 命中 2 张 | 命中 3 张 | 真实目标表逐步进入候选集合，说明主要问题在排序位置而非完全缺失 |
| Q671 | 命中 0 张 | 命中 1 张 | 命中 1 张 | 扩大候选池后部分真实表出现，但桥接关系表仍未有效召回      |


总体来看，Top-5 和 Top-10 的结果表明，当前方法在部分问题上已经能够把真实目标表放入较大的候选池中，但由于排序仍不够理想，这些表没有进入最终 Top-3 结果。因此，后续改进除了提高候选表覆盖率之外，还需要进一步优化候选表的排序质量，尤其是提升桥接表、关系表和低频实体表在前几名中的排序位置。