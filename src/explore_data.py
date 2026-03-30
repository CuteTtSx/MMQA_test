import json

def explore_mmqa_data(file_path):
    print(f"正在加载大文件: {file_path} ...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"加载成功！数据集中共有 {len(data)} 条多表查询样本。\n")
    print(data[0])

    # 提取第一条数据进行解剖
    first_item = data[0]
    print("================ 第一条数据的核心信息 ================")
    print(f"【ID】: {first_item.get('id_', '无ID')}")
    print(f"【大模型生成的问题 (Question)】:\n{first_item.get('Question')}\n")
    print(f"【人工写的标准答案 (SQL)】:\n{first_item.get('SQL')}\n")
    print(f"【解决这个问题需要关联的表 (table_names)】: {first_item.get('table_names')}\n")

    for i in range(len(first_item.get("tables"))):
        print(f"================ 第{i+1}张表的内部结构 ================")
        first_table = first_item['tables'][i]
        print(f"【表头 (table_columns)】: \n{first_table.get('table_columns')}\n")
        print(f"【第一行数据 (table_content)】: \n{first_table.get('table_content')[0]}\n")

    first_table = first_item['tables'][i]
    # 核心检查：寻找论文中提到的人工标注的主键和外键
    print("================ 关键字段检查 ================")
    print(f"是否有 primary_keys 字段？: {'primary_keys' in first_table}")
    print(f"是否有 foreign_keys 字段？: {'foreign_keys' in first_table}")

    print("================ 表的主键 ================")
    print(f"外键(foreign_keys)\n{first_item.get('foreign_keys')}\n")
    print(f"【主键(table_primary_key)】: \n{first_item.get('primary_keys')}\n")

    print("================ 答案 ================")
    print(f"答案(answer)\n{first_item.get('answer')}\n")

def get_table_nums(file_path):
    print(f"正在加载大文件: {file_path} ...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 【修复 1：格式防御装甲】适应大文件的字典嵌套格式
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                data = value
                break

    if not isinstance(data, list):
        print("❌ 数据格式异常，无法找到数据列表。")
        return

    print(f"✅ 加载成功！数据集中共有 {len(data)} 条多表查询样本")

    # ================= 全局表格数量统计逻辑 =================
    print("================ 全局表格统计 ================")
    unique_tables = set()  # 创建一个空集合用于去重

    for item in data:
        if not isinstance(item, dict):
            continue

        # 同时获取表名和表结构数据
        table_names = item.get('table_names', [])
        tables_data = item.get('tables', [])

        for i, t_name in enumerate(table_names):
            if i >= len(tables_data):
                continue

            # 【修复 2：引入表结构指纹】
            columns = tables_data[i].get('table_columns', [])
            columns_str = ",".join(columns)
            unique_table_id = f"{t_name}_[{columns_str}]"

            # 将带有列名特征的“指纹ID”加入集合
            unique_tables.add(unique_table_id)

    total_unique_tables = len(unique_tables)
    # 为了直观，我们只打印文件名部分
    short_name = file_path.split('/')[-1] if '/' in file_path else file_path
    print(f"🚀 统计完毕：在【{short_name}】中，一共包含 {total_unique_tables} 张真正独特的表！\n")

if __name__ == "__main__":
    file_names = ["../data/Synthesized_three_table.json", "../data/Synthesized_two_table.json"]
    for i in range(len(file_names)):
        filename = file_names[i]
        explore_mmqa_data(filename) # 打印样本的信息
        # get_table_nums(filename) # 打印总表的数量

# 只调用explore_mmqa_data的运行结果
"""
正在加载大文件: ./data/Synthesized_three_table.json ...
加载成功！数据集中共有 721 条多表查询样本。

{'id_': 0, 'Question': 'What are the names of heads serving as temporary acting heads in departments with rankings better than 5?', 'SQL': "SELECT head.head_Name FROM head INNER JOIN management ON head.head_ID = management.head_ID INNER JOIN department ON management.Department_ID = department.Department_ID WHERE department.Ranking < 5 AND management.temporary_acting = 'Yes';", 'table_names': ['department', 'head', 'management'], 'tables': [{'table_columns': ['Department_ID', 'Department_Name', 'Creation', 'Ranking', 'Budget_in_Billions', 'Num_Employees'], 'table_content': [[1, 'State', '1789', 1, 9.96, 30266.0], [2, 'Treasury', '1789', 2, 11.1, 115897.0], [3, 'Defense', '1947', 3, 439.3, 3000000.0], [4, 'Justice', '1870', 4, 23.4, 112557.0], [5, 'Interior', '1849', 5, 10.7, 71436.0], [6, 'Agriculture', '1889', 6, 77.6, 109832.0], [7, 'Commerce', '1903', 7, 6.2, 36000.0], [8, 'Labor', '1913', 8, 59.7, 17347.0], [9, 'Health and Human Services', '1953', 9, 543.2, 67000.0], [10, 'Housing and Urban Development', '1965', 10, 46.2, 10600.0], [11, 'Transportation', '1966', 11, 58.0, 58622.0], [12, 'Energy', '1977', 12, 21.5, 116100.0], [13, 'Education', '1979', 13, 62.8, 4487.0], [14, 'Veterans Affairs', '1989', 14, 73.2, 235000.0], [15, 'Homeland Security', '2002', 15, 44.6, 208000.0]]}, {'table_columns': ['head_ID', 'head_Name', 'born_state', 'age'], 'table_content': [[1, 'Tiger Woods', 'Alabama', 67.0], [2, 'Sergio GarcÃ\xada', 'California', 68.0], [3, 'K. J. Choi', 'Alabama', 69.0], [4, 'Dudley Hart', 'California', 52.0], [5, 'Jeff Maggert', 'Delaware', 53.0], [6, 'Billy Mayfair', 'California', 69.0], [7, 'Stewart Cink', 'Florida', 50.0], [8, 'Nick Faldo', 'California', 56.0], [9, 'PÃ¡draig Harrington', 'Connecticut', 43.0], [10, 'Franklin Langham', 'Connecticut', 67.0]]}, {'table_columns': ['Department_ID', 'head_ID', 'temporary_acting'], 'table_content': [[2, 5, 'Yes'], [15, 4, 'Yes'], [2, 6, 'Yes'], [7, 3, 'No'], [11, 10, 'No']]}], 'foreign_keys': ['head_ID', 'Department_ID'], 'primary_keys': ['Department_ID', 'head_ID', 'Department_ID'], 'answer': 'Jeff Maggert, Billy Mayfair'}
================ 第一条数据的核心信息 ================
【ID】: 0
【大模型生成的问题 (Question)】:
What are the names of heads serving as temporary acting heads in departments with rankings better than 5?

【人工写的标准答案 (SQL)】:
SELECT head.head_Name FROM head INNER JOIN management ON head.head_ID = management.head_ID INNER JOIN department ON management.Department_ID = department.Department_ID WHERE department.Ranking < 5 AND management.temporary_acting = 'Yes';

【解决这个问题需要关联的表 (table_names)】: ['department', 'head', 'management']

================ 第1张表的内部结构 ================
【表头 (table_columns)】: 
['Department_ID', 'Department_Name', 'Creation', 'Ranking', 'Budget_in_Billions', 'Num_Employees']

【第一行数据 (table_content)】: 
[1, 'State', '1789', 1, 9.96, 30266.0]

================ 第2张表的内部结构 ================
【表头 (table_columns)】: 
['head_ID', 'head_Name', 'born_state', 'age']

【第一行数据 (table_content)】: 
[1, 'Tiger Woods', 'Alabama', 67.0]

================ 第3张表的内部结构 ================
【表头 (table_columns)】: 
['Department_ID', 'head_ID', 'temporary_acting']

【第一行数据 (table_content)】: 
[2, 5, 'Yes']

================ 关键字段检查 ================
是否有 primary_keys 字段？: False
是否有 foreign_keys 字段？: False
================ 表的主键 ================
外键(foreign_keys)
['head_ID', 'Department_ID']

【主键(table_primary_key)】: 
['Department_ID', 'head_ID', 'Department_ID']

================ 答案 ================
答案(answer)
Jeff Maggert, Billy Mayfair

正在加载大文件: ./data/Synthesized_two_table.json ...
加载成功！数据集中共有 2592 条多表查询样本。

{'id_': 0, 'Question': 'Which department currently headed by a temporary acting manager has the largest number of employees, and how many employees does it have?', 'SQL': "SELECT d.Name, SUM(d.Num_Employees) FROM department d JOIN management m ON d.Department_ID = m.department_ID WHERE m.temporary_acting = 'Yes' GROUP BY d.Name ORDER BY SUM(d.Num_Employees) DESC LIMIT 1;", 'table_names': ['department', 'management'], 'tables': [{'table_columns': ['Department_ID', 'Name', 'Creation', 'Ranking', 'Budget_in_Billions', 'Num_Employees'], 'table_content': [[1, 'State', '1789', 1, 9.96, 30266.0], [2, 'Treasury', '1789', 2, 11.1, 115897.0], [3, 'Defense', '1947', 3, 439.3, 3000000.0], [4, 'Justice', '1870', 4, 23.4, 112557.0], [5, 'Interior', '1849', 5, 10.7, 71436.0], [6, 'Agriculture', '1889', 6, 77.6, 109832.0], [7, 'Commerce', '1903', 7, 6.2, 36000.0], [8, 'Labor', '1913', 8, 59.7, 17347.0], [9, 'Health and Human Services', '1953', 9, 543.2, 67000.0], [10, 'Housing and Urban Development', '1965', 10, 46.2, 10600.0], [11, 'Transportation', '1966', 11, 58.0, 58622.0], [12, 'Energy', '1977', 12, 21.5, 116100.0], [13, 'Education', '1979', 13, 62.8, 4487.0], [14, 'Veterans Affairs', '1989', 14, 73.2, 235000.0], [15, 'Homeland Security', '2002', 15, 44.6, 208000.0]]}, {'table_columns': ['department_ID', 'head_ID', 'temporary_acting'], 'table_content': [[2, 5, 'Yes'], [15, 4, 'Yes'], [2, 6, 'Yes'], [7, 3, 'No'], [11, 10, 'No']]}], 'foreign_keys': ['head id', 'department id'], 'primary_keys': ['department id', 'head id', 'department id'], 'answer': 'Treasury, 115897'}
================ 第一条数据的核心信息 ================
【ID】: 0
【大模型生成的问题 (Question)】:
Which department currently headed by a temporary acting manager has the largest number of employees, and how many employees does it have?

【人工写的标准答案 (SQL)】:
SELECT d.Name, SUM(d.Num_Employees) FROM department d JOIN management m ON d.Department_ID = m.department_ID WHERE m.temporary_acting = 'Yes' GROUP BY d.Name ORDER BY SUM(d.Num_Employees) DESC LIMIT 1;

【解决这个问题需要关联的表 (table_names)】: ['department', 'management']

================ 第1张表的内部结构 ================
【表头 (table_columns)】: 
['Department_ID', 'Name', 'Creation', 'Ranking', 'Budget_in_Billions', 'Num_Employees']

【第一行数据 (table_content)】: 
[1, 'State', '1789', 1, 9.96, 30266.0]

================ 第2张表的内部结构 ================
【表头 (table_columns)】: 
['department_ID', 'head_ID', 'temporary_acting']

【第一行数据 (table_content)】: 
[2, 5, 'Yes']

================ 关键字段检查 ================
是否有 primary_keys 字段？: False
是否有 foreign_keys 字段？: False
================ 表的主键 ================
外键(foreign_keys)
['head id', 'department id']

【主键(table_primary_key)】: 
['department id', 'head id', 'department id']

================ 答案 ================
答案(answer)
Treasury, 115897
"""

# 只调用get_table_nums的结果
"""
正在加载大文件: ./data/Synthesized_three_table.json ...
✅ 加载成功！数据集中共有 721 条多表查询样本
================ 全局表格统计 ================
🚀 统计完毕：在【Synthesized_three_table.json】中，一共包含 391 张真正独特的表！

正在加载大文件: ./data/Synthesized_two_table.json ...
✅ 加载成功！数据集中共有 2592 条多表查询样本
================ 全局表格统计 ================
🚀 统计完毕：在【Synthesized_two_table.json】中，一共包含 644 张真正独特的表！


进程已结束，退出代码为 0
"""