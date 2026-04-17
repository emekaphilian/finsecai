"""
Advanced Synthetic Data Generator for FinSecAI
Generates realistic behavioral sequences, attack patterns, and ML labels
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import random


class BehavioralSequenceGenerator:
    """Generate realistic user behavioral sequences"""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        self.num_users = 20
        self.days_of_history = 30
    
    def generate_transaction_history(self, user_id: str, num_days: int = 30) -> List[Dict]:
        """Generate transaction history for a user with realistic patterns"""
        transactions = []
        base_date = datetime.now()
        
        # User behavior profile (varies by user)
        user_num = int(user_id.split('-')[1])
        tx_per_day = np.random.poisson(3 + (user_num % 5))  # 3-8 transactions per day
        
        for day in range(num_days):
            date = base_date - timedelta(days=num_days - day)
            
            # Typically more active during business hours
            if np.random.random() > 0.3:  # 70% chance of activity
                daily_txs = np.random.poisson(tx_per_day)
                
                for _ in range(daily_txs):
                    # Time gaps between actions (realistic)
                    hour = np.random.choice(range(6, 22))  # Business hours
                    minute = np.random.randint(0, 60)
                    
                    amount = np.random.lognormal(mean=7, sigma=2)  # Realistic distribution
                    
                    transactions.append({
                        'timestamp': date.replace(hour=hour, minute=minute),
                        'amount': amount,
                        'type': np.random.choice(['TRANSFER', 'WITHDRAWAL', 'DEPOSIT'], p=[0.5, 0.3, 0.2])
                    })
        
        return sorted(transactions, key=lambda x: x['timestamp'])
    
    def calculate_time_gaps(self, transactions: List[Dict]) -> List[float]:
        """Calculate time gaps (in minutes) between consecutive transactions"""
        if len(transactions) < 2:
            return [0]
        
        gaps = []
        for i in range(1, len(transactions)):
            gap = (transactions[i]['timestamp'] - transactions[i-1]['timestamp']).total_seconds() / 60
            gaps.append(gap)
        
        return gaps
    
    def extract_behavioral_features(self, transactions: List[Dict]) -> Dict:
        """Extract behavioral features from transaction history"""
        if not transactions:
            return {}
        
        amounts = [tx['amount'] for tx in transactions]
        gaps = self.calculate_time_gaps(transactions)
        
        return {
            'txn_count': len(transactions),
            'avg_amount': np.mean(amounts),
            'std_amount': np.std(amounts),
            'min_gap': np.min(gaps) if gaps else 0,
            'max_gap': np.max(gaps) if gaps else 0,
            'avg_gap': np.mean(gaps) if gaps else 0,
            'high_variance': np.std(amounts) / (np.mean(amounts) + 0.01)  # Volatility
        }


class SyntheticAttackPatternGenerator:
    """Generate realistic attack pattern simulations"""
    
    @staticmethod
    def burst_fraud(base_date: datetime, num_transactions: int = 10, 
                   time_window_minutes: int = 1) -> List[Dict]:
        """
        Burst fraud: Multiple transactions in a very short time window
        Realistic scenario: Compromised account used intensively
        """
        transactions = []
        
        for i in range(num_transactions):
            seconds_offset = (i * 60 // num_transactions)  # Spread within window
            timestamp = base_date + timedelta(seconds=seconds_offset)
            
            transactions.append({
                'timestamp': timestamp,
                'amount': np.random.exponential(2000, 1)[0],  # Variable amounts
                'type': 'TRANSFER',
                'attack_type': 'burst_fraud',
                'anomaly_score': 0.95,
                'risk_score': 0.92
            })
        
        return transactions
    
    @staticmethod
    def geo_jump(base_date: datetime) -> List[Dict]:
        """
        Geo jump: Impossible travel between locations
        Realistic scenario: User location changes from Africa to North America instantly
        """
        locations = [
            ('Lagos', 'Nigeria', 6.5244, 3.3792),
            ('Abuja', 'Nigeria', 9.0765, 7.3986),
            ('New York', 'USA', 40.7128, 74.0060),
            ('Los Angeles', 'USA', 34.0522, 118.2437),
            ('London', 'UK', 51.5074, 0.1278),
            ('Tokyo', 'Japan', 35.6762, 139.6503),
        ]
        
        transactions = []
        
        # Start in Africa
        time1 = base_date
        loc1 = random.choice(locations[:2])  # Nigeria
        
        transactions.append({
            'timestamp': time1,
            'amount': 500,
            'location': f"{loc1[0]}, {loc1[1]}",
            'latitude': loc1[2],
            'longitude': loc1[3],
            'type': 'TRANSFER',
            'attack_type': 'geo_jump'
        })
        
        # Instant jump to North America (impossible travel)
        time2 = time1 + timedelta(minutes=30)  # Flight takes hours, impossible in 30 min
        loc2 = random.choice(locations[2:4])  # USA
        
        transactions.append({
            'timestamp': time2,
            'amount': 1500,
            'location': f"{loc2[0]}, {loc2[1]}",
            'latitude': loc2[2],
            'longitude': loc2[3],
            'type': 'TRANSFER',
            'attack_type': 'geo_jump',
            'anomaly_score': 0.98,
            'risk_score': 0.95
        })
        
        return transactions
    
    @staticmethod
    def device_hijack(base_date: datetime, num_days: int = 7) -> List[Dict]:
        """
        Device hijack: Unusual device activity and sudden device changes
        Realistic scenario: Account accessed from multiple new devices
        """
        transactions = []
        
        legitimate_device = 'DEVICE-001'
        attacker_devices = [f'DEVICE-NEW-{i}' for i in range(1, 5)]
        
        # Normal activity on original device
        for day in range(num_days):
            date = base_date - timedelta(days=num_days - day - 1)
            
            if np.random.random() > 0.3:
                transactions.append({
                    'timestamp': date.replace(hour=np.random.randint(8, 18)),
                    'amount': np.random.exponential(1000),
                    'device_id': legitimate_device,
                    'device_age_days': 365,
                    'type': 'TRANSFER'
                })
        
        # Sudden flood from new devices
        hijack_date = base_date - timedelta(days=1)
        for device in attacker_devices:
            for i in range(3):
                transactions.append({
                    'timestamp': hijack_date + timedelta(hours=i, minutes=np.random.randint(0, 60)),
                    'amount': np.random.exponential(2000),
                    'device_id': device,
                    'device_age_days': 0,  # Brand new device
                    'type': 'TRANSFER',
                    'attack_type': 'device_hijack',
                    'anomaly_score': 0.88,
                    'risk_score': 0.85
                })
        
        return transactions


class MLLabelGenerator:
    """Generate machine learning labels for supervised and unsupervised learning"""
    
    @staticmethod
    def generate_supervised_labels(df: pd.DataFrame) -> pd.Series:
        """
        Generate binary supervised labels based on risk patterns
        """
        labels = np.zeros(len(df), dtype=int)
        
        # Label based on risk_score
        labels[df['risk_score'] > 0.7] = 1
        
        # Label based on anomaly indicators
        if 'anomaly_score' in df.columns:
            labels[(df['anomaly_score'] > 0.75)] = 1
        
        # Label based on attack patterns
        if 'attack_type' in df.columns:
            labels[df['attack_type'].notna()] = 1
        
        return pd.Series(labels, name='supervised_label')
    
    @staticmethod
    def generate_unsupervised_labels(df: pd.DataFrame) -> pd.Series:
        """
        Generate unsupervised anomaly clusters based on features
        """
        try:
            from sklearn.preprocessing import StandardScaler
            from sklearn.cluster import DBSCAN
            
            # Select features for clustering
            feature_cols = ['risk_score', 'anomaly_score', 'amount']
            feature_cols = [col for col in feature_cols if col in df.columns]
            
            if not feature_cols:
                return pd.Series(0, index=df.index, name='anomaly_cluster')
            
            X = df[feature_cols].fillna(0).values
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # DBSCAN for anomaly detection
            clustering = DBSCAN(eps=0.5, min_samples=5).fit(X_scaled)
            labels = clustering.labels_
            
            # -1 indicates outliers/anomalies
            anomaly_labels = (labels == -1).astype(int)
            
            return pd.Series(anomaly_labels, name='anomaly_cluster')
        
        except Exception as e:
            print(f"Warning: Could not generate unsupervised labels: {e}")
            return pd.Series(0, index=df.index, name='anomaly_cluster')
    
    @staticmethod
    def assign_attack_categories(df: pd.DataFrame) -> pd.Series:
        """
        Assign attack category labels based on characteristics
        """
        categories = ['normal'] * len(df)
        
        for idx, row in df.iterrows():
            if pd.notna(row.get('attack_type')):
                categories[idx] = row['attack_type']
            elif row.get('risk_score', 0) > 0.8:
                if 'burst' in str(row.get('transaction_type', '')).lower():
                    categories[idx] = 'burst_fraud'
                elif 'device' in str(row.get('device_id', '')).lower():
                    categories[idx] = 'device_hijack'
                elif 'location' in row:
                    categories[idx] = 'geo_anomaly'
                else:
                    categories[idx] = 'high_risk'
            elif row.get('anomaly_score', 0) > 0.7:
                categories[idx] = 'suspicious'
        
        return pd.Series(categories, name='attack_category')


class AdvancedSyntheticDataGenerator:
    """Main generator combining all features"""
    
    def __init__(self, seed: int = 42):
        self.behavior_gen = BehavioralSequenceGenerator(seed)
        self.attack_gen = SyntheticAttackPatternGenerator()
        self.label_gen = MLLabelGenerator()
    
    def generate_dataset(self, 
                        num_users: int = 20,
                        num_days: int = 30,
                        include_attack_patterns: bool = True,
                        attack_percentage: float = 0.1) -> pd.DataFrame:
        """
        Generate complete synthetic dataset with behavioral sequences and attacks
        
        Args:
            num_users: Number of synthetic users
            num_days: Days of transaction history per user
            include_attack_patterns: Whether to include synthetic attacks
            attack_percentage: Percentage of records to have attack patterns
        
        Returns:
            DataFrame with transactions, behavioral features, and ML labels
        """
        
        records = []
        
        # Generate normal user data
        for user_idx in range(num_users):
            user_id = f'USER-{user_idx:04d}'
            base_date = datetime.now() - timedelta(days=num_days)
            
            # Generate transaction history
            txns = self.behavior_gen.generate_transaction_history(user_id, num_days)
            
            # Extract behavioral features
            behavior = self.behavior_gen.extract_behavioral_features(txns)
            
            # Create records for each transaction
            for txn in txns:
                record = {
                    'incident_id': f'INC-{len(records):06d}',
                    'user_id': user_id,
                    'timestamp': txn['timestamp'],
                    'amount': txn['amount'],
                    'transaction_type': txn['type'],
                    'device_id': f'DEV-{user_idx:05d}',
                    'risk_score': np.random.uniform(0.1, 0.6),
                    'anomaly_score': np.random.uniform(0.0, 0.5),
                    # Behavioral features
                    'txn_velocity': behavior.get('txn_count', 0),
                    'avg_amount_historical': behavior.get('avg_amount', 0),
                    'amount_volatility': behavior.get('high_variance', 0),
                    'min_time_gap': behavior.get('min_gap', 0),
                    'avg_time_gap': behavior.get('avg_gap', 0),
                }
                records.append(record)
        
        df = pd.DataFrame(records)
        
        # Add attack patterns
        if include_attack_patterns:
            attack_indices = np.random.choice(len(df), size=int(len(df) * attack_percentage), replace=False)
            
            for idx in attack_indices:
                attack_type = np.random.choice(['burst_fraud', 'geo_jump', 'device_hijack'])
                
                if attack_type == 'burst_fraud':
                    df.loc[idx, 'risk_score'] = 0.90
                    df.loc[idx, 'anomaly_score'] = 0.92
                    df.loc[idx, 'attack_type'] = 'burst_fraud'
                    df.loc[idx, 'txn_velocity'] = np.random.randint(8, 15)
                
                elif attack_type == 'geo_jump':
                    df.loc[idx, 'risk_score'] = 0.93
                    df.loc[idx, 'anomaly_score'] = 0.95
                    df.loc[idx, 'attack_type'] = 'geo_jump'
                    df.loc[idx, 'location_jump'] = True
                
                elif attack_type == 'device_hijack':
                    df.loc[idx, 'risk_score'] = 0.85
                    df.loc[idx, 'anomaly_score'] = 0.88
                    df.loc[idx, 'attack_type'] = 'device_hijack'
                    df.loc[idx, 'device_age_days'] = 0
        
        # Generate ML labels
        df['supervised_label'] = self.label_gen.generate_supervised_labels(df)
        df['anomaly_cluster'] = self.label_gen.generate_unsupervised_labels(df)
        df['attack_category'] = self.label_gen.assign_attack_categories(df)
        
        # Fill missing values
        df['attack_type'] = df['attack_type'].fillna('normal')
        df['location_jump'] = df.get('location_jump', False)
        df['device_age_days'] = df.get('device_age_days', 365)
        
        return df.sort_values('timestamp').reset_index(drop=True)


# Standalone utility functions
def generate_advanced_synthetic_data(num_users: int = 20, 
                                     num_days: int = 30,
                                     save_to_csv: bool = False,
                                     output_path: str = None) -> pd.DataFrame:
    """Utility function to generate advanced synthetic dataset"""
    
    generator = AdvancedSyntheticDataGenerator()
    df = generator.generate_dataset(
        num_users=num_users,
        num_days=num_days,
        include_attack_patterns=True,
        attack_percentage=0.15
    )
    
    if save_to_csv and output_path:
        df.to_csv(output_path, index=False)
        print(f"✓ Saved {len(df)} records to {output_path}")
    
    return df


if __name__ == "__main__":
    # Test script
    print("Generating advanced synthetic dataset...")
    df = generate_advanced_synthetic_data(
        num_users=30,
        num_days=60,
        save_to_csv=True,
        output_path='data/synthetic/advanced_synthetic_data.csv'
    )
    
    print(f"\n✓ Generated {len(df)} records")
    print(f"✓ Users: {df['user_id'].nunique()}")
    print(f"✓ Attack patterns: {(df['attack_type'] != 'normal').sum()} ({(df['attack_type'] != 'normal').sum()/len(df)*100:.1f}%)")
    print(f"✓ Supervised labels: {df['supervised_label'].value_counts().to_dict()}")
    print(f"✓ Anomaly clusters: {df['anomaly_cluster'].value_counts().to_dict()}")
    print(f"\nColumns: {list(df.columns)}")
