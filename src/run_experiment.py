"""
统一实验运行入口。

支持三个实验：
1. retrieval   -> 多表检索评估（E1/E2/E3）
2. text2sql    -> Text-to-SQL 模型评估
3. qa          -> 多表 QA 模型评估

示例：
- python src/run_experiment.py --experiment retrieval --experiment_type E1 --table_num 2
- python src/run_experiment.py --experiment retrieval --experiment_type E2 --table_num 3 --limit 100
- python src/run_experiment.py --experiment retrieval --experiment_type E3 --table_num 3
- python src/run_experiment.py --experiment text2sql --fp16 --limit 20
- python src/run_experiment.py --experiment qa --fp16 --limit 20
"""

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Unified runner for MMQA experiments")
    parser.add_argument("--experiment", choices=["retrieval", "text2sql", "qa"], required=True)

    # 通用参数
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--model_name", type=str, default="")
    parser.add_argument("--output_file", type=str, default="")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")

    # retrieval 专用
    parser.add_argument("--table_num", type=int, choices=[2, 3], default=3)
    parser.add_argument("--experiment_type", type=str, choices=["E1", "E2", "E3", "E3_PAPER"], default="E3")
    parser.add_argument("--num_iterations", type=int, default=2)

    # text2sql / qa 共享
    parser.add_argument("--max_new_tokens", type=int, default=0)

    # text2sql 专用
    parser.add_argument("--adapter_path", type=str, default="")
    parser.add_argument("--test_file", type=str, default="")

    # qa 专用
    parser.add_argument("--data_dir", type=str, default="")

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
        str(PROJECT_ROOT / "test" / "test_retrieval_evaluation_multi_k.py"),
        "--table_num",
        str(args.table_num),
        "--experiment_type",
        args.experiment_type,
        "--num_iterations",
        str(args.num_iterations),
    ]
    append_if_present(command, "--limit", args.limit)
    append_if_present(command, "--output_file", args.output_file)
    append_if_present(command, "--model_name", args.model_name)
    return command


def build_text2sql_command(args):
    command = [sys.executable, str(PROJECT_ROOT / "src" / "evaluate_model_text2sql.py")]
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


def build_qa_command(args):
    command = [sys.executable, str(PROJECT_ROOT / "src" / "evaluate_model_qa.py")]
    append_if_present(command, "--model_name", args.model_name)
    append_if_present(command, "--data_dir", args.data_dir)
    append_if_present(command, "--output_file", args.output_file)
    append_if_present(command, "--max_new_tokens", args.max_new_tokens)
    append_if_present(command, "--limit", args.limit)
    if args.fp16:
        command.append("--fp16")
    if args.bf16:
        command.append("--bf16")
    return command


def main():
    args = parse_args()

    if args.experiment == "retrieval":
        command = build_retrieval_command(args)
    elif args.experiment == "text2sql":
        command = build_text2sql_command(args)
    else:
        command = build_qa_command(args)

    run_command(command)


if __name__ == "__main__":
    main()
