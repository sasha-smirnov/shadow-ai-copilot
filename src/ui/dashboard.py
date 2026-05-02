import sys, os
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
import streamlit as st
import json
from pathlib import Path
from src.orchestration.pipeline import build_pipeline

st.set_page_config(page_title="Shadow AI Copilot | Expert Review", layout="wide")
st.title("🛡️ Expert Walkthrough Panel (EQ2/EQ3)")
st.caption("Design Science Research Artifact v1.0 | Ground-Truth vs Prototype Comparison")

@st.cache_resource
def load_resources():
    with open("data/simulated_logs.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data, build_pipeline()

dataset, app = load_resources()

case_idx = st.sidebar.slider("📂 Номер кейса", 1, len(dataset), 1)
current = dataset[case_idx - 1]

# Запуск пайплайна
result = app.invoke({
    "raw_log": current["raw_log"],
    "scenario": current.get("scenario_type", "accidental_use")
})
case_card = result["final_case"]

# 1. Отображение Ground Truth vs Prototype
st.subheader(f"🔍 {current['case_id']} | Ground Truth: `{current['expected_risk_level'].upper()}`")
col1, col2 = st.columns(2)
with col1:
    st.info(f"**📦 Metadata**\n- Tool: `{current['tool_name']}` ({current['tool_category']})\n- Status: `{current['tool_status']}`\n- Sensitivity: `{current['data_sensitivity']}`\n- Scenario: `{current['scenario_type']}`")
    st.info(f"**📜 Policy Context**\n- Policy Match: `{current['policy_match']}`\n- Matched Rule: `{current['matched_policy_rule']}`\n- Repeated Flag: `{current['repeated_behavior_flag']}`")
with col2:
    st.success(f"**🤖 Prototype Output**\n- Risk Level: `{case_card.risk_level.value}`\n- Confidence: `{case_card.confidence:.2f}`\n- Tool Detected: `{case_card.detected_tool or 'Unknown'}`\n- Data Sensitivity: `{case_card.data_sensitivity.value}`")

st.markdown(f"**🎯 Ground Truth Label:**\n> {current['ground_truth_label']}")
st.markdown(f"**💡 AI-Generated Rationale:**\n> {case_card.rationale}")

# 2. Форма экспертной оценки
with st.form("expert_eval"):
    st.subheader("👨‍💻 Expert Assessment")
    expert_risk = st.slider("1. Risk Severity (1=Low, 5=High)", 1, 5, 3)
    interpretability = st.slider("2. Rationale Interpretability (1=Unclear, 5=Crystal Clear)", 1, 5, 4)
    comment = st.text_area("3. Qualitative Feedback / Borderline Notes")
    submit = st.form_submit_button("💾 Save Evaluation")

    if submit:
        rec = {
            "case_id": current["case_id"],
            "ground_truth_risk": current["expected_risk_level"],
            "prototype_risk": case_card.risk_level.value,
            "expert_risk_1to5": expert_risk,
            "interpretability_1to5": interpretability,
            "comment": comment,
            "scenario": current["scenario_type"],
            "tool_status": current["tool_status"],
            "data_sensitivity": current["data_sensitivity"]
        }
        Path("data/expert_reviews.json").parent.mkdir(exist_ok=True)
        with open("data/expert_reviews.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        st.toast("✅ Оценка сохранена в data/expert_reviews.json", icon="🎉")