import graphviz

# 创建图表对象，设置自上而下的排版和高清分辨率
dot = graphviz.Digraph(comment='RAG Workflow', format='png')
dot.attr(rankdir='TB', dpi='300', nodesep='0.6', ranksep='0.8', compound='true')

# 全局字体与节点默认样式
font_name = 'Microsoft YaHei'
dot.attr('node', fontname=font_name, fontsize='11', shape='box', style='filled,rounded', height='0.6')
dot.attr('edge', fontname=font_name, fontsize='10')

# ================= 1. 第一排：数据索引层 (Indexing) =================
with dot.subgraph(name='cluster_indexing') as c1:
    c1.attr(label='阶段一：数据索引 (Data Indexing)', style='dashed', color='#1976d2', fontname=font_name,
            bgcolor='#f8fbff', margin='20')

    with c1.subgraph() as s1:
        s1.attr(rank='same')
        s1.node('Docs', '私有数据库 / 文档\n(Database / Docs)', shape='cylinder', fillcolor='#e3f2fd', color='#1976d2')
        s1.node('Chunk', '文本分块\n(Chunking)', fillcolor='#bbdefb', color='#1976d2')
        s1.node('Emb1', '向量化模型\n(Embedding Model)', fillcolor='#90caf9', color='#1976d2')
        s1.node('VecDB', '向量数据库\n(Vector DB)', shape='cylinder', fillcolor='#64b5f6', color='#1976d2')

        s1.edge('Docs', 'Chunk', color='#1976d2', penwidth='1.2')
        s1.edge('Chunk', 'Emb1', color='#1976d2', penwidth='1.2')
        s1.edge('Emb1', 'VecDB', color='#1976d2', penwidth='1.2')

# ================= 2. 第二排：检索层 (Retrieval) =================
with dot.subgraph(name='cluster_retrieval') as c2:
    c2.attr(label='阶段二：检索 (Context Retrieval)', style='dashed', color='#f57c00', fontname=font_name,
            bgcolor='#fffcf5', margin='20')

    with c2.subgraph() as s2:
        s2.attr(rank='same')
        s2.node('Query', '自然语言问题\n(User Query)', fillcolor='#fff3e0', color='#f57c00')
        s2.node('Emb2', '向量化模型\n(Embedding Model)', fillcolor='#ffe0b2', color='#f57c00')
        s2.node('Search', '相似度检索\n(Similarity Search)', fillcolor='#ffcc80', color='#f57c00')
        s2.node('TopK', '召回相关文档/知识\n(Top-K Context)', fillcolor='#ffb74d', color='#f57c00')

        s2.edge('Query', 'Emb2', color='#f57c00', penwidth='1.2')
        s2.edge('Emb2', 'Search', color='#f57c00', penwidth='1.2')
        s2.edge('Search', 'TopK', color='#f57c00', penwidth='1.2')

# ================= 3. 第三排：生成层 (Generation) =================
with dot.subgraph(name='cluster_generation') as c3:
    c3.attr(label='阶段三：生成 (Augmented Generation)', style='dashed', color='#388e3c', fontname=font_name,
            bgcolor='#f5fbf5', margin='20')

    with c3.subgraph() as s3:
        s3.attr(rank='same')
        s3.node('Prompt', '提示词组装\n(Prompt Assembly)', fillcolor='#c8e6c9', color='#388e3c')
        s3.node('LLM', '大语言模型\n(LLM Generator)', fillcolor='#a5d6a7', color='#388e3c')
        s3.node('Output', '最终答案 / SQL\n(Final Output)', fillcolor='#81c784', color='#388e3c', shape='note')

        s3.edge('Prompt', 'LLM', color='#388e3c', penwidth='1.2')
        s3.edge('LLM', 'Output', color='#388e3c', penwidth='1.2')

# ================= 4. 辅助网格对齐 (使用隐形连线强行固定纵向对齐) =================
dot.edge('Docs', 'Query', style='invis')
dot.edge('Query', 'Prompt', style='invis')

dot.edge('Chunk', 'Emb2', style='invis')
dot.edge('Emb2', 'LLM', style='invis')

dot.edge('Emb1', 'Search', style='invis')
dot.edge('Search', 'Output', style='invis')

dot.edge('VecDB', 'TopK', style='invis')

# ================= 5. 跨层级的核心业务连线 =================
# 向量数据库支撑相似度检索
dot.edge('VecDB:s', 'Search:n', style='dashed', color='#1976d2', label=' 支撑向量比对', constraint='false',
         penwidth='1.5')

# 用户问题透传至提示词
dot.edge('Query:s', 'Prompt:n', style='dashed', color='#f57c00', label=' 原始问题输入', constraint='false',
         penwidth='1.5')

# 检索结果注入大模型上下文
dot.edge('TopK:s', 'Prompt:e', color='#388e3c', penwidth='2.5', label=' 注入增强上下文', constraint='false')

# 渲染并保存为图片
dot.render('fig_rag_workflow', view=True, cleanup=True)
print("RAG 架构图生成成功！已保存在当前目录下的 fig_rag_workflow.png")