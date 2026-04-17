# Quick Start: Advanced Synthetic Data Generator

## In 30 Seconds

### Dashboard (Easiest)
1. Open http://localhost:8505
2. Open sidebar → "🧬 Advanced Synthetic Data Generator"
3. Set: 50 users, 30 days, attacks ON, 15% rate
4. Click "🚀 Generate Advanced Dataset"
5. Data loads automatically → Ready to analyze!

### Command Line (Fast)
```bash
python generate_advanced_synthetic_data.py \
  --users 50 --days 30 --attack-rate 0.15 --verbose
```

## What You Get

✅ **12,000+ realistic transactions** with:
- Transaction history per user (natural patterns)
- Time gaps between actions (behavioral analysis)
- Burst fraud (10 txs in 1 minute)
- Geo jump (Africa → USA instantly)
- Device hijack (new devices appearing)
- ML labels (supervised + unsupervised)
- Anomaly clusters

## Dataset Columns

### Core Data
```
incident_id      → INC-000001
user_id          → USER-0001
timestamp        → 2026-04-16 14:30:00
amount           → $2,345.67
transaction_type → TRANSFER, WITHDRAWAL, DEPOSIT
device_id        → DEV-00001
```

### Risk Scores
```
risk_score     → 0.75 (0=safe, 1=dangerous)
anomaly_score  → 0.82 (0=normal, 1=anomalous)
```

### Behavioral Features
```
txn_velocity         → 5 (transactions in period)
avg_amount_historical → $1,200
amount_volatility    → 0.68 (std dev)
min_time_gap         → 12 (minutes between txns)
avg_time_gap         → 287 (minutes between txns)
```

### Attack Patterns
```
attack_type     → 'burst_fraud', 'geo_jump', 'device_hijack', 'normal'
device_age_days → 0 (brand new, suspicious) or 365 (old, normal)
location_jump   → True/False (impossible travel)
```

### ML Labels (4 Columns!)
```
supervised_label → 0 (normal) or 1 (anomaly)
anomaly_cluster  → 0 (cluster member) or 1 (outlier)
attack_category  → 'normal', 'burst_fraud', 'geo_jump', 'device_hijack', etc
```

## Example Use Cases

### 1. Load Generated Data
```python
import pandas as pd
df = pd.read_csv('data/synthetic/advanced_synthetic_data.csv')
print(f"Loaded {len(df)} records")
print(f"Attack patterns: {df[df['attack_type'] != 'normal'].shape[0]}")
```

### 2. Analyze Behavioral Patterns
```python
# High velocity users (suspicious)
suspicious = df[df['txn_velocity'] > 8]
print(f"Users with >8 txns: {suspicious.shape[0]}")

# Highly volatile amounts (pattern change)
volatile = df[df['amount_volatility'] > 0.8]
print(f"High volatility txns: {volatile.shape[0]}")

# Small time gaps (rapid activity)
rapid = df[df['min_time_gap'] < 5]
print(f"Rapid transactions: {rapid.shape[0]}")
```

### 3. Detect Attack Patterns
```python
# Find all attacks
attacks = df[df['attack_type'] != 'normal']
print(f"Total attacks: {attacks.shape[0]} ({attacks.shape[0]/len(df)*100:.1f}%)")

# Burst fraud (fast txns)
burst = df[df['attack_type'] == 'burst_fraud']
print(f"Burst fraud: {burst.shape[0]} records")

# Geo jump (impossible travel)
geo = df[df['attack_type'] == 'geo_jump']
print(f"Geo jump: {geo.shape[0]} records")

# Device hijack (new devices)
device = df[df['attack_type'] == 'device_hijack']
print(f"Device hijack: {device.shape[0]} records")
```

### 4. Use ML Labels
```python
# Supervised learning (binary classification)
X = df[['risk_score', 'anomaly_score', 'amount', 'txn_velocity']]
y = df['supervised_label']  # 0 or 1

from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier()
model.fit(X, y)

# Unsupervised anomaly detection
outliers = df[df['anomaly_cluster'] == 1]
print(f"Detected {len(outliers)} outliers")

# Categorical attack labels
print(df['attack_category'].value_counts())
```

### 5. Test Your Model
```python
# Load your model
your_model = load_your_fraud_model()

# Evaluate on synthetic data
predictions = your_model.predict(df)
ground_truth = df['supervised_label']

# Compare performance
from sklearn.metrics import confusion_matrix, classification_report
print(classification_report(ground_truth, predictions))
```

## Advanced: Custom Generation

### Generate Only Specific Attack Types
```python
from utils.advanced_synthetic_generator import AdvancedSyntheticDataGenerator

generator = AdvancedSyntheticDataGenerator()
df = generator.generate_dataset(num_users=50, num_days=30)

# Keep only burst fraud
df_filtered = df[
    (df['attack_type'] == 'burst_fraud') | 
    (df['attack_type'] == 'normal')
]
```

### Generate Multiple Scenarios
```python
# Scenario 1: Clean data (10% attacks)
df_clean = generator.generate_dataset(attack_percentage=0.10)

# Scenario 2: High fraud (30% attacks)  
df_fraud = generator.generate_dataset(attack_percentage=0.30)

# Scenario 3: Normal month (5% attacks)
df_normal = generator.generate_dataset(attack_percentage=0.05)

# Combine for comprehensive testing
combined = pd.concat([df_clean, df_fraud, df_normal], ignore_index=True)
```

## Common Commands

| Task | Command |
|------|---------|
| Generate 1000 records | `python generate_advanced_synthetic_data.py --users 10 --days 7` |
| Large dataset | `python generate_advanced_synthetic_data.py --users 200 --days 90` |
| No attacks | `python generate_advanced_synthetic_data.py --no-attacks` |
| Custom output | `python generate_advanced_synthetic_data.py --output my_data.csv` |
| Same data twice | `python generate_advanced_synthetic_data.py --seed 42` |
| See details | `python generate_advanced_synthetic_data.py --verbose` |

## Tips & Tricks

✅ **Use seed for reproducibility** - Same seed = same data every time
✅ **Start small** - Test with 10 users × 7 days first
✅ **Check attack distribution** - Adjust attack-rate if needed
✅ **Use --verbose flag** - See detailed statistics
✅ **Load many times** - Each run generates different data (unless seed is fixed)

## Example Output

```
✨ Generating Advanced Synthetic Dataset...
   Users: 50
   Days: 30
   Attack Rate: 15.0%
   Output: data/synthetic/advanced_synthetic_data.csv

✅ Generated 14,567 records
   Users: 50
   Attack Records: 2,185 (15.0%)
   ML Labels: ✓ Included

📊 Dataset Preview (with --verbose):
   ⚠️ High Risk (>0.7): 1,247 (8.5%)
   🔴 Attacks: 2,185 (15.0%)
   🧠 Anomalies: 892 (6.1%)
```

## Troubleshooting

**Q: How long does generation take?**
A: ~2 seconds per 1000 records. 50 users × 30 days ≈ 12 seconds

**Q: Is the data realistic?**
A: Yes! Behavioral features are based on real fraud patterns

**Q: Can I use this to train my model?**
A: Absolutely! Use `supervised_label` for training, validate on real data

**Q: What if I need more data?**
A: Increase `--users` or `--days`. 200 users × 90 days = 140K records

## Next Steps

1. **Generate data** → Run generate_advanced_synthetic_data.py
2. **Load in dashboard** → http://localhost:8505
3. **Analyze all incidents** → Click "▶️ Analyze All Incidents"
4. **Check results** → Review 📊 Overview, 🔔 Incidents, 📈 Analytics tabs
5. **Train your model** → Export CSV and build your fraud detector
6. **Evaluate** → Use labeled data to measure accuracy

## Support

For detailed documentation, see: `ADVANCED_SYNTHETIC_DATA_GUIDE.md`

## Quick Reference Card

```
BEHAVIORAL SEQUENCES:
├─ txn_velocity: Transaction count
├─ avg_amount_historical: Historical baseline
├─ amount_volatility: Value variability
├─ min_time_gap: Fastest transactions
└─ avg_time_gap: Normal pace

ATTACK PATTERNS:
├─ burst_fraud: 10 txs in 1 min
├─ geo_jump: Africa→USA in 30 min
└─ device_hijack: New device storm

ML LABELS (x3):
├─ supervised_label: 0/1 (binary)
├─ anomaly_cluster: 0/1 (outlier?)
└─ attack_category: Named category
```
