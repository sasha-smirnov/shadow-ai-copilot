import json
import random
from datetime import datetime, timedelta

random.seed(42)  # DSR-воспроизводимость

# Синхронизировано с config/ai_tool_registry.json
TOOLS_REGISTRY = {
    "api.openai.com": {"name": "ChatGPT API", "category": "generative_text", "status": "under_review"},
    "chat.openai.com": {"name": "ChatGPT Web", "category": "generative_text", "status": "under_review"},
    "copilot.github.com": {"name": "GitHub Copilot", "category": "code_assistant", "status": "approved"},
    "midjourney.com": {"name": "Midjourney", "category": "image_generation", "status": "prohibited"},
    "notebooklm.google.com": {"name": "NotebookLM", "category": "analytical_assistant", "status": "approved"},
    "claude.ai": {"name": "Claude", "category": "generative_text", "status": "unknown"}
}

CATEGORIES = ["generative_text", "code_assistant", "image_generation", "analytical_assistant"]
SENSITIVITIES = ["public", "internal", "confidential"]
SCENARIOS = ["accidental_use", "deliberate_violation", "tool_testing", "normalized_practice"]
USER_ROLES = ["developer", "analyst", "manager", "support", "marketing"]
BUSINESS_UNITS = ["Engineering", "Finance", "Marketing", "HR", "Operations"]
ACCOUNT_TYPES = ["personal", "corporate_sso", "guest"]
SIGNAL_SOURCES = ["proxy_log", "dlp_alert", "siem_correlation", "casb_event"]
EVENT_TYPES = ["domain_access", "api_call", "file_upload", "prompt_submit"]

def determine_policy_violation(tool_status: str, sensitivity: str) -> bool:
    """Упрощённая логика нарушения для генерации ground truth."""
    if tool_status == "prohibited": return True
    if tool_status == "unknown" and sensitivity == "confidential": return True
    return False

def assign_ground_truth(tool_status: str, sensitivity: str, policy_violated: bool) -> tuple:
    """Rubric из текста 5.1: tool status × data sensitivity × policy relevance"""
    if tool_status in ["prohibited", "unknown"] and sensitivity == "confidential" and policy_violated:
        return "high", "High Risk: Prohibited/Unknown tool + Confidential data + Explicit policy violation"
    elif tool_status == "approved" and sensitivity in ["public", "internal"] and not policy_violated:
        return "low", "Low Risk: Approved tool + Public/Internal data + Policy compliant"
    else:
        return "medium", "Medium Risk: Mixed indicators / Gray-zone status / Partial policy mismatch"

def generate_case(idx: int, base_time: datetime, force_scenario: str = None, force_repeat: bool = False):
    domain = random.choice(list(TOOLS_REGISTRY.keys()))
    tool = TOOLS_REGISTRY[domain]
    
    sensitivity = random.choice(SENSITIVITIES)
    scenario = force_scenario if force_scenario else random.choice(SCENARIOS)
    policy_violated = determine_policy_violation(tool["status"], sensitivity)
    expected_risk, ground_truth_label = assign_ground_truth(tool["status"], sensitivity, policy_violated)
    
    # Временные метки
    if force_repeat:
        ts = (base_time + timedelta(minutes=random.randint(0, 25))).isoformat()
    else:
        ts = (base_time + timedelta(hours=random.uniform(0, 72), minutes=random.randint(0, 59))).isoformat()
        
    # raw_log для совместимости с LogProcessor
    raw_log = {
        "ts": ts,
        "user": f"emp_{random.randint(1000, 9999)}",
        "dst": domain,
        "bytes_sent": random.randint(200, 1500000),
        "dlp_classification": f"{sensitivity}_context",
        "source_type": random.choice(SIGNAL_SOURCES)
    }
    
    case = {
        "case_id": f"CASE-{idx:04d}",
        "signal_source": raw_log["source_type"],
        "event_type": random.choice(EVENT_TYPES),
        "timestamp": ts,
        "user_role": random.choice(USER_ROLES),
        "business_unit": random.choice(BUSINESS_UNITS),
        "tool_name": tool["name"],
        "tool_category": tool["category"],
        "tool_status": tool["status"],
        "account_type": random.choice(ACCOUNT_TYPES),
        "destination_domain": domain,
        "data_sensitivity": sensitivity,
        "policy_match": not policy_violated,
        "scenario_type": scenario,
        "expected_risk_level": expected_risk,
        "ground_truth_label": ground_truth_label,
        # Supporting fields (для rationale & evaluation)
        "confidence_note": "High" if expected_risk in ["low", "high"] else "Moderate",
        "repeated_behavior_flag": force_repeat,
        "matched_policy_rule": "Rule #1: Approved AI Tools" if tool["status"] == "approved" else "Rule #3: Restricted/Prohibited Tools",
        "raw_log": raw_log
    }
    return case

# 📦 Генерация сбалансированного датасета
dataset = []
base_time = datetime(2026, 5, 1, 9, 0, 0)

# 1. Базовое покрытие (40 кейсов)
for i in range(1, 41):
    dataset.append(generate_case(i, base_time))

# 2. Интенционально повторяющиеся паттерны (проверка normalized_practice)
repeat_domains = ["chat.openai.com", "midjourney.com"]
idx = 41
for domain in repeat_domains:
    tool = TOOLS_REGISTRY[domain]
    for j in range(5):
        case = generate_case(idx, base_time, force_scenario="normalized_practice", force_repeat=True)
        case["destination_domain"] = domain
        case["tool_name"] = tool["name"]
        case["tool_category"] = tool["category"]
        case["tool_status"] = tool["status"]
        # При повторении риск обычно растёт
        case["expected_risk_level"] = "high" if tool["status"] == "prohibited" else "medium"
        dataset.append(case)
        idx += 1

# 💾 Сохранение
with open("data/simulated_logs.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"✅ Сгенерировано {len(dataset)} кейсов с ground-truth разметкой (seed=42).")
print(f"📊 Распределение рисков: {[c['expected_risk_level'] for c in dataset].count('low')} low, "
      f"{[c['expected_risk_level'] for c in dataset].count('medium')} medium, "
      f"{[c['expected_risk_level'] for c in dataset].count('high')} high")