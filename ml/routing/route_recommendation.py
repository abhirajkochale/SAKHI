from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

METRICS_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_safety_metrics.csv"
)

TRADEOFF_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_tradeoff_analysis.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_recommendation.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading route safety metrics...")

metrics = pd.read_csv(
    METRICS_FILE
)

print(
    f"Safety metric rows: {len(metrics)}"
)


print("\nLoading trade-off analysis...")

tradeoff = pd.read_csv(
    TRADEOFF_FILE
)

print(
    f"Trade-off rows: {len(tradeoff)}"
)


# ============================================================
# VALIDATION
# ============================================================

required_metrics = [
    "route_id",
    "segments",
    "segment_count",
    "time_period",
    "is_weekend",
    "distance_m",
    "travel_time_s",
    "average_risk",
    "maximum_risk",
    "high_risk_segments",
    "moderate_risk_segments",
    "low_risk_segments",
    "high_risk_percentage",
    "average_lighting_score",
    "average_cctv_score",
    "average_distance_to_police_m",
    "average_distance_to_hospital_m",
    "average_hotspot_distance_m",
    "average_hotspot_intensity",
    "night_context",
    "route_safety_score",
    "route_safety_band",
]

required_tradeoff = [
    "fastest_route_id",
    "safest_route_id",
    "fastest_travel_time_s",
    "safest_travel_time_s",
    "fastest_average_risk",
    "safest_average_risk",
    "additional_time_s",
    "risk_reduction_percent",
    "recommendation",
]


missing_metrics = [
    column
    for column in required_metrics
    if column not in metrics.columns
]

missing_tradeoff = [
    column
    for column in required_tradeoff
    if column not in tradeoff.columns
]


if missing_metrics:

    raise ValueError(
        "Missing route metric columns:\n"
        + "\n".join(missing_metrics)
    )


if missing_tradeoff:

    raise ValueError(
        "Missing trade-off columns:\n"
        + "\n".join(missing_tradeoff)
    )


if metrics.empty:

    raise ValueError(
        "No route metrics available."
    )


if tradeoff.empty:

    raise ValueError(
        "No trade-off analysis available."
    )


# ============================================================
# SELECT RECOMMENDED ROUTE
# ============================================================

# The safest route is the primary safety recommendation.
# If multiple routes have identical risk, use safety score
# and then travel time as tie-breakers.

metrics_sorted = metrics.sort_values(
    by=[
        "average_risk",
        "maximum_risk",
        "travel_time_s",
    ],
    ascending=[
        True,
        True,
        True,
    ],
)


recommended = metrics_sorted.iloc[0]


recommended_route_id = int(
    recommended["route_id"]
)


# ============================================================
# TRADE-OFF VALUES
# ============================================================

tradeoff_row = tradeoff.iloc[0]


fastest_route_id = int(
    tradeoff_row[
        "fastest_route_id"
    ]
)

safest_route_id = int(
    tradeoff_row[
        "safest_route_id"
    ]
)


additional_time = float(
    tradeoff_row[
        "additional_time_s"
    ]
)


risk_reduction = float(
    tradeoff_row[
        "risk_reduction_percent"
    ]
)


# ============================================================
# ROUTE CHARACTERISTICS
# ============================================================

distance_m = float(
    recommended[
        "distance_m"
    ]
)

travel_time_s = float(
    recommended[
        "travel_time_s"
    ]
)

average_risk = float(
    recommended[
        "average_risk"
    ]
)

maximum_risk = float(
    recommended[
        "maximum_risk"
    ]
)

route_safety_score = float(
    recommended[
        "route_safety_score"
    ]
)

route_safety_band = str(
    recommended[
        "route_safety_band"
    ]
)

high_risk_segments = int(
    recommended[
        "high_risk_segments"
    ]
)

moderate_risk_segments = int(
    recommended[
        "moderate_risk_segments"
    ]
)

low_risk_segments = int(
    recommended[
        "low_risk_segments"
    ]
)

lighting_score = float(
    recommended[
        "average_lighting_score"
    ]
)

cctv_score = float(
    recommended[
        "average_cctv_score"
    ]
)

police_distance = float(
    recommended[
        "average_distance_to_police_m"
    ]
)

hospital_distance = float(
    recommended[
        "average_distance_to_hospital_m"
    ]
)

hotspot_distance = float(
    recommended[
        "average_hotspot_distance_m"
    ]
)

hotspot_intensity = float(
    recommended[
        "average_hotspot_intensity"
    ]
)

time_period = str(
    recommended[
        "time_period"
    ]
)

is_weekend = int(
    recommended[
        "is_weekend"
    ]
)

night_context = bool(
    recommended[
        "night_context"
    ]
)


# ============================================================
# UNIT CONVERSION
# ============================================================

distance_km = (
    distance_m / 1000
)

travel_time_minutes = (
    travel_time_s / 60
)


# ============================================================
# SAFETY OBSERVATIONS
# ============================================================

observations = []


# Risk observation

if high_risk_segments > 0:

    observations.append(
        f"{high_risk_segments} segment(s) "
        "are classified as high risk."
    )

elif moderate_risk_segments > 0:

    observations.append(
        f"{moderate_risk_segments} segment(s) "
        "are classified as moderate risk, "
        "with no high-risk segments."
    )

else:

    observations.append(
        "No high-risk segments were identified."
    )


# Lighting observation

if lighting_score >= 75:

    observations.append(
        "The route has strong lighting coverage."
    )

elif lighting_score >= 50:

    observations.append(
        "The route has moderate lighting coverage."
    )

else:

    observations.append(
        "The route has relatively low lighting coverage."
    )


# CCTV observation

if cctv_score >= 75:

    observations.append(
        "CCTV coverage is strong."
    )

elif cctv_score >= 50:

    observations.append(
        "CCTV coverage is moderate."
    )

else:

    observations.append(
        "CCTV coverage is relatively limited."
    )


# Night observation

if night_context:

    observations.append(
        "This recommendation is for a night-time context, "
        "so contextual night risk is included."
    )


# ============================================================
# TRADE-OFF EXPLANATION
# ============================================================

if (
    recommended_route_id
    == fastest_route_id
    and
    recommended_route_id
    == safest_route_id
):

    tradeoff_explanation = (
        "The recommended route is both the fastest "
        "and safest available route."
    )

elif (
    recommended_route_id
    == safest_route_id
):

    tradeoff_explanation = (
        f"The recommended route reduces average risk "
        f"by {risk_reduction:.2f}% compared with the "
        f"fastest route, at the cost of approximately "
        f"{additional_time:.0f} additional seconds."
    )

else:

    tradeoff_explanation = (
        "The recommended route provides the best "
        "available safety profile in the current "
        "candidate set."
    )


# ============================================================
# FINAL EXPLANATION
# ============================================================

explanation = (
    f"SAKHI recommends Route {recommended_route_id}. "
    f"The route covers {distance_km:.2f} km and takes "
    f"approximately {travel_time_minutes:.1f} minutes. "
    f"Its average contextual risk is {average_risk:.2f}, "
    f"with a maximum segment risk of {maximum_risk:.2f}. "
    f"The overall route safety score is "
    f"{route_safety_score:.2f}/100 "
    f"({route_safety_band}). "
    f"{tradeoff_explanation} "
    + " ".join(observations)
)


# ============================================================
# SHORT USER-FACING SUMMARY
# ============================================================

if route_safety_band == "Safer":

    summary = (
        f"Recommended Route {recommended_route_id}: "
        f"Safer option with a safety score of "
        f"{route_safety_score:.1f}/100."
    )

elif route_safety_band == "Moderate":

    summary = (
        f"Recommended Route {recommended_route_id}: "
        f"Moderate safety profile with a score of "
        f"{route_safety_score:.1f}/100."
    )

else:

    summary = (
        f"Route {recommended_route_id}: "
        f"Higher-risk profile. Exercise caution."
    )


# ============================================================
# OUTPUT
# ============================================================

result = pd.DataFrame(
    [
        {
            "recommended_route_id":
                recommended_route_id,

            "segments":
                recommended[
                    "segments"
                ],

            "time_period":
                time_period,

            "is_weekend":
                is_weekend,

            "distance_m":
                round(
                    distance_m,
                    2
                ),

            "distance_km":
                round(
                    distance_km,
                    2
                ),

            "travel_time_s":
                round(
                    travel_time_s,
                    2
                ),

            "travel_time_minutes":
                round(
                    travel_time_minutes,
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

            "route_safety_score":
                round(
                    route_safety_score,
                    2
                ),

            "route_safety_band":
                route_safety_band,

            "high_risk_segments":
                high_risk_segments,

            "moderate_risk_segments":
                moderate_risk_segments,

            "low_risk_segments":
                low_risk_segments,

            "high_risk_percentage":
                round(
                    float(
                        recommended[
                            "high_risk_percentage"
                        ]
                    ),
                    2
                ),

            "lighting_score":
                round(
                    lighting_score,
                    2
                ),

            "cctv_score":
                round(
                    cctv_score,
                    2
                ),

            "average_distance_to_police_m":
                round(
                    police_distance,
                    2
                ),

            "average_distance_to_hospital_m":
                round(
                    hospital_distance,
                    2
                ),

            "average_hotspot_distance_m":
                round(
                    hotspot_distance,
                    2
                ),

            "average_hotspot_intensity":
                round(
                    hotspot_intensity,
                    2
                ),

            "night_context":
                night_context,

            "fastest_route_id":
                fastest_route_id,

            "safest_route_id":
                safest_route_id,

            "additional_time_s":
                round(
                    additional_time,
                    2
                ),

            "risk_reduction_percent":
                round(
                    risk_reduction,
                    2
                ),

            "summary":
                summary,

            "explanation":
                explanation,
        }
    ]
)


# ============================================================
# VALIDATION
# ============================================================

if result.empty:

    raise ValueError(
        "Route recommendation is empty."
    )


required_output = [
    "recommended_route_id",
    "route_safety_score",
    "route_safety_band",
    "summary",
    "explanation",
]


for column in required_output:

    if result[column].isna().any():

        raise ValueError(
            f"{column} contains missing values."
        )


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\n")
print("=" * 70)
print("STEP 3D: ROUTE RECOMMENDATION")
print("=" * 70)

print(
    f"\nRecommended route:"
    f" Route {recommended_route_id}"
)

print(
    f"Distance:"
    f" {distance_km:.2f} km"
)

print(
    f"Travel time:"
    f" {travel_time_minutes:.1f} minutes"
)

print(
    f"Average risk:"
    f" {average_risk:.2f}"
)

print(
    f"Maximum risk:"
    f" {maximum_risk:.2f}"
)

print(
    f"Route safety score:"
    f" {route_safety_score:.2f}/100"
)

print(
    f"Safety band:"
    f" {route_safety_band}"
)

print(
    f"High-risk segments:"
    f" {high_risk_segments}"
)

print(
    f"Lighting score:"
    f" {lighting_score:.2f}"
)

print(
    f"CCTV score:"
    f" {cctv_score:.2f}"
)

print(
    f"\nSummary:"
    f"\n{summary}"
)

print(
    f"\nExplanation:"
    f"\n{explanation}"
)


print("\n")
print("=" * 70)
print("STEP 3D COMPLETE")
print("=" * 70)

print(
    f"\nOutput:"
    f"\n{OUTPUT_FILE}"
)

print(
    "\nSTEP 3 ROUTE INTELLIGENCE COMPLETE."
)

print(
    "\nNext stage:"
    "\nStep 4 → Live/API integration and SAKHI backend connection"
)