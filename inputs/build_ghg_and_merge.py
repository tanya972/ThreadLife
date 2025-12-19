#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------- helpers ----------
def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def _read_all_sheets(xlsx_path: Path) -> pd.DataFrame:
    """Read all tabs from a Modeling Parameters Excel and stack them."""
    xl = pd.read_excel(xlsx_path, sheet_name=None)
    frames = []
    for sname, df in xl.items():
        if df is None or len(df) == 0:
            continue
        df = _norm_cols(df.copy())
        df["__sheet__"] = sname
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def _infer_material_name_from_filename(path: Path) -> str:
    """Robust inference for your 11 materials."""
    stem = path.stem.lower()
    squashed = re.sub(r"[\s_\-]+", "", stem)
    if re.search(r"(nylon6|pa6|polyamide6|nylon-?6)", squashed):  return "Nylon 6 (PA6)"
    if re.search(r"(nylon66|pa66|polyamide66|nylon-?66)", squashed): return "Nylon 66 (PA66)"
    if re.search(r"(polypropylene|pp\b)", squashed):               return "Polypropylene (PP)"
    if ("polyester" in squashed) or ("pet" in squashed):           return "Polyester (Virgin PET)"
    if ("viscose" in squashed) or ("rayon" in squashed):           return "Viscose Rayon"
    if ("flax" in squashed) or ("linen" in squashed):              return "Flax (Linen)"
    if "acrylic" in squashed:                                      return "Acrylic"
    if "cotton" in squashed:                                       return "Cotton (Conventional)"
    if "hemp" in squashed:                                         return "Hemp"
    if "silk" in squashed:                                         return "Silk"
    if "wool" in squashed:                                         return "Wool (Conventional)"
    if ("nylon" in squashed) or ("polyamide" in squashed):         return "Nylon 6 (PA6)"
    # fallback
    tok = stem.split()
    return tok[0].capitalize() if tok else "Unknown Material"

# unit conversion helpers
_ELECTRICITY_ALIASES = ("electricity", "grid electricity", "elec")
_DIESEL_ALIASES      = ("diesel", "diesel fuel")
_NG_ALIASES          = ("natural gas", "ng", "methane gas")
_STEAM_ALIASES       = ("steam",)
_HEAT_ALIASES        = ("heat", "thermal energy", "process heat")

# (name -> canonical key)
def _canonical_input_key(name: str) -> Optional[str]:
    s = str(name).strip().lower()
    # quick contains checks
    if any(k in s for k in _ELECTRICITY_ALIASES): return "electricity"
    if any(k in s for k in _DIESEL_ALIASES):      return "diesel"
    if any(k in s for k in _NG_ALIASES):          return "natural gas"
    if any(k in s for k in _STEAM_ALIASES):       return "steam"
    if any(k in s for k in _HEAT_ALIASES):        return "thermal energy"
    # generic fallbacks
    for generic in ("electric", "kwh"):
        if generic in s: return "electricity"
    return None  # leave chemicals & non-energy without EF unless you add them

def _norm_unit(u: str) -> Optional[str]:
    if pd.isna(u): return None
    s = str(u).strip().lower()
    # unify plural
    s = s.replace("kilowatt-hour", "kwh").replace("kilowatt hours", "kwh").replace("kilowatt hour", "kwh")
    s = s.replace("kw h", "kwh").replace("kW h", "kwh")
    s = s.replace("mwh", "kwh")  # will handle with multiplier outside if needed
    s = s.replace("megajoule", "mj").replace("mega joule", "mj")
    if s in ("kwh","mj","kg","l","liter","litre","m3","m^3","kg/h","kwh/kg","mj/kg"):
        return s
    # common typos
    if s in ("kw/h","kw"): return "kwh"
    return s

def _apply_multiplier(value: float, unit: str) -> Tuple[float, str]:
    """Convert MWh->kWh etc. Expand if needed."""
    s = unit
    v = float(value)
    if s == "mwh":         return v * 1000.0, "kwh"
    if s in ("l","liter","litre"):  # keep L as L
        return v, "l"
    return v, s

def _load_emission_factors(factors_csv: Path) -> pd.DataFrame:
    ef = pd.read_csv(factors_csv)
    ef = _norm_cols(ef)
    # enforce types
    ef["input_key"] = ef["input_key"].astype(str).str.strip().str.lower()
    ef["unit"]      = ef["unit"].astype(str).str.strip().str.lower()
    return ef

def _lookup_ef(ef_df: pd.DataFrame, key: str, unit: str) -> Optional[float]:
    row = ef_df[(ef_df["input_key"] == key) & (ef_df["unit"] == unit)]
    if len(row) == 1:
        return float(row["ef_kgco2e_per_unit"].iloc[0])
    return None

def compute_co2e_from_model_params(model_df: pd.DataFrame, ef_df: pd.DataFrame):
    df = _norm_cols(model_df)

    # 1. NAME column (what the input actually is)
    name_col = next(
        (c for c in df.columns if "compound" in c or "material" in c or "input" in c),
        None
    )

    # 2. FIXED numeric column
    val_col = "indicator_value" if "indicator_value" in df.columns else None

    # 3. FIXED units column
    unit_col = "indicator_uom" if "indicator_uom" in df.columns else None

    # Error messages if something is missing
    if name_col is None:
        raise ValueError(
            f"Could not find an input name column. Columns: {list(df.columns)}"
        )
    if val_col is None:
        raise ValueError(
            f"Missing required numeric column 'indicator_value'. Columns: {list(df.columns)}"
        )
    if unit_col is None:
        raise ValueError(
            f"Missing required unit column 'indicator_uom'. Columns: {list(df.columns)}"
        )

    rows = []
    total = 0.0

    for _, r in df.iterrows():
        nm = r.get(name_col, "")
        qty = r.get(val_col, np.nan)
        if pd.isna(qty):
            continue

        raw_unit = r.get(unit_col, None)
        unit = _norm_unit(raw_unit)
        qty_norm, unit_norm = _apply_multiplier(qty, unit)

        key = _canonical_input_key(nm)
        ef = _lookup_ef(ef_df, key, unit_norm) if key else None

        co2e = qty_norm * ef if ef is not None else np.nan
        if not pd.isna(co2e):
            total += co2e

        rows.append({
            "input_name": nm,
            "canonical_key": key,
            "quantity": qty,
            "unit": raw_unit,
            "normalized_quantity": qty_norm,
            "normalized_unit": unit_norm,
            "ef_kgco2e_per_unit": ef,
            "co2e": co2e
        })

    return float(total), pd.DataFrame(rows)

# ---------- recommendation merge ----------
def parse_percent_range(s: str) -> Tuple[Optional[float], Optional[float]]:
    if not isinstance(s, str):
        return (None, None)
    s2 = s.replace("–","-")
    nums = re.findall(r"(\d+(?:\.\d+)?)", s2)
    if not nums:
        return (None, None)
    if len(nums) == 1:
        v = float(nums[0])/100.0
        return (v, v)
    a, b = float(nums[0]), float(nums[1])
    return (min(a,b)/100.0, max(a,b)/100.0)

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
    merged["alt_estimated_ghg_low"]  = merged["ghg_kgco2e_perkg"] * (1 - merged["reduction_hi_frac"].fillna(0))   # best case
    merged["alt_estimated_ghg_high"] = merged["ghg_kgco2e_perkg"] * (1 - merged["reduction_lo_frac"].fillna(0))   # conservative
    cols = [
        "current_material", "alt_material",
        "ghg_kgco2e_perkg",
        "emission_reduction_potential",
        "alt_estimated_ghg_low", "alt_estimated_ghg_high",
        "why_preferred", "certifications", "source_report"
    ]
    for c in cols:
        if c not in merged.columns:
            merged[c] = np.nan
    return merged[cols]

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Compute kg CO2e from Modeling Parameters and merge with substitution mapping")
    ap.add_argument("--modelparams", nargs="+", required=True, help="Paths to Modeling Parameters Excel files (one or more).")
    ap.add_argument("--emission_factors_csv", required=True, help="CSV with columns: input_key,unit,ef_kgco2e_per_unit")
    ap.add_argument("--mapping_csv", required=True, help="Material substitution mapping CSV")
    ap.add_argument("--out_impacts_csv", default="material_impact_data.csv")
    ap.add_argument("--out_merged_csv", default="merged_material_recommendations.csv")
    ap.add_argument("--out_details_dir", default="mp_details", help="Directory to write per-file input-to-CO2e breakdowns")
    args = ap.parse_args()

    ef_df = _load_emission_factors(Path(args.emission_factors_csv))

    # process each modeling-parameters file
    records = []
    details_dir = Path(args.out_details_dir)
    details_dir.mkdir(parents=True, exist_ok=True)

    for pstr in args.modelparams:
        p = Path(pstr)
        mdl = _read_all_sheets(p)
        material = _infer_material_name_from_filename(p)
        total_kgco2e, detail = compute_co2e_from_model_params(mdl, ef_df)
        # write per-file breakdown
        detail_path = details_dir / f"{material.replace(' ','_')}_breakdown.csv"
        detail.to_csv(detail_path, index=False)
        records.append({"material": material, "source_file": str(p), "ghg_kgco2e_perkg": total_kgco2e})

    impacts = pd.DataFrame(records)
    impacts.to_csv(args.out_impacts_csv, index=False)

    merged = build_recommendations(impacts, Path(args.mapping_csv))
    merged.to_csv(args.out_merged_csv, index=False)

    print("Wrote:", args.out_impacts_csv)
    print("Wrote:", args.out_merged_csv)
    print("Per-file breakdowns in:", str(details_dir))

if __name__ == "__main__":
    main()
