#!/usr/bin/env python
"""
Standalone utility script for generating advanced synthetic data with attack patterns
Usage: python generate_advanced_synthetic_data.py --users 50 --days 90 --include-attacks

Features:
- Behavioral sequences with transaction history
- Time gaps between actions
- Synthetic attack patterns (burst fraud, geo jump, device hijack)
- Supervised and unsupervised ML labels
"""

import argparse
import sys
from pathlib import Path

# Add utils directory to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from advanced_synthetic_generator import (
    AdvancedSyntheticDataGenerator,
    BehavioralSequenceGenerator,
    SyntheticAttackPatternGenerator,
    MLLabelGenerator
)


def print_dataset_summary(df, attack_patterns=None):
    """Print comprehensive summary of generated dataset"""
    print("\n" + "="*70)
    print("📊 ADVANCED SYNTHETIC DATASET SUMMARY")
    print("="*70)
    
    print(f"\n📈 Dataset Size:")
    print(f"   Total Records: {len(df):,}")
    print(f"   Unique Users: {df['user_id'].nunique()}")
    print(f"   Date Range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
    print(f"   Days Covered: {(df['timestamp'].max() - df['timestamp'].min()).days}")
    
    print(f"\n💰 Transaction Statistics:")
    print(f"   Avg Amount: ${df['amount'].mean():.2f}")
    print(f"   Min Amount: ${df['amount'].min():.2f}")
    print(f"   Max Amount: ${df['amount'].max():.2f}")
    print(f"   Median: ${df['amount'].median():.2f}")
    
    print(f"\n⚠️  Risk & Anomaly Scores:")
    print(f"   High Risk (>0.7): {(df['risk_score'] > 0.7).sum()} ({(df['risk_score'] > 0.7).sum()/len(df)*100:.1f}%)")
    print(f"   Anomalous (>0.75): {(df['anomaly_score'] > 0.75).sum()} ({(df['anomaly_score'] > 0.75).sum()/len(df)*100:.1f}%)")
    print(f"   Avg Risk Score: {df['risk_score'].mean():.3f}")
    print(f"   Avg Anomaly Score: {df['anomaly_score'].mean():.3f}")
    
    print(f"\n🔐 Attack Patterns:")
    if 'attack_type' in df.columns:
        attacks = df['attack_type'].value_counts()
        for attack, count in attacks.items():
            print(f"   {attack.replace('_', ' ').title()}: {count} ({count/len(df)*100:.1f}%)")
    
    print(f"\n🧬 ML Labels (Supervised):")
    if 'supervised_label' in df.columns:
        labels = df['supervised_label'].value_counts()
        print(f"   Normal (0): {labels.get(0, 0)} ({labels.get(0, 0)/len(df)*100:.1f}%)")
        print(f"   Anomalous (1): {labels.get(1, 0)} ({labels.get(1, 0)/len(df)*100:.1f}%)")
    
    print(f"\n🎯 Attack Categories:")
    if 'attack_category' in df.columns:
        categories = df['attack_category'].value_counts()
        for cat, count in categories.items():
            print(f"   {cat.replace('_', ' ').title()}: {count} ({count/len(df)*100:.1f}%)")
    
    print(f"\n🧠 Anomaly Clustering:")
    if 'anomaly_cluster' in df.columns:
        clusters = df['anomaly_cluster'].value_counts()
        for cluster, count in clusters.items():
            print(f"   Cluster {cluster}: {count} ({count/len(df)*100:.1f}%)")
    
    print(f"\n📊 Behavioral Features:")
    print(f"   Avg Transaction Velocity: {df['txn_velocity'].mean():.2f}")
    print(f"   Avg Amount Volatility: {df['amount_volatility'].mean():.3f}")
    print(f"   Avg Time Gap (mins): {df['avg_time_gap'].mean():.2f}")
    
    print(f"\n📁 Columns in Dataset ({len(df.columns)}):")
    for col in df.columns:
        dtype = df[col].dtype
        non_null = df[col].notna().sum()
        print(f"   • {col:<30} ({str(dtype):<10}) - {non_null} non-null values")
    
    print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate advanced synthetic data for FinSecAI with behavioral sequences and attack patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate basic dataset
  python generate_advanced_synthetic_data.py
  
  # Generate large dataset with attacks
  python generate_advanced_synthetic_data.py --users 100 --days 90 --attack-rate 0.2
  
  # Save to custom location
  python generate_advanced_synthetic_data.py --output /path/to/data.csv
  
  # Generate only supervised labels
  python generate_advanced_synthetic_data.py --no-unsupervised
        """
    )
    
    parser.add_argument('--users', type=int, default=30, 
                       help='Number of synthetic users (default: 30)')
    parser.add_argument('--days', type=int, default=30,
                       help='Days of transaction history (default: 30)')
    parser.add_argument('--attack-rate', type=float, default=0.15,
                       help='Percentage of records with attack patterns (default: 0.15)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path (default: data/synthetic/advanced_synthetic_data.csv)')
    parser.add_argument('--no-attacks', action='store_true',
                       help='Disable synthetic attack patterns')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--verbose', action='store_true',
                       help='Print detailed dataset summary')
    
    args = parser.parse_args()
    
    # Default output path
    if args.output is None:
        output_path = Path(__file__).parent.parent / 'data' / 'synthetic' / 'advanced_synthetic_data.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✨ Generating Advanced Synthetic Dataset...")
    print(f"   Users: {args.users}")
    print(f"   Days: {args.days}")
    print(f"   Attack Rate: {args.attack_rate*100:.1f}%")
    print(f"   Output: {output_path}")
    
    # Generate dataset
    generator = AdvancedSyntheticDataGenerator(seed=args.seed)
    df = generator.generate_dataset(
        num_users=args.users,
        num_days=args.days,
        include_attack_patterns=not args.no_attacks,
        attack_percentage=args.attack_rate
    )
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\n✅ Successfully saved {len(df):,} records to:")
    print(f"   {output_path}")
    
    # Print summary
    if args.verbose:
        print_dataset_summary(df)
    else:
        print(f"\n📊 Dataset Preview:")
        print(f"   Columns: {len(df.columns)}")
        print(f"   Rows: {len(df):,}")
        print(f"   Normal: {(df['attack_type'] == 'normal').sum()} ({(df['attack_type'] == 'normal').sum()/len(df)*100:.1f}%)")
        print(f"   Attack: {(df['attack_type'] != 'normal').sum()} ({(df['attack_type'] != 'normal').sum()/len(df)*100:.1f}%)")
        print(f"\n   Use --verbose flag for detailed summary")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
