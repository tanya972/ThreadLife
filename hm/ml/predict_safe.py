import json
import numpy as np
import pandas as pd
from pathlib import Path
from joblib import load

MODEL_PATH = Path(r"C:\Users\tanya\data\hm\data\hm\lifespan_pipeline.joblib")    # your saved sklearn Pipeline
SCHEMA_PATH = Path(r"C:\Users\tanya\data\hm\data\hm\lifespan_schema.json")       # saved schema from training

# ---------- load artifacts ----------
pipe = load(MODEL_PATH)

if SCHEMA_PATH.exists():
    schema = json.loads(SCHEMA_PATH.read_text())
    NUM_COLS = schema.get("num_cols", [])
    CAT_COLS = schema.get("cat_cols", [])
    DEFAULTS = schema.get("defaults", {})
else:
    # Fallback if schema wasn't saved: try to read from the ColumnTransformer
    prep = pipe.named_steps.get("prep")
    if hasattr(prep, "transformers"):
        NUM_COLS, CAT_COLS = [], []
        for name, trans, cols in prep.transformers:
            if name == "num":
                NUM_COLS = list(cols)
            elif name == "cat":
                CAT_COLS = list(cols)
        DEFAULTS = {}
    else:
        raise RuntimeError(
            "Schema file not found and pipeline doesn't expose transformers. "
            "Re-train while saving schema."
        )

EXPECTED_COLS = NUM_COLS + CAT_COLS

def _align_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure df has the same columns/dtypes the pipeline saw at training."""
    df = df.copy()

    # 1) Add missing columns with sensible defaults (or NaN)
    for c in EXPECTED_COLS:
        if c not in df.columns:
            df[c] = DEFAULTS.get(c, np.nan)

    # 2) Drop extra columns (pipeline’s ColumnTransformer uses column names)
    df = df[EXPECTED_COLS]

    # 3) Coerce dtypes (best-effort)
    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in CAT_COLS:
        # keep as string/object; OneHotEncoder(handle_unknown="ignore") will cope with unseen values
        df[c] = df[c].astype("string").fillna(pd.NA)

    return df

def predict_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with 'pred_lifespan_months' appended."""
    X = _align_to_schema(df)
    yhat = pipe.predict(X)
    out = df.copy()
    out["pred_lifespan_months"] = yhat
    return out

def predict_one(row: dict) -> float:
    """Predict for a single item provided as a dict of features."""
    df = pd.DataFrame([row])
    return float(predict_df(df)["pred_lifespan_months"].iloc[0])

# --------- demo usage ---------
if __name__ == "__main__":
    # Example: batch from CSV (any file that has some/all of the expected columns)
    IN_PATH = Path(r"C:\Users\tanya\data\hm\data\hm\hm_train_ready.csv")
    OUT_PATH = Path(r"C:\Users\tanya\data\hm\data\hm\preds_safe.csv")

    df = pd.read_csv(IN_PATH)
    if "lifespan_months" in df.columns:
        df = df.drop(columns=["lifespan_months"])

    out = predict_df(df.head(20))  # demo on first 20 rows
    out.to_csv(OUT_PATH, index=False)
    print(f"Saved predictions → {OUT_PATH.resolve()}")

    # Example: single item
    sample = {
        "category": "tshirt",
        "product_group_name": "Garments",
        "graphical_appearance_name": "Solid",
        "colour_group_name": "White",
        "perceived_colour_value_name": "Light",
        "index_group_name": "Ladieswear",
        "price": 24.99,
        "mat_score": 1.05,
        "cotton_pct": 1.0, "poly_pct": 0.0, "wool_pct": 0.0, "elastane_pct": 0.0,
        "gap_months": 8.0, "price_decay": 0.25,
    }
    print("One-off prediction:", predict_one(sample))
