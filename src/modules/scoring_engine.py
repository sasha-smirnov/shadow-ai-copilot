import os
from src.models.case import RiskLevel, ToolStatus, DataSensitivity, ShadowAIScenario
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

class RiskScoringEngine:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        else:
            self.llm = None  # Fallback без ключа

    def score(self, tool_status: ToolStatus, sensitivity: DataSensitivity, policy_violated: bool, scenario: str) -> tuple[RiskLevel, float, str]:
        # 1. Rule-based scoring (воспроизводимое ядро)
        score = 0
        if tool_status == ToolStatus.prohibited: score += 3
        elif tool_status == ToolStatus.unknown: score += 2
        elif tool_status == ToolStatus.under_review: score += 1

        if sensitivity == DataSensitivity.confidential: score += 3
        elif sensitivity == DataSensitivity.internal: score += 1

        if policy_violated: score += 2
        if scenario == ShadowAIScenario.normalized_practice.value: score += 1

        # 2. Маппинг в уровни риска
        if score >= 5: level, conf = RiskLevel.high, 0.9
        elif score >= 3: level, conf = RiskLevel.medium, 0.75
        else: level, conf = RiskLevel.low, 0.85

        # 3. Генерация rationale
        rationale = self._generate_rationale(tool_status, sensitivity, policy_violated, scenario, score)
        return level, conf, rationale

    def _generate_rationale(self, status, sensitivity, violated, scenario, score):
        # Если LLM недоступен → возвращаем детерминированную строку
        if not self.llm:
            return f"Risk score: {score}. Factors: tool={status.value}, data={sensitivity.value}, policy_breach={violated}."
        
        prompt = (
            f"Act as an InfoSec analyst. Based on these facts: "
            f"tool_status='{status.value}', data_sensitivity='{sensitivity.value}', "
            f"policy_violated={violated}, scenario='{scenario}', risk_score={score}. "
            f"Write a 2-3 sentence rationale for a risk case card. "
            f"Be factual, policy-grounded, and avoid speculation. Output only the rationale."
        )
        try:
            return self.llm.invoke(prompt).content.strip()
        except Exception:
            return f"Risk score: {score}. Factors: tool={status.value}, data={sensitivity.value}, policy_breach={violated}."