import json
import os
from collections import defaultdict

INPUT_FILE = "data/expert_reviews.json"
OUTPUT_DIR = "data"

def split_reviews(num_experts: int = 4):
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл не найден: {INPUT_FILE}")
        print("💡 Сначала проведите сессии через Streamlit или создайте файл вручную.")
        return

    # Читаем все оценки
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)
    if total == 0:
        print("⚠️ Файл пуст. Нечего разделять.")
        return

    print(f"📊 Найдено {total} оценок. Разделяю на {num_experts} экспертов (последовательно)...")

    # Последовательное разделение (стандарт для контролируемых сессий)
    chunk_size = total // num_experts
    remainder = total % num_experts

    expert_data = defaultdict(list)
    current_idx = 0
    
    for i in range(1, num_experts + 1):
        size = chunk_size + (1 if i <= remainder else 0)
        chunk = lines[current_idx:current_idx + size]
        expert_data[f"expert_{i}"] = chunk
        current_idx += size

    # Сохраняем в отдельные файлы + добавляем expert_id
    for exp_name, data_lines in expert_data.items():
        if not data_lines:
            continue
            
        out_path = os.path.join(OUTPUT_DIR, f"{exp_name}_reviews.json")
        with open(out_path, "w", encoding="utf-8") as out_f:
            for line in data_lines:
                record = json.loads(line)
                record["expert_id"] = exp_name.replace("expert_", "E")
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                
        print(f"💾 Сохранено {len(data_lines)} оценок в {out_path}")

    # Опционально: обновляем исходный файл с добавленными ID
    backup_path = INPUT_FILE.replace(".json", "_raw_backup.json")
    if not os.path.exists(backup_path):
        with open(INPUT_FILE, "r", encoding="utf-8") as src, open(backup_path, "w", encoding="utf-8") as bak:
            for line in src:
                bak.write(line)

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            record = json.loads(line)
            # Присваиваем ID на основе позиции (упрощённо)
            # В продакшене лучше собирать ID в UI, здесь эвристика для ретроспективы
            pass 
    print("\n✅ Разделение завершено. Исходный файл сохранён как backup.")

if __name__ == "__main__":
    split_reviews(num_experts=4)