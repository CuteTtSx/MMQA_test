"""
通用 Text-to-SQL LoRA 微调脚本。

使用方式示例：
python src/text2sql/finetune_qwen.py --model_key qwen
python src/text2sql/finetune_qwen.py --model_key deepseek_coder
python src/text2sql/finetune_qwen.py --model_key minimax
python src/text2sql/finetune_qwen.py --model_name Qwen/Qwen2.5-3B-Instruct --output_dir outputs/custom_text2sql_lora

默认读取：
- data/finetuning_train.jsonl
- data/finetuning_val.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import Config


DEFAULT_TRAIN_FILE = str(Config.FINETUNING_TRAIN_JSONL)
DEFAULT_VAL_FILE = str(Config.FINETUNING_VAL_JSONL)

MODEL_PRESETS = {
    "qwen": {
        "model_name": Config.FINETUNING_BASE_MODEL,
        "output_dir": str(Config.OUTPUTS_DIR / "qwen_text2sql_lora"),
    },
    "deepseek_coder": {
        "model_name": "deepseek-ai/deepseek-coder-1.3b-instruct",
        "output_dir": str(Config.OUTPUTS_DIR / "deepseek_coder_text2sql_lora"),
    },
    "minimax": {
        "model_name": "MiniMaxAI/MiniMax-M2",
        "output_dir": str(Config.OUTPUTS_DIR / "minimax_text2sql_lora"),
    },
}

DEFAULT_MODEL_KEY = "qwen"


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune an open-source LLM for Text-to-SQL with LoRA")
    parser.add_argument(
        "--model_key",
        type=str,
        default=DEFAULT_MODEL_KEY,
        choices=sorted(MODEL_PRESETS.keys()),
        help="预设模型：qwen / deepseek_coder / minimax。若同时传入 --model_name，则以 --model_name 为准。",
    )
    parser.add_argument("--model_name", type=str, default=None)
    parser.add_argument("--train_file", type=str, default=DEFAULT_TRAIN_FILE)
    parser.add_argument("--val_file", type=str, default=DEFAULT_VAL_FILE)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--max_length", type=int, default=Config.FINETUNING_CONFIG["max_length"])
    parser.add_argument("--num_train_epochs", type=int, default=Config.FINETUNING_CONFIG["num_train_epochs"])
    parser.add_argument("--per_device_train_batch_size", type=int, default=Config.FINETUNING_CONFIG["per_device_train_batch_size"])
    parser.add_argument("--per_device_eval_batch_size", type=int, default=Config.FINETUNING_CONFIG["per_device_eval_batch_size"])
    parser.add_argument("--gradient_accumulation_steps", type=int, default=Config.FINETUNING_CONFIG["gradient_accumulation_steps"])
    parser.add_argument("--learning_rate", type=float, default=Config.FINETUNING_CONFIG["learning_rate"])
    parser.add_argument("--warmup_steps", type=int, default=Config.FINETUNING_CONFIG["warmup_steps"])
    parser.add_argument("--weight_decay", type=float, default=Config.FINETUNING_CONFIG["weight_decay"])
    parser.add_argument("--logging_steps", type=int, default=Config.FINETUNING_CONFIG["logging_steps"])
    parser.add_argument("--eval_steps", type=int, default=Config.FINETUNING_CONFIG["eval_steps"])
    parser.add_argument("--save_steps", type=int, default=Config.FINETUNING_CONFIG["save_steps"])
    parser.add_argument("--save_total_limit", type=int, default=Config.FINETUNING_CONFIG["save_total_limit"])
    parser.add_argument("--lora_r", type=int, default=Config.FINETUNING_CONFIG["lora_r"])
    parser.add_argument("--lora_alpha", type=int, default=Config.FINETUNING_CONFIG["lora_alpha"])
    parser.add_argument("--lora_dropout", type=float, default=Config.FINETUNING_CONFIG["lora_dropout"])
    parser.add_argument("--seed", type=int, default=Config.DATASET_CONFIG["seed"])
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    return parser.parse_args()


def load_jsonl(path: str) -> List[Dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def apply_chat_template(messages: List[Dict], tokenizer: AutoTokenizer) -> str:
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )

    text_parts = []
    for message in messages:
        role = message["role"].upper()
        content = message["content"]
        text_parts.append(f"<{role}>\n{content}")
    return "\n\n".join(text_parts)


def build_dataset(records: List[Dict], tokenizer: AutoTokenizer, max_length: int) -> Dataset:
    formatted_texts = [apply_chat_template(item["messages"], tokenizer) for item in records]
    dataset = Dataset.from_dict({"text": formatted_texts})

    def tokenize_fn(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_length,
            padding=False,
        )

    return dataset.map(tokenize_fn, batched=True, remove_columns=["text"])


def resolve_model_args(args):
    preset = MODEL_PRESETS[args.model_key]
    model_name = args.model_name or preset["model_name"]
    output_dir = args.output_dir or preset["output_dir"]
    return model_name, output_dir


def main():
    args = parse_args()
    model_name, output_dir_value = resolve_model_args(args)

    print(f"[INFO] Model preset: {args.model_key}")
    print(f"[INFO] Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[INFO] Loading model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.bfloat16 if args.bf16 else (torch.float16 if args.fp16 else torch.float32),
        trust_remote_code=True,
    )

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("[INFO] Loading datasets...")
    train_records = load_jsonl(args.train_file)
    val_records = load_jsonl(args.val_file)
    print(f"[OK] Train samples: {len(train_records)}")
    print(f"[OK] Val samples: {len(val_records)}")

    train_dataset = build_dataset(train_records, tokenizer, args.max_length)
    val_dataset = build_dataset(val_records, tokenizer, args.max_length)

    output_dir = Path(output_dir_value)
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        weight_decay=args.weight_decay,
        logging_steps=args.logging_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        bf16=args.bf16,
        fp16=args.fp16,
        report_to="none",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        seed=args.seed,
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator
    )

    print("[INFO] Start training...")
    trainer.train()

    print("[INFO] Saving model...")
    trainer.save_model(str(output_dir / "final_checkpoint"))
    tokenizer.save_pretrained(str(output_dir / "final_checkpoint"))
    print(f"[OK] Model saved to: {output_dir / 'final_checkpoint'}")


if __name__ == "__main__":
    main()
