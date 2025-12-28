#!/usr/bin/env python3
"""
Convert all Modeling Parameters Excel files to CSV format.
Each sheet in the Excel file will become a separate CSV file.
"""
import pandas as pd
from pathlib import Path
import sys

def convert_excel_to_csv(excel_path: Path, output_dir: Path = None):
    """Convert an Excel file to CSV(s). If multiple sheets, create one CSV per sheet."""
    if output_dir is None:
        output_dir = excel_path.parent
    
    print(f"Converting: {excel_path.name}")
    
    try:
        # Read all sheets
        excel_data = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')
        
        if not excel_data:
            print(f"  ⚠ Warning: {excel_path.name} has no sheets")
            return
        
        # If single sheet, use the base filename
        if len(excel_data) == 1:
            sheet_name, df = next(iter(excel_data.items()))
            csv_path = output_dir / f"{excel_path.stem}.csv"
            df.to_csv(csv_path, index=False)
            print(f"  ✓ Created: {csv_path.name} ({len(df)} rows, {len(df.columns)} cols)")
        else:
            # Multiple sheets - create one CSV per sheet
            for sheet_name, df in excel_data.items():
                # Sanitize sheet name for filename
                safe_sheet = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_sheet = safe_sheet.replace(' ', '_')
                csv_path = output_dir / f"{excel_path.stem}_{safe_sheet}.csv"
                df.to_csv(csv_path, index=False)
                print(f"  ✓ Created: {csv_path.name} (sheet: {sheet_name}, {len(df)} rows, {len(df.columns)} cols)")
        
    except Exception as e:
        print(f"  ✗ Error converting {excel_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    input_dir = Path(__file__).parent
    
    # Find all Modeling Parameters Excel files
    excel_files = list(input_dir.glob("*Modeling Parameters*.xlsx"))
    
    if not excel_files:
        print("No Modeling Parameters Excel files found!")
        return
    
    print(f"Found {len(excel_files)} Excel file(s) to convert:\n")
    
    success_count = 0
    for excel_file in sorted(excel_files):
        if convert_excel_to_csv(excel_file):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"Conversion complete: {success_count}/{len(excel_files)} files converted successfully")
    print("=" * 60)

if __name__ == "__main__":
    main()


