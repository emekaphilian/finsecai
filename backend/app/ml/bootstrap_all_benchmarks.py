"""
FinSecAI Multi-Dataset Bootstrap
Downloads IEEE Fraud Detection + PaySim, merges with existing creditcard.csv,
trains an XGBoost fraud classifier, and saves a versioned model artifact.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import hashlib
import json
import sys
import shutil

sys.path.insert(0, ".")
print("=== FinSecAI Multi-Dataset Bootstrap ===")

def _ensure_creditcard_dataset() -> Path:
    dest = Path("datasets/public_benchmark/creditcard")
    dest.mkdir(parents=True, exist_ok=True)
    finsec_path = dest / "finsec_compatible.csv"
    if finsec_path.exists():
        return finsec_path

    raw_path = dest / "creditcard.csv"
    if not raw_path.exists():
        print("Downloading CreditCard public benchmark...")
        try:
            import kagglehub
            p = kagglehub.dataset_download("mlg-ulb/creditcardfraud")
            df_raw = pd.read_csv(Path(p) / "creditcard.csv")
        except Exception as exc:
            print(f"CreditCard kagglehub failed {exc}, using OpenML mirror")
            df_raw = pd.read_csv("https://files.openml.org/datasets/1597/dataset_1597_creditcardfraud.csv")
        df_raw.to_csv(raw_path, index=False)
    else:
        df_raw = pd.read_csv(raw_path)

    finsec_df = pd.DataFrame()
    finsec_df["user_id"] = [f"user_{idx % 5000}" for idx in range(len(df_raw))]
    finsec_df["amount"] = df_raw["Amount"]
    finsec_df["transaction_type"] = df_raw["Amount"].apply(lambda x: "TRANSFER" if x > 1000 else "PAYMENT")
    finsec_df["device_id"] = [f"dev_{abs(hash(v)) % 1000}" for v in df_raw["V1"]]
    finsec_df["is_fraud"] = df_raw["Class"]
    finsec_df.to_csv(finsec_path, index=False)
    return finsec_path


# ----------------------------------------------------------------------
# 1. IEEE FRAUD DETECTION - 590k rows, real device_id / transaction_type
#    NOTE: This is a Kaggle *competition*, not a plain dataset, so it
#    requires: (a) accepted competition rules on kaggle.com, and
#    (b) kagglehub.competition_download(), not dataset_download("c/...").
# ----------------------------------------------------------------------
ieee_path = Path("datasets/public_benchmark/ieee-fraud")
ieee_path.mkdir(parents=True, exist_ok=True)

ieee_transaction = ieee_path / "train_transaction.csv"
if not ieee_transaction.exists():
    print("Downloading IEEE Fraud Detection (590k rows)...")
    try:
        import kagglehub
        p = Path(kagglehub.competition_download("ieee-fraud-detection"))
        print(f"Downloaded to {p}")
        for f in p.glob("*.csv"):
            shutil.copy(f, ieee_path / f.name)
            print(f"Copied {f.name}")
    except Exception as e:
        print(f"IEEE download failed: {e}")
        print("Checklist if this still fails:")
        print("  1. Rules accepted at https://www.kaggle.com/c/ieee-fraud-detection/rules")
        print("  2. kaggle.json present at ~/.kaggle/kaggle.json (or KAGGLE_USERNAME/KAGGLE_KEY set)")
        print("  3. Manual fallback: download train_transaction.csv / train_identity.csv")
        print("     from the competition Data tab and place them in:")
        print(f"     {ieee_path.resolve()}")
        print("Skipping IEEE dataset for this run and continuing with the available sources.")
        ieee_transaction = None
else:
    print("IEEE already exists")

# ----------------------------------------------------------------------
# 2. PaySim - synthetic mobile money transactions
# ----------------------------------------------------------------------
paysim_path = Path("datasets/public_benchmark/paysim")
paysim_path.mkdir(parents=True, exist_ok=True)
paysim_file = paysim_path / "PS_20174392719_1491204439457_log.csv"

if not paysim_file.exists():
    print("Downloading PaySim...")
    try:
        import kagglehub
        p = Path(kagglehub.dataset_download("ealaxi/paysim1"))
        found = list(p.glob("*.csv"))
        if found:
            shutil.copy(found[0], paysim_file)
            print(f"Copied {found[0].name}")
        else:
            raise FileNotFoundError("No CSV found in downloaded PaySim dataset")
    except Exception as e:
        print(f"PaySim kagglehub failed ({e}), trying direct URL fallback...")
        try:
            df = pd.read_csv(
                "https://raw.githubusercontent.com/EdgarLopezPhD/PaySim/master/"
                "PS_20174392719_1491204439457_log.csv",
                nrows=100000,
            )
            df.to_csv(paysim_file, index=False)
            print("Downloaded 100k-row sample of PaySim")
        except Exception as e2:
            print(f"PaySim skip - not critical: {e2}")
else:
    print("PaySim already exists")

# ----------------------------------------------------------------------
# 3. Load + merge all sources into a common schema
# ----------------------------------------------------------------------
print("Loading and merging...")

cc_path = _ensure_creditcard_dataset()
cc = pd.read_csv(cc_path)
print(f"CreditCard: {len(cc)}")

if "event_time" not in cc.columns:
    cc["event_time"] = np.arange(len(cc))  # synthetic monotonic order, not wall-clock

frames = [cc]

# --- IEEE ---
if ieee_transaction is not None and ieee_transaction.exists():
    trans = pd.read_csv(
        ieee_transaction,
        usecols=[
            "TransactionID", "TransactionDT", "isFraud",
            "TransactionAmt", "ProductCD", "card1", "DeviceInfo",
        ],
    )
    ieee_finsec = pd.DataFrame()
    ieee_finsec["user_id"] = trans["card1"].astype(str).apply(lambda x: f"user_{x}")
    ieee_finsec["amount"] = trans["TransactionAmt"]
    ieee_finsec["transaction_type"] = trans["ProductCD"].map(
        {"W": "PAYMENT", "C": "TRANSFER", "R": "TRANSFER", "S": "PAYMENT", "H": "PAYMENT"}
    ).fillna("PAYMENT")
    ieee_finsec["device_id"] = trans["DeviceInfo"].fillna("unknown_device").astype(str)
    ieee_finsec["is_fraud"] = trans["isFraud"]
    ieee_finsec["event_time"] = trans["TransactionDT"]
    frames.append(ieee_finsec)
    print(f"IEEE: {len(ieee_finsec)} rows, {ieee_finsec['is_fraud'].sum()} frauds")

# --- PaySim ---
if paysim_file.exists():
    try:
        pay = pd.read_csv(paysim_file, nrows=200000)
        pay_finsec = pd.DataFrame()
        pay_finsec["user_id"] = pay["nameOrig"].astype(str)
        pay_finsec["amount"] = pay["amount"]
        pay_finsec["transaction_type"] = pay["type"]
        pay_finsec["device_id"] = pay["nameDest"].astype(str)
        pay_finsec["is_fraud"] = pay["isFraud"]
        pay_finsec["event_time"] = pay["step"].astype(float) * 3600
        frames.append(pay_finsec)
        print(f"PaySim: {len(pay_finsec)}")
    except Exception as e:
        print(f"PaySim load failed: {e}")

full_df = pd.concat(frames, ignore_index=True)
print(f"TOTAL MERGED: {len(full_df)} rows, {full_df['is_fraud'].sum()} frauds")
full_df.to_csv("datasets/public_benchmark/combined_finsec_training.csv", index=False)

# ----------------------------------------------------------------------
# 4. Feature engineering + time-aware split
# ----------------------------------------------------------------------
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
import xgboost as XGB
import joblib

device_le = LabelEncoder()
type_le = LabelEncoder()
user_le = LabelEncoder()

full_df["device_id_enc"] = device_le.fit_transform(full_df["device_id"].astype(str))
full_df["transaction_type_enc"] = type_le.fit_transform(full_df["transaction_type"].astype(str))
full_df["user_id_enc"] = user_le.fit_transform(full_df["user_id"].astype(str))
full_df["log_amount"] = np.log1p(full_df["amount"])

full_df = full_df.sort_values("event_time").reset_index(drop=True)

feature_cols = ["amount", "log_amount", "device_id_enc", "transaction_type_enc", "user_id_enc"]
X = full_df[feature_cols]
y = full_df["is_fraud"]

split_idx = int(len(full_df) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

scale = (y_train == 0).sum() / max(1, (y_train == 1).sum())
print(f"Training XGBoost scale_pos_weight={scale:.1f}")

clf = XGB.XGBClassifier(
    n_estimators=300,
    max_depth=8,
    learning_rate=0.05,
    scale_pos_weight=scale,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42,
)
clf.fit(X_train, y_train)

proba = clf.predict_proba(X_test)[:, 1]
pred = clf.predict(X_test)
precision, recall, f1, _ = precision_recall_fscore_support(y_test, pred, average="binary", zero_division=0)
roc = roc_auc_score(y_test, proba)
print(f"FINAL METRICS: ROC_AUC={roc:.4f} Precision={precision:.4f} Recall={recall:.4f} F1={f1:.4f}")

# ----------------------------------------------------------------------
# 5. Save model + fitted encoders
# ----------------------------------------------------------------------
version_id = hashlib.sha256(f"combined_{len(full_df)}_{roc}".encode()).hexdigest()[:12]
art_dir = Path(f"artifacts/versions/model-{version_id}")
art_dir.mkdir(parents=True, exist_ok=True)

joblib.dump(clf, art_dir / "model.joblib")
joblib.dump(
    {"device_le": device_le, "type_le": type_le, "user_le": user_le},
    art_dir / "encoders.joblib",
)

(art_dir / "meta.json").write_text(json.dumps({
    "version": version_id,
    "dataset_version": "combined_public_benchmark_v1",
    "datasets": ["creditcard", "ieee", "paysim"],
    "record_count": len(full_df),
    "fraud_count": int(full_df["is_fraud"].sum()),
    "split_method": "chronological_80_20",
    "metrics": {
        "roc_auc": float(roc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    },
    "feature_columns": feature_cols,
    "can_be_production": False,
}, indent=2))

print(f"\nDONE version_id={version_id}")
print(
    f"PROMOTE: python -c \"from app.ml.model_registry import promote_to_production; "
    f"promote_to_production('{version_id}', 'jay@finsec.ai', "
    f"'interim cold-start model for live evaluation - combined public benchmark')\""
)
