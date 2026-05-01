from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from src.models.case import ShadowAICase, ToolCategory, ToolStatus, DataSensitivity, RiskLevel, ShadowAIScenario
from src.modules.tool_matcher import ToolMatcher
from src.modules.log_processor import LogProcessor
from src.modules.context_classifier import DataContextClassifier
from src.modules.scoring_engine import RiskScoringEngine
import uuid

class PipelineState(TypedDict):
    raw_log: dict
    normalized: dict
    tool_name: Optional[str]
    tool_category: Optional[str]
    tool_status: ToolStatus
    sensitivity: DataSensitivity
    scenario: str
    policy_violated: bool
    risk_level: RiskLevel
    confidence: float
    rationale: str
    final_case: Optional[ShadowAICase]

def build_pipeline():
    matcher = ToolMatcher()
    processor = LogProcessor()
    classifier = DataContextClassifier()
    scorer = RiskScoringEngine()

    workflow = StateGraph(PipelineState)

    def normalize_node(state: PipelineState):
        norm = processor.normalize(state["raw_log"])
        return {"normalized": norm}

    def match_node(state: PipelineState):
        name, cat, status = matcher.match(state["normalized"]["domain"])
        # Безопасное преобразование статуса
        ts = ToolStatus(status) if status in ToolStatus._value2member_map_ else ToolStatus.unknown
        return {"tool_name": name, "tool_category": cat, "tool_status": ts}

    def classify_node(state: PipelineState):
        sens = classifier.classify(state["normalized"]["dlp_tag"], state["normalized"]["volume_kb"])
        return {"sensitivity": sens}

    def score_node(state: PipelineState):
        # Упрощённая логика нарушения политики для прототипа
        violated = state["tool_status"] == ToolStatus.prohibited or (
            state["tool_status"] == ToolStatus.unknown and state["sensitivity"] == DataSensitivity.confidential
        )
        level, conf, rationale = scorer.score(
            state["tool_status"], state["sensitivity"], violated, state.get("scenario", "accidental_use")
        )
        return {"risk_level": level, "confidence": conf, "rationale": rationale, "policy_violated": violated}

    def finalize_node(state: PipelineState):
        tc = ToolCategory(state["tool_category"]) if state["tool_category"] in ToolCategory._value2member_map_ else None
        st = ShadowAIScenario(state.get("scenario", "accidental_use")) if state.get("scenario") in ShadowAIScenario._value2member_map_ else ShadowAIScenario.accidental_use
        
        case = ShadowAICase(
            case_id=str(uuid.uuid4())[:8].upper(),
            source_event_type=state["normalized"]["source"],
            timestamp=state["normalized"]["timestamp"],
            user_id=state["normalized"]["user_id"],
            detected_tool=state["tool_name"],
            tool_category=tc,
            tool_status=state["tool_status"],
            data_sensitivity=state["sensitivity"],
            scenario_type=st,
            policy_rule_match="Policy v1.0 " + ("- VIOLATION" if state["policy_violated"] else "- COMPLIANT"),
            risk_level=state["risk_level"],
            confidence=state["confidence"],
            rationale=state["rationale"]
        )
        return {"final_case": case}

    # Связываем узлы
    workflow.add_node("normalize", normalize_node)
    workflow.add_node("match", match_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("score", score_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("normalize")
    workflow.add_edge("normalize", "match")
    workflow.add_edge("match", "classify")
    workflow.add_edge("classify", "score")
    workflow.add_edge("score", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()