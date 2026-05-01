import pytest
from src.modules.tool_matcher import ToolMatcher
from src.modules.log_processor import LogProcessor

@pytest.fixture
def matcher():
    return ToolMatcher("config/ai_tool_registry.json")

@pytest.fixture
def processor():
    return LogProcessor(dedup_window_minutes=30)

def test_tool_matcher_known_domain(matcher):
    name, cat, status = matcher.match("copilot.github.com")
    assert name == "GitHub Copilot"
    assert cat == "code_assistant"
    assert status == "approved"

def test_tool_matcher_unknown_domain(matcher):
    name, cat, status = matcher.match("random-site.com")
    assert name is None
    assert cat == "unknown"
    assert status == "unknown"

def test_log_processor_deduplication(processor):
    raw = [
        {"ts": "2026-05-02T10:00:00", "user": "u1", "dst": "api.openai.com", "bytes_sent": 1000, "dlp_classification": "internal"},
        {"ts": "2026-05-02T10:05:00", "user": "u1", "dst": "api.openai.com", "bytes_sent": 2000, "dlp_classification": "confidential"},
        {"ts": "2026-05-02T10:08:00", "user": "u1", "dst": "api.openai.com", "bytes_sent": 1500, "dlp_classification": "public"}
    ]
    normalized = [processor.normalize(r) for r in raw]
    deduped = processor.deduplicate(normalized)
    assert len(deduped) == 1  # все в одном 30-минутном окне
    assert deduped[0]["dlp_tag"] == "internal"  # берётся первое событие