from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PREDICTIONS_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "risk_predictions.csv"
)

FEATURES_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "segment_temporal_features.csv"
)

SHAP_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "shap_segment_explanations.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "risk_with_confidence.csv"
)


# ============================================================
# LOAD
# ============================================================

print("\nLoading model predictions...")

predictions = pd.read_csv(PREDICTIONS_FILE)

print(f"Prediction rows: {len(predictions)}")


print("\nLoading segment features...")

features = pd.read_csv(FEATURES_FILE)

print(f"Feature rows: {len(features)}")


print("\nLoading SHAP explanations...")

shap_df = pd.read_csv(SHAP_FILE)

print(f"SHAP rows: {len(shap_df)}")


# ============================================================
# BASIC COLUMN CHECKS
# ============================================================

prediction_columns = [
    "segment_id",
    "segment_name",
    "district",
    "time_period",
    "is_weekend",
    "predicted_risk",
]

feature_columns = [
    "segment_id",
    "confidence",
    "lighting_data_synthetic",
    "cctv_data_synthetic",
    "mobility_data_synthetic",
    "hotspot_data_synthetic",
]

shap_columns = [
    "segment_id",
    "time_period",
    "is_weekend",
    "top_feature_1_shap",
    "top_feature_2_shap",
    "top_feature_3_shap",
]


for column in prediction_columns:

    if column not in predictions.columns:
        raise ValueError(
            f"Missing prediction column: {column}"
        )


for column in feature_columns:

    if column not in features.columns:
        raise ValueError(
            f"Missing feature column: {column}"
        )


for column in shap_columns:

    if column not in shap_df.columns:
        raise ValueError(
            f"Missing SHAP column: {column}"
        )


# ============================================================
# CLEAN PREDICTIONS
# ============================================================

predictions["predicted_risk"] = pd.to_numeric(
    predictions["predicted_risk"],
    errors="coerce"
)

if predictions["predicted_risk"].isna().any():

    raise ValueError(
        "predicted_risk contains NaN values."
    )


# ============================================================
# SEGMENT-LEVEL DATA QUALITY
# ============================================================

feature_context = features[
    [
        "segment_id",
        "confidence",
        "lighting_data_synthetic",
        "cctv_data_synthetic",
        "mobility_data_synthetic",
        "hotspot_data_synthetic",
    ]
].copy()


# Remove duplicate segment rows
feature_context = feature_context.drop_duplicates(
    subset=["segment_id"]
)


# ------------------------------------------------------------
# Clean mapping confidence
# ------------------------------------------------------------

feature_context["confidence"] = pd.to_numeric(
    feature_context["confidence"],
    errors="coerce"
)


# If confidence is missing, use a conservative value.
feature_context["confidence"] = (
    feature_context["confidence"]
    .fillna(0.5)
)


# Convert 0-1 confidence to 0-100.
feature_context["mapping_confidence"] = np.where(
    feature_context["confidence"] <= 1,
    feature_context["confidence"] * 100,
    feature_context["confidence"],
)


feature_context["mapping_confidence"] = (
    feature_context["mapping_confidence"]
    .clip(0, 100)
)


# ------------------------------------------------------------
# Clean synthetic flags
# ------------------------------------------------------------

synthetic_columns = [
    "lighting_data_synthetic",
    "cctv_data_synthetic",
    "mobility_data_synthetic",
    "hotspot_data_synthetic",
]


for column in synthetic_columns:

    feature_context[column] = (
        feature_context[column]
        .fillna(True)
        .astype(bool)
    )


# ============================================================
# MERGE PREDICTIONS + DATA QUALITY
# ============================================================

preds_clean = predictions.drop(
    columns=[c for c in synthetic_columns if c in predictions.columns],
    errors="ignore"
)

df = preds_clean.merge(
    feature_context[
        [
            "segment_id",
            "mapping_confidence",
            "lighting_data_synthetic",
            "cctv_data_synthetic",
            "mobility_data_synthetic",
            "hotspot_data_synthetic",
        ]
    ],
    on="segment_id",
    how="left",
)


# ============================================================
# HANDLE MISSING DATA AFTER MERGE
# ============================================================

df["mapping_confidence"] = (
    pd.to_numeric(
        df["mapping_confidence"],
        errors="coerce"
    )
    .fillna(50.0)
    .clip(0, 100)
)


for column in synthetic_columns:

    df[column] = (
        df[column]
        .fillna(True)
        .astype(bool)
    )


# ============================================================
# RISK SCORE
# ============================================================

df["risk_score"] = (
    pd.to_numeric(
        df["predicted_risk"],
        errors="coerce"
    )
    .fillna(0)
    .clip(0, 100)
)


# ============================================================
# SYNTHETIC DATA RATIO
# ============================================================

df["synthetic_data_ratio"] = (
    df[synthetic_columns]
    .astype(int)
    .mean(axis=1)
)


# ============================================================
# DATA QUALITY SCORE
# ============================================================

df["data_quality_score"] = (
    100
    * (
        1
        - df["synthetic_data_ratio"]
    )
)


# ============================================================
# SHAP EVIDENCE
# ============================================================

shap_context = shap_df[
    [
        "segment_id",
        "time_period",
        "is_weekend",
        "top_feature_1_shap",
        "top_feature_2_shap",
        "top_feature_3_shap",
    ]
].copy()


# Clean SHAP numbers

for column in [
    "top_feature_1_shap",
    "top_feature_2_shap",
    "top_feature_3_shap",
]:

    shap_context[column] = pd.to_numeric(
        shap_context[column],
        errors="coerce"
    )


# Replace missing SHAP values with zero

shap_context[
    [
        "top_feature_1_shap",
        "top_feature_2_shap",
        "top_feature_3_shap",
    ]
] = shap_context[
    [
        "top_feature_1_shap",
        "top_feature_2_shap",
        "top_feature_3_shap",
    ]
].fillna(0)


# Calculate SHAP evidence strength

shap_context["shap_evidence_strength"] = (
    shap_context[
        [
            "top_feature_1_shap",
            "top_feature_2_shap",
            "top_feature_3_shap",
        ]
    ]
    .abs()
    .sum(axis=1)
)


# ============================================================
# MATCH SHAP TO PREDICTIONS
# ============================================================

prediction_keys = predictions[
    [
        "segment_id",
        "time_period",
        "is_weekend",
    ]
].copy()


prediction_keys = prediction_keys.drop_duplicates()


shap_context = shap_context.merge(
    prediction_keys,
    on=[
        "segment_id",
        "time_period",
        "is_weekend",
    ],
    how="inner",
)


# ============================================================
# COLLAPSE DUPLICATES
# ============================================================

shap_context = (
    shap_context
    .groupby(
        [
            "segment_id",
            "time_period",
            "is_weekend",
        ],
        as_index=False
    )[
        "shap_evidence_strength"
    ]
    .mean()
)


# ============================================================
# MERGE SHAP
# ============================================================

df = df.merge(
    shap_context,
    on=[
        "segment_id",
        "time_period",
        "is_weekend",
    ],
    how="left",
    validate="many_to_one",
)


# Missing SHAP means we don't have explanation evidence
# for that particular prediction.

df["shap_evidence_strength"] = (
    pd.to_numeric(
        df["shap_evidence_strength"],
        errors="coerce"
    )
    .fillna(0)
)


# ============================================================
# SHAP EVIDENCE SCORE
# ============================================================

max_shap = df[
    "shap_evidence_strength"
].max()


if (
    pd.isna(max_shap)
    or max_shap <= 0
):

    df["shap_evidence_score"] = 50.0

else:

    df["shap_evidence_score"] = (
        df["shap_evidence_strength"]
        / max_shap
        * 100
    )


# ============================================================
# FINAL SAFETY CLEANING
# ============================================================

confidence_inputs = [
    "data_quality_score",
    "mapping_confidence",
    "shap_evidence_score",
]


for column in confidence_inputs:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    # Conservative fallback if something is still missing
    df[column] = (
        df[column]
        .fillna(50.0)
        .clip(0, 100)
    )


# ============================================================
# CONFIDENCE SCORE
# ============================================================

df["confidence_score"] = (
    0.45
    * df["data_quality_score"]

    +

    0.35
    * df["mapping_confidence"]

    +

    0.20
    * df["shap_evidence_score"]
)


df["confidence_score"] = (
    df["confidence_score"]
    .fillna(50.0)
    .clip(0, 100)
)


# ============================================================
# CONFIDENCE LEVEL
# ============================================================

df["confidence_level"] = pd.cut(
    df["confidence_score"],
    bins=[
        -np.inf,
        40,
        70,
        np.inf,
    ],
    labels=[
        "Low",
        "Moderate",
        "High",
    ],
)


# ============================================================
# RISK BAND
# ============================================================

df["risk_band"] = pd.cut(
    df["risk_score"],
    bins=[
        -np.inf,
        25,
        40,
        np.inf,
    ],
    labels=[
        "Low",
        "Moderate",
        "High",
    ],
)


# ============================================================
# DATA QUALITY NOTE
# ============================================================

def data_quality_note(row):

    synthetic = []

    if row["lighting_data_synthetic"]:
        synthetic.append("lighting")

    if row["cctv_data_synthetic"]:
        synthetic.append("CCTV")

    if row["mobility_data_synthetic"]:
        synthetic.append("mobility")

    if row["hotspot_data_synthetic"]:
        synthetic.append("crime hotspots")

    if len(synthetic) == 0:

        return (
            "Contextual inputs are based on "
            "non-synthetic data."
        )

    return (
        "Prototype/proxy inputs used: "
        + ", ".join(synthetic)
        + "."
    )


df["data_quality_note"] = df.apply(
    data_quality_note,
    axis=1
)


# ============================================================
# CONFIDENCE NOTE
# ============================================================

def confidence_note(row):

    level = str(
        row["confidence_level"]
    )

    if level == "High":

        return (
            "Higher confidence based on "
            "available contextual coverage."
        )

    if level == "Moderate":

        return (
            "Moderate confidence; some contextual "
            "inputs are proxy-based."
        )

    return (
        "Lower confidence; interpret this "
        "risk estimate cautiously."
    )


df["confidence_note"] = df.apply(
    confidence_note,
    axis=1
)


# ============================================================
# OUTPUT
# ============================================================

output_columns = [
    "segment_id",
    "segment_name",
    "district",
    "time_period",
    "is_weekend",

    "risk_score",
    "risk_band",

    "confidence_score",
    "confidence_level",

    "data_quality_score",
    "mapping_confidence",
    "synthetic_data_ratio",

    "shap_evidence_score",

    "data_quality_note",
    "confidence_note",
]


output = df[
    output_columns
].copy()


# ============================================================
# ROUND
# ============================================================

numeric_columns = [
    "risk_score",
    "confidence_score",
    "data_quality_score",
    "mapping_confidence",
    "synthetic_data_ratio",
    "shap_evidence_score",
]


for column in numeric_columns:

    output[column] = pd.to_numeric(
        output[column],
        errors="coerce"
    ).round(2)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\nChecking final confidence fields...")

for column in [
    "risk_score",
    "confidence_score",
    "data_quality_score",
    "mapping_confidence",
    "shap_evidence_score",
]:

    missing_count = output[
        column
    ].isna().sum()

    print(
        f"{column}: "
        f"{missing_count} missing"
    )

    if missing_count > 0:

        raise ValueError(
            f"{column} still contains "
            "missing values."
        )


if len(output) != len(predictions):

    raise ValueError(
        "Output row count does not match "
        "prediction row count."
    )


# ============================================================
# SAVE
# ============================================================

output.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("\n")
print("=" * 70)
print("CONFIDENCE-AWARE RISK DATASET CREATED")
print("=" * 70)

print(
    f"\nOutput:\n{OUTPUT_FILE}"
)

print(
    f"\nRows: {len(output)}"
)


print("\nRisk bands:")

print(
    output[
        "risk_band"
    ]
    .value_counts()
    .to_string()
)


print("\nConfidence levels:")

print(
    output[
        "confidence_level"
    ]
    .value_counts()
    .to_string()
)


print("\nConfidence statistics:")

print(
    output[
        "confidence_score"
    ]
    .describe()
    .round(2)
    .to_string()
)


print("\nData quality statistics:")

print(
    output[
        "data_quality_score"
    ]
    .describe()
    .round(2)
    .to_string()
)


print("\nSample:")

print(
    output[
        [
            "segment_id",
            "district",
            "time_period",
            "risk_score",
            "risk_band",
            "confidence_score",
            "confidence_level",
            "data_quality_score",
            "mapping_confidence",
        ]
    ]
    .head(15)
    .to_string(index=False)
)


print("\n")
print("=" * 70)
print("STEP 1J COMPLETE")
print("=" * 70)

print(
    "\nSAFERA now has:"
)

print(
    "Risk Score + Risk Band + Confidence + Data Quality"
)

print(
    "\nNext stage:"
)

print(
    "Risk Engine -> Route Optimization"
)