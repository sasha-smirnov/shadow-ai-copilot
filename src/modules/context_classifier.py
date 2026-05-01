from src.models.case import DataSensitivity

class DataContextClassifier:
    def __init__(self):
        # Ключевые маркеры для эвристической классификации
        self.confidential_keywords = ["pii", "confidential", "financial", "source_code", "legal", "passport", "salary", "contract"]
        self.internal_keywords = ["internal", "restricted", "business", "project", "draft", "report"]

    def classify(self, dlp_tag: str = "", volume_kb: int = 0, user_role: str = "") -> DataSensitivity:
        tag_lower = dlp_tag.lower()

        # 1. Приоритет: явные маркеры конфиденциальности
        if any(kw in tag_lower for kw in self.confidential_keywords):
            return DataSensitivity.confidential

        # 2. Внутренние данные или аномально высокий объём передачи (>500 КБ)
        if any(kw in tag_lower for kw in self.internal_keywords) or volume_kb > 500:
            return DataSensitivity.internal

        # 3. По умолчанию: публичный контекст
        return DataSensitivity.public