#!/usr/bin/env python3
import sys
from pathlib import Path
import pandas as pd
import traceback

print("=" * 60)
print("DEBUGGING build_ghg_and_merge.py")
print("=" * 60)

# Check files exist
files_to_check = [
    "Polyester Modeling Parameters.xlsx",
    "Cotton Modeling Parameters.xlsx",
    "Nylon6 Parameters.xlsx",
    "emission_factors_textile_industry.csv",
    "material_substitution_mapping_pfmr2022.csv"
]

print("\n1. Checking input files:")
for f in files_to_check:
    exists = Path(f).exists()
    print(f"   {f}: {'✓' if exists else '✗'}")
    if not exists:
        print(f"      ERROR: File not found!")
        sys.exit(1)

print("\n2. Testing openpyxl import:")
try:
    import openpyxl
    print(f"   ✓ openpyxl {openpyxl.__version__} imported successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    sys.exit(1)

print("\n3. Testing Excel file reading:")
try:
    df = pd.read_excel("Polyester Modeling Parameters.xlsx", sheet_name=None)
    print(f"   ✓ Successfully read Excel file")
    print(f"   Sheets: {list(df.keys())}")
    for sheet_name, sheet_df in df.items():
        print(f"   - {sheet_name}: {sheet_df.shape[0]} rows, {sheet_df.shape[1]} cols")
        print(f"     Columns: {list(sheet_df.columns)[:5]}...")
except Exception as e:
    print(f"   ✗ ERROR reading Excel: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing emission factors CSV:")
try:
    ef_df = pd.read_csv("emission_factors_textile_industry.csv")
    print(f"   ✓ Successfully read CSV")
    print(f"   Shape: {ef_df.shape}")
    print(f"   Columns: {list(ef_df.columns)}")
except Exception as e:
    print(f"   ✗ ERROR reading CSV: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n5. Now running the actual script:")
print("-" * 60)
try:
    import build_ghg_and_merge
    sys.argv = [
        'build_ghg_and_merge.py',
        '--modelparams',
        'Polyester Modeling Parameters.xlsx',
        'Cotton Modeling Parameters.xlsx',
        'Nylon6 Parameters.xlsx',
        '--emission_factors_csv',
        'emission_factors_textile_industry.csv',
        '--mapping_csv',
        'material_substitution_mapping_pfmr2022.csv',
        '--out_impacts_csv',
        'material_impact_data.csv',
        '--out_merged_csv',
        'merged_material_recommendations.csv',
        '--out_details_dir',
        'mp_details'
    ]
    build_ghg_and_merge.main()
    print("-" * 60)
    print("\n6. Checking output files:")
    if Path("material_impact_data.csv").exists():
        print("   ✓ material_impact_data.csv created")
        df = pd.read_csv("material_impact_data.csv")
        print(f"      Rows: {len(df)}")
        print(f"      Content:\n{df.to_string()}")
    else:
        print("   ✗ material_impact_data.csv NOT created")
    
    if Path("merged_material_recommendations.csv").exists():
        print("   ✓ merged_material_recommendations.csv created")
        df = pd.read_csv("merged_material_recommendations.csv")
        print(f"      Rows: {len(df)}")
        print(f"      Content:\n{df.to_string()}")
    else:
        print("   ✗ merged_material_recommendations.csv NOT created")
        
except Exception as e:
    print(f"\n✗ ERROR during script execution:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)


