"""Schema validation and normalization for incident data"""

import pandas as pd
import numpy as np


def ensure_incident_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure dataframe has required incident schema columns.
    
    Args:
        df: Input dataframe
        
    Returns:
        DataFrame with standardized schema
    """
    # Define required columns with defaults
    required_columns = {
        'incident_id': 'INC-00000',
        'user_id': 'USR-00000',
        'amount': 0.0,
        'risk_score': 0.5,
        'anomaly_score': 0.0,
        'confidence': 0.0,
        'governance_flags': '',
        'timestamp': pd.Timestamp.now(),
        'transaction_type': 'UNKNOWN',
        'device_id': 'DEV-00000',
        'tenant_id': 'default'
    }
    
    # Add missing columns with defaults
    for col, default_val in required_columns.items():
        if col not in df.columns:
            if isinstance(default_val, (int, float)):
                df[col] = default_val
            elif isinstance(default_val, str):
                df[col] = default_val
            else:
                df[col] = default_val
    
    # Ensure correct dtypes
    df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce').fillna(0.5)
    df['anomaly_score'] = pd.to_numeric(df['anomaly_score'], errors='coerce').fillna(0.0)
    df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce').fillna(0.0)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    
    # Ensure timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    return df


def validate_incident_row(row: dict) -> bool:
    """Validate a single incident row"""
    required_fields = ['incident_id', 'user_id', 'risk_score', 'tenant_id']
    return all(field in row for field in required_fields)
