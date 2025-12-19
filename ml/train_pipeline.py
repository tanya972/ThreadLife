# train_pipeline.py
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ------------------- paths -------------------
DATA_PATH = Path(r"C:\Users\tanya\data\hm\data\hm\hm_train_ready.csv")
OUT_DIR   = DATA_PATH.parent
MODEL_PATH  = OUT_DIR / "lifespan_pipeline.joblib"
SCHEMA_PATH = OUT_DIR / "lifespan_schema.json"
IMP_PATH    = OUT_DIR / "feature_importances.csv"   # NEW: save importances
REPORT_PATH = OUT_DIR / "training_report.json"      # NEW: save a tiny report

TARGET = "lifespan_months"
DROP_IF_PRESENT = ["article_id", "detail_desc"]

# ------------------- load -------------------
df = pd.read_csv(DATA_PATH)

# ------------------- dtype hygiene -------------------
INTENDED_NUM = [
    "price","cotton_pct","poly_pct","wool_pct","elastane_pct","price_decay",
    "mat_score","gap_months","median_gap_days"
]
for c in INTENDED_NUM:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# drop columns that are entirely NaN (prevents imputer warnings)
df = df.dropna(axis=1, how="all")

# make categoricals explicitly string/object (helps OHE)
for c in df.columns:
    if df[c].dtype == "object":
        df[c] = df[c].astype("string")

# ------------------- split X/y -------------------
X = df.copy()
y = X.pop(TARGET)

for c in DROP_IF_PRESENT:
    if c in X.columns:
        X = X.drop(columns=[c])

# identify column types AFTER cleaning
cat_cols = [c for c in X.columns if X[c].dtype == "string"]
num_cols = [c for c in X.columns if c not in cat_cols]

# ------------------- preprocess -------------------
numeric = Pipeline(steps=[
    ("impute", SimpleImputer(strategy="median")),
    ("scale", StandardScaler()),
])
categorical = Pipeline(steps=[
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])
preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric, num_cols),
        ("cat", categorical, cat_cols),
    ],
    remainder="drop",
    verbose_feature_names_out=False,  # cleaner names
)

# ------------------- model -------------------
model = RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

pipe = Pipeline(steps=[
    ("prep", preprocess),
    ("model", model),
])

# ------------------- train/eval -------------------
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42
)
pipe.fit(X_tr, y_tr)
pred = pipe.predict(X_te)

mae = float(mean_absolute_error(y_te, pred))
r2  = float(r2_score(y_te, pred))
print(f"MAE (months): {mae:.3f}")
print(f"R^2: {r2:.3f}")

# ------------------- feature importances -------------------
# Build post-preprocessing feature names to pair with RF importances
prep = pipe.named_steps["prep"]
rf   = pipe.named_steps["model"]

# numeric names are as-is; categorical names come from OHE
num_names = list(num_cols)
cat_ohe = prep.named_transformers_["cat"].named_steps["ohe"]
cat_names = list(cat_ohe.get_feature_names_out(cat_cols))
feat_names = num_names + cat_names

imp = getattr(rf, "feature_importances_", None)
if imp is not None and len(feat_names) == len(imp):
    fi = (
        pd.DataFrame({"feature": feat_names, "importance": imp})
        .sort_values("importance", ascending=False)
    )
    fi.to_csv(IMP_PATH, index=False)
    print(f"Saved feature importances → {IMP_PATH}")

# ------------------- save pipeline & schema -------------------
dump(pipe, MODEL_PATH)
print(f"Saved pipeline → {MODEL_PATH}")

schema = {
    "num_cols": num_cols,
    "cat_cols": cat_cols,
    "defaults": {
        "price": 0.0,
        "mat_score": 0.65,
        "cotton_pct": None,
        "poly_pct": None,
        "wool_pct": None,
        "elastane_pct": None,
        "gap_months": None,
        "price_decay": None,
    }
}
SCHEMA_PATH.write_text(json.dumps(schema, indent=2))
print(f"Saved schema → {SCHEMA_PATH}")

# ------------------- save a small report (handy in UI/CI) -------------------
REPORT_PATH.write_text(json.dumps({
    "data_path": str(DATA_PATH),
    "rows": int(df.shape[0]),
    "features_used": num_cols + cat_cols,
    "metrics": {"mae_months": mae, "r2": r2},
}, indent=2))
print(f"Saved report → {REPORT_PATH}")
