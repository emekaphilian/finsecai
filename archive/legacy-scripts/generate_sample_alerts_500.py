# generate_sample_alerts_500.py
import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

# Project data folder
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_RAW = PROJECT_ROOT / "data/raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

# Parameters
num_alerts = 500
start_time = datetime(2026, 1, 16, 8, 0, 0)
alert_types = ["fraud", "suspicious", "transaction"]

# Generate sample alerts
data = []
for i in range(num_alerts):
    user_id = random.randint(1000, 1999)
    amount = round(random.uniform(10, 10000), 2)
    ml_fraud_score = round(random.uniform(0, 1), 2)
    timestamp = (start_time + timedelta(minutes=i*5)).isoformat()
    alert_type = random.choice(alert_types)
    data.append({
        "user_id": user_id,
        "amount": amount,
        "ml_fraud_score": ml_fraud_score,
        "timestamp": timestamp,
        "alert_type": alert_type
    })

# Create DataFrame
df = pd.DataFrame(data)

# Output file path
output_file = DATA_RAW / f"sample_alerts_500_{int(datetime.now().timestamp())}.csv"

# Save CSV
df.to_csv(output_file, index=False)
print(f"✅ Sample alerts CSV generated at: {output_file}")
