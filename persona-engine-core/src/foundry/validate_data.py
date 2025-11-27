import json
import logging
from pathlib import Path
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self, model_id: str = "meta-llama/Meta-Llama-3-8B-Instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

    def validate_file(self, file_path: str):
        print(f"🔍 Validating {file_path}...")
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")

        valid_count = 0
        errors = []
        
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                try:
                    data = json.loads(line)
                    
                    # 1. Check Schema
                    if "text" not in data:
                        errors.append(f"Line {i}: Missing 'text' field")
                        continue
                        
                    # 2. Check Token Length
                    # Very long sequences cause OOM during training
                    tokens = len(self.tokenizer.encode(data["text"]))
                    if tokens > 4096:
                        errors.append(f"Line {i}: Too long ({tokens} tokens > 4096)")
                        continue
                        
                    if tokens < 10:
                        errors.append(f"Line {i}: Too short (<10 tokens)")
                        continue

                    valid_count += 1
                    
                except json.JSONDecodeError:
                    errors.append(f"Line {i}: Invalid JSON")

        print(f"✅ Validation Result: {valid_count} valid samples.")
        if errors:
            print(f"❌ Found {len(errors)} errors:")
            for e in errors[:10]: # Show first 10
                print(f"   - {e}")
            return False
        return True

if __name__ == "__main__":
    # Example usage
    validator = DataValidator()
    # Create dummy data if not exists to test
    dummy_path = "data/raw/roleplay_dataset.json"
    if Path(dummy_path).exists():
        validator.validate_file(dummy_path)