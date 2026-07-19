import pandas as pd
import numpy as np
from datetime import datetime

def load_enriched_data(filepath='../data/enriched/ethiopia_fi_unified_data_enriched.csv'):
    """Load the enriched dataset with proper date parsing."""
    df = pd.read_csv(filepath)
    df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
    return df

def filter_by_type(df, record_type):
    """Return rows filtered by record_type."""
    return df[df['record_type'] == record_type]

def get_indicator_coverage(df, indicator_code):
    """Get observations for a specific indicator."""
    sub = df[(df['record_type'] == 'observation') & (df['indicator_code'] == indicator_code)]
    return sub.sort_values('observation_date')
