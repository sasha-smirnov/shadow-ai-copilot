import json
from typing import Tuple, Optional

class ToolMatcher:
    def __init__(self, registry_path: str = "config/ai_tool_registry.json"):
        """Загружает реестр AI-инструментов из JSON-конфига."""
        with open(registry_path, "r", encoding="utf-8") as f:
            self.registry = json.load(f)

    def match(self, domain: str) -> Tuple[Optional[str], str, str]:
        """
        Сопоставляет домен с реестром.
        Возвращает кортеж: (tool_name, tool_category, tool_status)
        Если домена нет в реестре → возвращает (None, "unknown", "unknown")
        """
        domain = domain.strip().lower()
        if domain in self.registry:
            entry = self.registry[domain]
            return entry.get("name"), entry.get("category", "unknown"), entry.get("status", "unknown")
        return None, "unknown", "unknown"