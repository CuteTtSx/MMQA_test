import graphviz
import os

# 创建一个有向图
dot = graphviz.Digraph(comment='解耦的模块化系统架构图', format='png')

# 整体排版设置：TB 表示自上而下 (Top to Bottom)，独立的子图会自动左右并列
dot.attr(rankdir='TB', dpi='300', nodesep='0.8', ranksep='0.8')

# 全局字体设置 (Windows推荐 Microsoft YaHei 或 SimHei，Mac 推荐 PingFang SC)
font_name = 'Microsoft YaHei'
dot.attr('node', fontname=font_name, fontsize='12')
dot.attr('edge', fontname=font_name, fontsize='10')

# ================= 左侧链路：多表检索模块 (MTR) =================
with dot.subgraph(name='cluster_mtr') as c1:
    # 设置外框样式（虚线大框）
    c1.attr(label='多表检索链路 (MTR)', style='dashed', color='#0066cc', penwidth='2',
            fontname=font_name, fontsize='14', fontcolor='#0066cc')

    # 1. MTR 输入
    c1.node('In_MTR', '全量数据库表池\n+ 复杂自然语言问题',
            shape='cylinder', style='filled', fillcolor='#e6f3ff', color='#0066cc')

    # 2. MTR 处理中心
    c1.node('Proc_MTR', '多表检索核心算法\n(问题分解、向量相似度计算、结构传播)',
            shape='box', style='filled,rounded', fillcolor='#cce5ff', color='#004c99', height='0.8')

    # 3. MTR 输出
    c1.node('Out_MTR', 'Top-K 候选表',
            shape='note', style='filled', fillcolor='#e6f3ff', color='#0066cc')

    # 4. MTR 评估 (与处理逻辑使用不同颜色区分)
    c1.node('Eval_MTR', '检索指标独立评估\n(Recall, Precision, MRR, MAP 等)',
            shape='component', style='filled', fillcolor='#fff3e6', color='#ff9900')

    # MTR 内部连线
    c1.edge('In_MTR', 'Proc_MTR', penwidth='1.5')
    c1.edge('Proc_MTR', 'Out_MTR', penwidth='1.5')
    c1.edge('Out_MTR', 'Eval_MTR', color='#ff9900', style='dashed', penwidth='1.5', label=' 输入评估 ')

# ================= 右侧链路：Text-to-SQL 生成模块 =================
with dot.subgraph(name='cluster_t2s') as c2:
    # 设置外框样式（虚线大框）
    c2.attr(label='Text-to-SQL 生成链路', style='dashed', color='#2ca02c', penwidth='2',
            fontname=font_name, fontsize='14', fontcolor='#2ca02c')

    # 1. T2S 输入 (强调使用无噪声的 Oracle Schema)
    c2.node('In_T2S', '标准答案表头 (Oracle Schema)\n+ 复杂自然语言问题',
            shape='folder', style='filled', fillcolor='#e8f5e9', color='#2ca02c')

    # 2. T2S 处理中心
    c2.node('Proc_T2S', '大语言模型 API 生成\n(基于零样本提示词的结构化映射)',
            shape='box', style='filled,rounded', fillcolor='#c8e6c9', color='#1b5e20', height='0.8')

    # 3. T2S 输出
    c2.node('Out_T2S', '生成的 SQL 查询',
            shape='note', style='filled', fillcolor='#e8f5e9', color='#2ca02c')

    # 4. T2S 评估
    c2.node('Eval_T2S', '生成语法与语义独立评估\n(BLEU, ROUGE 等文本匹配指标)',
            shape='component', style='filled', fillcolor='#fff3e6', color='#ff9900')

    # T2S 内部连线
    c2.edge('In_T2S', 'Proc_T2S', penwidth='1.5')
    c2.edge('Proc_T2S', 'Out_T2S', penwidth='1.5')
    c2.edge('Out_T2S', 'Eval_T2S', color='#ff9900', style='dashed', penwidth='1.5', label=' 输入评估 ')

# ================= 渲染与保存 =================
# render 会在当前目录下生成名为 'decoupled_architecture.png' 的文件
dot.render('decoupled_architecture', view=True, cleanup=True)

print("架构图生成成功！已保存在当前目录下。")