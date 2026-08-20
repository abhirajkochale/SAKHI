from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "segment_context_features.csv"
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

OUTPUT_FILE = (
    OUTPUT_DIR
    / "segment_temporal_features.csv"
)


# ============================================================
# TEMPORAL CONTEXTS
# ============================================================

TIME_CONTEXTS = [
    {
        "time_period": "Morning",
        "start_hour": 6,
        "end_hour": 10,
        "representative_hour": 8,
    },
    {
        "time_period": "Day",
        "start_hour": 10,
        "end_hour": 17,
        "representative_hour": 13,
    },
    {
        "time_period": "Evening",
        "start_hour": 17,
        "end_hour": 22,
        "representative_hour": 19,
    },
    {
        "time_period": "Night",
        "start_hour": 22,
        "end_hour": 24,
        "representative_hour": 23,
    },
    {
        "time_period": "Late Night",
        "start_hour": 0,
        "end_hour": 6,
        "representative_hour": 2,
    },
]


# ============================================================
# LOAD
# ============================================================

print("\nLoading segment context data...")

segments = pd.read_csv(
    INPUT_FILE
)

print(
    f"Segments loaded: {len(segments)}"
)


# ============================================================
# VALIDATION
# ============================================================

if len(segments) != 30:

    raise ValueError(
        f"Expected 30 segments, found {len(segments)}"
    )


required_columns = [
    "segment_id",
    "footfall_proxy",
    "lighting_score",
    "historical_baseline",
]


missing = [
    column
    for column in required_columns
    if column not in segments.columns
]


if missing:

    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# BUILD TEMPORAL OBSERVATIONS
# ============================================================

rows = []


for _, segment in segments.iterrows():

    evening_footfall = float(
        segment["footfall_proxy"]
    )

    for context in TIME_CONTEXTS:

        period = context[
            "time_period"
        ]

        hour = context[
            "representative_hour"
        ]


        # ----------------------------------------------------
        # Temporal footfall proxy
        # ----------------------------------------------------
        #
        # The existing mobility data represents:
        #
        # Evening Peak (18:00-22:00)
        #
        # We therefore treat it as the reference value.
        #
        # These multipliers are prototype assumptions and
        # are explicitly labelled as synthetic/proxy data.
        #

        if period == "Morning":

            multiplier = 0.65

        elif period == "Day":

            multiplier = 0.55

        elif period == "Evening":

            multiplier = 1.00

        elif period == "Night":

            multiplier = 0.35

        else:

            multiplier = 0.20


        contextual_footfall = (
            evening_footfall
            * multiplier
        )


        # ----------------------------------------------------
        # Temporal flags
        # ----------------------------------------------------

        is_night = int(
            period in [
                "Night",
                "Late Night"
            ]
        )


        is_late_night = int(
            period == "Late Night"
        )


        is_evening_peak = int(
            period == "Evening"
        )


        # ----------------------------------------------------
        # Weekend observations
        # ----------------------------------------------------
        #
        # We create two observations for every time period:
        #
        # weekday
        # weekend
        #
        # This gives the model a weekend context without
        # claiming that we have observed weekend-specific
        # mobility measurements.
        #

        for is_weekend in [0, 1]:

            # Peak-hour definition
            is_peak_hour = int(
                period in [
                    "Morning",
                    "Evening"
                ]
            )

            row = segment.to_dict()

            row.update(
                {
                    "representative_hour": hour,
                    "time_period": period,

                    "is_night": is_night,
                    "is_late_night": is_late_night,
                    "is_evening_peak": is_evening_peak,

                    "is_weekend": is_weekend,
                    "is_peak_hour": is_peak_hour,

                    "base_evening_footfall":
                        evening_footfall,

                    "contextual_footfall_proxy":
                        round(
                            contextual_footfall,
                            2
                        ),

                    "temporal_data_synthetic":
                        True,
                }
            )

            rows.append(row)


# ============================================================
# DATAFRAME
# ============================================================

temporal = pd.DataFrame(
    rows
)


# ============================================================
# TEMPORAL RISK CONTEXT
# ============================================================
#
# This is NOT the final risk score.
#
# It is simply a contextual indicator representing reduced
# activity conditions during late hours.
#
# The ML model will eventually learn how this interacts with
# lighting, mobility, infrastructure and historical context.
#

temporal[
    "reduced_activity_context"
] = (
    temporal[
        "contextual_footfall_proxy"
    ]
    < temporal[
        "base_evening_footfall"
    ] * 0.5
).astype(int)


# ============================================================
# LOW-LIGHT CONTEXT
# ============================================================
#
# We don't claim that nighttime automatically means unsafe.
#
# Instead, nighttime makes lighting more relevant.
#

temporal[
    "lighting_relevance"
] = np.where(
    temporal["is_night"] == 1,
    1.0,
    0.5
)


# ============================================================
# VALIDATION
# ============================================================

expected_rows = (
    len(segments)
    * len(TIME_CONTEXTS)
    * 2
)

if len(temporal) != expected_rows:

    raise ValueError(
        f"Expected {expected_rows} rows, "
        f"got {len(temporal)}"
    )


if temporal["segment_id"].nunique() != 30:

    raise ValueError(
        "Segment count changed unexpectedly."
    )


# ============================================================
# SAVE
# ============================================================

temporal.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("TEMPORAL CONTEXT DATASET CREATED")
print("=" * 70)

print(
    f"\nOutput:\n{OUTPUT_FILE}"
)

print(
    f"\nRows: {len(temporal)}"
)

print(
    f"Columns: {len(temporal.columns)}"
)

print(
    f"\nSegments: "
    f"{temporal['segment_id'].nunique()}"
)

print(
    f"Time periods: "
    f"{temporal['time_period'].nunique()}"
)

print(
    f"Weekend/weekday contexts: "
    f"{temporal['is_weekend'].nunique()}"
)

print("\nTime distribution:")

print(
    temporal[
        "time_period"
    ].value_counts()
)

print("\nSample:")

print(
    temporal[
        [
            "segment_id",
            "district",
            "time_period",
            "representative_hour",
            "is_night",
            "is_late_night",
            "is_weekend",
            "contextual_footfall_proxy",
            "lighting_relevance",
        ]
    ]
    .head(15)
    .to_string(index=False)
)