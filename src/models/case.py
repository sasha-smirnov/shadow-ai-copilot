# src/models/case.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

# 1. Категории AI-инструментов (п. 4.1: 4 фиксированных измерения)
class ToolCategory(str, Enum):
    generative_text = "generative_text"
    code_assistant = "code_assistant"
    image_generation = "image_generation"
    analytical_assistant = "analytical_assistant"

# 2. Уровни чувствительности данных (п. 4.1: public/internal/confidential)
class DataSensitivity(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"

# 3. Статус инструмента в реестре
class ToolStatus(str, Enum):
    approved = "approved"
    prohibited = "prohibited"
    unknown = "unknown"
    under_review = "under_review"

# 4. Сценарии Shadow AI (п. 4.1)
class ShadowAIScenario(str, Enum):
    accidental_use = "accidental_use"
    deliberate_violation = "deliberate_violation"
    tool_testing = "tool_testing"
    normalized_practice = "normalized_practice"

# 5. Уровни риска
class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

# 6. Основная карточка кейса (Audit-ready output, п. 3.1)
class ShadowAICase(BaseModel):
    case_id: str = Field(..., description="Уникальный ID инцидента")
    source_event_type: str = Field(..., description="proxy_log | dlp_alert | siem_correlation")
    timestamp: str = Field(..., description="ISO 8601 время события")
    user_id: str = Field(..., description="ID сотрудника")
    
    detected_tool: Optional[str] = None
    tool_category: Optional[ToolCategory] = None
    tool_status: ToolStatus = ToolStatus.unknown
    
    data_sensitivity: DataSensitivity = DataSensitivity.public
    scenario_type: Optional[ShadowAIScenario] = None
    
    policy_rule_match: str = Field(..., description="Конкретное нарушенное/соответствующее правило")
    risk_level: RiskLevel
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность классификации [0,1]")
    rationale: str = Field(..., description="Объяснимое обоснование для аналитика")
    
    group_key: Optional[str] = None
    analyst_comment: Optional[str] = None
    status: Literal["new", "reviewed", "escalated"] = "new"