import streamlit as st
import pandas as pd
import json
from pathlib import Path
from src.orchestration.pipeline import build_pipeline

st.set_page_config(page_title="Shadow AI Copilot | Expert Review", layout="wide")
st.title("🛡️ Expert Walkthrough Panel (EQ2/EQ3)")
st.caption("Design Science Research Artifact v1.0 | Blind Evaluation Mode")

# 1. Загрузка датасета и пайплайна
@st.cache_resource
def load_resources():
    with open("data/simulated_logs.json", "r") as f:
        data = json.load(f)
    return data, build_pipeline()

dataset, app = load_resources()

# 2. Сайдбар навигации
case_idx = st.sidebar.slider("📂 Номер кейса", 1, len(dataset), 1)
current = dataset[case_idx - 1]

# 3. Запуск пайплайна для текущего события
result = app.invoke({"raw_log": current["raw_log"], "scenario": current["ground_truth"]["scenario"]})
case_card = result["final_case"]

# 4. Отображение карточки
st.subheader(f"🔍 Case {case_card.case_id} | GT: {current['ground_truth']['true_risk']}")
col1, col2 = st.columns(2)
with col1:
    st.info(f"**Tool:** {case_card.detected_tool or 'Unknown'} ({case_card.tool_category})")
    st.info(f"**Status:** `{case_card.tool_status}` | **Policy:** `{case_card.policy_rule_match}`")
with col2:
    st.info(f"**Sensitivity:** `{case_card.data_sensitivity}` | **Scenario:** `{case_card.scenario_type}`")
    st.info(f"**Proto Risk:** 🟢`{case_card.risk_level}` (Conf: `{case_card.confidence:.2f}`)")

st.markdown("**📜 AI-Generated Rationale:**")
st.success(case_card.rationale)

# 5. Сбор экспертных оценок (Blind Evaluation)
with st.form("expert_eval"):
    st.subheader("👨‍💻 Expert Assessment")
    expert_risk = st.slider("1. Risk Severity (1=Low, 5=High)", 1, 5, 3)
    interpretability = st.slider("2. Rationale Interpretability (1=Unclear, 5=Crystal Clear)", 1, 5, 4)
    comment = st.text_area("3. Qualitative Feedback / Edge Case Notes")
    submit = st.form_submit_button("💾 Save Evaluation")

    if submit:
        rec = {
            "case_id": case_card.case_id,
            "gt_risk": current["ground_truth"]["true_risk"],
            "proto_risk": case_card.risk_level,
            "expert_risk_1to5": expert_risk,
            "interpretability_1to5": interpretability,
            "comment": comment
        }
        Path("data/expert_reviews.json").parent.mkdir(exist_ok=True)
        with open("data/expert_reviews.json", "a") as f:
            f.write(json.dumps(rec) + "\n")
        st.toast("✅ Оценка сохранена", icon="🎉")