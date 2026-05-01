import json
import random
from datetime import datetime, timedelta

random.seed(42)  # Фиксируем seed для DSR-воспроизводимости

TOOLS = {
    "generative_text": ["chat.openai.com", "api.openai.com", "claude.ai"],
    "code_assistant": ["copilot.github.com", "cursor.sh"],
    "image_generation": ["midjourney.com", "leonardo.ai"],
    "analytical_assistant": ["notebooklm.google.com", "perplexity.ai"]
}

SCENARIOS = ["accidental_use", "deliberate_violation", "tool_testing", "normalized_practice"]
SENSITIVITIES = ["public", "internal", "confidential"]
DLP_TAGS = {
    "public": ["web_traffic", "general_browsing"],
    "internal": ["draft_report", "business_internal", "project_specs"],
    "confidential": ["pii_detected", "source_code", "financial_data", "legal_contract"]
}

def generate_event(idx):
    cat = random.choice(list(TOOLS.keys()))
    domain = random.choice(TOOLS[cat])
    sens = random.choice(SENSITIVITIES)
    scenario = random.choice(SCENARIOS)
    dlp = random.choice(DLP_TAGS[sens])
    
    # Генерируем временные метки с разбросом
    base_time = datetime(2026, 5, 1, 9, 0, 0)
    ts = (base_time + timedelta(hours=random.uniform(0, 48), minutes=random.randint(0, 59))).isoformat()
    
    # Ground-truth логика для оценки (упрощённая версия scoring для датасета)
    is_violation = (domain in ["midjourney.com", "leonardo.ai"]) or (sens == "confidential" and scenario == "deliberate_violation")
    true_risk = "high" if is_violation else ("medium" if sens == "internal" or scenario == "tool_testing" else "low")
    
    return {
        "id": f"EVT-{idx:03d}",
        "raw_log": {
            "ts": ts,
            "user": f"emp_{random.randint(1000, 9999)}",
            "dst": domain,
            "bytes_sent": random.randint(100, 2_000_000),
            "dlp_classification": dlp,
            "source_type": random.choice(["proxy_log", "casb_alert"])
        },
        "ground_truth": {
            "tool_category": cat,
            "sensitivity": sens,
            "scenario": scenario,
            "true_risk": true_risk
        }
    }

dataset = [generate_event(i) for i in range(1, 51)]  # 50 событий

with open("data/simulated_logs.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"✅ Generated {len(dataset)} events with ground-truth labels.")