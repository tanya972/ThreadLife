#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def _infer_material_name_from_filename(path: Path) -> str:
    stem = path.stem.lower()
    squashed = re.sub(r"[\s_\-]+", "", stem)

    if "acrylic" in squashed:
        return "Acrylic"
    if "cotton" in squashed:
        return "Cotton (Conventional)"
    if "flax" in squashed:
        return "Flax (Linen)"
    if "hemp" in squashed:
        return "Hemp"
    if "nylon6" in squashed:
        return "Nylon 6 (PA6)"
    if "nylon66" in squashed:
        return "Nylon 66 (PA66)"
    if "polyester" in squashed:
        return "Polyester (Virgin PET)"
    if "polypropylene" in squashed:
        return "Polypropylene (PP)"
    if "silk" in squashed:
        return "Silk"
    if "viscoserayon" in squashed or "viscose" in squashed or "rayon" in squashed:
        return "Viscose Rayon"
    if "wool" in squashed:
        return "Wool (Conventional)"
    return stem.split()[0].capitalize() if stem else "Unknown"

def _row_mentions_climate(row: pd.Series) -> bool:
    """True if any string cell in the row looks like 'climate change', 'global warming', 'GWP', etc."""
    for v in row:
        try:
            s = str(v).lower()
        except Exception:
            continue
        # Expanded search terms for climate indicators
        if any(term in s for term in [
            "climate change", "global warming", "climate-change",
            "gwp", "carbon footprint", "greenhouse gas", "ghg"
        ]):
            return True
    return False

def extract_ghg_indicator_from_file(path: Path) -> float:
    """
    Look through all sheets, and:
    - normalize columns
    - require 'indicator_value' + 'indicator_uom'
    - find rows where:
        indicator_uom contains 'kg co2'
        OR (if no climate text found) just take first row with 'kg co2' in UoM
    Return the first matching indicator_value (kg CO2e per FU).
    """
    xl = pd.read_excel(path, sheet_name=None)
    best_val: Optional[float] = None

    for sheet_name, df in xl.items():
        if df is None or df.empty:
            continue
        df = _norm_cols(df)

        if "indicator_value" not in df.columns or "indicator_uom" not in df.columns:
            continue

        # filter by unit: something like "kg CO2 eq", "kg CO2e/FU", etc.
        uom = df["indicator_uom"].astype(str).str.lower()
        mask_uom = uom.str.contains("kg") & uom.str.contains("co2")

        # Try to filter rows that talk about climate change
        climate_mask = df.apply(_row_mentions_climate, axis=1)

        cand = df[mask_uom & climate_mask]
        
        # If no rows with climate text, just use first row with kg CO2 in UoM
        if cand.empty:
            print(f"  Warning: No 'climate change' text found in {path.name}, using first kg CO2 row")
            cand = df[mask_uom]
        
        if not cand.empty:
            # take the first one — usually there's exactly one climate-change row
            val = float(cand["indicator_value"].iloc[0])
            best_val = val
            print(f"  Found GHG value for {path.name}: {val} kg CO2e")
            break

    if best_val is None:
        raise ValueError(
            f"Could not find any indicator in {path.name} with UoM containing 'kg CO2'. "
            f"Please check the file has an 'indicator_uom' column with CO2 units."
        )
    return best_val

def parse_percent_range(s: str) -> Tuple[Optional[float], Optional[float]]:
    if not isinstance(s, str):
        return (None, None)
    s2 = s.replace("–", "-")
    nums = re.findall(r"(\d+(?:\.\d+)?)", s2)
    if not nums:
        return (None, None)
    if len(nums) == 1:
        v = float(nums[0]) / 100.0
        return (v, v)
    a, b = float(nums[0]), float(nums[1])
    return (min(a, b) / 100.0, max(a, b) / 100.0)

def build_recommendations(impacts: pd.DataFrame, mapping_csv: Path) -> pd.DataFrame:
    mapping = pd.read_csv(mapping_csv)
    merged = mapping.merge(impacts, left_on="current_material", right_on="material", how="left")

    lo_list, hi_list = [], []
    for s in merged["emission_reduction_potential"].fillna("0%"):
        lo, hi = parse_percent_range(s)
        lo_list.append(lo)
        hi_list.append(hi)

    merged["reduction_lo_frac"] = lo_list
    merged["reduction_hi_frac"] = hi_list

    merged["alt_estimated_ghg_low"] = (
        merged["ghg_kgco2e_perkg"] * (1 - merged["reduction_hi_frac"].fillna(0))
    )
    merged["alt_estimated_ghg_high"] = (
        merged["ghg_kgco2e_perkg"] * (1 - merged["reduction_lo_frac"].fillna(0))
    )

    cols = [
        "current_material", "alt_material",
        "ghg_kgco2e_perkg",
        "emission_reduction_potential",
        "alt_estimated_ghg_low", "alt_estimated_ghg_high",
        "why_preferred", "certifications", "source_report",
    ]
    for c in cols:
        if c not in merged.columns:
            merged[c] = np.nan
    return merged[cols]

def main():
    ap = argparse.ArgumentParser(
        description="Extract GHG indicator (kg CO2e/FU) from Modeling Parameters and merge with substitution mapping."
    )
    ap.add_argument(
        "--modelparams", nargs="+", required=True,
        help="Paths to *Modeling Parameters.xlsx files (one or more)."
    )
    ap.add_argument(
        "--mapping_csv", required=True,
        help="Material substitution mapping CSV"
    )
    ap.add_argument("--out_impacts_csv", default="material_impact_data.csv")
    ap.add_argument("--out_merged_csv", default="merged_material_recommendations.csv")
    args = ap.parse_args()

    records = []
    print("Extracting GHG indicators from modeling parameters files...")
    for pstr in args.modelparams:
        p = Path(pstr)
        try:
            ghg_val = extract_ghg_indicator_from_file(p)  # kg CO2e per FU (usually per kg fiber)
            material_name = _infer_material_name_from_filename(p)
            records.append({
                "material": material_name,
                "source_file": str(p),
                "ghg_kgco2e_perkg": ghg_val,
            })
        except Exception as e:
            print(f"  ERROR processing {p.name}: {e}")
            continue

    if not records:
        raise ValueError("No valid GHG data extracted from any files!")

    impacts = pd.DataFrame(records)
    impacts.to_csv(args.out_impacts_csv, index=False)
    print(f"\n✓ Wrote: {args.out_impacts_csv}")

    merged = build_recommendations(impacts, Path(args.mapping_csv))
    merged.to_csv(args.out_merged_csv, index=False)
    print(f"✓ Wrote: {args.out_merged_csv}")

if __name__ == "__main__":
    main()
