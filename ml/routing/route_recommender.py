from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ROUTE_RESULTS_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_test_results.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_recommendation.csv"
)


# ============================================================
# LOAD ROUTES
# ============================================================

print("\nLoading route comparison results...")

df = pd.read_csv(
    ROUTE_RESULTS_FILE
)

if df.empty:
    raise ValueError(
        "No route results available."
    )

print(
    f"Routes loaded: {len(df)}"
)


# ============================================================
# VALIDATE
# ============================================================

required_columns = [
    "mode",
    "segments",
    "segment_count",
    "distance_m",
    "travel_time_s",
    "average_risk",
    "maximum_risk",
    "routing_cost",
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:

    raise ValueError(
        "Missing route columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        (series - minimum)
        /
        (maximum - minimum)
    )


# ============================================================
# ROUTE SCORES
# ============================================================
#
# Lower is better.
#
# We combine:
#
# 50% safety
# 30% travel time
# 20% distance
#
# This is deliberately transparent and easy to explain
# during the hackathon.
#

df[
    "normalized_risk"
] = normalize(
    df[
        "average_risk"
    ]
)


df[
    "normalized_time"
] = normalize(
    df[
        "travel_time_s"
    ]
)


df[
    "normalized_distance"
] = normalize(
    df[
        "distance_m"
    ]
)


df[
    "recommendation_score"
] = (
    0.50
    *
    df[
        "normalized_risk"
    ]
    +
    0.30
    *
    df[
        "normalized_time"
    ]
    +
    0.20
    *
    df[
        "normalized_distance"
    ]
)


# ============================================================
# RECOMMENDATION
# ============================================================

best_index = (
    df[
        "recommendation_score"
    ]
    .idxmin()
)


recommended = df.loc[
    best_index
]


# ============================================================
# FASTEST ROUTE
# ============================================================

fastest = df.loc[
    df[
        "travel_time_s"
    ].idxmin()
]


# ============================================================
# SAFEST ROUTE
# ============================================================

safest = df.loc[
    df[
        "average_risk"
    ].idxmin()
]


# ============================================================
# COMPARISON
# ============================================================

time_difference = (
    recommended[
        "travel_time_s"
    ]
    -
    fastest[
        "travel_time_s"
    ]
)


risk_difference = (
    fastest[
        "average_risk"
    ]
    -
    recommended[
        "average_risk"
    ]
)


if fastest[
    "average_risk"
] > 0:

    risk_reduction_percent = (
        risk_difference
        /
        fastest[
            "average_risk"
        ]
        *
        100
    )

else:

    risk_reduction_percent = 0


# ============================================================
# DETERMINE ROUTE RELATIONSHIP
# ============================================================

recommended_segments = (
    str(
        recommended[
            "segments"
        ]
    )
)


fastest_segments = (
    str(
        fastest[
            "segments"
        ]
    )
)


if (
    recommended_segments
    ==
    fastest_segments
):

    route_relationship = (
        "same_as_fastest"
    )

elif (
    recommended_segments
    ==
    str(
        safest[
            "segments"
        ]
    )
):

    route_relationship = (
        "safest_route_selected"
    )

else:

    route_relationship = (
        "balanced_tradeoff"
    )


# ============================================================
# GENERATE EXPLANATION
# ============================================================

if route_relationship == "same_as_fastest":

    explanation = (
        "SAKHI recommends the same route as the "
        "fastest-route strategy because no lower-risk "
        "alternative route was identified in the current "
        "road network."
    )

elif route_relationship == "safest_route_selected":

    explanation = (
        "SAKHI recommends the safest available route "
        "because its reduction in contextual risk "
        "outweighs the additional travel cost."
    )

else:

    explanation = (
        "SAKHI recommends a balanced route because it "
        "provides a better safety-versus-travel-time "
        "trade-off than the fastest route."
    )


# ============================================================
# BUILD OUTPUT
# ============================================================

result = pd.DataFrame(
    [
        {
            "recommended_mode":
                recommended[
                    "mode"
                ],

            "recommended_segments":
                recommended[
                    "segments"
                ],

            "recommended_distance_m":
                recommended[
                    "distance_m"
                ],

            "recommended_travel_time_s":
                recommended[
                    "travel_time_s"
                ],

            "recommended_average_risk":
                recommended[
                    "average_risk"
                ],

            "recommended_maximum_risk":
                recommended[
                    "maximum_risk"
                ],

            "fastest_travel_time_s":
                fastest[
                    "travel_time_s"
                ],

            "safest_average_risk":
                safest[
                    "average_risk"
                ],

            "time_difference_s":
                round(
                    time_difference,
                    2
                ),

            "risk_reduction_percent":
                round(
                    risk_reduction_percent,
                    2
                ),

            "route_relationship":
                route_relationship,

            "explanation":
                explanation,
        }
    ]
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
print("SAKHI ROUTE RECOMMENDATION")
print("=" * 70)


print(
    f"\nRecommended mode:"
    f" {recommended['mode']}"
)


print(
    f"\nRecommended route:"
)


print(
    recommended[
        "segments"
    ]
)


print(
    f"\nDistance:"
    f" {recommended['distance_m']} m"
)


print(
    f"Travel time:"
    f" {recommended['travel_time_s']} s"
)


print(
    f"Average risk:"
    f" {recommended['average_risk']}"
)


print(
    f"Maximum risk:"
    f" {recommended['maximum_risk']}"
)


print(
    f"\nFastest route time:"
    f" {fastest['travel_time_s']} s"
)


print(
    f"Safest route risk:"
    f" {safest['average_risk']}"
)


print(
    f"\nTime difference:"
    f" {time_difference:.2f} s"
)


print(
    f"Risk reduction:"
    f" {risk_reduction_percent:.2f}%"
)


print(
    "\nExplanation:"
)


print(
    explanation
)


print("\n")
print("=" * 70)
print("STEP 2D COMPLETE")
print("=" * 70)


print(
    "\nSAKHI can now select and explain "
    "a safety-aware route."
)


print(
    "\nSTEP 2 COMPLETE"
)


print(
    "\nNext stage:"
)


print(
    "Step 3 → Route Intelligence"
)