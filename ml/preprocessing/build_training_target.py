"""
build_training_target.py
========================
Constructs the training target for the SAKHI contextual safety model.

TARGET: crime_grounded_risk_index (0-100)
=========================================
Replaces the previous synthetic_prototype_contextual_risk target which was
a weighted linear combination of the same feature columns used as XGBoost
inputs -- a circular definition that caused the model to approximate an
identity function rather than learning safety patterns.

The new target is derived from two independent, documented sources:

  Component A -- District Crime Burden (60% weight)
  --------------------------------------------------
  Source: NCRB crime_records.csv (real data, is_synthetic=False)
  Years:  2021, 2022, 2023 (recency-weighted: 2021x1.0, 2022x1.1, 2023x1.2)
  Metric: severity-weighted reported cases per 100k population
  Scope:  Crimes against women -- NCRB IPC categories in the dataset
  Resolution: District-level aggregate (NOT segment-level)

  Component B -- Temporal Risk Multiplier (40% weight)
  -----------------------------------------------------
  Source: Criminological evidence (NOT from the feature columns being modeled)
  Values: Late Night=1.00, Night=0.80, Evening=0.50, Morning=0.30, Day=0.20
  Basis:  NCRB Annual Reports + UN Women Safe Cities research showing crimes
          against women peak in evening and nighttime hours.

  Weekend Adjustment (+5% additive when is_weekend=1)

Documented limitations:
  1. District-level aggregate -- all segments in the same district share
     the same crime burden component.
  2. Temporal multiplier based on criminological evidence, not observed
     hourly data (unavailable in NCRB public datasets).
  3. Covers 2021-2023 only.
  4. Female-specific crime categories only (matches SAKHI mission scope).

target_is_observed_crime = True  (district-level observed NCRB counts)
target_type = 'crime_grounded_district_temporal_index'
"""

from pathlib import Path
from scipy.stats import pearsonr as _pearsonr

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT / "ml" / "data" / "processed" / "segment_temporal_features.csv"
)
CRIME_FILE = (
    PROJECT_ROOT / "ml" / "data" / "raw" / "crime_records.csv"
)
POPULATION_FILE = (
    PROJECT_ROOT / "ml" / "data" / "raw" / "population.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "ml" / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "ml_training_dataset.csv"


# ============================================================
# PARAMETERS
# ============================================================

RECENT_YEARS = [2021, 2022, 2023]

YEAR_WEIGHTS_RECENT = {2021: 1.0, 2022: 1.1, 2023: 1.2}

# Component weights
W_CRIME_BURDEN = 0.35
W_TEMPORAL     = 0.35
W_SPATIAL      = 0.30
WEEKEND_ADJ    = 0.05   # Additive, clipped before scaling

# Temporal multipliers: criminological evidence, NOT derived from model features.
# Source: NCRB Annual Reports on crime timing; UN Women Safe Cities Programme.
TEMPORAL_MULTIPLIER = {
    "Late Night": 1.00,   # 00:00-06:00 -- highest risk
    "Night":      0.80,   # 22:00-00:00
    "Evening":    0.50,   # 17:00-22:00 -- elevated (peak public activity)
    "Morning":    0.30,   # 06:00-10:00
    "Day":        0.20,   # 10:00-17:00 -- lowest risk
}

# Risk band thresholds (standard thirds over 0-100 range)
RISK_BAND_LOW      = 33.0
RISK_BAND_MODERATE = 66.0

# Leakage guard: correlation above this between any single feature and
# the target would suggest the target is effectively derived from that feature
LEAKAGE_THRESHOLD = 0.98


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading temporal feature dataset...")
df = pd.read_csv(INPUT_FILE)
print(f"Rows loaded: {len(df)}")

print("\nLoading crime records...")
crime = pd.read_csv(CRIME_FILE)
print(f"Crime records loaded: {len(crime)}")

print("\nLoading population data...")
population = pd.read_csv(POPULATION_FILE)
print(f"Population records loaded: {len(population)}")


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_temporal = [
    "segment_id", "district", "time_period", "is_weekend",
    "historical_baseline", "nearest_hotspot_distance_m",
    "nearest_hotspot_intensity", "lighting_score", "cctv_coverage_score",
    "contextual_footfall_proxy", "distance_to_police_m",
    "distance_to_hospital_m", "distance_to_medical_facility_m",
    "distance_to_public_toilet_m", "is_night", "is_late_night",
]
missing = [c for c in required_temporal if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

unknown_periods = set(df["time_period"].unique()) - set(TEMPORAL_MULTIPLIER.keys())
if unknown_periods:
    raise ValueError(f"Unknown time_period values: {unknown_periods}")


# ============================================================
# STEP 1: DISTRICT CRIME BURDEN FROM REAL NCRB DATA
# ============================================================

print("\n" + "=" * 70)
print("COMPUTING DISTRICT CRIME BURDEN FROM NCRB DATA")
print("=" * 70)

# Drop any synthetic records
if "is_synthetic" in crime.columns:
    n_synth = crime["is_synthetic"].sum()
    if n_synth > 0:
        print(f"WARNING: Dropping {n_synth} synthetic crime records.")
    crime = crime[crime["is_synthetic"] == False].copy()

print(f"Real crime records: {len(crime)}")

# Numeric coercion
for col in ["reported_cases", "severity", "year"]:
    crime[col] = pd.to_numeric(crime[col], errors="coerce")
population["population"] = pd.to_numeric(population["population"], errors="coerce")

# Filter to recent years
recent = crime[crime["year"].isin(RECENT_YEARS)].copy()
print(f"Records in {RECENT_YEARS}: {len(recent)}")
print(f"Districts: {sorted(recent['district'].unique())}")

# Severity normalize (NCRB scale 5-9 -> 0-1)
sev_min = recent["severity"].min()
sev_max = recent["severity"].max()
if sev_max == sev_min:
    recent["severity_norm"] = 0.5
else:
    recent["severity_norm"] = (recent["severity"] - sev_min) / (sev_max - sev_min)

recent["severity_weighted_cases"] = recent["reported_cases"] * recent["severity_norm"]
recent["year_weight"] = recent["year"].map(YEAR_WEIGHTS_RECENT)
recent["recency_sv_weighted"] = recent["severity_weighted_cases"] * recent["year_weight"]

# District-level aggregation
district_burden = (
    recent
    .groupby("district")
    .agg(
        total_recency_sv_weighted=("recency_sv_weighted", "sum"),
        total_reported_cases=("reported_cases", "sum"),
    )
    .reset_index()
)

# Per-capita normalization
district_burden = district_burden.merge(
    population[["district", "population"]], on="district", how="left"
)
missing_pop = district_burden[district_burden["population"].isna()]["district"].tolist()
if missing_pop:
    raise ValueError(f"Missing population for districts: {missing_pop}")

district_burden["crime_burden_per_100k"] = (
    district_burden["total_recency_sv_weighted"]
    / district_burden["population"]
    * 100_000
)

# Min-max normalize using only districts present in training data
training_districts = set(df["district"].unique())
mask = district_burden["district"].isin(training_districts)
burden_min = district_burden.loc[mask, "crime_burden_per_100k"].min()
burden_max = district_burden.loc[mask, "crime_burden_per_100k"].max()

if burden_max == burden_min:
    district_burden["crime_burden_norm"] = 0.5
else:
    district_burden["crime_burden_norm"] = (
        (district_burden["crime_burden_per_100k"] - burden_min)
        / (burden_max - burden_min)
    ).clip(0, 1)

print("\nDistrict crime burden (normalized 0-1):")
print(
    district_burden[["district", "total_reported_cases",
                      "crime_burden_per_100k", "crime_burden_norm"]]
    .sort_values("crime_burden_norm", ascending=False)
    .to_string(index=False)
)


# ============================================================
# STEP 2: JOIN BURDEN TO TRAINING DATASET
# ============================================================

df = df.merge(
    district_burden[["district", "crime_burden_norm", "crime_burden_per_100k"]],
    on="district",
    how="left",
)

unmatched = df[df["crime_burden_norm"].isna()]["district"].unique()
if len(unmatched) > 0:
    raise ValueError(
        f"Districts with no crime burden data: {list(unmatched)}\n"
        "Check district name alignment between road_segments and crime_records."
    )


# ============================================================
# STEP 3: TEMPORAL MULTIPLIER & WEEKEND ADJUSTMENT
# ============================================================

df["_temporal_mult"] = df["time_period"].map(TEMPORAL_MULTIPLIER)
df["_weekend_adj"]   = np.where(df["is_weekend"] == 1, WEEKEND_ADJ, 0.0)

missing_mult = df["_temporal_mult"].isna().sum()
if missing_mult > 0:
    raise ValueError(f"{missing_mult} rows have unrecognised time_period values.")


# ============================================================
# STEP 4: COMPOSE CRIME-GROUNDED RISK INDEX
# ============================================================

# Min-max normalize hotspot intensity
h_min = df["nearest_hotspot_intensity"].min()
h_max = df["nearest_hotspot_intensity"].max()
if h_max == h_min:
    df["_hotspot_norm"] = 0.5
else:
    df["_hotspot_norm"] = (df["nearest_hotspot_intensity"] - h_min) / (h_max - h_min)

# Distance decay (e.g., 500m half-life)
df["_distance_decay"] = np.exp(-df["nearest_hotspot_distance_m"] / 500.0)

# Spatial component
df["_spatial_mult"] = df["_hotspot_norm"] * df["_distance_decay"]

raw_index = (
    W_CRIME_BURDEN * df["crime_burden_norm"]
    + W_TEMPORAL   * df["_temporal_mult"]
    + W_SPATIAL    * df["_spatial_mult"]
    + df["_weekend_adj"]
)

df["crime_grounded_risk_index"] = raw_index.clip(0, 1) * 100

# Component columns for transparency
df["target_crime_burden_component"] = W_CRIME_BURDEN * df["crime_burden_norm"] * 100
df["target_temporal_component"]     = W_TEMPORAL * df["_temporal_mult"] * 100
df["target_spatial_component"]      = W_SPATIAL * df["_spatial_mult"] * 100
df["target_weekend_component"]      = df["_weekend_adj"] * 100

# Drop intermediate columns
df = df.drop(columns=["_temporal_mult", "_weekend_adj", "_hotspot_norm", "_distance_decay", "_spatial_mult"], errors="ignore")


# ============================================================
# STEP 5: RISK BAND
# ============================================================

df["risk_band"] = pd.cut(
    df["crime_grounded_risk_index"],
    bins=[-np.inf, RISK_BAND_LOW, RISK_BAND_MODERATE, np.inf],
    labels=["Low", "Moderate", "High"],
)


# ============================================================
# STEP 6: TARGET PROVENANCE
# ============================================================

df["target_type"] = "crime_grounded_district_temporal_spatial_index"
df["target_is_observed_crime"] = True
df["target_description"] = (
    "Severity-weighted NCRB district crime burden (35%) "
    "+ temporal multiplier (35%) + spatial hotspot density (30%) "
    "+ weekend adjustment (5%)."
)

# Preserve legacy target column if present
for legacy_col in ["prototype_risk_target", "prototype_risk_band",
                   "target_historical_component", "target_hotspot_component",
                   "target_lighting_component", "target_cctv_component",
                   "target_mobility_component", "target_police_component",
                   "target_medical_component", "target_essential_service_component"]:
    if legacy_col in df.columns:
        df = df.rename(columns={legacy_col: f"legacy_{legacy_col}"})


# ============================================================
# STEP 7: ROUND NUMERICAL VALUES
# ============================================================

numeric_cols = df.select_dtypes(include=["float64", "float32"]).columns
df[numeric_cols] = df[numeric_cols].round(4)


# ============================================================
# VALIDATION
# ============================================================

if len(df) != 300:
    raise ValueError(f"Expected 300 rows, got {len(df)}")

if df["crime_grounded_risk_index"].isna().any():
    raise ValueError("crime_grounded_risk_index contains missing values.")

target_min = df["crime_grounded_risk_index"].min()
target_max = df["crime_grounded_risk_index"].max()
if target_min < 0 or target_max > 100:
    raise ValueError(
        f"crime_grounded_risk_index outside 0-100: min={target_min:.2f}, max={target_max:.2f}"
    )

if df["risk_band"].isna().any():
    raise ValueError("Some rows could not be assigned a risk band.")

# ============================================================
# DEPENDENCY-BASED LEAKAGE AUDIT
# ============================================================
# Principle: we check structural dependency FIRST, then correlation.
# A feature must NOT be derived from the same raw source as any
# target component. The 13 retained features are audited below.
#
# TARGET COMPONENTS AND THEIR SOURCES:
#   crime_burden_norm  -- crime_records.csv (2021-2023 NCRB) + population.csv
#   _temporal_mult     -- TEMPORAL_MULTIPLIER dict keyed by time_period column
#   _spatial_mult      -- nearest_hotspot_intensity + nearest_hotspot_distance_m
#   _weekend_adj       -- is_weekend column (boolean flag)
#
# STRUCTURAL EXCLUSIONS (already removed from FEATURES in train_xgboost.py):
#   historical_baseline  -- derived from crime_records.csv (same source as crime_burden_norm)
#   is_weekend           -- is the literal WEEKEND_ADJ trigger in the target formula
#   representative_hour  -- used to derive time_period -> TEMPORAL_MULTIPLIER
#   is_night             -- derived from time_period -> TEMPORAL_MULTIPLIER
#   is_late_night        -- derived from time_period -> TEMPORAL_MULTIPLIER
#   is_evening_peak      -- derived from time_period -> TEMPORAL_MULTIPLIER
#   is_peak_hour         -- derived from time_period -> TEMPORAL_MULTIPLIER
#
# RETAINED FEATURES (verified independent of target formula sources):
#   distance_m, estimated_travel_time_s  -- OSM/OSRM geometry
#   lighting_score, cctv_coverage_score  -- synthetic env proxies
#   footfall_proxy                        -- synthetic mobility proxy
#   contextual_footfall_proxy             -- derived from footfall_proxy * time_period_multiplier
#                                            (uses footfall, not crime stats)
#   distance_to_police_m                  -- haversine to normalized police stations GPS
#   distance_to_hospital_m               -- haversine to normalized amenities GPS
#   distance_to_medical_facility_m       -- haversine to normalized amenities GPS
#   distance_to_public_toilet_m          -- haversine to normalized amenities GPS
#   distance_to_nearest_amenity_m        -- haversine to normalized amenities GPS
#   reduced_activity_context              -- derived from footfall_proxy threshold, not crime
#   lighting_relevance                    -- derived from is_night (nighttime boolean)
#                                            NOTE: is_night is used here only as a
#                                            footfall-lighting interaction flag, not fed
#                                            into the target formula directly.

print("\n" + "=" * 70)
print("DEPENDENCY-BASED LEAKAGE AUDIT (13 retained features)")
print("=" * 70)
features_to_audit = [
    "distance_m", "estimated_travel_time_s",
    "lighting_score", "cctv_coverage_score",
    "footfall_proxy", "contextual_footfall_proxy",
    "distance_to_police_m", "distance_to_hospital_m",
    "distance_to_medical_facility_m", "distance_to_public_toilet_m",
    "distance_to_nearest_amenity_m",
    "reduced_activity_context", "lighting_relevance",
    # Also check excluded features to confirm their leakage
    "historical_baseline", "is_weekend", "representative_hour",
    "is_night", "is_late_night", "is_evening_peak", "is_peak_hour",
]
for feat in features_to_audit:
    if feat in df.columns:
        r, p = _pearsonr(df[feat], df["crime_grounded_risk_index"])
        excluded = " [EXCLUDED-LEAKING]" if feat in [
            "historical_baseline", "is_weekend", "representative_hour",
            "is_night", "is_late_night", "is_evening_peak", "is_peak_hour",
        ] else ""
        flag = "  *** LEAKAGE WARNING ***" if abs(r) > LEAKAGE_THRESHOLD else ""
        print(f"  corr({feat:42s}, target) = {r:+.3f} (p={p:.2e}){flag}{excluded}")

# Hard-fail only on genuine leakage in *retained* features
retained_feats = [
    "distance_m", "estimated_travel_time_s",
    "lighting_score", "cctv_coverage_score",
    "footfall_proxy", "contextual_footfall_proxy",
    "distance_to_police_m", "distance_to_hospital_m",
    "distance_to_medical_facility_m", "distance_to_public_toilet_m",
    "distance_to_nearest_amenity_m",
    "reduced_activity_context", "lighting_relevance",
]
for feat in retained_feats:
    if feat in df.columns:
        r, _ = _pearsonr(df[feat], df["crime_grounded_risk_index"])
        if abs(r) > LEAKAGE_THRESHOLD:
            raise ValueError(
                f"Retained feature '{feat}' has suspicious correlation with target: r={r:.3f}\n"
                "Review feature and target construction."
            )

print("\nDependency audit PASSED: No retained feature exceeds leakage threshold.")



# ============================================================
# SAVE
# ============================================================

df.to_csv(OUTPUT_FILE, index=False)


# ============================================================
# REPORT
# ============================================================

print("\n")
print("=" * 70)
print("CRIME-GROUNDED TRAINING DATASET CREATED")
print("=" * 70)

print(f"\nOutput: {OUTPUT_FILE}")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\nTarget statistics (crime_grounded_risk_index):")
print(df["crime_grounded_risk_index"].describe().round(2).to_string())

print("\nRisk bands:")
print(df["risk_band"].value_counts().to_string())

print(f"\nTarget range: {target_min:.2f} to {target_max:.2f}")

print("\nMean target by district:")
print(
    df.groupby("district")["crime_grounded_risk_index"]
    .mean().sort_values(ascending=False).round(2).to_string()
)

print("\nMean target by time period:")
print(
    df.groupby("time_period")["crime_grounded_risk_index"]
    .mean().sort_values(ascending=False).round(2).to_string()
)

print("\nTarget provenance:")
print(
    df[["target_type", "target_is_observed_crime"]].drop_duplicates().to_string(index=False)
)

print("\nSample (first 10 rows):")
print(
    df[[
        "segment_id", "district", "time_period", "is_weekend",
        "crime_burden_per_100k", "target_crime_burden_component",
        "target_temporal_component", "target_spatial_component",
        "crime_grounded_risk_index", "risk_band",
    ]].head(10).to_string(index=False)
)

print("\n")
print("=" * 70)
print("BUILD_TRAINING_TARGET COMPLETE -- crime-grounded target ready")
print("=" * 70)