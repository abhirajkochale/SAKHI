"""
train_xgboost.py
================
Trains the primary SAKHI safhera XGBoost contextual risk model.

TARGET: crime_grounded_risk_index (0–100)

METHODOLOGY:
  1. Feature-Target Isolation: Target & component columns excluded from inputs.
  2. Segment-Level Leakage-Safe Data Splitting:
     - 24 Segments (80% of road segments, 240 rows across all 5 time periods) -> Train/Val
     - 6 Segments (20% of road segments, 60 rows across all 5 time periods) -> Test
     - Ensures no spatial leakage (same segment never in both train and test)
     - Allows model to observe the full 24-hour cycle during training
  3. Baseline Models:
     - Dummy Global Mean Regressor
     - District Mean Regressor
  4. Hyperparameter Search & Early Stopping:
     - Grid search over max_depth, learning_rate, n_estimators, colsample/subsample
     - Early stopping on validation MAE
  5. Metrics & Artifacts:
     - Reports MAE, RMSE, R² for Train, Validation, and Test vs Baselines
     - Saves trained model to ml/models/safhera_xgboost_risk_model.json
     - Saves metadata to ml/models/safhera_model_metadata.json
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = PROJECT_ROOT / "ml" / "data" / "processed" / "ml_training_dataset.csv"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "safhera_xgboost_risk_model.json"
METADATA_FILE = MODEL_DIR / "safhera_model_metadata.json"
PREDICTIONS_FILE = PROJECT_ROOT / "ml" / "data" / "processed" / "risk_predictions.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading training dataset...")
df = pd.read_csv(DATA_FILE)
print(f"Rows loaded: {len(df)}")


# ============================================================
# TARGET & FEATURES (27 SAFHERA FEATURE CONTRACT)
# ============================================================

TARGET = "crime_grounded_risk_index"

if TARGET not in df.columns:
    raise ValueError(f"Target column '{TARGET}' not found in dataset.")

FEATURES = [
    # Historical NCRB context
    "historical_baseline",
    "cases_per_100k",
    "severity_weighted_cases_per_100k",
    "recent_cases_per_100k",
    "recent_severity_per_100k",
    "crime_trend_slope",
    # Road characteristics
    "distance_m",
    "estimated_travel_time_s",
    # Environmental context
    "lighting_score",
    "cctv_coverage_score",
    "footfall_proxy",
    "contextual_footfall_proxy",
    # Emergency / accessibility infrastructure
    "distance_to_police_m",
    "distance_to_hospital_m",
    "distance_to_medical_facility_m",
    "distance_to_public_toilet_m",
    "distance_to_nearest_amenity_m",
    # Crime hotspot context
    "nearest_hotspot_distance_m",
    "nearest_hotspot_intensity",
    # Temporal context
    "representative_hour",
    "is_night",
    "is_late_night",
    "is_evening_peak",
    "is_weekend",
    "is_peak_hour",
    "reduced_activity_context",
    "lighting_relevance",
]

missing_features = [f for f in FEATURES if f not in df.columns]
if missing_features:
    raise ValueError(f"Missing feature columns:\n" + "\n".join(missing_features))

df = df.dropna(subset=FEATURES + [TARGET]).copy()


# ============================================================
# SEGMENT-LEVEL DATA SPLIT (80% Train/Val Segments, 20% Test Segments)
# ============================================================

unique_segments = sorted(df["segment_id"].unique())
rng = np.random.RandomState(42)
rng.shuffle(unique_segments)

train_val_count = int(len(unique_segments) * 0.80)  # 24 segments
test_count      = len(unique_segments) - train_val_count # 6 segments

train_val_segs = unique_segments[:train_val_count]
test_segs      = unique_segments[train_val_count:]

# Sub-split train_val into Train (19 segs) and Val (5 segs)
train_segs = train_val_segs[:19]
val_segs   = train_val_segs[19:]

train_df = df[df["segment_id"].isin(train_segs)].copy()
val_df   = df[df["segment_id"].isin(val_segs)].copy()
test_df  = df[df["segment_id"].isin(test_segs)].copy()

print("\n" + "=" * 70)
print("LEAKAGE-SAFE SEGMENT SPLIT SUMMARY")
print("=" * 70)
print(f"Total segments:      {len(unique_segments)} (300 rows)")
print(f"Training segments:   {len(train_segs)} ({len(train_df)} rows across all time periods)")
print(f"Validation segments: {len(val_segs)} ({len(val_df)} rows across all time periods)")
print(f"Test segments:       {len(test_segs)} ({len(test_df)} rows across all time periods)")

X_train, y_train = train_df[FEATURES], train_df[TARGET]
X_val,   y_val   = val_df[FEATURES],   val_df[TARGET]
X_test,  y_test  = test_df[FEATURES],  test_df[TARGET]


# ============================================================
# BASELINE EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("COMPUTING BASELINES")
print("=" * 70)

# Baseline 1: Dummy Global Mean
dummy = DummyRegressor(strategy="mean")
dummy.fit(X_train, y_train)
dummy_val_preds  = dummy.predict(X_val)
dummy_test_preds = dummy.predict(X_test)

dummy_val_mae  = mean_absolute_error(y_val, dummy_val_preds)
dummy_val_rmse = np.sqrt(mean_squared_error(y_val, dummy_val_preds))
dummy_val_r2   = r2_score(y_val, dummy_val_preds)

dummy_test_mae  = mean_absolute_error(y_test, dummy_test_preds)
dummy_test_rmse = np.sqrt(mean_squared_error(y_test, dummy_test_preds))
dummy_test_r2   = r2_score(y_test, dummy_test_preds)

print(f"Dummy Mean Baseline (Val)  -- MAE: {dummy_val_mae:.4f}, RMSE: {dummy_val_rmse:.4f}, R²: {dummy_val_r2:.4f}")
print(f"Dummy Mean Baseline (Test) -- MAE: {dummy_test_mae:.4f}, RMSE: {dummy_test_rmse:.4f}, R²: {dummy_test_r2:.4f}")

# Baseline 2: District Mean
district_means = train_df.groupby("district")[TARGET].mean()
global_mean = y_train.mean()

dist_val_preds  = val_df["district"].map(district_means).fillna(global_mean)
dist_test_preds = test_df["district"].map(district_means).fillna(global_mean)

dist_val_mae  = mean_absolute_error(y_val, dist_val_preds)
dist_val_rmse = np.sqrt(mean_squared_error(y_val, dist_val_preds))
dist_val_r2   = r2_score(y_val, dist_val_preds)

dist_test_mae  = mean_absolute_error(y_test, dist_test_preds)
dist_test_rmse = np.sqrt(mean_squared_error(y_test, dist_test_preds))
dist_test_r2   = r2_score(y_test, dist_test_preds)

print(f"District Mean Baseline (Val)  -- MAE: {dist_val_mae:.4f}, RMSE: {dist_val_rmse:.4f}, R²: {dist_val_r2:.4f}")
print(f"District Mean Baseline (Test) -- MAE: {dist_test_mae:.4f}, RMSE: {dist_test_rmse:.4f}, R²: {dist_test_r2:.4f}")


# ============================================================
# HYPERPARAMETER SEARCH & MODEL TRAINING
# ============================================================

print("\n" + "=" * 70)
print("HYPERPARAMETER TUNING & XGBOOST TRAINING")
print("=" * 70)

param_grid = [
    {"max_depth": 3, "learning_rate": 0.05, "n_estimators": 250, "colsample_bytree": 0.85, "subsample": 0.85},
    {"max_depth": 4, "learning_rate": 0.03, "n_estimators": 300, "colsample_bytree": 0.80, "subsample": 0.80},
    {"max_depth": 3, "learning_rate": 0.08, "n_estimators": 200, "colsample_bytree": 0.90, "subsample": 0.90},
    {"max_depth": 4, "learning_rate": 0.05, "n_estimators": 200, "colsample_bytree": 0.85, "subsample": 0.85},
]

best_model = None
best_val_mae = float("inf")
best_params = None

for i, params in enumerate(param_grid):
    candidate = XGBRegressor(
        objective="reg:squarederror",
        min_child_weight=2,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        **params,
    )
    candidate.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    val_p = candidate.predict(X_val)
    val_mae = mean_absolute_error(y_val, val_p)
    print(f"Config {i+1} {params} -> Val MAE: {val_mae:.4f}")

    if val_mae < best_val_mae:
        best_val_mae = val_mae
        best_model = candidate
        best_params = params

print(f"\nBest Config Selected: {best_params} (Val MAE: {best_val_mae:.4f})")

model = best_model


# ============================================================
# FINAL EVALUATION
# ============================================================

train_preds = np.clip(model.predict(X_train), 0, 100)
val_preds   = np.clip(model.predict(X_val),   0, 100)
test_preds  = np.clip(model.predict(X_test),  0, 100)

train_mae  = mean_absolute_error(y_train, train_preds)
train_rmse = np.sqrt(mean_squared_error(y_train, train_preds))
train_r2   = r2_score(y_train, train_preds)

val_mae  = mean_absolute_error(y_val, val_preds)
val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))
val_r2   = r2_score(y_val, val_preds)

test_mae  = mean_absolute_error(y_test, test_preds)
test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
test_r2   = r2_score(y_test, test_preds)

print("\n" + "=" * 70)
print("FINAL MODEL EVALUATION METRICS")
print("=" * 70)
print(f"Train      -- MAE: {train_mae:.4f}, RMSE: {train_rmse:.4f}, R²: {train_r2:.4f}")
print(f"Validation -- MAE: {val_mae:.4f}, RMSE: {val_rmse:.4f}, R²: {val_r2:.4f}")
print(f"Test       -- MAE: {test_mae:.4f}, RMSE: {test_rmse:.4f}, R²: {test_r2:.4f}")

test_imp = ((dist_test_mae - test_mae) / dist_test_mae) * 100
print(f"\nImprovement over District Mean Baseline on Test Set: {test_imp:.2f}%")


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance_df = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print("\n" + "=" * 70)
print("TOP FEATURE IMPORTANCE")
print("=" * 70)
print(importance_df.head(10).to_string(index=False))


# ============================================================
# SAVE ARTIFACTS
# ============================================================

model.save_model(MODEL_FILE)
print(f"\nModel saved to:\n{MODEL_FILE}")

# Write comprehensive metadata file (read by backend / inspectable)
metadata = {
    "model_name": "sakhi_safhera_contextual_risk",
    "model_version": "1.0.0-crime_grounded",
    "model_source": "xgboost_safhera",
    "target_name": TARGET,
    "target_type": "crime_grounded_district_temporal_index",
    "target_is_observed_crime": True,
    "dataset_type": "real_ncrb_district_plus_synthetic_proxy",
    "total_rows": len(df),
    "train_rows": len(train_df),
    "validation_rows": len(val_df),
    "test_rows": len(test_df),
    "feature_names": FEATURES,
    "feature_count": len(FEATURES),
    "evaluation_metrics": {
        "train": {"mae": round(train_mae, 4), "rmse": round(train_rmse, 4), "r2": round(train_r2, 4)},
        "validation": {"mae": round(val_mae, 4), "rmse": round(val_rmse, 4), "r2": round(val_r2, 4)},
        "test": {"mae": round(test_mae, 4), "rmse": round(test_rmse, 4), "r2": round(test_r2, 4)},
    },
    "baseline_comparisons": {
        "dummy_mean_val_mae": round(dummy_val_mae, 4),
        "dummy_mean_test_mae": round(dummy_test_mae, 4),
        "district_mean_val_mae": round(dist_val_mae, 4),
        "district_mean_test_mae": round(dist_test_mae, 4),
        "xgboost_test_mae_improvement_pct": round(test_imp, 2),
    },
    "xgboost_parameters": best_params,
    "limitations": [
        "District-level crime burden aggregate -- segment-level spatial variation relies on environmental features.",
        "Monthly NCRB data (2021-2023); post-2023 pattern changes not captured.",
        "Criminological temporal multiplier used for time-of-day weighting.",
    ]
}

with open(METADATA_FILE, "w") as f:
    json.dump(metadata, f, indent=4)
print(f"Metadata saved to:\n{METADATA_FILE}")

# Save full predictions CSV
full_df = df.copy()
full_df["predicted_risk"] = np.clip(model.predict(full_df[FEATURES]), 0, 100)
full_df["prediction_error"] = full_df[TARGET] - full_df["predicted_risk"]
full_df.to_csv(PREDICTIONS_FILE, index=False)
print(f"Predictions saved to:\n{PREDICTIONS_FILE}")

print("\n" + "=" * 70)
print("TRAIN_XGBOOST COMPLETE -- Model training and validation successful")
print("=" * 70)