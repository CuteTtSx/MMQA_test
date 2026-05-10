import graphviz
import os

# 创建一个有向图
dot = graphviz.Digraph(comment='传统 RAG 流水线的级联误差', format='png')

# 整体排版设置：LR 表示从左到右 (Left to Right)
dot.attr(rankdir='LR', dpi='300')

# 全局字体设置 (Windows推荐 Microsoft YaHei 或 SimHei，Mac 推荐 PingFang SC)
font_name = 'Microsoft YaHei'
dot.attr('node', fontname=font_name, fontsize='12')
dot.attr('edge', fontname=font_name, fontsize='10')

# ================= 1. 定义节点 =================

# 输入节点 1: 自然语言问题 (【修改】背景换成绿色)
dot.node('Q', '自然语言问题\n(复杂多跳)', shape='box', style='filled,rounded', fillcolor='#e8f5e9', color='#4caf50')

# 输入节点 2: 数据库表池
dot.node('DB', '全局数据库表池\n(海量干扰表)', shape='cylinder', style='filled', fillcolor='#f2f2f2', color='#b3b3b3')

# 警告/误差节点 (【修改】表述改为"可能引入误差")
dot.node('ErrorNote', '⚠️ 可能引入误差:\n漏召回桥接表 / 召回干扰表',
         shape='note', style='filled', fillcolor='#ffe6e6', color='#ff4d4d', fontcolor='#d90000')

# 输出节点: 错误的SQL/答案
dot.node('Out', '错误的 SQL\n或 错误答案', shape='box', style='filled,rounded', fillcolor='#ffe6e6', color='#ff4d4d',
         fontcolor='#d90000')

# 评估困境节点
dot.node('Dilemma', '性能评估无法归因:\n是多表检索问题还是LLMs生成能力弱?',
         shape='hexagon', style='filled,dashed', fillcolor='#fff3e6', color='#ff9900')

# ================= 2. 定义聚类子图 (虚线框) =================
with dot.subgraph(name='cluster_pipeline') as c:
    c.attr(label='黑盒流水线导致能力边界模糊', style='dashed', color='#808080', fontname=font_name)

    # 检索模块
    c.node('R', '多表检索模块\n(Retriever)', shape='box', style='filled,rounded', fillcolor='#e6f3ff', color='#0066cc')

    # 中间产物 (【修改】背景换成黄色)
    c.node('T', '检索出的\n候选表结构', shape='box', style='filled,rounded', fillcolor='#fff9c4', color='#fbc02d')

    # 生成模块
    c.node('G', 'LLM SQL生成模块\n(Generator)', shape='box', style='filled,rounded', fillcolor='#e6f3ff',
           color='#0066cc')

    # 流水线内部连线
    c.edge('R', 'T')
    c.edge('T', 'G', label=' 级联误差传递 ', color='#ff4d4d', fontcolor='#ff4d4d', style='dashed', penwidth='2')

# ================= 3. 定义全局连线 =================

dot.edge('Q', 'R')
dot.edge('DB', 'R')

# 误差节点指向中间产物
dot.edge('ErrorNote', 'T', color='#ff4d4d', style='dotted', penwidth='1.5')

# 离开流水线指向输出
dot.edge('G', 'Out', color='#ff4d4d', penwidth='2')

# 疑问节点指向流水线外框（【修改】明确指向最后的红色框）
dot.edge('Dilemma', 'Out', style='dashed', color='#ff9900', penwidth='1.5')

# ================= 4. 渲染并保存 =================
dot.render('rag_error_pipeline', view=True, cleanup=True)

print("图片生成成功！已保存在当前目录下。")