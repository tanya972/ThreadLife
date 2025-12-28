#!/usr/bin/env python3
"""
H&M Clothing Lifespan Prep - IMPROVED VERSION
--------------------------------
Builds a train-ready CSV with a synthetic `lifespan_months` label from:
- material text (keyword durability score + % shares if present),
- transaction gaps (median days between repeat purchases per product type),
- price-decay proxy (txn price vs MSRP),
- usage intensity adjustments (NEW!)
- improved category nudges

IMPROVEMENTS:
- Added usage intensity multipliers (socks wear out faster than jackets)
- Better synthetic label formula
- Support for full transaction dataset
- More realistic lifespan predictions

Usage:
  python training.py

Output:
  hm_train_ready.csv
"""

import os
import re
import numpy as np
import pandas as pd
from pathlib import Path


# ---------- Config ----------
DATA_DIR = Path(r"C:\Users\tanya\clothing predictor\hm\data")
ARTICLES_CSV = DATA_DIR / "articles.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"  # CHANGED: Use full dataset!
CUSTOMERS_CSV = DATA_DIR / "fcustomers.csv"
OUT_PATH = DATA_DIR / "hm_train_ready.csv"


# ---------- NEW: Usage Intensity Database ----------
# How often items are worn (higher = more frequent use = faster wear)
USAGE_INTENSITY = {
    # Very high usage (worn daily/frequently)
    'sock': 3.0,
    'underwear': 3.0,
    'bra': 2.8,
    'tights': 2.8,
    'brief': 3.0,
    
    # High usage (worn multiple times per week)
    't shirt': 2.5,
    'tshirt': 2.5,
    'vest top': 2.5,
    'vest': 2.5,
    'tank': 2.5,
    'top': 2.0,
    'leggings': 2.3,
    
    # Medium usage (worn weekly)
    'jeans': 1.5,
    'trousers': 1.5,
    'shorts': 1.8,
    'skirt': 1.6,
    'blouse': 1.7,
    'shirt': 1.6,
    'sweater': 1.4,
    'cardigan': 1.4,
    'dress': 1.2,
    
    # Low usage (occasional wear)
    'jacket': 0.8,
    'coat': 0.7,
    'blazer': 0.8,
    'suit': 0.6,
    'outdoor': 0.9,
    
    # Very low usage (rarely worn out from use)
    'jewelry': 0.2,
    'earring': 0.2,
    'necklace': 0.2,
    'ring': 0.2,
    'bracelet': 0.2,
    'accessory': 0.3,
    'belt': 0.5,
    'bag': 0.6,
    'scarf': 0.5,
    'sunglasses': 0.4,
    
    # Special cases (wear out from specific use)
    'swimwear': 1.5,  # Chlorine damage
    'bikini': 1.5,
    'activewear': 2.0,  # High intensity use
    'sportswear': 2.0,
}


def get_usage_multiplier(category):
    """
    Get usage intensity multiplier for a category.
    Higher value = more frequent use = shorter lifespan
    """
    if not isinstance(category, str):
        return 1.0
    
    category_lower = category.lower()
    
    # Check for matches
    for key, value in USAGE_INTENSITY.items():
        if key in category_lower:
            return value
    
    return 1.0  # Default: medium usage


# ---------- Mock data (runs if real CSVs not found) ----------
def _ensure_mock_data():
    """Create tiny mock CSVs so the pipeline runs end-to-end if real Kaggle files are missing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not ARTICLES_CSV.exists():
        art = pd.DataFrame({
            "article_id": [1, 2, 3, 4, 5],
            "product_type_name": ["T-shirt", "Jeans", "Sweater", "Dress", "Jacket"],
            "product_group_name": ["Garments"] * 5,
            "graphical_appearance_name": ["Solid", "Solid", "Pattern", "Solid, ", "Solid"],
            "colour_group_name": ["White", "Blue", "Gray", "Red", "Black"],
            "perceived_colour_value_name": ["Light", "Regular", "Dark", "Regular", "Dark"],
            "index_group_name": ["Ladieswear"] * 5,
            "detail_desc": [
                "100% cotton jersey tee",
                "Denim jeans 98% cotton 2% elastane",
                "Wool-blend knit 60% wool 40% poly",
                "Viscose crepe dress 100% viscose",
                "Recycled polyester shell 100% polyester",
            ],
        })
        art.to_csv(ARTICLES_CSV, index=False)

    if not TRANSACTIONS_CSV.exists():
        tx = pd.DataFrame({
            "t_dat": pd.to_datetime([
                "2020-09-01", "2020-10-01", "2020-11-15", "2021-01-15", "2021-04-01",
                "2020-09-10", "2020-12-01", "2021-02-02", "2021-06-01",
            ]),
            "customer_id": [f"C{i}" for i in [1, 1, 1, 1, 1, 2, 2, 2, 2]],
            "article_id": [1, 1, 1, 1, 2, 3, 3, 4, 5],
            "price": [9.99, 9.99, 9.99, 9.99, 39.99, 59.99, 59.99, 29.99, 79.99],
            "sales_channel_id": [1, 1, 1, 1, 1, 1, 2, 2, 1],
        })
        tx.to_csv(TRANSACTIONS_CSV, index=False)

    if not CUSTOMERS_CSV.exists():
        cu = pd.DataFrame({
            "customer_id": [f"C{i}" for i in [1, 2, 3]],
            "age": [25, 31, 45],
            "club_member_status": ["ACTIVE", "PRE-CREATE", "ACTIVE"],
        })
        cu.to_csv(CUSTOMERS_CSV, index=False)


def read_data():
    _ensure_mock_data()
    articles = pd.read_csv(ARTICLES_CSV)
    
    # Load transactions with progress indicator
    print(f"Loading transactions from {TRANSACTIONS_CSV}...")
    tx = pd.read_csv(TRANSACTIONS_CSV, parse_dates=["t_dat"])
    print(f"  Loaded {len(tx):,} transactions")
    print(f"  Date range: {tx['t_dat'].min()} to {tx['t_dat'].max()}")
    
    customers = pd.read_csv(CUSTOMERS_CSV) if CUSTOMERS_CSV.exists() else pd.DataFrame()
    return articles, tx, customers


# ---------- Feature engineering ----------
# Order matters a bit: check 'recycled polyester' before 'polyester'
MATERIAL_KEYWORDS = {
    r"100\s*%\s*cotton|cotton": 1.0,
    r"recycled polyester": 0.50,
    r"polyester|poly\b": 0.45,
    r"wool": 0.85,
    r"cashmere": 0.90,
    r"linen": 0.80,
    r"hemp": 0.80,
    r"nylon|polyamide": 0.50,
    r"viscose|rayon": 0.55,
    r"elastane|spandex": 0.60,
    r"silk": 0.75,
    r"leather": 0.90,
    r"denim": 0.80,
}


def material_score(desc: str) -> float:
    """Return a durability multiplier ~[0.4, 1.2] from material text."""
    if not isinstance(desc, str) or not desc:
        return 0.65
    s = desc.lower()
    score = 0.65
    hits = 0
    for pat, w in MATERIAL_KEYWORDS.items():
        if re.search(pat, s):
            score += (w - 0.60)  # center near 0.60
            hits += 1
    # if none of the words are in s but there's blend 
    if hits == 0 and "blend" in s:
        score += 0.05
    return float(np.clip(score, 0.40, 1.20))


def extract_material_shares(desc: str) -> dict:
    """Extract rough % shares if present like '60% wool 40% poly'."""
    out = {"cotton_pct": np.nan, "poly_pct": np.nan, "wool_pct": np.nan, "elastane_pct": np.nan}
    if not isinstance(desc, str):
        return out
    s = desc.lower()
    pairs = re.findall(r"(\d{1,3})\s*%\s*([a-z]+)", s)
    tmp = {}
    for pct, name in pairs:
        pct = min(max(int(pct), 0), 100)
        tmp[name] = tmp.get(name, 0) + pct
    if tmp:
        for k, v in tmp.items():
            if "cotton" in k:
                out["cotton_pct"] = v / 100.0
            if "poly" in k:
                out["poly_pct"] = v / 100.0
            if "wool" in k:
                out["wool_pct"] = v / 100.0
            if "elastane" in k or "spandex" in k:
                out["elastane_pct"] = v / 100.0
    return out


def build_features(articles: pd.DataFrame, tx: pd.DataFrame = None) -> pd.DataFrame:
    a = articles.copy()
    a["detail_desc"] = a["detail_desc"].fillna("")
    a["mat_score"] = a["detail_desc"].apply(material_score)
    
    # Extract material shares
    shares = a["detail_desc"].apply(extract_material_shares).apply(pd.Series)
    a = pd.concat([a, shares], axis=1)

    # Normalized category
    a["category"] = (
        a["product_type_name"].astype(str).str.lower()
        .str.replace(r"[^a-z]+", " ", regex=True)
        .str.strip()
    )

    # Get price from transactions (median price per article)
    if tx is not None and "price" in tx.columns:
        print("Calculating median prices from transactions...")
        txn_price = tx.groupby("article_id")["price"].median().rename("price")
        a = a.merge(txn_price, left_on="article_id", right_index=True, how="left")
    else:
        a["price"] = np.nan
    
    return a


def compute_transaction_gaps(tx: pd.DataFrame, articles: pd.DataFrame) -> pd.DataFrame:
    """Median days between repeat purchases per product_type_name."""
    print("Computing transaction gaps...")
    t = tx.copy()
    t["t_dat"] = pd.to_datetime(t["t_dat"], errors="coerce")
    prod_map = articles.set_index("article_id")["product_type_name"].to_dict()
    t["product_type_name"] = t["article_id"].map(prod_map)

    t = t.dropna(subset=["product_type_name"]).sort_values(["customer_id", "product_type_name", "t_dat"])
    t["gap_days"] = t.groupby(["customer_id", "product_type_name"])["t_dat"].diff().dt.days

    gap_stats = (
        t.groupby("product_type_name")["gap_days"]
        .median()
        .rename("median_gap_days")
        .reset_index()
    )
    
    print(f"  Computed gaps for {len(gap_stats)} product types")
    art_gap = articles[["article_id", "product_type_name"]].merge(gap_stats, on="product_type_name", how="left")
    return art_gap


def price_decay_proxy(tx: pd.DataFrame, articles: pd.DataFrame) -> pd.DataFrame:
    """Compute price variance as a proxy for price decay (since we don't have MSRP)."""
    t = tx.copy()
    if "price" not in t.columns:
        return pd.DataFrame({"article_id": articles["article_id"], "price_decay": np.nan})
    
    # Use price std/mean as volatility proxy (higher volatility = more price decay)
    stats = t.groupby("article_id")["price"].agg(['mean', 'std']).reset_index()
    stats["price_decay"] = (stats["std"] / stats["mean"]).fillna(0).clip(0, 1)
    
    return stats[["article_id", "price_decay"]]


def synthesize_lifespan(a_feat: pd.DataFrame, art_gap: pd.DataFrame, price_decay: pd.DataFrame) -> pd.DataFrame:
    """
    IMPROVED LIFESPAN SYNTHESIS
    Now accounts for usage intensity and better category adjustments
    """
    df = (
        a_feat
        .merge(art_gap[["article_id", "median_gap_days"]], on="article_id", how="left")
        .merge(price_decay, on="article_id", how="left")
    )

    # Convert gaps to months
    df["gap_months"] = df["median_gap_days"] / 30.4

    # NEW: Add usage intensity
    df["usage_intensity"] = df["category"].apply(get_usage_multiplier)
    
    print(f"\nUsage intensity examples:")
    sample = df[['category', 'usage_intensity']].drop_duplicates().head(10)
    for idx, row in sample.iterrows():
        print(f"  {row['category']:30s} → {row['usage_intensity']:.1f}x")

    # Base lifespan from material score (scale to ~30–73 months)
    base = 30 + df["mat_score"] * 36
    
    # NEW: Adjust by usage intensity (high usage = shorter life)
    base = base / df["usage_intensity"]

    # Adjust by transaction gap (fallback to median or 8 months if missing)
    fallback = df["gap_months"].median() if not df["gap_months"].dropna().empty else 8.0
    gap_adj = df["gap_months"].fillna(fallback)

    # Adjust by price decay (higher variance => shorter lifespan)
    pdx = 1 - df["price_decay"].clip(0, 0.8).fillna(0.2)

    # IMPROVED: Category nudges (now more realistic)
    cat_nudge = df["category"].map({
        # Fast fashion / high wear items
        't shirt': -6, 'tshirt': -6, 'vest': -6, 'tank': -6,
        'sock': -12,  # NEW: Socks wear out fast!
        'underwear': -10,  # NEW: High frequency use
        'tights': -10,
        
        # Durable items
        'jeans': +8, 'denim': +8,
        'sweater': +6, 'cardigan': +5,
        'jacket': +10, 'coat': +12, 'blazer': +8,
        
        # Medium durability
        'dress': +2, 'skirt': +3,
        'trousers': +5, 'shorts': +2,
        
        # Low wear items (don't wear out from use)
        'jewelry': +20,  # NEW: Jewelry lasts forever unless lost!
        'earring': +20, 'necklace': +20, 'ring': +20,
        'belt': +12, 'bag': +10,
        'sunglasses': +8,
        
        # Special cases
        'swimwear': -5,  # Chlorine damage
        'bikini': -5,
        'activewear': -4,  # High intensity use
    }).fillna(0)

    lifespan = base + 0.6 * gap_adj + 8 * (pdx - 0.6) + cat_nudge
    lifespan += np.random.normal(0, 3.0, size=len(lifespan))  # small noise
    df["lifespan_months"] = np.clip(lifespan, 6, 120)

    return df


def main():
    print(f"[info] Using HM_DATA_DIR = {DATA_DIR}")
    print("="*80)
    print("IMPROVED TRAINING DATA GENERATION")
    print("="*80)
    
    articles, tx, customers = read_data()
    
    a_feat = build_features(articles, tx)  # Pass tx to get prices
    art_gap = compute_transaction_gaps(tx, articles)
    price_decay = price_decay_proxy(tx, articles)
    out = synthesize_lifespan(a_feat, art_gap, price_decay)

    keep_cols = [
        "article_id", "category", "product_group_name", "graphical_appearance_name",
        "colour_group_name", "perceived_colour_value_name", "index_group_name",
        "price", "mat_score", "cotton_pct", "poly_pct", "wool_pct", "elastane_pct",
        "median_gap_days", "gap_months", "price_decay", "usage_intensity", "lifespan_months", "detail_desc"
    ]
    for c in keep_cols:
        if c not in out.columns:
            out[c] = np.nan

    out = out[keep_cols]
    out.to_csv(OUT_PATH, index=False)
    
    print(f"\n[done] Wrote train-ready data to: {OUT_PATH}")
    print("\nSample predictions:")
    print(out[["article_id", "category", "usage_intensity", "price", "lifespan_months"]].head(10))
    
    # Summary statistics
    print("\n" + "="*80)
    print("LIFESPAN DISTRIBUTION BY USAGE INTENSITY")
    print("="*80)
    
    for usage_level in [0.2, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        subset = out[np.abs(out['usage_intensity'] - usage_level) < 0.1]
        if len(subset) > 0:
            avg_life = subset['lifespan_months'].mean()
            categories = subset['category'].value_counts().head(3).index.tolist()
            print(f"Usage {usage_level:.1f}x: {avg_life:5.1f} months avg  (e.g., {', '.join(categories[:2])})")


if __name__ == "__main__":
    main()
