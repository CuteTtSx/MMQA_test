# MMQA 系统项目任务书 (优化版)

**项目目标**: 构建一个多表问答系统，通过多表检索(MTR)算法和微调模型实现高精度的Text-to-SQL生成

**项目周期**: 3个阶段，预计8-12周

---

## 📋 阶段一：前期准备 (已部分完成，需优化)

### 1.1 环境搭建 ✅
- [x] WSL + Python虚拟环境配置
- [x] PyCharm集成开发环境
- [x] .env配置文件(API密钥管理)
- [ ] **改进**: 添加requirements.txt，统一依赖版本管理
- [ ] **改进**: 添加logging配置，便于调试和监控

### 1.2 数据解析与探索 ✅ (部分完成)
- [x] explore_data.py - 数据集基本探索
- [x] 提取Question、SQL、表结构、主外键信息

### 1.3 全局表库构建 ✅ (已完成)
- [x] build_table_pool.py - 表去重与结构指纹识别
- [x] 生成global_table_pool_three.json (391张表)
- [x] 生成global_table_pool_two.json (644张表)
- [ ] **改进**: 添加表库统计分析
  - 表的平均列数、行数分布
  - 主外键关系图可视化
  - 表的复用频率统计

### 1.4 问题数据集提取 ✅ (已完成)
**文件**: `extract_questions.py`
- 从两个JSON文件中提取所有问题
- 格式: `{id, question, sql, answer}`
- 输出: `data/QA_SQL_three_table.json` 和 `data/QA_SQL_two_table.json`
- **用途**: 为问题分解器提供训练/测试数据

---

## 🎯 阶段二：核心攻坚 - 多表检索(MTR)算法 (当前阶段)

### 2.1 问题分解器 ✅ (基本完成)

**文件**: `question_decomposer.py` (改进版)

**当前状态**:
- ✅ 基础框架已搭建(LangChain + GPT-4o-mini)
- ⚠️ Prompt需要优化(添加few-shot示例后, 出现{}匹配的的问题, 暂时没有加进prompt, 待修改)
- ✅ 错误处理和重试机制

**改进任务**:
1. **补充Few-shot示例** (3-5个高质量例子)
   ```
   示例1: 多跳问题 → 子问题分解
   示例2: 复杂聚合问题 → 子问题分解
   示例3: 条件过滤问题 → 子问题分解
   ```

2. **添加错误处理**
   - API调用失败重试(指数退避)
   - JSON解析异常捕获
   - 子问题数量验证(1-5个)

3. **性能优化**
   - 批量处理问题(减少API调用次数)
   - 缓存已分解的问题(避免重复调用)

4. **输出格式标准化**
   ```python
   {
     "original_question": str,
     "sub_questions": List[str],
     "decomposition_confidence": float,  # 0-1
     "timestamp": str
   }
   ```

### 2.2 语义相似度计算模块 ✅ (已完成)

**文件**: `semantic_similarity.py`

**功能**: 计算问题与表的语义相关性

**实现方案**:
```python
class SemanticSimilarityCalculator:
    def __init__(self):
        # 使用开源embedding模型(如sentence-transformers)
        # 或调用OpenAI embedding API
        pass
    
    def compute_question_table_similarity(self, question: str, table_schema: dict) -> float:
        """
        计算问题与表的相似度
        输入: 问题文本 + 表结构(列名+类型)
        输出: 相似度分数 [0, 1]
        """
        pass
    
    def compute_table_table_similarity(self, table1: dict, table2: dict) -> float:
        """
        计算两张表的相似度(用于FK关系判断)
        """
        pass
```

**关键参数**:
- Embedding模型: `text-embedding-3-small` (OpenAI) 或 `all-MiniLM-L6-v2` (本地)
- 相似度阈值: 0.5-0.7(可调)

### 2.3 多表检索(MTR)核心算法 ⚠️ (新增)

**文件**: `multi_table_retrieval.py`

**算法实现** (按论文伪代码):

```python
class MultiTableRetriever:
    def __init__(self, table_pool: dict, llm, similarity_calculator):
        self.table_pool = table_pool
        self.llm = llm
        self.sim_calc = similarity_calculator
    
    def retrieve(self, multi_hop_question: str, top_k: int = 5) -> List[dict]:
        """
        核心MTR算法
        
        步骤1: 问题分解
        - 调用question_decomposer获取子问题列表
        
        步骤2: 第一轮检索(单表)
        - 对每个子问题q_i，计算与所有表的相似度
        - γ = α(q_i, table_j)  [只计算问题-表相关性]
        
        步骤3: 迭代式多表检索(n轮)
        - 对于第i轮(i=1到n):
          - 对于每个子问题q_i:
            - 对于每张表table_j:
              - 对于每张前一轮检索的表table_k:
                - 计算: γ += α(q_i, table_j) · β(table_k, table_j)
                  其中 α = 问题-表相关性
                       β = 表-表关系强度(FK/PK重叠)
        
        步骤4: 排序与选择
        - 按γ降序排列
        - 返回top-K张表
        
        返回: [
          {
            "table_id": str,
            "table_name": str,
            "columns": List[str],
            "relevance_score": float,
            "retrieval_round": int,
            "related_tables": List[str]
          },
          ...
        ]
        """
        pass
    
    def compute_table_relationship_score(self, table1_id: str, table2_id: str) -> float:
        """
        计算两张表的关系强度β
        - 检查FK/PK重叠
        - 检查列名相似度
        - 返回 [0, 1] 的关系强度
        """
        pass
```

**关键设计**:
- 第一轮: 只计算问题-表相似度
- 后续轮: 结合问题相似度 + 表关系强度
- 迭代轮数: 2-3轮(可配置)
- 每轮保留top-K候选表

### 2.4 检索结果验证与评估 ⚠️ (新增)

**文件**: `retrieval_evaluator.py`

**功能**: 评估MTR算法的检索质量

```python
class RetrievalEvaluator:
    def evaluate(self, 
                 retrieved_tables: List[str],
                 ground_truth_tables: List[str]) -> dict:
        """
        评估指标:
        - Recall@K: 真实表中有多少被检索到
        - Precision@K: 检索到的表中有多少是真实的
        - F1@K: 综合指标
        - MRR: Mean Reciprocal Rank (排名质量)
        """
        pass
```

**测试集**: 从QA_SQL_three_table.json和QA_SQL_two_table.json中随机抽取100-200条问题进行评估

---

## 🔧 阶段三：模型微调 - Qwen2.5 LoRA (后续阶段)

### 3.1 微调数据准备 ⚠️ (新增)

**文件**: `prepare_finetuning_data.py`

**输入**: 
- QA_SQL_three_table.json和QA_SQL_two_table.json (3313条问题)
- global_table_pool_*.json (表结构)

**输出格式** (Instruction Tuning):
```json
{
  "instruction": "根据以下表结构和自然语言问题，生成对应的SQL查询语句。\n\n表结构:\n{schema}\n\n问题: {question}",
  "input": "",
  "output": "{sql}",
  "answer": "{expected_answer}"
}
```

**数据分割**:
- 训练集: 80% (2650条)
- 验证集: 10% (331条)
- 测试集: 10% (332条)

### 3.2 LoRA微调执行 ⚠️ (新增)

**文件**: `finetune_qwen.py`

**配置**:
```python
lora_config = {
    "r": 8,                    # LoRA秩
    "lora_alpha": 16,
    "target_modules": ["q_proj", "v_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": "CAUSAL_LM"
}

training_args = {
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "per_device_eval_batch_size": 4,
    "learning_rate": 2e-4,
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "logging_steps": 50,
    "eval_steps": 200,
    "save_steps": 200,
}
```

### 3.3 模型评估与优化 ⚠️ (新增)

**文件**: `evaluate_model.py`

**评估指标**:
- Exact Match (EM): SQL完全匹配
- Execution Accuracy: SQL执行结果正确
- BLEU Score: 文本相似度

---

## 📁 项目文件结构 (优化后)

```
MMQA/
├── data/
│   ├── Synthesized_three_table.json      # 原始数据(3表)
│   ├── Synthesized_two_table.json        # 原始数据(2表)
│   ├── global_table_pool_three.json      # 表库(3表)
│   ├── global_table_pool_two.json        # 表库(2表)
│   ├── all_questions.json                # 提取的所有问题 [新增]
│   ├── finetuning_data.json              # 微调数据 [新增]
│   └── retrieval_results/                # 检索结果缓存 [新增]
│
├── src/
│   ├── __init__.py
│   ├── explore_data.py                   # 数据探索
│   ├── build_table_pool.py               # 表库构建
│   ├── extract_questions.py              # 问题提取 [新增]
│   ├── question_decomposer.py            # 问题分解(改进版)
│   ├── semantic_similarity.py            # 语义相似度 [新增]
│   ├── multi_table_retrieval.py          # MTR算法 [新增]
│   ├── retrieval_evaluator.py            # 检索评估 [新增]
│   ├── prepare_finetuning_data.py        # 微调数据准备 [新增]
│   ├── finetune_qwen.py                  # LoRA微调 [新增]
│   ├── evaluate_model.py                 # 模型评估 [新增]
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                     # 日志工具 [新增]
│       ├── config.py                     # 配置管理 [新增]
│       └── cache.py                      # 缓存管理 [新增]
│
├── tests/
│   ├── test_question_decomposer.py       # 单元测试 [新增]
│   ├── test_mtr_algorithm.py             # 算法测试 [新增]
│   └── test_retrieval_evaluator.py       # 评估测试 [新增]
│
├── notebooks/
│   ├── 01_data_exploration.ipynb         # 数据分析 [新增]
│   ├── 02_mtr_analysis.ipynb             # MTR算法分析 [新增]
│   └── 03_finetuning_results.ipynb       # 微调结果 [新增]
│
├── requirements.txt                      # 依赖管理 [新增]
├── .env                                  # API配置
├── .env.example                          # 配置模板 [新增]
├── PROJECT_PLAN.md                       # 本文件
└── README.md                             # 项目说明 [新增]
```

---

## 🚀 执行优先级与时间规划

### 第1周 (数据准备)
- [ ] 创建requirements.txt和logging配置
- [ ] 完成extract_questions.py (提取3313条问题)
- [ ] 数据质量检查和统计分析
- **交付物**: all_questions.json + 数据质量报告

### 第2-3周 (问题分解优化)
- [ ] 优化question_decomposer.py (添加few-shot + 错误处理)
- [ ] 在100条问题上测试分解效果
- [ ] 调整Prompt和参数
- **交付物**: 优化后的分解器 + 测试报告

### 第4-5周 (语义相似度 + MTR算法)
- [ ] 实现semantic_similarity.py
- [ ] 实现multi_table_retrieval.py (核心算法)
- [ ] 在200条问题上测试检索效果
- **交付物**: MTR算法实现 + 检索评估报告

### 第6周 (检索优化与评估)
- [ ] 完成retrieval_evaluator.py
- [ ] 在全量数据上评估(Recall/Precision/F1)
- [ ] 调整算法参数(迭代轮数、相似度阈值等)
- **交付物**: 最终检索性能指标

### 第7-8周 (微调数据准备)
- [ ] 完成prepare_finetuning_data.py
- [ ] 生成微调数据集(2650/331/332)
- [ ] 数据格式验证
- **交付物**: 微调数据集 + 数据统计

### 第9-10周 (LoRA微调)
- [ ] 实现finetune_qwen.py
- [ ] 在小批量数据上跑通流程
- [ ] 调整超参数
- **交付物**: 微调模型 + 训练日志

### 第11-12周 (评估与优化)
- [ ] 完成evaluate_model.py
- [ ] 评估模型性能(EM/Execution Accuracy)
- [ ] 对比微调前后效果
- **交付物**: 最终评估报告 + 优化建议

---

## 📊 关键指标与成功标准

### MTR算法指标
- **Recall@5**: ≥ 85% (真实表被检索到的概率)
- **Precision@5**: ≥ 80% (检索结果的准确率)
- **F1@5**: ≥ 82%
- **平均检索时间**: < 2秒/问题

### 微调模型指标
- **Exact Match (EM)**: ≥ 70%
- **Execution Accuracy**: ≥ 75%
- **BLEU Score**: ≥ 0.85

---

## ⚠️ 风险与应对

| 风险 | 影响 | 应对方案 |
|------|------|--------|
| API调用成本过高 | 预算超支 | 使用本地embedding模型 + 缓存机制 |
| 表关系复杂度高 | MTR算法效果差 | 增加迭代轮数 + 优化相似度计算 |
| 微调数据不足 | 模型过拟合 | 数据增强 + 正则化 |
| 模型推理速度慢 | 实际应用困难 | 量化 + 蒸馏 |

---

## 📝 备注

1. **API成本优化**: 建议在semantic_similarity.py中集成本地embedding模型(如sentence-transformers)，仅在必要时调用OpenAI API
2. **缓存策略**: 为问题分解、相似度计算等结果添加缓存，避免重复计算
3. **版本控制**: 使用git管理代码，每个阶段提交一个milestone
4. **文档完善**: 每个模块添加详细的docstring和使用示例
5. **测试覆盖**: 为核心模块编写单元测试，确保代码质量

