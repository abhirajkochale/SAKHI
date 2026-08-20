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

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "route_tradeoff_analysis.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading route safety metrics...")

df = pd.read_csv(METRICS_FILE)

print(f"Routes loaded: {len(df)}")


# ============================================================
# VALIDATION
# ============================================================

required_columns = [
    "route_id",
    "distance_m",
    "travel_time_s",
    "average_risk",
    "maximum_risk",
    "route_safety_score",
    "route_safety_band",
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:
    raise ValueError(
        "Missing columns:\n"
        + "\n".join(missing)
    )

if df.empty:
    raise ValueError(
        "No routes available for comparison."
    )


# ============================================================
# FIND FASTEST AND SAFEST ROUTES
# ============================================================

fastest_idx = df["travel_time_s"].idxmin()

safest_idx = df["average_risk"].idxmin()

fastest = df.loc[fastest_idx]

safest = df.loc[safest_idx]


# ============================================================
# BASE VALUES
# ============================================================

fastest_route_id = int(
    fastest["route_id"]
)

safest_route_id = int(
    safest["route_id"]
)

fastest_time = float(
    fastest["travel_time_s"]
)

safest_time = float(
    safest["travel_time_s"]
)

fastest_risk = float(
    fastest["average_risk"]
)

safest_risk = float(
    safest["average_risk"]
)


# ============================================================
# CALCULATE TIME DIFFERENCE
# ============================================================

time_difference = (
    safest_time
    - fastest_time
)

if abs(time_difference) < 0.01:
    time_difference = 0.0


# ============================================================
# CALCULATE RISK REDUCTION
# ============================================================

if fastest_risk > 0:

    risk_reduction = (
        (
            fastest_risk
            - safest_risk
        )
        / fastest_risk
    ) * 100

else:

    risk_reduction = 0.0


if abs(risk_reduction) < 0.01:
    risk_reduction = 0.0


# ============================================================
# RECOMMENDATION LOGIC
# ============================================================

if len(df) == 1:

    recommendation = (
        "Only one connected candidate route "
        "is currently available in the prototype "
        "road network. No lower-risk alternative "
        "route was identified."
    )

elif fastest_route_id == safest_route_id:

    recommendation = (
        "SAKHI recommends the same route as the "
        "fastest-route strategy because it is also "
        "the safest available route."
    )

elif (
    risk_reduction >= 20
    and time_difference <= 600
):

    recommendation = (
        "SAKHI recommends the safer route because "
        "it provides a substantial risk reduction "
        "with a reasonable additional travel time."
    )

elif (
    risk_reduction >= 10
    and time_difference <= 900
):

    recommendation = (
        "SAKHI recommends considering the safer route "
        "because the reduction in risk justifies the "
        "additional travel time."
    )

else:

    recommendation = (
        "The safer route requires a larger time "
        "trade-off for the available reduction in risk."
    )


# ============================================================
# CREATE OUTPUT
# ============================================================

result = pd.DataFrame(
    [
        {
            "fastest_route_id":
                fastest_route_id,

            "safest_route_id":
                safest_route_id,

            "fastest_travel_time_s":
                round(
                    fastest_time,
                    2
                ),

            "safest_travel_time_s":
                round(
                    safest_time,
                    2
                ),

            "fastest_average_risk":
                round(
                    fastest_risk,
                    2
                ),

            "safest_average_risk":
                round(
                    safest_risk,
                    2
                ),

            "additional_time_s":
                round(
                    time_difference,
                    2
                ),

            "risk_reduction_percent":
                round(
                    risk_reduction,
                    2
                ),

            "fastest_route_safety_band":
                fastest[
                    "route_safety_band"
                ],

            "safest_route_safety_band":
                safest[
                    "route_safety_band"
                ],

            "recommendation":
                recommendation,
        }
    ]
)


# ============================================================
# VALIDATE OUTPUT
# ============================================================

if result.empty:

    raise ValueError(
        "Trade-off analysis produced no results."
    )

if result[
    "additional_time_s"
].isna().any():

    raise ValueError(
        "Additional travel time contains "
        "missing values."
    )

if result[
    "risk_reduction_percent"
].isna().any():

    raise ValueError(
        "Risk reduction contains "
        "missing values."
    )


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("STEP 3C: SAFETY VS TRAVEL-TIME TRADE-OFF")
print("=" * 70)

print(
    f"\nFastest route:"
    f" {fastest_route_id}"
)

print(
    f"Fastest travel time:"
    f" {fastest_time:.1f} s"
)

print(
    f"Fastest average risk:"
    f" {fastest_risk:.2f}"
)

print(
    f"\nSafest route:"
    f" {safest_route_id}"
)

print(
    f"Safest travel time:"
    f" {safest_time:.1f} s"
)

print(
    f"Safest average risk:"
    f" {safest_risk:.2f}"
)

print(
    f"\nAdditional travel time:"
    f" {time_difference:.1f} s"
)

print(
    f"Risk reduction:"
    f" {risk_reduction:.2f}%"
)

print(
    f"\nRecommendation:\n"
    f"{recommendation}"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n")
print("=" * 70)
print("STEP 3C COMPLETE")
print("=" * 70)

print(
    f"\nOutput:"
    f"\n{OUTPUT_FILE}"
)

print(
    "\nNext:"
    "\nStep 3D → Route recommendation and explanation"
)