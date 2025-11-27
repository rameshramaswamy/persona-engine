import torch
import os
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig, 
    TrainingArguments
)
from peft import LoraConfig
from trl import SFTTrainer
from datasets import load_dataset

def train_character(
    base_model_id: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    data_path: str = "data/raw/roleplay_dataset.json",
    output_dir: str = "models/adapter_v1"
):
    print(f"🧙 Starting QLoRA Training for {base_model_id}...")

    # 1. Quantization Config (4-bit to fit on consumer GPU)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    # 2. Load Model & Tokenizer
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        quantization_config=bnb_config,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    tokenizer.pad_token = tokenizer.eos_token # Fix for Llama-3

    # 3. LoRA Configuration (Target all linear layers)
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )

    # 4. Load Data
    # Expects JSONL: {"text": "<|system|>...<|user|>...<|assistant|>..."}
    dataset = load_dataset("json", data_files=data_path, split="train")

    # 5. Training Arguments
    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=100, # Short run for demo
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_strategy="steps",
        optim="paged_adamw_32bit" # Memory saver
    )

    # 6. Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        tokenizer=tokenizer,
        args=args,
        peft_config=peft_config,
    )

    trainer.train()
    trainer.save_model(output_dir)
    print(f"✅ Training Complete. Adapter saved to {output_dir}")

if __name__ == "__main__":
    # Ensure you have a 'data/raw/roleplay_dataset.json' before running
    train_character()