# scripts/evaluate_metrics.py
import json
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, cohen_kappa_score
from scipy.stats import pearsonr
import os
import sys

def load_reviews(path="data/expert_reviews.json"):
    """Загружает JSONL файл в DataFrame."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Файл не найден: {path}")
    reviews = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                reviews.append(json.loads(line))
    return pd.DataFrame(reviews)

def calculate_metrics_for_expert(df_expert: pd.DataFrame, expert_name: str):
    """Рассчитывает EQ1-EQ3 для одного эксперта."""
    print(f"\n{'='*60}")
    print(f"👤 EXPERT: {expert_name} (N={len(df_expert)} кейсов)")
    print(f"{'='*60}")

    # 🟦 EQ1: Detection Metrics (Prototype vs Ground Truth)
    df_expert["proto_detected"] = df_expert["prototype_risk"].isin(["high", "medium"]).astype(int)
    df_expert["gt_flag"] = df_expert["ground_truth_risk"].isin(["high", "medium"]).astype(int)
    
    prec, rec, f1, _ = precision_recall_fscore_support(
        df_expert["gt_flag"], df_expert["proto_detected"], average="binary", zero_division=0
    )
    print(f"📊 EQ1: Precision: {prec:.3f} | Recall: {rec:.3f} | F1-Score: {f1:.3f}")

    # 🟨 EQ2: Expert Alignment (Prototype vs Expert Judgment)
    # Маппинг прототипа: low=1, medium=2, high=3
    df_expert["proto_mapped"] = df_expert["prototype_risk"].map({"low": 1, "medium": 2, "high": 3})
    
    # Маппинг эксперта (1-5 → 1-3): 1-2→low, 3→med, 4-5→high (согласно п. 5.3)
    def map_1to5(score):
        if score <= 2: return 1
        elif score == 3: return 2
        else: return 3
    df_expert["expert_mapped"] = df_expert["expert_risk_1to5"].apply(map_1to5)

    cm = confusion_matrix(df_expert["expert_mapped"], df_expert["proto_mapped"], labels=[1, 2, 3])
    kappa = cohen_kappa_score(df_expert["expert_mapped"], df_expert["proto_mapped"])
    try:
        corr, p_val = pearsonr(df_expert["expert_mapped"], df_expert["proto_mapped"])
    except Exception:
        corr, p_val = 0.0, 1.0

    print(f"🤝 EQ2: Confusion Matrix (Rows=Expert, Cols=Prototype):\n{cm}")
    print(f"🤝 EQ2: Cohen's Kappa: {kappa:.3f} (≥0.60 = substantial agreement)")
    print(f"🤝 EQ2: Pearson Correlation: {corr:.3f} (p={p_val:.4f})")

    # 🟩 EQ3: Interpretability & Qualitative Feedback
    avg_interp = df_expert["interpretability_1to5"].mean()
    print(f"🧠 EQ3: Avg Rationale Interpretability: {avg_interp:.2f} / 5.0")

    comments = df_expert[df_expert["comment"].notna()]["comment"].tolist()
    if comments:
        print(f"📝 EQ3: Qualitative Comments ({len(comments)}):")
        for c in comments:
            print(f"  • {c}")

def main():
    # Поддержка аргумента CLI или дефолтного пути
    path = sys.argv[1] if len(sys.argv) > 1 else "data/expert_reviews.json"
    print(f"📂 Loading reviews from: {path}")
    df = load_reviews(path)

    if df.empty:
        print("❌ Файл пуст. Сначала проведите экспертные сессии через Streamlit.")
        return

    # Автоматическая группировка по expert_id
    if "expert_id" in df.columns:
        grouped = df.groupby("expert_id")
        print(f"✅ Обнаружено {len(grouped)} эксперта(ов). Считаем метрики изолированно...\n")
        for exp_id, group_df in grouped:
            calculate_metrics_for_expert(group_df, exp_id)
    else:
        print("⚠️ Поле 'expert_id' не найдено. Считаем общие метрики по всем строкам.\n")
        calculate_metrics_for_expert(df, "ALL_EXPERTS")

    print(f"\n{'='*60}")
    print("✅ Evaluation complete. Results ready for Chapter 5.4 tables & figures.")

if __name__ == "__main__":
    main()