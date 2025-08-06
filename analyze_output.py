#!/usr/bin/env python3
"""
Analyze Output.csv for Google Sheets testing
"""

import pandas as pd

def analyze_output():
    """Analyze the existing Output.csv file"""
    try:
        df = pd.read_csv('Output.csv')
        
        print("📊 OUTPUT.CSV ANALYSIS")
        print("="*50)
        print(f"   📋 Total schools: {len(df)}")
        print(f"   🔗 Schools with know_more_links: {len(df[df['has_know_more_link'] == True])}")
        print(f"   📊 Total columns: {len(df.columns)}")
        print(f"   🏛️ States: {df['state'].unique()}")
        print(f"   🏘️ Districts: {df['district'].unique()}")
        
        print("\n🎯 Sample affiliation data:")
        for i, row in df.head(3).iterrows():
            name = row['school_name'][:30]
            sec = row['affiliation_board_sec']
            hsec = row['affiliation_board_hsec']
            print(f"   {i+1}. {name} | Sec: {sec} | HSec: {hsec}")
        
        print("\n📋 Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error analyzing Output.csv: {e}")
        return None

if __name__ == "__main__":
    analyze_output()
