from pathlib import Path
import pandas as pd, hashlib, json, sys
sys.path.insert(0, ".")
print("=== FinSecAI Bootstrap - FINAL FIX underscore NO DeviceInfo ===")

base = Path("backend/datasets/public_benchmark")
ieee_path = base / "ieee_fraud" if (base / "ieee_fraud").exists() else base / "ieee-fraud"
paysim_file = base / "paysim" / "PS_20174392719_1491204439457_log.csv"
cc_dir = base / "creditcard"
cc_path = cc_dir / "finsec_compatible.csv"

frames = []

if cc_path.exists():
    cc = pd.read_csv(cc_path)
    frames.append(cc)
    print(f"CreditCard: {len(cc):,}")

if (ieee_path / "train_transaction.csv").exists():
    # Load without DeviceInfo, it is in identity file
    cols = ['TransactionID','isFraud','TransactionAmt','ProductCD','card1']
    trans = pd.read_csv(ieee_path / "train_transaction.csv", usecols=cols)
    ieee_finsec = pd.DataFrame()
    ieee_finsec["user_id"] = trans["card1"].astype(str).apply(lambda x: f"user_{x}")
    ieee_finsec["amount"] = trans["TransactionAmt"]
    ieee_finsec["transaction_type"] = trans["ProductCD"].map({'W':'PAYMENT','C':'TRANSFER','R':'TRANSFER','S':'PAYMENT','H':'PAYMENT'}).fillna('PAYMENT')
    ieee_finsec["device_id"] = "ieee_device_" + trans["TransactionID"].astype(str) # placeholder
    ieee_finsec["is_fraud"] = trans["isFraud"]
    frames.append(ieee_finsec)
    print(f"IEEE: {len(ieee_finsec):,} rows, {ieee_finsec['is_fraud'].sum():,} frauds")

if paysim_file.exists():
    pay = pd.read_csv(paysim_file)
    pay_finsec = pd.DataFrame()
    pay_finsec["user_id"] = pay["nameOrig"].astype(str)
    pay_finsec["amount"] = pay["amount"]
    pay_finsec["transaction_type"] = pay["type"]
    pay_finsec["device_id"] = pay["nameDest"].astype(str)
    pay_finsec["is_fraud"] = pay["isFraud"]
    frames.append(pay_finsec)
    print(f"PaySim FULL: {len(pay_finsec):,} rows, {pay_finsec['is_fraud'].sum():,} frauds")

full_df = pd.concat(frames, ignore_index=True)
print(f"TOTAL MERGED: {len(full_df):,} rows, {full_df['is_fraud'].sum():,} frauds")
full_df.to_csv(base / "combined_finsec_training.csv", index=False)

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as XGB
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
import joblib, numpy as np

le_device = LabelEncoder()
le_type = LabelEncoder()
le_user = LabelEncoder()
full_df["device_id_enc"] = le_device.fit_transform(full_df["device_id"].astype(str))
full_df["transaction_type_enc"] = le_type.fit_transform(full_df["transaction_type"].astype(str))
full_df["user_id_enc"] = le_user.fit_transform(full_df["user_id"].astype(str))
full_df["log_amount"] = np.log1p(full_df["amount"])

X = full_df[["amount","log_amount","device_id_enc","transaction_type_enc","user_id_enc"]]
y = full_df["is_fraud"]
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,stratify=y,random_state=42)

scale = (y_train==0).sum() / max(1,(y_train==1).sum())
print(f"Training XGBoost scale_pos_weight={scale:.1f} on {len(X_train):,} rows...")
clf = XGB.XGBClassifier(n_estimators=400,max_depth=8,learning_rate=0.05,scale_pos_weight=scale,subsample=0.8,colsample_bytree=0.8,eval_metric="logloss",random_state=42, n_jobs=-1)
clf.fit(X_train,y_train)

proba = clf.predict_proba(X_test)[:,1]
print("\nThreshold tuning:")
for thr in [0.5,0.7,0.8,0.9,0.95]:
    pred = (proba >= thr).astype(int)
    p,r,f,_ = precision_recall_fscore_support(y_test,pred,average='binary',zero_division=0)
    print(f"thr={thr:.2f} -> P={p:.4f} R={r:.4f} F1={f:.4f}")

pred05 = (proba >= 0.5).astype(int)
p,r,f,_ = precision_recall_fscore_support(y_test,pred05,average='binary',zero_division=0)
roc = roc_auc_score(y_test,proba)
print(f"\nFINAL @0.5: ROC_AUC={roc:.4f} P={p:.4f} R={r:.4f} F1={f:.4f}")

version_id = hashlib.sha256(f"combined_{len(full_df)}_{roc}".encode()).hexdigest()[:12]
art_dir = Path(f"backend/artifacts/versions/model-{version_id}")
art_dir.mkdir(parents=True, exist_ok=True)
joblib.dump(clf, art_dir/"model.joblib")
joblib.dump({"device_le": le_device, "type_le": le_type, "user_le": le_user}, art_dir/"encoders.joblib")
(art_dir/"meta.json").write_text(json.dumps({
    "version": version_id,
    "record_count": len(full_df),
    "fraud_count": int(full_df["is_fraud"].sum()),
    "metrics": {"roc_auc": float(roc), "precision": float(p), "recall": float(r), "f1": float(f)},
    "feature_columns": list(X.columns)
}, indent=2))
print(f"\nDONE version_id={version_id}")
