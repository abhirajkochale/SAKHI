from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "candidate_routes.csv"
)

RISK_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_ready_segments.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_safety_metrics.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading candidate routes...")

routes = pd.read_csv(
    CANDIDATE_FILE
)

print(
    f"Candidate routes: {len(routes)}"
)


print("\nLoading segment risk data...")

risk = pd.read_csv(
    RISK_FILE
)

print(
    f"Risk rows: {len(risk)}"
)


# ============================================================
# VALIDATION
# ============================================================

required_route_columns = [
    "route_id",
    "segments",
    "segment_count",
    "distance_m",
    "travel_time_s",
    "time_period",
    "is_weekend",
]

required_risk_columns = [
    "segment_id",
    "time_period",
    "is_weekend",
    "model_risk_score",
    "model_risk_band",
    "lighting_score",
    "cctv_coverage_score",
    "distance_to_police_m",
    "distance_to_hospital_m",
    "nearest_hotspot_distance_m",
    "nearest_hotspot_intensity",
]


missing_routes = [
    column
    for column in required_route_columns
    if column not in routes.columns
]

missing_risk = [
    column
    for column in required_risk_columns
    if column not in risk.columns
]


if missing_routes:

    raise ValueError(
        "Missing candidate-route columns:\n"
        + "\n".join(missing_routes)
    )


if missing_risk:

    raise ValueError(
        "Missing risk columns:\n"
        + "\n".join(missing_risk)
    )


# ============================================================
# BUILD SEGMENT LOOKUP
# ============================================================

risk_lookup = {}

for _, row in risk.iterrows():

    key = (
        int(row["segment_id"]),
        str(row["time_period"]),
        int(row["is_weekend"]),
    )

    risk_lookup[key] = row


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_inverse(
    value,
    minimum,
    maximum
):

    if maximum == minimum:

        return 1.0

    value = max(
        minimum,
        min(
            value,
            maximum
        )
    )

    return (
        1
        -
        (
            value - minimum
        )
        /
        (
            maximum - minimum
        )
    )


# ============================================================
# PROCESS ROUTES
# ============================================================

results = []


for _, route in routes.iterrows():

    route_id = int(
        route["route_id"]
    )

    time_period = str(
        route["time_period"]
    )

    is_weekend = int(
        route["is_weekend"]
    )


    # --------------------------------------------------------
    # Parse segment IDs
    # --------------------------------------------------------

    segment_ids = [
        int(segment.strip())
        for segment
        in str(
            route["segments"]
        ).split("→")
    ]


    segment_records = []


    for segment_id in segment_ids:

        key = (
            segment_id,
            time_period,
            is_weekend,
        )

        if key not in risk_lookup:

            raise ValueError(
                f"No risk data found for "
                f"segment {segment_id}, "
                f"{time_period}, "
                f"weekend={is_weekend}"
            )

        segment_records.append(
            risk_lookup[key]
        )


    segment_df = pd.DataFrame(
        segment_records
    )


    # ========================================================
    # RISK METRICS
    # ========================================================

    risk_scores = pd.to_numeric(
        segment_df[
            "model_risk_score"
        ],
        errors="coerce"
    )


    average_risk = (
        risk_scores.mean()
    )

    maximum_risk = (
        risk_scores.max()
    )


    # --------------------------------------------------------
    # Risk bands
    # --------------------------------------------------------

    high_count = int(
        (
            segment_df[
                "model_risk_band"
            ]
            == "High"
        ).sum()
    )


    moderate_count = int(
        (
            segment_df[
                "model_risk_band"
            ]
            == "Moderate"
        ).sum()
    )


    low_count = int(
        (
            segment_df[
                "model_risk_band"
            ]
            == "Low"
        ).sum()
    )


    # ========================================================
    # ENVIRONMENTAL SAFETY
    # ========================================================

    lighting = pd.to_numeric(
        segment_df[
            "lighting_score"
        ],
        errors="coerce"
    )


    cctv = pd.to_numeric(
        segment_df[
            "cctv_coverage_score"
        ],
        errors="coerce"
    )


    police_distance = pd.to_numeric(
        segment_df[
            "distance_to_police_m"
        ],
        errors="coerce"
    )


    hospital_distance = pd.to_numeric(
        segment_df[
            "distance_to_hospital_m"
        ],
        errors="coerce"
    )


    hotspot_distance = pd.to_numeric(
        segment_df[
            "nearest_hotspot_distance_m"
        ],
        errors="coerce"
    )


    hotspot_intensity = pd.to_numeric(
        segment_df[
            "nearest_hotspot_intensity"
        ],
        errors="coerce"
    )


    average_lighting = (
        lighting.mean()
    )


    average_cctv = (
        cctv.mean()
    )


    average_police_distance = (
        police_distance.mean()
    )


    average_hospital_distance = (
        hospital_distance.mean()
    )


    average_hotspot_distance = (
        hotspot_distance.mean()
    )


    average_hotspot_intensity = (
        hotspot_intensity.mean()
    )


    # ========================================================
    # SAFETY COMPONENTS
    # ========================================================
    #
    # All components are normalized to approximately 0-100.
    #
    # Higher = safer.
    #


    lighting_component = (
        average_lighting
    )


    cctv_component = (
        average_cctv
    )


    police_component = (
        normalize_inverse(
            average_police_distance,
            0,
            5000
        )
        * 100
    )


    hospital_component = (
        normalize_inverse(
            average_hospital_distance,
            0,
            8000
        )
        * 100
    )


    hotspot_distance_component = (
        normalize_inverse(
            average_hotspot_distance,
            0,
            10000
        )
        * 100
    )


    hotspot_component = (
        100
        -
        average_hotspot_intensity
    )


    # ========================================================
    # RISK COMPONENT
    # ========================================================

    risk_safety_component = (
        max(
            0,
            100
            -
            average_risk
        )
    )


    # ========================================================
    # ROUTE SAFETY SCORE
    # ========================================================
    #
    # Transparent weighted score.
    #
    # Contextual risk receives the largest weight.
    #

    route_safety_score = (
        0.40
        *
        risk_safety_component

        +

        0.15
        *
        lighting_component

        +

        0.15
        *
        cctv_component

        +

        0.10
        *
        police_component

        +

        0.05
        *
        hospital_component

        +

        0.10
        *
        hotspot_distance_component

        +

        0.05
        *
        hotspot_component
    )


    route_safety_score = max(
        0,
        min(
            100,
            route_safety_score
        )
    )


    # ========================================================
    # ROUTE SAFETY BAND
    # ========================================================

    if route_safety_score >= 70:

        safety_band = "Safer"

    elif route_safety_score >= 45:

        safety_band = "Moderate"

    else:

        safety_band = "Higher Risk"


    # ========================================================
    # NIGHT RISK FLAG
    # ========================================================

    night_context = (
        time_period
        in [
            "Night",
            "Late Night"
        ]
    )


    # ========================================================
    # HIGH-RISK EXPOSURE
    # ========================================================

    high_risk_percentage = (
        high_count
        /
        len(segment_ids)
        *
        100
    )


    # ========================================================
    # ROUTE SUMMARY
    # ========================================================

    results.append(
        {
            "route_id":
                route_id,

            "segments":
                route["segments"],

            "segment_count":
                len(segment_ids),

            "time_period":
                time_period,

            "is_weekend":
                is_weekend,

            "distance_m":
                round(
                    float(
                        route[
                            "distance_m"
                        ]
                    ),
                    2
                ),

            "travel_time_s":
                round(
                    float(
                        route[
                            "travel_time_s"
                        ]
                    ),
                    2
                ),

            "average_risk":
                round(
                    average_risk,
                    2
                ),

            "maximum_risk":
                round(
                    maximum_risk,
                    2
                ),

            "high_risk_segments":
                high_count,

            "moderate_risk_segments":
                moderate_count,

            "low_risk_segments":
                low_count,

            "high_risk_percentage":
                round(
                    high_risk_percentage,
                    2
                ),

            "average_lighting_score":
                round(
                    average_lighting,
                    2
                ),

            "average_cctv_score":
                round(
                    average_cctv,
                    2
                ),

            "average_distance_to_police_m":
                round(
                    average_police_distance,
                    2
                ),

            "average_distance_to_hospital_m":
                round(
                    average_hospital_distance,
                    2
                ),

            "average_hotspot_distance_m":
                round(
                    average_hotspot_distance,
                    2
                ),

            "average_hotspot_intensity":
                round(
                    average_hotspot_intensity,
                    2
                ),

            "night_context":
                night_context,

            "route_safety_score":
                round(
                    route_safety_score,
                    2
                ),

            "route_safety_band":
                safety_band,
        }
    )


# ============================================================
# OUTPUT
# ============================================================

output = pd.DataFrame(
    results
)


# ============================================================
# VALIDATE
# ============================================================

if output.empty:

    raise ValueError(
        "No route safety metrics generated."
    )


if output[
    "route_safety_score"
].isna().any():

    raise ValueError(
        "Route safety score contains "
        "missing values."
    )


# ============================================================
# SAVE
# ============================================================

output.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\n")
print("=" * 70)
print("ROUTE-LEVEL SAFETY METRICS CREATED")
print("=" * 70)


print(
    f"\nOutput:"
    f"\n{OUTPUT_FILE}"
)


print(
    f"\nRoutes analyzed:"
    f" {len(output)}"
)


print("\nRoute safety scores:")

print(
    output[
        [
            "route_id",
            "average_risk",
            "maximum_risk",
            "average_lighting_score",
            "average_cctv_score",
            "high_risk_segments",
            "route_safety_score",
            "route_safety_band",
        ]
    ].to_string(
        index=False
    )
)


print("\n")
print("=" * 70)
print("STEP 3B COMPLETE")
print("=" * 70)


print(
    "\nSAKHI now evaluates safety at "
    "the complete-route level."
)


print(
    "\nNext:"
    "\nStep 3C → Safety vs travel-time trade-off"
)