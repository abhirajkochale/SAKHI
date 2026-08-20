from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "ml_training_dataset.csv"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "sakhi_xgboost_risk_model.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SHAP_OUTPUT_FILE = (
    OUTPUT_DIR
    / "shap_segment_explanations.csv"
)

GLOBAL_OUTPUT_FILE = (
    OUTPUT_DIR
    / "shap_global_importance.csv"
)


# ============================================================
# FEATURES
# ============================================================
#
# MUST MATCH THE FEATURES USED DURING XGBOOST TRAINING.
#

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
# LOAD DATA
# ============================================================

print("\nLoading training dataset...")

df = pd.read_csv(
    DATA_FILE
)

print(
    f"Rows loaded: {len(df)}"
)


# ============================================================
# VALIDATE FEATURES
# ============================================================

missing = [
    feature
    for feature in FEATURES
    if feature not in df.columns
]

if missing:

    raise ValueError(
        "Missing required features:\n"
        + "\n".join(missing)
    )


X = df[
    FEATURES
].copy()


# ============================================================
# LOAD XGBOOST MODEL
# ============================================================

print(
    "\nLoading trained XGBoost model..."
)

from xgboost import XGBRegressor

model = XGBRegressor()

model.load_model(
    MODEL_FILE
)

print(
    "Model loaded successfully."
)


# ============================================================
# CREATE SHAP EXPLAINER
# ============================================================

print(
    "\nCreating SHAP TreeExplainer..."
)

explainer = shap.TreeExplainer(
    model
)


# ============================================================
# CALCULATE SHAP VALUES
# ============================================================

print(
    "Calculating SHAP values..."
)

shap_values = explainer.shap_values(
    X
)

shap_values = np.asarray(
    shap_values
)


print(
    f"SHAP matrix shape: "
    f"{shap_values.shape}"
)


# ============================================================
# GLOBAL SHAP IMPORTANCE
# ============================================================
#
# Mean absolute SHAP value tells us how strongly each feature
# influences the model across the entire dataset.
#

mean_abs_shap = np.mean(
    np.abs(shap_values),
    axis=0
)


global_importance = pd.DataFrame(
    {
        "feature": FEATURES,
        "mean_abs_shap": mean_abs_shap,
    }
)


global_importance = (
    global_importance
    .sort_values(
        "mean_abs_shap",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


global_importance[
    "rank"
] = (
    global_importance.index
    + 1
)


global_importance = global_importance[
    [
        "rank",
        "feature",
        "mean_abs_shap",
    ]
]


global_importance[
    "mean_abs_shap"
] = global_importance[
    "mean_abs_shap"
].round(4)


global_importance.to_csv(
    GLOBAL_OUTPUT_FILE,
    index=False
)


# ============================================================
# SEGMENT-LEVEL EXPLANATIONS
# ============================================================

print(
    "\nBuilding segment-level explanations..."
)


explanation_rows = []


for index in range(
    len(df)
):

    row = df.iloc[index]

    values = shap_values[
        index
    ]

    prediction = model.predict(
        X.iloc[
            [index]
        ]
    )[0]

    prediction = float(
        np.clip(
            prediction,
            0,
            100
        )
    )


    # --------------------------------------------------------
    # Sort SHAP contributions by absolute magnitude
    # --------------------------------------------------------

    feature_contributions = sorted(
        zip(
            FEATURES,
            values
        ),
        key=lambda item: abs(
            item[1]
        ),
        reverse=True
    )


    # --------------------------------------------------------
    # Top 5 contributing features
    # --------------------------------------------------------

    top_features = (
        feature_contributions[:5]
    )


    # --------------------------------------------------------
    # Build human-readable explanation
    # --------------------------------------------------------

    explanation_parts = []


    for feature, contribution in top_features:

        direction = (
            "increased"
            if contribution > 0
            else "reduced"
        )

        explanation_parts.append(
            f"{feature} "
            f"{direction} risk "
            f"({contribution:+.2f})"
        )


    explanation = (
        "; ".join(
            explanation_parts
        )
    )


    # --------------------------------------------------------
    # Store row
    # --------------------------------------------------------

    explanation_rows.append(
        {
            "segment_id": row[
                "segment_id"
            ],

            "segment_name": row[
                "segment_name"
            ],

            "district": row[
                "district"
            ],

            "time_period": row[
                "time_period"
            ],

            "is_weekend": row[
                "is_weekend"
            ],

            "model_risk_score": round(
                prediction,
                4
            ),

            "target_risk_score": row[
                "crime_grounded_risk_index"
            ],

            "risk_band": row[
                "risk_band"
            ],

            "top_feature_1": top_features[0][0],
            "top_feature_1_shap": round(
                float(
                    top_features[0][1]
                ),
                4
            ),

            "top_feature_2": top_features[1][0],
            "top_feature_2_shap": round(
                float(
                    top_features[1][1]
                ),
                4
            ),

            "top_feature_3": top_features[2][0],
            "top_feature_3_shap": round(
                float(
                    top_features[2][1]
                ),
                4
            ),

            "top_feature_4": top_features[3][0],
            "top_feature_4_shap": round(
                float(
                    top_features[3][1]
                ),
                4
            ),

            "top_feature_5": top_features[4][0],
            "top_feature_5_shap": round(
                float(
                    top_features[4][1]
                ),
                4
            ),

            "explanation": explanation,
        }
    )


# ============================================================
# SAVE SEGMENT EXPLANATIONS
# ============================================================

segment_explanations = pd.DataFrame(
    explanation_rows
)


segment_explanations.to_csv(
    SHAP_OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("\n")
print("=" * 70)
print("SHAP EXPLAINABILITY CREATED")
print("=" * 70)


print(
    f"\nSegment explanations:"
    f"\n{SHAP_OUTPUT_FILE}"
)


print(
    f"\nGlobal importance:"
    f"\n{GLOBAL_OUTPUT_FILE}"
)


print(
    f"\nRows explained: "
    f"{len(segment_explanations)}"
)


# ============================================================
# TOP GLOBAL FEATURES
# ============================================================

print("\n")
print("=" * 70)
print("TOP GLOBAL SHAP FEATURES")
print("=" * 70)

print(
    global_importance
    .head(15)
    .to_string(index=False)
)


# ============================================================
# SAMPLE EXPLANATIONS
# ============================================================

print("\n")
print("=" * 70)
print("SAMPLE SEGMENT EXPLANATIONS")
print("=" * 70)


print(
    segment_explanations[
        [
            "segment_id",
            "district",
            "time_period",
            "model_risk_score",
            "top_feature_1",
            "top_feature_1_shap",
            "top_feature_2",
            "top_feature_2_shap",
            "top_feature_3",
            "top_feature_3_shap",
            "explanation",
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\n")
print("=" * 70)
print("STEP 1I COMPLETE")
print("=" * 70)

print(
    "\nSAFERA now has explainable contextual risk scoring."
)

print(
    "\nNext stage:"
)

print(
    "SHAP -> Confidence-aware risk estimation"
)