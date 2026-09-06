from pathlib import Path
import pandas as pd, hashlib, json, os, sys
sys.path.insert(0, ".")
dest = Path("datasets/public_benchmark/creditcard")
dest.mkdir(parents=True, exist_ok=True)
csv_path = dest / "creditcard.csv"
if not csv_path.exists():
    print("Downloading public benchmark...")
    try:
        import kagglehub
        p = kagglehub.dataset_download("mlg-ulb/creditcardfraud")
        df_raw = pd.read_csv(Path(p)/"creditcard.csv")
    except Exception as e:
        print(f"kagglehub failed {e}, using OpenML mirror")
        df_raw = pd.read_csv("https://files.openml.org/datasets/1597/dataset_1597_creditcardfraud.csv")
    df_raw.to_csv(csv_path, index=False)
else:
    df_raw = pd.read_csv(csv_path)
print(f"Raw: {len(df_raw)} rows, {df_raw['Class'].sum()} frauds")
# Map to FinSecAI
import pandas as pd
finsec_df = pd.DataFrame()
finsec_df["user_id"] = ["user_"+str(i%5000) for i in range(len(df_raw))]
finsec_df["amount"] = df_raw["Amount"]
finsec_df["transaction_type"] = df_raw["Amount"].apply(lambda x: "TRANSFER" if x>1000 else "PAYMENT")
finsec_df["device_id"] = ["dev_"+str(abs(hash(v))%1000) for v in df_raw["V1"]]
finsec_df["is_fraud"] = df_raw["Class"]
finsec_df.to_csv(dest/"finsec_compatible.csv", index=False)
print("Created finsec_compatible.csv - now training interim model...")

# Train
from app.ml.features import build_features_for_row
import xgboost as XGB
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
import joblib

X_list, y_list = [], []
sample = finsec_df.sample(n=min(20000, len(finsec_df)), random_state=42)
for _, row in sample.iterrows():
    try:
        vec, fv = build_features_for_row(None, row["user_id"], row["amount"], row["transaction_type"], row["device_id"])
        X_list.append(list(fv.values()))
    except:
        X_list.append([row["amount"], abs(hash(row["device_id"]))%100])
    y_list.append(row["is_fraud"])

X_train,X_test,y_train,y_test = train_test_split(X_list,y_list,test_size=0.2,stratify=y_list,random_state=42)
clf = XGB.XGBClassifier(n_estimators=100,max_depth=6,learning_rate=0.1,random_state=42)
clf.fit(X_train,y_train)
proba = clf.predict_proba(X_test)[:,1]
pred = clf.predict(X_test)
precision,recall,f1,_ = precision_recall_fscore_support(y_test,pred,average='binary',zero_division=0)
metrics = {"roc_auc": float(roc_auc_score(y_test,proba)), "precision": float(precision), "recall": float(recall), "f1": float(f1)}
print(f"Metrics: {metrics}")

version_id = hashlib.sha256(f"public_benchmark_{metrics}".encode()).hexdigest()[:12]
art_dir = Path(f"artifacts/versions/model-{version_id}")
art_dir.mkdir(parents=True, exist_ok=True)
joblib.dump(clf, art_dir/"model.joblib")
(art_dir/"meta.json").write_text(json.dumps({"version": version_id, "dataset_version": "public_benchmark_creditcard_v1", "metrics": metrics, "can_be_production": False}, indent=2))
print(f"DONE version_id={version_id}")
print(f"Promote: python -c \"from app.ml.model_registry import promote_to_production; promote_to_production('{version_id}', 'jay@finsec.ai', 'interim cold-start model for live evaluation')\"")
