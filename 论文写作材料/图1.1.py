import graphviz

font_name = 'Microsoft YaHei'

dot = graphviz.Digraph('MultiHop_DB_Infographic', format='png')
dot.attr(dpi='300', nodesep='0.5', ranksep='0.8', fontname=font_name)
dot.attr('node', shape='none', fontsize='11', fontname=font_name)

# ================= 1. 海量干扰表 =================
with dot.subgraph(name='cluster_distractors') as d:
    d.attr(style='rounded', color='#cccccc', label='海量干扰表 (Distractors) 多表多跳，表中包含目标表', fontsize='12')

    # 干扰表1 - 部门表
    d.node('Departments', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#e0e0e0" STYLE="ROUNDED">
        <TR><TD BGCOLOR="#f0f0f0"><B>部门表 (Departments)</B><BR/>(Dept_ID, Name, Head)</TD></TR>
        <TR><TD>
        Dept_ID Name Head<BR/>
        1 计算机系 张教授<BR/>
        ...<BR/>
        5 物理系 李教授
        </TD></TR>
    </TABLE>>''')

    # 干扰表2 - 教师表
    d.node('Professors', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#e0e0e0" STYLE="ROUNDED">
        <TR><TD BGCOLOR="#f0f0f0"><B>教师表 (Professors)</B><BR/>(Prof_ID, Name, Dept_ID)</TD></TR>
        <TR><TD>
        Prof_ID Name Dept_ID<BR/>
        101 张教授 1<BR/>
        ...<BR/>
        105 李教授 5
        </TD></TR>
    </TABLE>>''')

    # 干扰表3 - 薪资表
    d.node('Salaries', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#e0e0e0" STYLE="ROUNDED">
        <TR><TD BGCOLOR="#f0f0f0"><B>薪资表 (Salaries)</B><BR/>(Emp_ID, Amount, Date)</TD></TR>
        <TR><TD>
        Emp_ID Amount Date<BR/>
        1001 12000 2024-01-01<BR/>
        ...<BR/>
        1005 9500 2024-01-01
        </TD></TR>
    </TABLE>>''')

    # 干扰表4 - 科研项目表
    d.node('Projects', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#e0e0e0" STYLE="ROUNDED">
        <TR><TD BGCOLOR="#f0f0f0"><B>科研项目表 (Projects)</B><BR/>(Proj_ID, Fund, Date)</TD></TR>
        <TR><TD>
        Proj_ID Fund Date<BR/>
        P001 500000 2024-02-01<BR/>
        ...<BR/>
        P010 300000 2024-06-01
        </TD></TR>
    </TABLE>>''')

    # 目标表1 - Students
    d.node('Students', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#c0e8c0" STYLE="ROUNDED">
        <TR><TD BGCOLOR="#d8f0d8"><B>学生表 (Students) ★目标表</B><BR/>(Student_ID, Name, Major)</TD></TR>
        <TR><TD>
        Student_ID Name Major<BR/>
        1 Alice 计算机科学<BR/>
        ...<BR/>
        4 Bob 物理
        </TD></TR>
    </TABLE>>''')

    # 目标表2 - Courses
    d.node('Courses', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#c0e8c0" STYLE="ROUNDED">
        <TR><TD BGCOLOR="#d8f0d8"><B>课程表 (Courses) ★目标表</B><BR/>(Course_ID, Course_Name, Credits)</TD></TR>
        <TR><TD>
        Course_ID Course_Name Credits<BR/>
        101 机器学习 3<BR/>
        ...<BR/>
        102 数据结构 4
        </TD></TR>
    </TABLE>>''')

    # 目标表3 - Enrollments
    d.node('Enrollments', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#c0e8c0" STYLE="ROUNDED">
        <TR><TD BGCOLOR="#d8f0d8"><B>评分表 (Enrollments) ★目标表</B><BR/>(Course_ID, Student_ID, Grade)</TD></TR>
        <TR><TD>
        Course_ID Student_ID Grade<BR/>
        101 1 A<BR/>
        ...<BR/>
        105 4 B
        </TD></TR>
    </TABLE>>''')

# 强制海量干扰表水平排列
with dot.subgraph() as s_align:
    s_align.attr(rank='same')
    s_align.edge('Departments', 'Professors', style='invis')
    s_align.edge('Professors', 'Salaries', style='invis')
    s_align.edge('Salaries', 'Projects', style='invis')
    s_align.edge('Projects', 'Students', style='invis')
    s_align.edge('Students', 'Courses', style='invis')
    s_align.edge('Courses', 'Enrollments', style='invis')

# ================= 2. 关键证据链 =================
with dot.subgraph(name='cluster_key') as k:
    k.attr(label='关键证据链 (Key Proof Chain)', style='dashed', color='#ffa500', penwidth='1.2')
    k.node('Stu', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#e0e0e0">
        <TR><TD BGCOLOR="#008080"><B><FONT COLOR="#ffffff">Students</FONT></B></TD></TR>
        <TR><TD PORT="pk">Student_ID</TD><TD>Name</TD><TD>Major</TD></TR>
        <TR><TD>1</TD><TD>Alice</TD><TD>计算机科学</TD></TR>
        <TR><TD>4</TD><TD>Bob</TD><TD>物理</TD></TR>
    </TABLE>>''')

    k.node('Enr', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#e0e0e0">
        <TR><TD BGCOLOR="#008080"><B><FONT COLOR="#ffffff">Enrollments</FONT></B></TD></TR>
        <TR><TD PORT="fk1">Course_ID</TD><TD PORT="fk2">Student_ID</TD><TD>Grade</TD></TR>
        <TR><TD>101</TD><TD>1</TD><TD>A</TD></TR>
        <TR><TD>105</TD><TD>4</TD><TD>B</TD></TR>
    </TABLE>>''')

    k.node('Cou', '''<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="#e0e0e0">
        <TR><TD BGCOLOR="#008080"><B><FONT COLOR="#ffffff">Courses</FONT></B></TD></TR>
        <TR><TD PORT="pk">Course_ID</TD><TD>Course_Name</TD><TD>Credits</TD></TR>
        <TR><TD>101</TD><TD>机器学习</TD><TD>3</TD></TR>
        <TR><TD>102</TD><TD>数据结构</TD><TD>4</TD></TR>
    </TABLE>>''')

    # 水平排列
    k.edge('Stu', 'Enr', style='invis')
    k.edge('Enr', 'Cou', style='invis')

    # 主外键连线
    k.edge('Stu:pk', 'Enr:fk2', color='#0066cc', penwidth='1.2', label='PK-FK', constraint='false')
    k.edge('Cou:pk', 'Enr:fk1', color='#0066cc', penwidth='1.2', label='PK-FK', constraint='false')

# ================= 3. 自然语言问题 =================
dot.node('Reasoning', '''<
<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="8" COLOR="#b2dfdb" BGCOLOR="#e0f7fa" STYLE="ROUNDED">
<TR>
    <TD>
        <B>自然语言问题 (多跳逻辑推理)</B><BR/>
        问题：<BR/>
        找出“计算机科学”专业学生在“机器学习”课程中的成绩？<BR/><BR/>
        步骤1：在 Students 表中找到专业为 计算机科学 的学生ID。<BR/>
        步骤2：在 Courses 表中找到课程名为 机器学习 的课程ID。<BR/>
        步骤3：根据 学生ID 和 课程ID 在 Enrollments 表中找到成绩。<BR/>
        答案：A
    </TD>
</TR>
</TABLE>>''')

# 将关键证据链与推理面板连接
dot.edge('Enr', 'Reasoning', color='#ff9900', style='dashed', penwidth='1.5', label='多跳逻辑推理')

# 渲染
dot.render('multihop_infographic', view=True, cleanup=True)
print("图生成成功！已保存为 multihop_infographic.png")