# RETRAIN CORRECTLY - no leakage
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as XGB, joblib, json, hashlib
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

base = Path("backend/datasets/public_benchmark")
df = pd.read_csv(base / "combined_finsec_training.csv")
train_df, test_df = train_test_split(df, test_size=0.2, stratify=df["is_fraud"], random_state=42)

le_device = LabelEncoder()
le_type = LabelEncoder()
le_user = LabelEncoder()

train_df = train_df.copy()
train_df["device_id_enc"] = le_device.fit_transform(train_df["device_id"].astype(str))
train_df["transaction_type_enc"] = le_type.fit_transform(train_df["transaction_type"].astype(str))
train_df["user_id_enc"] = le_user.fit_transform(train_df["user_id"].astype(str))
train_df["log_amount"] = np.log1p(train_df["amount"])

test_df = test_df.copy()
mapping_d = {c:i for i,c in enumerate(le_device.classes_)}
mapping_t = {c:i for i,c in enumerate(le_type.classes_)}
mapping_u = {c:i for i,c in enumerate(le_user.classes_)}
test_df["device_id_enc"] = [mapping_d.get(str(v), -1) for v in test_df["device_id"]]
test_df["transaction_type_enc"] = [mapping_t.get(str(v), -1) for v in test_df["transaction_type"]]
test_df["user_id_enc"] = [mapping_u.get(str(v), -1) for v in test_df["user_id"]]
test_df["log_amount"] = np.log1p(test_df["amount"])

X_train = train_df[["amount","log_amount","device_id_enc","transaction_type_enc","user_id_enc"]]
y_train = train_df["is_fraud"]
X_test = test_df[["amount","log_amount","device_id_enc","transaction_type_enc","user_id_enc"]]
y_test = test_df["is_fraud"]

scale = (y_train==0).sum() / (y_train==1).sum()
print(f"Training CORRECT 7.2M scale={scale:.1f} on {len(X_train):,} rows")

clf = XGB.XGBClassifier(n_estimators=600, max_depth=10, learning_rate=0.05, scale_pos_weight=scale, subsample=0.8, colsample_bytree=0.8, eval_metric="logloss", random_state=42, n_jobs=-1)
clf.fit(X_train, y_train)

proba = clf.predict_proba(X_test)[:,1]
roc = roc_auc_score(y_test, proba)
pr = average_precision_score(y_test, proba)
print(f"CORRECT MODEL ROC={roc:.4f} PR-AUC={pr:.4f}")

version_id = hashlib.sha256(f"correct_{len(df)}_{roc}".encode()).hexdigest()[:12]
art_dir = Path(f"backend/artifacts/versions/model-{version_id}")
art_dir.mkdir(parents=True, exist_ok=True)
joblib.dump(clf, art_dir/"model.joblib")
joblib.dump({"device_le": le_device, "type_le": le_type, "user_le": le_user}, art_dir/"encoders.joblib")
(art_dir/"meta.json").write_text(json.dumps({"version": version_id, "record_count": len(df), "fraud_count": int(df["is_fraud"].sum()), "metrics": {"roc_auc": float(roc), "pr_auc": float(pr)}, "train_method": "encoders fit only on train, no leakage", "threshold_analysis": "pending"}, indent=2))
print(f"DONE CORRECT version_id={version_id}")
