"""
统一实验运行入口。

本脚本用于从一个统一入口启动 MMQA 项目的三类核心实验：
1. retrieval：多表检索实验
2. text2sql：本地模型 Text-to-SQL 评估实验
3. text2sql_api：基于阿里百炼 OpenAI 兼容接口的 Text-to-SQL 评估实验

一、功能说明
- 当 `--experiment retrieval` 时，会转调：`src/runner/test_retrieval_evaluation_multi_k.py`
- 当 `--experiment text2sql` 时，会转调：`src/runner/evaluate_model_text2sql.py`
- 当 `--experiment text2sql_api` 时，会转调：`src/runner/evaluate_api_text2sql_bailian.py`
- 本脚本本身不直接执行检索或推理逻辑，而是负责统一解析参数、拼接命令并调用对应子脚本。

二、基础用法
1. 运行多表检索实验：
   `python src/run_experiment.py --experiment retrieval --experiment_type E3 --table_num 3`

2. 运行本地 Text-to-SQL 评估实验：
   `python src/run_experiment.py --experiment text2sql --model_name <模型路径或名称>`

3. 运行百炼 API Text-to-SQL 评估实验：
   `python src/run_experiment.py --experiment text2sql_api --model_key qwen36`

三、retrieval 模式说明
适用场景：评估二表 / 三表多表检索效果，并比较不同检索策略。

常用参数：
- `--experiment retrieval`
  - 指定运行检索实验。
- `--experiment_type`
  - 可选值：`E1`, `E2`, `E3`, `E3_PAPER`, `E4_HYBRID`, `E5_HYBRID_LOCAL`
  - 含义：
    - `E1`：不分解，不传播
    - `E2`：分解，不传播
    - `E3`：分解 + 传播
    - `E3_PAPER`：更接近论文伪代码版本的传播实现
    - `E4_HYBRID`：不确定性门控传播
    - `E5_HYBRID_LOCAL`：局部扩展 + 重排
- `--table_num`
  - 可选值：`2` 或 `3`
  - 表示运行二表实验还是三表实验。
- `--limit`
  - 仅评估前 N 条样本；默认 `0` 表示使用该实验配置下的全部样本。
- `--model_name`
  - 指定问题分解器模型名，例如 `gpt-4o-mini`、`gpt-5.4`。
  - 当实验类型涉及问题分解时，该参数会传递给分解器。
- `--output_file`
  - 自定义输出报告路径；若不传，则使用默认命名。

retrieval 示例：
- 三表 E3：
  `python src/run_experiment.py --experiment retrieval --experiment_type E3 --table_num 3`
- 三表 E5，仅跑前 100 条：
  `python src/run_experiment.py --experiment retrieval --experiment_type E5_HYBRID_LOCAL --table_num 3 --limit 100`
- 使用 `gpt-5.4` 作为问题分解器运行三表 E2：
  `python src/run_experiment.py --experiment retrieval --experiment_type E2 --table_num 3 --model_name gpt-5.4`
- 自定义输出文件：
  `python src/run_experiment.py --experiment retrieval --experiment_type E3 --table_num 2 --output_file outputs/custom_e3_two_table.json`

四、text2sql 模式说明
适用场景：评估基础模型或 LoRA/Adapter 微调后的 Text-to-SQL 生成效果。

常用参数：
- `--experiment text2sql`
  - 指定运行本地 Text-to-SQL 评估。
- `--model_name`
  - 基础模型路径或模型名称。
- `--adapter_path`
  - LoRA / Adapter 权重路径；若为空则只评估基础模型。
- `--test_file`
  - 指定测试集文件路径；若为空则由子脚本使用默认测试集。
- `--output_file`
  - 指定评估结果输出路径。
- `--max_new_tokens`
  - 控制生成最大长度。
- `--limit`
  - 只评估前 N 条测试样本。
- `--fp16`
  - 以半精度加载/推理。
- `--bf16`
  - 以 bfloat16 精度加载/推理。

text2sql 示例：
- 基础模型评估：
  `python src/run_experiment.py --experiment text2sql --model_name Qwen/Qwen2.5-1.5B-Instruct`
- 评估 Adapter：
  `python src/run_experiment.py --experiment text2sql --model_name Qwen/Qwen2.5-1.5B-Instruct --adapter_path outputs/qwen_text2sql_lora/final_checkpoint`
- 限制样本数并开启 fp16：
  `python src/run_experiment.py --experiment text2sql --model_name Qwen/Qwen2.5-1.5B-Instruct --limit 20 --fp16`

五、text2sql_api 模式说明
适用场景：通过阿里百炼兼容接口评估云端大模型的 Text-to-SQL 效果。

常用参数：
- `--experiment text2sql_api`
  - 指定运行百炼 API 评估。
- `--model_key`
  - 预设模型键，例如 `qwen36`、`deepseek_v4_flash`、`kimi_k26`、`minimax_m25`、`glm5`，或 `all`。
- `--model_name`
  - 在非 `all` 模式下覆盖预设模型名。
- `--api_key`
  - 显式传入阿里百炼 API Key。
- `--base_url`
  - API 基础地址，默认是百炼兼容接口地址。
- `--test_file`
  - 指定测试集文件路径。
- `--output_file`
  - 指定预测明细输出文件。
- `--metrics_file`
  - 指定指标输出文件。
- `--max_new_tokens`
  - 控制生成最大长度。
- `--temperature`
  - 生成温度。
- `--limit`
  - 只评估前 N 条测试样本。
- `--request_timeout`
  - 单次请求超时时间。
- `--max_retries`
  - 失败后的最大重试次数。
- `--retry_sleep`
  - 重试间隔基准秒数。

text2sql_api 示例：
- 使用预设 qwen36：
  `python src/run_experiment.py --experiment text2sql_api --model_key qwen36`
- 指定模型名并只评估前 20 条：
  `python src/run_experiment.py --experiment text2sql_api --model_key qwen36 --model_name qwen3.6-flash --limit 20`
- 自定义输出路径：
  `python src/run_experiment.py --experiment text2sql_api --model_key glm5 --output_file outputs/glm5_predictions.jsonl --metrics_file outputs/glm5_metrics.json`

六、输出说明
- retrieval 模式通常会输出：
  - 总体指标报告 JSON
  - case 级别明细 JSON
- text2sql / text2sql_api 模式通常会输出：
  - 预测结果
  - 评估统计结果
- 若传入 `--output_file`，则结果写入指定路径；否则由对应子脚本决定默认输出位置。

七、注意事项
- 请在项目根目录或能正确解析 `src/` 相对路径的位置运行该脚本。
- retrieval、text2sql、text2sql_api 三类实验的参数并不完全通用；未被对应模式使用的参数会被忽略。
- `--model_name` 在 retrieval 模式下表示“问题分解模型”，在 text2sql / text2sql_api 模式下表示“生成模型”，语义不同。
- 若运行 `text2sql_api`，请提前配置好 `DASHSCOPE_API_KEY`，或通过 `--api_key` 显式传入。
"""

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(description="Unified runner for MMQA retrieval and Text-to-SQL experiments")
    parser.add_argument("--experiment", choices=["retrieval", "text2sql", "text2sql_api"], required=True)

    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--model_name", type=str, default="")
    parser.add_argument("--output_file", type=str, default="")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")

    parser.add_argument("--table_num", type=int, choices=[2, 3], default=3)
    parser.add_argument(
        "--experiment_type",
        type=str,
        choices=["E1", "E2", "E3", "E3_PAPER", "E4_HYBRID", "E5_HYBRID_LOCAL"],
        default="E3",
    )

    parser.add_argument("--max_new_tokens", type=int, default=0)
    parser.add_argument("--adapter_path", type=str, default="")
    parser.add_argument("--test_file", type=str, default="")
    parser.add_argument("--model_key", type=str, default="")
    parser.add_argument("--api_key", type=str, default="")
    parser.add_argument("--base_url", type=str, default="")
    parser.add_argument("--metrics_file", type=str, default="")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--request_timeout", type=float, default=0.0)
    parser.add_argument("--max_retries", type=int, default=0)
    parser.add_argument("--retry_sleep", type=float, default=0.0)

    return parser.parse_args()


def append_if_present(command, flag, value):
    if value not in ("", None, 0):
        command.extend([flag, str(value)])


def run_command(command):
    print("[INFO] Running command:")
    print(" ".join(command))
    result = subprocess.run(command, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def build_retrieval_command(args):
    command = [
        sys.executable,
        str(PROJECT_ROOT / "src" / "runner" / "test_retrieval_evaluation_multi_k.py"),
        "--table_num",
        str(args.table_num),
        "--experiment_type",
        args.experiment_type,
    ]
    append_if_present(command, "--limit", args.limit)
    append_if_present(command, "--output_file", args.output_file)
    append_if_present(command, "--model_name", args.model_name)
    return command


def build_text2sql_command(args):
    command = [sys.executable, str(PROJECT_ROOT / "src" / "runner" / "evaluate_model_text2sql.py")]
    append_if_present(command, "--model_name", args.model_name)
    append_if_present(command, "--adapter_path", args.adapter_path)
    append_if_present(command, "--test_file", args.test_file)
    append_if_present(command, "--output_file", args.output_file)
    append_if_present(command, "--max_new_tokens", args.max_new_tokens)
    append_if_present(command, "--limit", args.limit)
    if args.fp16:
        command.append("--fp16")
    if args.bf16:
        command.append("--bf16")
    return command


def build_text2sql_api_command(args):
    command = [sys.executable, str(PROJECT_ROOT / "src" / "runner" / "evaluate_api_text2sql_bailian.py")]
    append_if_present(command, "--model_key", args.model_key)
    append_if_present(command, "--model_name", args.model_name)
    append_if_present(command, "--api_key", args.api_key)
    append_if_present(command, "--base_url", args.base_url)
    append_if_present(command, "--test_file", args.test_file)
    append_if_present(command, "--output_file", args.output_file)
    append_if_present(command, "--metrics_file", args.metrics_file)
    append_if_present(command, "--max_new_tokens", args.max_new_tokens)
    append_if_present(command, "--temperature", args.temperature)
    append_if_present(command, "--limit", args.limit)
    append_if_present(command, "--request_timeout", args.request_timeout)
    append_if_present(command, "--max_retries", args.max_retries)
    append_if_present(command, "--retry_sleep", args.retry_sleep)
    return command


def main():
    args = parse_args()

    if args.experiment == "retrieval":
        command = build_retrieval_command(args)
    elif args.experiment == "text2sql":
        command = build_text2sql_command(args)
    else:
        command = build_text2sql_api_command(args)

    run_command(command)


if __name__ == "__main__":
    main()
