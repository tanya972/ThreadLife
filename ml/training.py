#!/usr/bin/env python3
"""
H&M Clothing Lifespan Prep
--------------------------------
Builds a train-ready CSV with a synthetic `lifespan_months` label from:
- material text (keyword durability score + % shares if present),
- transaction gaps (median days between repeat purchases per product type),
- price-decay proxy (txn price vs MSRP),
- light category nudges.

Usage:
  # Put Kaggle files in HM_DATA_DIR (or default: /mnt/data on Linux, current dir on Windows if set)
  #   - articles.csv
  #   - transactions_train.csv
  #   - customers.csv (optional; not required yet)
  #
  # Then run:
  python hm_lifespan_prep.py

Env:
  HM_DATA_DIR=/path/to/hm
Output:
  hm_train_ready.csv
"""

import os
import re
import numpy as np
import pandas as pd
from pathlib import Path


# ---------- Config ----------
DATA_DIR = Path(os.environ.get("HM_DATA_DIR", ".")).resolve()
ARTICLES_CSV = DATA_DIR / "articles.csv"
TRANSACTIONS_CSV = DATA_DIR / "smaller_transactions.csv"
CUSTOMERS_CSV = DATA_DIR / "smaller_customers.csv"
OUT_PATH = DATA_DIR / "hm_train_ready.csv"


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
            "price": [9.99, 39.99, 59.99, 29.99, 79.99],
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
    tx = pd.read_csv(TRANSACTIONS_CSV, parse_dates=["t_dat"])
    customers = pd.read_csv(CUSTOMERS_CSV) if CUSTOMERS_CSV.exists() else pd.DataFrame()
    if "price" not in articles.columns:
        articles["price"] = np.nan
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


def build_features(articles: pd.DataFrame) -> pd.DataFrame:
    a = articles.copy()
    a["detail_desc"] = a["detail_desc"].fillna("")
    a["mat_score"] = a["detail_desc"].apply(material_score)
    # tur
    shares = a["detail_desc"].apply(extract_material_shares).apply(pd.Series)
    a = pd.concat([a, shares], axis=1)

    # Normalized category
    a["category"] = (
        a["product_type_name"].astype(str).str.lower()
        .str.replace(r"[^a-z]+", " ", regex=True)
        .str.strip()
    )

    # Ensure numeric price if present
    a["price"] = pd.to_numeric(a.get("price", np.nan), errors="coerce")
    return a


def compute_transaction_gaps(tx: pd.DataFrame, articles: pd.DataFrame) -> pd.DataFrame:
    """Median days between repeat purchases per product_type_name."""
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
    art_gap = articles[["article_id", "product_type_name"]].merge(gap_stats, on="product_type_name", how="left")
    return art_gap


def price_decay_proxy(tx: pd.DataFrame, articles: pd.DataFrame) -> pd.DataFrame:
    """If articles has MSRP 'price' and tx has actual 'price', compute discount rate."""
    a = articles[["article_id", "price"]].rename(columns={"price": "msrp"})
    t = tx.copy()
    if "price" not in t.columns:
        return pd.DataFrame({"article_id": articles["article_id"], "price_decay": np.nan})
    tt = t.groupby("article_id")["price"].median().rename("txn_price").reset_index()
    m = a.merge(tt, on="article_id", how="left")
    m["price_decay"] = (m["msrp"] - m["txn_price"]) / m["msrp"]
    return m[["article_id", "price_decay"]]


def synthesize_lifespan(a_feat: pd.DataFrame, art_gap: pd.DataFrame, price_decay: pd.DataFrame) -> pd.DataFrame:
    df = (
        a_feat
        .merge(art_gap[["article_id", "median_gap_days"]], on="article_id", how="left")
        .merge(price_decay, on="article_id", how="left")
    )

    # Convert gaps to months
    df["gap_months"] = df["median_gap_days"] / 30.4

    # Base lifespan from material score (scale to ~30–73 months)
    base = 30 + df["mat_score"] * 36

    # Adjust by transaction gap (fallback to median or 8 months if missing)
    fallback = df["gap_months"].median() if not df["gap_months"].dropna().empty else 8.0
    gap_adj = df["gap_months"].fillna(fallback)

    # Adjust by price decay (slower decay => longer lifespan)
    pdx = 1 - df["price_decay"].clip(0, 0.8).fillna(0.4)

    # Category nudges
    cat_nudge = df["category"].map({
        "t shirt": -6, "tshirt": -6, "jeans": +8, "sweater": +6, "jacket": +10, "dress": +2, "activewear": -4
    }).fillna(0)

    lifespan = base + 0.6 * gap_adj + 8 * (pdx - 0.6) + cat_nudge
    lifespan += np.random.normal(0, 3.0, size=len(lifespan))  # small noise
    df["lifespan_months"] = np.clip(lifespan, 6, 120)

    return df


def main():
    print(f"[info] Using HM_DATA_DIR = {DATA_DIR}")
    articles, tx, customers = read_data()
    a_feat = build_features(articles)
    art_gap = compute_transaction_gaps(tx, articles)
    price_decay = price_decay_proxy(tx, articles)
    out = synthesize_lifespan(a_feat, art_gap, price_decay)

    keep_cols = [
        "article_id", "category", "product_group_name", "graphical_appearance_name",
        "colour_group_name", "perceived_colour_value_name", "index_group_name",
        "price", "mat_score", "cotton_pct", "poly_pct", "wool_pct", "elastane_pct",
        "median_gap_days", "gap_months", "price_decay", "lifespan_months", "detail_desc"
    ]
    for c in keep_cols:
        if c not in out.columns:
            out[c] = np.nan

    out = out[keep_cols]
    out.to_csv(OUT_PATH, index=False)
    print(f"[done] Wrote train-ready data to: {OUT_PATH}")
    print(out.head(8))


if __name__ == "__main__":
    main()
