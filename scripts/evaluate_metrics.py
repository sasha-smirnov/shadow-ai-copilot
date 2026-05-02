import json
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, cohen_kappa_score
from scipy.stats import pearsonr
import os

def load_reviews(path="data/expert_reviews.json"):
    if not os.path.exists(path):
        raise FileNotFoundError("No expert reviews found. Run Streamlit UI first.")
    return pd.read_json(path, lines=True)

def eq1_detection_metrics(reviews):
    # Маппинг: medium/high = 1 (detected), low = 0
    reviews["proto_detected"] = reviews["prototype_risk"].isin(["high", "medium"]).astype(int)
    reviews["gt_flag"] = reviews["ground_truth_risk"].isin(["high", "medium"]).astype(int)
    prec, rec, f1, _ = precision_recall_fscore_support(reviews["gt_flag"], reviews["proto_detected"], average="binary", zero_division=0)
    print("\n📊 EQ1: Detection Metrics (Prototype vs Ground Truth)")
    print(f"Precision: {prec:.3f} | Recall: {rec:.3f} | F1-Score: {f1:.3f}")

def eq2_expert_alignment(reviews):
    # Маппинг 1-5 → 1-3 для сравнения с прототипом
    reviews["proto_mapped"] = reviews["prototype_risk"].map({"low":1, "medium":2, "high":3})
    reviews["expert_mapped"] = pd.cut(reviews["expert_risk_1to5"], bins=[0,2,3,5], labels=[1,2,3]).astype(int)
    
    cm = confusion_matrix(reviews["expert_mapped"], reviews["proto_mapped"], labels=[1,2,3])
    kappa = cohen_kappa_score(reviews["expert_mapped"], reviews["proto_mapped"])
    corr, p_val = pearsonr(reviews["expert_mapped"], reviews["proto_mapped"])
    
    print("\n🤝 EQ2: Expert Alignment")
    print(f"Confusion Matrix:\n{cm}")
    print(f"Cohen's Kappa: {kappa:.3f} (≥0.60 = substantial agreement)")
    print(f"Pearson Correlation: {corr:.3f} (p={p_val:.4f})")

def eq3_interpretability(reviews):
    avg_interp = reviews["interpretability_1to5"].mean()
    print(f"\n🧠 EQ3: Rationale Interpretability")
    print(f"Average Score: {avg_interp:.2f} / 5.0 (Target: ≥4.0)")
    print(f"Qualitative Comments: {reviews['comment'].dropna().shape[0]} submitted")
    
    if reviews["comment"].dropna().shape[0] > 0:
        print("\n📝 Thematic Notes (for Ch. 5.4 & 6.5):")
        for idx, row in reviews[reviews["comment"].notna()].iterrows():
            print(f"- {row['case_id']}: {row['comment']}")

if __name__ == "__main__":
    try:
        df = load_reviews()
        eq1_detection_metrics(df)
        eq2_expert_alignment(df)
        eq3_interpretability(df)
        print("\n✅ Metrics ready for Chapter 5.4 tables & figures.")
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")