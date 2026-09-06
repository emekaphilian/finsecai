import joblib, pandas as pd, json
from pathlib import Path
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
import sys
sys.path.insert(0, ".")
# Load last model
version_id = "ec3271ed184f"
art_dir = Path(f"backend/artifacts/versions/model-{version_id}")
clf = joblib.load(art_dir/"model.joblib")

# Load test split again for tuning
full_df = pd.read_csv("backend/datasets/public_benchmark/combined_finsec_training.csv")
# Recreate features quickly
from sklearn.preprocessing import LabelEncoder
import numpy as np
le_device = LabelEncoder()
le_type = LabelEncoder()
le_user = LabelEncoder()
full_df["device_id_enc"] = le_device.fit_transform(full_df["device_id"].astype(str))
full_df["transaction_type_enc"] = le_type.fit_transform(full_df["transaction_type"].astype(str))
full_df["user_id_enc"] = le_user.fit_transform(full_df["user_id"].astype(str))
full_df["log_amount"] = np.log1p(full_df["amount"])
X = full_df[["amount","log_amount","device_id_enc","transaction_type_enc","user_id_enc"]]
y = full_df["is_fraud"]
from sklearn.model_selection import train_test_split
_, X_test, _, y_test = train_test_split(X,y,test_size=0.2,stratify=y,random_state=42)

proba = clf.predict_proba(X_test)[:,1]
print("Threshold tuning on full 6.6M model:")
for thr in [0.5,0.7,0.8,0.85,0.9,0.95,0.98]:
    pred = (proba >= thr).astype(int)
    p,r,f,_ = precision_recall_fscore_support(y_test,pred,average='binary',zero_division=0)
    print(f"thr={thr:.2f} -> Precision={p:.4f} Recall={r:.4f} F1={f:.4f}")
