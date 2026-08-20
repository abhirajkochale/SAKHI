from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CRIME_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "crime_records.csv"
)

POPULATION_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "population.csv"
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
    / "district_historical_baseline.csv"
)


# =========================================================
# PARAMETERS
# =========================================================

BASELINE_START_YEAR = 2018
BASELINE_END_YEAR = 2023

# More recent years receive more weight.
# 2018 = 1.0
# 2019 = 1.1
# ...
# 2023 = 1.5

YEAR_WEIGHTS = {
    year: 1.0 + 0.1 * (year - BASELINE_START_YEAR)
    for year in range(
        BASELINE_START_YEAR,
        BASELINE_END_YEAR + 1
    )
}


# =========================================================
# LOAD DATA
# =========================================================

print("\nLoading crime data...")

crime = pd.read_csv(CRIME_FILE)

print(
    f"Crime records loaded: {len(crime)}"
)


print("\nLoading population data...")

population = pd.read_csv(
    POPULATION_FILE
)

print(
    f"Population records loaded: {len(population)}"
)


# =========================================================
# VALIDATION
# =========================================================

required_crime_columns = [
    "district",
    "crime_category",
    "reported_cases",
    "severity",
    "year",
    "month",
]

required_population_columns = [
    "district",
    "population",
]


missing_crime_columns = [
    column
    for column in required_crime_columns
    if column not in crime.columns
]

missing_population_columns = [
    column
    for column in required_population_columns
    if column not in population.columns
]


if missing_crime_columns:

    raise ValueError(
        "Missing crime columns: "
        + str(missing_crime_columns)
    )


if missing_population_columns:

    raise ValueError(
        "Missing population columns: "
        + str(missing_population_columns)
    )


# =========================================================
# DATA CLEANING
# =========================================================

crime["reported_cases"] = pd.to_numeric(
    crime["reported_cases"],
    errors="coerce"
)

crime["severity"] = pd.to_numeric(
    crime["severity"],
    errors="coerce"
)

crime["year"] = pd.to_numeric(
    crime["year"],
    errors="coerce"
)

crime["month"] = pd.to_numeric(
    crime["month"],
    errors="coerce"
)

population["population"] = pd.to_numeric(
    population["population"],
    errors="coerce"
)


# Remove records outside our defined period.

crime = crime[
    crime["year"].between(
        BASELINE_START_YEAR,
        BASELINE_END_YEAR
    )
].copy()


# =========================================================
# SEVERITY NORMALIZATION
# =========================================================

# Your dataset contains severity values:
# 5, 6, 7, 8, 9
#
# We normalize them to 0-1.

crime["severity_normalized"] = (
    crime["severity"] / 9.0
)


# =========================================================
# SEVERITY-WEIGHTED CASES
# =========================================================

crime["severity_weighted_cases"] = (
    crime["reported_cases"]
    * crime["severity_normalized"]
)


# =========================================================
# TEMPORAL WEIGHT
# =========================================================

crime["year_weight"] = (
    crime["year"]
    .map(YEAR_WEIGHTS)
)


# =========================================================
# RECENCY-WEIGHTED CASES
# =========================================================

crime["recency_weighted_cases"] = (
    crime["reported_cases"]
    * crime["year_weight"]
)


crime["recency_severity_weighted_cases"] = (
    crime["severity_weighted_cases"]
    * crime["year_weight"]
)


# =========================================================
# DISTRICT AGGREGATION
# =========================================================

district_stats = (
    crime
    .groupby("district")
    .agg(
        total_reported_cases=(
            "reported_cases",
            "sum"
        ),

        total_severity_weighted_cases=(
            "severity_weighted_cases",
            "sum"
        ),

        recency_weighted_cases=(
            "recency_weighted_cases",
            "sum"
        ),

        recency_severity_weighted_cases=(
            "recency_severity_weighted_cases",
            "sum"
        ),

        average_severity=(
            "severity",
            "mean"
        ),

        crime_record_count=(
            "reported_cases",
            "count"
        ),
    )
    .reset_index()
)


# =========================================================
# POPULATION JOIN
# =========================================================

district_stats = district_stats.merge(
    population[
        [
            "district",
            "population",
            "area_sq_km",
            "population_density",
        ]
    ],
    on="district",
    how="left",
    validate="one_to_one",
)


# =========================================================
# POPULATION VALIDATION
# =========================================================

missing_population = district_stats[
    district_stats["population"].isna()
]

if not missing_population.empty:

    raise ValueError(
        "Some districts have no population data:\n"
        + str(
            missing_population[
                ["district"]
            ]
        )
    )


# =========================================================
# POPULATION-NORMALIZED BURDEN
# =========================================================

district_stats["cases_per_100k"] = (
    district_stats["total_reported_cases"]
    / district_stats["population"]
    * 100000
)


district_stats["severity_weighted_cases_per_100k"] = (
    district_stats[
        "total_severity_weighted_cases"
    ]
    / district_stats["population"]
    * 100000
)


district_stats["recent_cases_per_100k"] = (
    district_stats[
        "recency_weighted_cases"
    ]
    / district_stats["population"]
    * 100000
)


district_stats["recent_severity_per_100k"] = (
    district_stats[
        "recency_severity_weighted_cases"
    ]
    / district_stats["population"]
    * 100000
)


# =========================================================
# YEARLY TREND
# =========================================================

yearly = (
    crime
    .groupby(
        ["district", "year"]
    )["reported_cases"]
    .sum()
    .reset_index()
)


trend_values = []


for district, group in yearly.groupby(
    "district"
):

    group = group.sort_values(
        "year"
    )

    x = group["year"].to_numpy(
        dtype=float
    )

    y = group["reported_cases"].to_numpy(
        dtype=float
    )

    if len(group) >= 2:

        slope = np.polyfit(
            x,
            y,
            1
        )[0]

    else:

        slope = 0.0

    trend_values.append(
        {
            "district": district,
            "crime_trend_slope": slope,
        }
    )


trend_df = pd.DataFrame(
    trend_values
)


district_stats = district_stats.merge(
    trend_df,
    on="district",
    how="left",
    validate="one_to_one",
)


# =========================================================
# NORMALIZATION HELPER
# =========================================================

def min_max_normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            0.5,
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    )


# =========================================================
# NORMALIZED COMPONENTS
# =========================================================

district_stats[
    "normalized_case_burden"
] = min_max_normalize(
    district_stats[
        "cases_per_100k"
    ]
)


district_stats[
    "normalized_severity_burden"
] = min_max_normalize(
    district_stats[
        "severity_weighted_cases_per_100k"
    ]
)


district_stats[
    "normalized_recent_burden"
] = min_max_normalize(
    district_stats[
        "recent_severity_per_100k"
    ]
)


district_stats[
    "normalized_trend"
] = min_max_normalize(
    district_stats[
        "crime_trend_slope"
    ]
)


# =========================================================
# HISTORICAL BASELINE
# =========================================================

# The baseline is intentionally interpretable.
#
# 40% historical crime burden
# 30% severity-weighted burden
# 20% recent burden
# 10% trend
#
# This is a CONTEXTUAL PRIOR.
# It is NOT the final SAFERA risk score.

district_stats[
    "historical_baseline"
] = (
    0.40
    * district_stats[
        "normalized_case_burden"
    ]

    + 0.30
    * district_stats[
        "normalized_severity_burden"
    ]

    + 0.20
    * district_stats[
        "normalized_recent_burden"
    ]

    + 0.10
    * district_stats[
        "normalized_trend"
    ]
)


# Convert to 0-100.

district_stats[
    "historical_baseline"
] = (
    district_stats[
        "historical_baseline"
    ]
    * 100
)


# =========================================================
# ROUND VALUES
# =========================================================

numeric_columns = district_stats.select_dtypes(
    include=["float64", "float32"]
).columns

district_stats[
    numeric_columns
] = district_stats[
    numeric_columns
].round(4)


# =========================================================
# SORT
# =========================================================

district_stats = district_stats.sort_values(
    "historical_baseline",
    ascending=False
)


# =========================================================
# SAVE
# =========================================================

district_stats.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# OUTPUT
# =========================================================

print("\n")
print("=" * 70)
print("NCRB HISTORICAL BASELINE CREATED")
print("=" * 70)

print(
    f"\nOutput file:\n{OUTPUT_FILE}"
)

print(
    f"\nDistricts processed: "
    f"{len(district_stats)}"
)

print("\nHistorical baseline:")

print(
    district_stats[
        [
            "district",
            "total_reported_cases",
            "cases_per_100k",
            "average_severity",
            "crime_trend_slope",
            "historical_baseline",
        ]
    ].to_string(
        index=False
    )
)