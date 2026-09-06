import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score

base = Path("backend/datasets/public_benchmark")
# Load originals to evaluate separately
print("Loading for per-dataset eval...")
ieee = pd.read_csv(base / "combined_finsec_training.csv")
# Split by source heuristic: user_id prefix and transaction_type distribution
# IEEE has user_ prefix, PaySim has C... M..., CC has numeric
ieee_only = ieee[ieee["user_id"].str.startswith("user_")]
paysim_only = ieee[ieee["user_id"].str.startswith("C")]
cc_only = ieee[~ieee["user_id"].str.startswith("user_") & ~ieee["user_id"].str.startswith("C")]

for name, df in [("IEEE", ieee_only), ("PaySim", paysim_only), ("CC", cc_only), ("Combined", ieee)]:
    print(f"{name}: {len(df):,} rows, {df['is_fraud'].sum():,} frauds, {df['is_fraud'].mean():.4%} prevalence")
