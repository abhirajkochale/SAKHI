from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEMPORAL_DATA = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "segment_temporal_features.csv"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "sakhi_xgboost_risk_model.json"
)

CONFIDENCE_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "risk_with_confidence.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_ready_segments.csv"
)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [
    "historical_baseline",
    "cases_per_100k",
    "severity_weighted_cases_per_100k",
    "recent_cases_per_100k",
    "recent_severity_per_100k",
    "crime_trend_slope",

    "distance_m",
    "estimated_travel_time_s",

    "lighting_score",
    "cctv_coverage_score",
    "footfall_proxy",
    "contextual_footfall_proxy",

    "distance_to_police_m",
    "distance_to_hospital_m",
    "distance_to_medical_facility_m",
    "distance_to_public_toilet_m",
    "distance_to_nearest_amenity_m",

    "nearest_hotspot_distance_m",
    "nearest_hotspot_intensity",

    "representative_hour",
    "is_night",
    "is_late_night",
    "is_evening_peak",
    "is_weekend",
    "is_peak_hour",
    "reduced_activity_context",
    "lighting_relevance",
]


# ============================================================
# RISK BAND
# ============================================================

def get_risk_band(score):

    if score < 25:
        return "Low"

    if score < 40:
        return "Moderate"

    return "High"


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading XGBoost risk model...")

model = XGBRegressor()

model.load_model(
    MODEL_FILE
)

print("Model loaded successfully.")


# ============================================================
# LOAD TEMPORAL DATA
# ============================================================

print("\nLoading temporal segment data...")

df = pd.read_csv(
    TEMPORAL_DATA
)

print(
    f"Rows loaded: {len(df)}"
)


# ============================================================
# VALIDATE FEATURES
# ============================================================

missing_features = [
    feature
    for feature in FEATURES
    if feature not in df.columns
]

if missing_features:

    raise ValueError(
        "Missing model features:\n"
        + "\n".join(missing_features)
    )


# ============================================================
# PREPARE MODEL INPUT
# ============================================================

X = df[
    FEATURES
].copy()


# Make sure everything is numeric

for column in FEATURES:

    X[column] = pd.to_numeric(
        X[column],
        errors="coerce"
    )


# Check missing values

missing_counts = (
    X.isna()
    .sum()
)


if missing_counts.sum() > 0:

    print("\nMissing model inputs:")

    print(
        missing_counts[
            missing_counts > 0
        ]
        .to_string()
    )

    raise ValueError(
        "Model input contains missing values."
    )


# ============================================================
# PREDICT RISK
# ============================================================

print("\nGenerating segment risk scores...")

predictions = model.predict(
    X
)


df[
    "model_risk_score"
] = np.clip(
    predictions,
    0,
    100
)


# ============================================================
# RISK BANDS
# ============================================================

df[
    "model_risk_band"
] = df[
    "model_risk_score"
].apply(
    get_risk_band
)


# ============================================================
# LOAD CONFIDENCE DATA
# ============================================================

print("\nLoading confidence information...")

if CONFIDENCE_FILE.exists():

    confidence = pd.read_csv(
        CONFIDENCE_FILE
    )

    print(
        f"Confidence rows: "
        f"{len(confidence)}"
    )

    # Keep only useful columns
    confidence_columns = [
        "segment_id",
        "time_period",
        "is_weekend",
        "confidence_score",
        "confidence_level",
        "data_quality_score",
    ]

    available_columns = [
        column
        for column in confidence_columns
        if column in confidence.columns
    ]

    confidence = confidence[
        available_columns
    ].copy()

    # Merge confidence where available
    df = df.merge(
        confidence,
        on=[
            "segment_id",
            "time_period",
            "is_weekend",
        ],
        how="left",
    )

else:

    print(
        "WARNING: Confidence file not found."
    )

    df[
        "confidence_score"
    ] = 0

    df[
        "confidence_level"
    ] = "Unknown"

    df[
        "data_quality_score"
    ] = 0


# ============================================================
# HANDLE CONFIDENCE
# ============================================================

df[
    "confidence_score"
] = pd.to_numeric(
    df[
        "confidence_score"
    ],
    errors="coerce"
).fillna(0)


df[
    "data_quality_score"
] = pd.to_numeric(
    df[
        "data_quality_score"
    ],
    errors="coerce"
).fillna(0)


df[
    "confidence_level"
] = (
    df[
        "confidence_level"
    ]
    .fillna("Unknown")
)


# ============================================================
# ROUTING COST
# ============================================================
#
# This is the bridge between ML and routing.
#
# A route should not simply minimize distance.
#
# We create a safety-aware edge cost:
#
# routing_cost =
#     travel_time
#     ×
#     safety_multiplier
#
# Higher risk → higher routing cost.
#
# ============================================================

# Normalize risk from 0-100 to 0-1

df[
    "risk_normalized"
] = (
    df[
        "model_risk_score"
    ]
    / 100.0
)


# Safety multiplier

df[
    "safety_multiplier"
] = (
    1.0
    +
    2.0
    * df[
        "risk_normalized"
    ]
)


# Base travel time

df[
    "base_travel_time_s"
] = pd.to_numeric(
    df[
        "estimated_travel_time_s"
    ],
    errors="coerce"
)


# Final routing cost

df[
    "routing_cost"
] = (
    df[
        "base_travel_time_s"
    ]
    *
    df[
        "safety_multiplier"
    ]
)


# ============================================================
# SAFETY PENALTY
# ============================================================

df[
    "risk_penalty_s"
] = (
    df[
        "routing_cost"
    ]
    -
    df[
        "base_travel_time_s"
    ]
)


# ============================================================
# CONFIDENCE-AWARE ADJUSTMENT
# ============================================================
#
# Low-confidence predictions should not be treated as
# perfectly reliable.
#
# We therefore slightly reduce the safety penalty when
# confidence is low rather than pretending the estimate is
# exact.
#
# This prevents uncertainty from creating extreme routing
# behavior.
#

confidence_factor = (
    df[
        "confidence_score"
    ]
    / 100.0
)


df[
    "confidence_adjusted_risk"
] = (
    df[
        "model_risk_score"
    ]
    *
    (
        0.75
        +
        0.25
        *
        confidence_factor
    )
)


# ============================================================
# FINAL ROUTING COST
# ============================================================

df[
    "routing_cost"
] = (
    df[
        "base_travel_time_s"
    ]
    *
    (
        1
        +
        2
        *
        (
            df[
                "confidence_adjusted_risk"
            ]
            / 100
        )
    )
)


df[
    "risk_penalty_s"
] = (
    df[
        "routing_cost"
    ]
    -
    df[
        "base_travel_time_s"
    ]
)


# ============================================================
# ROUTE PRIORITY
# ============================================================

df[
    "route_priority"
] = np.select(
    [
        df[
            "model_risk_score"
        ] >= 60,

        df[
            "model_risk_score"
        ] >= 40,

        df[
            "model_risk_score"
        ] >= 25,
    ],
    [
        "Avoid if practical",
        "Use with caution",
        "Acceptable",
    ],
    default="Preferred",
)


# ============================================================
# OUTPUT COLUMNS
# ============================================================

output_columns = [
    "segment_id",
    "segment_name",

    "district",

    "midpoint_latitude",
    "midpoint_longitude",

    "time_period",
    "representative_hour",
    "is_weekend",

    "distance_m",
    "estimated_travel_time_s",

    "model_risk_score",
    "model_risk_band",

    "confidence_score",
    "confidence_level",

    "data_quality_score",

    "confidence_adjusted_risk",

    "base_travel_time_s",
    "risk_penalty_s",
    "routing_cost",

    "route_priority",

    "lighting_score",
    "cctv_coverage_score",
    "contextual_footfall_proxy",

    "distance_to_police_m",
    "distance_to_hospital_m",

    "nearest_hotspot_distance_m",
    "nearest_hotspot_intensity",
]


# Keep only columns that exist

output_columns = [
    column
    for column in output_columns
    if column in df.columns
]


output = df[
    output_columns
].copy()


# ============================================================
# ROUND NUMBERS
# ============================================================

numeric_columns = [
    "model_risk_score",
    "confidence_score",
    "data_quality_score",
    "confidence_adjusted_risk",
    "base_travel_time_s",
    "risk_penalty_s",
    "routing_cost",
]


for column in numeric_columns:

    if column in output.columns:

        output[column] = (
            pd.to_numeric(
                output[column],
                errors="coerce"
            )
            .round(2)
        )


# ============================================================
# VALIDATION
# ============================================================

if output[
    "model_risk_score"
].isna().any():

    raise ValueError(
        "Risk scores contain missing values."
    )


if output[
    "routing_cost"
].isna().any():

    raise ValueError(
        "Routing costs contain missing values."
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
print("ROUTE-READY RISK ENGINE CREATED")
print("=" * 70)


print(
    f"\nOutput:\n{OUTPUT_FILE}"
)


print(
    f"\nRows: {len(output)}"
)


print(
    f"\nUnique road segments: "
    f"{output['segment_id'].nunique()}"
)


print("\nRisk distribution:")

print(
    output[
        "model_risk_band"
    ]
    .value_counts()
    .to_string()
)


print("\nRoute priority:")

print(
    output[
        "route_priority"
    ]
    .value_counts()
    .to_string()
)


print("\nRisk statistics:")

print(
    output[
        "model_risk_score"
    ]
    .describe()
    .round(2)
    .to_string()
)


print("\nSample route-ready segments:")

print(
    output[
        [
            "segment_id",
            "segment_name",
            "district",
            "time_period",
            "model_risk_score",
            "model_risk_band",
            "confidence_score",
            "routing_cost",
            "route_priority",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


print("\n")
print("=" * 70)
print("STEP 2A COMPLETE")
print("=" * 70)

print(
    "\nSAKHI now has a safety-aware routing cost "
    "for every road segment and time context."
)

print(
    "\nNext stage:"
)

print(
    "Build road-network graph → Dijkstra/A* "
    "safety-aware routing"
)