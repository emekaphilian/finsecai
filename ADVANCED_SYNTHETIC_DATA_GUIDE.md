# Advanced Synthetic Data Generator - Documentation

## Overview

The **Advanced Synthetic Data Generator** is a comprehensive tool for creating realistic, labeled datasets with behavioral sequences, synthetic attack patterns, and machine learning labels. It's designed to help test and train the FinSecAI fraud detection system with realistic scenarios.

## Features

### 1. 🧠 Behavioral Sequences
Generate realistic user transaction patterns including:

- **Transaction History per User**: Complete history of user transactions over configurable time periods
- **Time Gaps Between Actions**: Realistic intervals between transactions (minutes to days)
- **Behavioral Features**:
  - Transaction velocity (transactions per day)
  - Amount volatility (std dev of transaction amounts)
  - Time gap analysis (min, max, average)
  - Historical baselines

**Output Columns:**
- `txn_velocity`: Number of transactions
- `avg_amount_historical`: Historical average transaction amount
- `amount_volatility`: Standard deviation of amounts
- `min_time_gap`: Minimum time between transactions (minutes)
- `avg_time_gap`: Average time between transactions

### 2. 🧬 Synthetic Attack Patterns

#### Burst Fraud Pattern
Multiple transactions in a very short time window (unrealistic and indicative of fraud).
- **Characteristics**: 10+ transactions in 1-5 minutes
- **Risk Score**: ~0.90
- **Output**: `attack_type=burst_fraud`, high `txn_velocity`

**Real-world scenario:** Compromised account used intensively by attacker
```python
Burst Fraud: 
  - 10 transactions in 1 minute
  - Risk Score: 0.92
  - Anomaly Score: 0.95
```

#### Geo Jump Pattern
Impossible travel between distant locations instantly.
- **Route Examples**: 
  - Abuja (Nigeria) → New York (USA) in 30 minutes (requires 10+ hours flight)
  - Lagos (Nigeria) → London (UK) in 15 minutes
- **Risk Score**: ~0.93
- **Output**: `attack_type=geo_jump`, high `location_jump` flag

**Real-world scenario:** Account accessed from multiple continents within minutes
```python
Geo Jump:
  - Transaction 1: Abuja, Nigeria at 10:00 AM
  - Transaction 2: New York, USA at 10:30 AM
  - Physical impossibility: 30 minutes for transatlantic travel
  - Risk Score: 0.95
```

#### Device Hijack Pattern
Sudden usage from multiple new, suspicious devices.
- **Characteristics**: 
  - Normal activity on device A for weeks
  - Sudden appearance of 4+ new devices
  - All new devices are brand new (age = 0 days)
  - High transaction frequency on new devices
- **Risk Score**: ~0.85
- **Output**: `attack_type=device_hijack`, `device_age_days=0`

**Real-world scenario:** Account compromised, accessed from attacker's devices
```python
Device Hijack:
  - Normal pattern: DEVICE-001 (365 days old)
  - Suspicious: DEVICE-NEW-1, DEVICE-NEW-2, DEVICE-NEW-3 (0 days old)
  - Risk Score: 0.85
  - Anomaly Score: 0.88
```

### 3. 🎯 ML Labels

#### Supervised Labels (Binary Classification)
Binary labels for supervised learning: 0 (normal) or 1 (anomalous)

**Labeling Rules:**
- Label = 1 if: Risk Score > 0.7
- Label = 1 if: Anomaly Score > 0.75
- Label = 1 if: Attack type is not 'normal'
- Otherwise: Label = 0

**Output Column:** `supervised_label`

#### Unsupervised Labels (Anomaly Clustering)
Use DBSCAN clustering for anomaly detection without labels.
- **Method**: DBSCAN with eps=0.5, min_samples=5
- **Features**: Risk score, anomaly score, transaction amount
- **Output**: 
  - `anomaly_cluster=0`: Normal transaction (within cluster)
  - `anomaly_cluster=1`: Outlier/anomaly (outside clusters)

**Output Column:** `anomaly_cluster`

#### Attack Category Labels
Categorical labels identifying attack type:
- `normal`: Regular transaction
- `burst_fraud`: Rapid transaction sequence
- `geo_jump`: Impossible travel
- `device_hijack`: New device usage
- `suspicious`: Anomalous but unclassified
- `high_risk`: High risk score unclassified

**Output Column:** `attack_category`

## Usage

### Option 1: Dashboard UI Controls

1. **Navigate to the sidebar** → **Advanced Synthetic Data Generator**
2. **Configure parameters:**
   - Number of Users: 5-100
   - Days of History: 7-365
   - Include Attack Patterns: Toggle on/off
   - Attack Rate: 0-50%
   - Select specific attack types: Burst Fraud, Geo Jump, Device Hijack

3. **Click "🚀 Generate Advanced Dataset"**
4. **View statistics** in the dashboard
5. **Data is automatically loaded** and ready for analysis

### Option 2: Command-Line Utility

#### Basic Usage
```bash
python generate_advanced_synthetic_data.py
```

#### Advanced Options
```bash
# Generate with custom parameters
python generate_advanced_synthetic_data.py \
  --users 50 \
  --days 90 \
  --attack-rate 0.2 \
  --output data/custom_synthetic.csv \
  --verbose

# Generate without attack patterns
python generate_advanced_synthetic_data.py \
  --users 30 \
  --days 30 \
  --no-attacks

# Use custom random seed for reproducibility
python generate_advanced_synthetic_data.py \
  --users 20 \
  --seed 12345 \
  --verbose
```

#### Command-Line Arguments
| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--users` | int | 30 | Number of synthetic users |
| `--days` | int | 30 | Days of transaction history |
| `--attack-rate` | float | 0.15 | Percentage of records with attacks (0-1) |
| `--output` | str | `data/synthetic/advanced_synthetic_data.csv` | Output file path |
| `--no-attacks` | flag | False | Disable synthetic attack patterns |
| `--seed` | int | 42 | Random seed for reproducibility |
| `--verbose` | flag | False | Print detailed dataset summary |

### Option 3: Python API

```python
from utils.advanced_synthetic_generator import AdvancedSyntheticDataGenerator

# Create generator
generator = AdvancedSyntheticDataGenerator(seed=42)

# Generate dataset
df = generator.generate_dataset(
    num_users=50,
    num_days=90,
    include_attack_patterns=True,
    attack_percentage=0.15
)

# Now df contains all features and labels
print(df.columns)
print(df.head())
```

## Output Dataset Structure

Generated datasets contain the following columns:

### Core Transaction Data
| Column | Type | Description |
|--------|------|-------------|
| `incident_id` | str | Unique identifier |
| `user_id` | str | User identifier |
| `timestamp` | datetime | Transaction timestamp |
| `amount` | float | Transaction amount |
| `transaction_type` | str | TRANSFER, WITHDRAWAL, DEPOSIT |
| `device_id` | str | Device identifier |

### Risk & Anomaly Scoring
| Column | Type | Description |
|--------|------|-------------|
| `risk_score` | float | Risk score (0.0-1.0) |
| `anomaly_score` | float | Anomaly score (0.0-1.0) |

### Behavioral Features
| Column | Type | Description |
|--------|------|-------------|
| `txn_velocity` | int | Transactions in period |
| `avg_amount_historical` | float | Average historical amount |
| `amount_volatility` | float | Std deviation of amounts |
| `min_time_gap` | float | Min gap between txns (min) |
| `avg_time_gap` | float | Avg gap between txns (min) |

### Attack Pattern Indicators
| Column | Type | Description |
|--------|------|-------------|
| `attack_type` | str | Attack category (see below) |
| `device_age_days` | int | Device age in days |
| `location_jump` | bool | Impossible travel flag |

### ML Labels
| Column | Type | Description |
|--------|------|-------------|
| `supervised_label` | int | 0=normal, 1=anomalous |
| `anomaly_cluster` | int | 0=cluster, 1=outlier |
| `attack_category` | str | Detailed classification |

## Dataset Examples

### Small Dataset (Quick Testing)
```bash
python generate_advanced_synthetic_data.py \
  --users 10 \
  --days 7 \
  --attack-rate 0.20
```
**Output:** ~500-1000 records

### Medium Dataset (Analysis)
```bash
python generate_advanced_synthetic_data.py \
  --users 50 \
  --days 30 \
  --attack-rate 0.15 \
  --verbose
```
**Output:** ~3000-5000 records

### Large Dataset (Model Training)
```bash
python generate_advanced_synthetic_data.py \
  --users 200 \
  --days 90 \
  --attack-rate 0.10 \
  --verbose
```
**Output:** ~30000+ records

## Sample Output Statistics

### Dataset Summary
```
✨ Advanced Synthetic Dataset
================================================================================
📈 Dataset Size:
   Total Records: 12,847
   Unique Users: 50
   Date Range: 2026-02-15 to 2026-04-16
   Days Covered: 60

💰 Transaction Statistics:
   Avg Amount: $2,345.67
   Min Amount: $5.32
   Max Amount: $89,234.12
   Median: $1,234.56

⚠️  Risk & Anomaly Scores:
   High Risk (>0.7): 1,247 (9.7%)
   Anomalous (>0.75): 1,150 (8.9%)
   Avg Risk Score: 0.485
   Avg Anomaly Score: 0.389

🔐 Attack Patterns:
   Burst Fraud: 385 (3.0%)
   Geo Jump: 298 (2.3%)
   Device Hijack: 312 (2.4%)

🧬 ML Labels (Supervised):
   Normal (0): 11,600 (90.3%)
   Anomalous (1): 1,247 (9.7%)

🎯 Attack Categories:
   Normal: 11,552 (89.9%)
   Burst Fraud: 385 (3.0%)
   Geo Jump: 298 (2.3%)
   Device Hijack: 312 (2.4%)
   High Risk: 300 (2.3%)

🧠 Anomaly Clustering:
   Normal (inlier): 12,100 (94.2%)
   Anomaly (outlier): 747 (5.8%)

📊 Behavioral Features:
   Avg Transaction Velocity: 3.45 txn/day
   Avg Amount Volatility: 0.782
   Avg Time Gap (mins): 287.3
```

## Integration with FinSecAI

### Dashboard
1. **Sidebar**: Expand "🧬 Advanced Synthetic Data Generator"
2. **Configure**: Set users, days, attacks, and types
3. **Generate**: Click "🚀 Generate Advanced Dataset"
4. **Analyze**: Data loads automatically into current tenant
5. **Process**: Use "▶️ Analyze All Incidents" button to process

### Evaluation
The generated datasets are perfect for:
- **Model Training**: Labeled data for supervised learning
- **Validation**: Test model performance on known attacks
- **Stress Testing**: Edge cases with burst fraud, geo jumps
- **Fairness Evaluation**: Uniform distribution across user segments
- **Drift Detection**: Compare baseline with attack periods

## Advanced Use Cases

### 1. A/B Testing Detection Models
```python
# Generate clean dataset
df_clean = generator.generate_dataset(num_users=100, include_attack_patterns=False)

# Generate with 25% attacks
df_attacks = generator.generate_dataset(num_users=100, attack_percentage=0.25)

# Train and compare models
model1 = train_model(df_clean)
model2 = train_model(df_attacks)
compare_performance(model1, model2)
```

### 2. Threshold Optimization
```python
# Generate varied risk datasets
for attack_rate in [0.05, 0.10, 0.15, 0.20, 0.30]:
    df = generator.generate_dataset(attack_percentage=attack_rate)
    # Test different decision thresholds
    for threshold in np.arange(0.5, 0.95, 0.05):
        metrics = evaluate(df, threshold)
```

### 3. Time-Series Analysis
```python
# Generate multiple months
dfs = []
for month in range(1, 13):
    df = generator.generate_dataset(
        num_users=50,
        num_days=30,
        attack_percentage=month * 0.01  # Increasing attack rate
    )
    dfs.append(df)

# Analyze drift over time
monthly_data = pd.concat(dfs)
analyze_temporal_drift(monthly_data)
```

## Reproducibility

Use the `--seed` parameter to ensure reproducible datasets:

```bash
# Always generates the same dataset
python generate_advanced_synthetic_data.py --users 100 --seed 42

# Different seed = different dataset
python generate_advanced_synthetic_data.py --users 100 --seed 12345
```

## Performance

**Generation Speed:**
- ~1000 records per second on standard hardware
- 50 users × 30 days = ~12,000 records = ~12 seconds
- 200 users × 90 days = ~140,000 records = ~140 seconds

**Output File Size:**
- ~0.5 MB per 10,000 records (CSV format)

## Troubleshooting

### Issue: ImportError when running script
**Solution:** Ensure `utils/advanced_synthetic_generator.py` exists in the project

### Issue: Memory error with very large datasets
**Solution:** Generate in batches using smaller `--days` or `--users` values

### Issue: Unbalanced attack distribution
**Solution:** Increase `--attack-rate` or use smaller datasets with specific attack types

## References

- **MITRE**: https://attack.mitre.org/ (Attack patterns reference)
- **Fraud Detection**: Common fraud indicators in financial systems
- **Anomaly Detection**: DBSCAN clustering methodology
- **Machine Learning**: Supervised/unsupervised label generation best practices
