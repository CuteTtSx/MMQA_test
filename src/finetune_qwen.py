"""
Qwen Text-to-SQL LoRA 微调脚本。

使用方式示例：
python src/finetune_qwen.py --model_name Qwen/Qwen2.5-3B-Instruct

默认读取：
- data/finetuning_train.jsonl
- data/finetuning_val.jsonl
"""

import argparse
import json
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


DEFAULT_TRAIN_FILE = "data/finetuning_train.jsonl"
DEFAULT_VAL_FILE = "data/finetuning_val.jsonl"
DEFAULT_OUTPUT_DIR = "outputs/qwen_text2sql_lora"


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune Qwen for Text-to-SQL with LoRA")
    parser.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--train_file", type=str, default=DEFAULT_TRAIN_FILE)
    parser.add_argument("--val_file", type=str, default=DEFAULT_VAL_FILE)
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max_length", type=int, default=1024)
    parser.add_argument("--num_train_epochs", type=int, default=3)
    parser.add_argument("--per_device_train_batch_size", type=int, default=2)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=2)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--warmup_steps", type=int, default=100)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--logging_steps", type=int, default=20)
    parser.add_argument("--eval_steps", type=int, default=100)
    parser.add_argument("--save_steps", type=int, default=100)
    parser.add_argument("--save_total_limit", type=int, default=2)
    parser.add_argument("--lora_r", type=int, default=8)
    parser.add_argument("--lora_alpha", type=int, default=16)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
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
        tokenized = tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_length,
            padding=False,
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    return dataset.map(tokenize_fn, batched=True, remove_columns=["text"])


def main():
    args = parse_args()

    print(f"[INFO] Loading tokenizer: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[INFO] Loading model: {args.model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
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

    output_dir = Path(args.output_dir)
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
