from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

class LogProcessor:
    def __init__(self, dedup_window_minutes: int = 30):
        self.window = timedelta(minutes=dedup_window_minutes)

    def normalize(self, raw_log: Dict) -> Dict:
        """Приводит сырой лог к единому машиночитаемому формату."""
        return {
            "timestamp": raw_log.get("ts", raw_log.get("timestamp")),
            "user_id": raw_log.get("user", raw_log.get("user_id")),
            "domain": raw_log.get("dst", raw_log.get("domain", "")).lower(),
            "volume_kb": raw_log.get("bytes_sent", 0) // 1024,
            "dlp_tag": raw_log.get("dlp_classification", ""),
            "source": raw_log.get("source_type", "proxy")
        }

    def deduplicate(self, events: List[Dict]) -> List[Dict]:
        """
        Группирует события по пользователю + домену.
        Оставляет только первое событие в окне self.window.
        """
        seen = {}  # ключ -> timestamp последнего события
        unique_events = []
        
        for evt in events:
            key = f"{evt['user_id']}|{evt['domain']}"
            ts = datetime.fromisoformat(evt["timestamp"])
            
            if key not in seen:
                seen[key] = ts
                unique_events.append(evt)
            elif ts - seen[key] > self.window:
                seen[key] = ts
                unique_events.append(evt)
                
        return unique_events