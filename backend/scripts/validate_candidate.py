import pandas as pd, json, joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support, average_precision_score, confusion_matrix
import numpy as np

base = Path("backend/datasets/public_benchmark")
df = pd.read_csv(base / "combined_finsec_training.csv")

train_df, test_df = train_test_split(df, test_size=0.2, stratify=df["is_fraud"], random_state=42)

le_device = LabelEncoder()
le_type = LabelEncoder()
le_user = LabelEncoder()

train_df = train_df.copy()
test_df = test_df.copy()

train_df["device_id_enc"] = le_device.fit_transform(train_df["device_id"].astype(str))
train_df["transaction_type_enc"] = le_type.fit_transform(train_df["transaction_type"].astype(str))
train_df["user_id_enc"] = le_user.fit_transform(train_df["user_id"].astype(str))
train_df["log_amount"] = np.log1p(train_df["amount"])

# Safe transform for test
def transform_safe(le, vals):
    mapping = {cls:i for i,cls in enumerate(le.classes_)}
    return [mapping.get(str(v), -1) for v in vals]

test_df["device_id_enc"] = transform_safe(le_device, test_df["device_id"])
test_df["transaction_type_enc"] = transform_safe(le_type, test_df["transaction_type"])
test_df["user_id_enc"] = transform_safe(le_user, test_df["user_id"])
test_df["log_amount"] = np.log1p(test_df["amount"])

X_test = test_df[["amount","log_amount","device_id_enc","transaction_type_enc","user_id_enc"]]
y_test = test_df["is_fraud"]

clf = joblib.load("backend/artifacts/production/model.joblib")
proba = clf.predict_proba(X_test)[:,1]

roc = roc_auc_score(y_test, proba)
pr_auc = average_precision_score(y_test, proba)

print(f"CORRECTED EVAL (no leakage) - 7.2M model 69519e58f5bc")
print(f"ROC-AUC: {roc:.4f}")
print(f"PR-AUC: {pr_auc:.4f}")
print(f"Prevalence: {y_test.mean():.4%}")
print("\nThr | Prec | Rec | F1 | Alerts | AlertRate | TP | FP | FN")
for thr in [0.5,0.7,0.8,0.9,0.92,0.95,0.99]:
    pred = (proba >= thr).astype(int)
    p,r,f,_ = precision_recall_fscore_support(y_test, pred, average='binary', zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    alerts = int(tp+fp)
    print(f"{thr:.2f} | {p:.4f} | {r:.4f} | {f:.4f} | {alerts} | {alerts/len(y_test):.4%} | {tp} | {fp} | {fn}")
