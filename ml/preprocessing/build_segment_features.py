from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw"
SYNTHETIC_DIR = PROJECT_ROOT / "ml" / "data" / "synthetic"
PROCESSED_DIR = PROJECT_ROOT / "ml" / "data" / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


ROAD_FILE = RAW_DIR / "road_segments.csv"
POLICE_FILE = RAW_DIR / "police_stations.csv"
HOSPITAL_FILE = RAW_DIR / "hospitals.csv"
MEDICAL_FILE = RAW_DIR / "medical_facilities.csv"
AMENITY_FILE = RAW_DIR / "public_amenities.csv"

LIGHTING_FILE = SYNTHETIC_DIR / "synthetic_lighting.csv"
CCTV_FILE = SYNTHETIC_DIR / "synthetic_cctv.csv"
MOBILITY_FILE = SYNTHETIC_DIR / "synthetic_mobility.csv"
HOTSPOT_FILE = SYNTHETIC_DIR / "synthetic_crime_hotspots.csv"

DISTRICT_MAP_FILE = (
    PROCESSED_DIR /
    "segment_district_mapping.csv"
)

BASELINE_FILE = (
    PROCESSED_DIR /
    "district_historical_baseline.csv"
)

OUTPUT_FILE = (
    PROCESSED_DIR /
    "segment_context_features.csv"
)


# ============================================================
# CONSTANT
# ============================================================

EARTH_RADIUS_M = 6_371_000


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate great-circle distance in metres.
    """

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_M
        * np.arcsin(
            np.sqrt(a)
        )
    )


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading datasets...")


roads = pd.read_csv(
    ROAD_FILE
)

district_map = pd.read_csv(
    DISTRICT_MAP_FILE
)

baseline = pd.read_csv(
    BASELINE_FILE
)

police = pd.read_csv(
    POLICE_FILE
)

hospitals = pd.read_csv(
    HOSPITAL_FILE
)

medical = pd.read_csv(
    MEDICAL_FILE
)

amenities = pd.read_csv(
    AMENITY_FILE
)

lighting = pd.read_csv(
    LIGHTING_FILE
)

cctv = pd.read_csv(
    CCTV_FILE
)

mobility = pd.read_csv(
    MOBILITY_FILE
)

hotspots = pd.read_csv(
    HOTSPOT_FILE
)


print(f"Road segments: {len(roads)}")
print(f"District mappings: {len(district_map)}")
print(f"Police stations: {len(police)}")
print(f"Hospitals: {len(hospitals)}")
print(f"Medical facilities: {len(medical)}")
print(f"Public amenities: {len(amenities)}")
print(f"Lighting records: {len(lighting)}")
print(f"CCTV records: {len(cctv)}")
print(f"Mobility records: {len(mobility)}")
print(f"Crime hotspots: {len(hotspots)}")


# ============================================================
# BASIC VALIDATION
# ============================================================

if len(roads) != 30:

    raise ValueError(
        f"Expected 30 road segments, found {len(roads)}"
    )


if district_map["segment_id"].nunique() != len(district_map):

    raise ValueError(
        "Duplicate segment IDs found in district mapping."
    )


# ============================================================
# ROAD MIDPOINTS
# ============================================================

roads["midpoint_latitude"] = (
    roads["start_latitude"]
    + roads["end_latitude"]
) / 2


roads["midpoint_longitude"] = (
    roads["start_longitude"]
    + roads["end_longitude"]
) / 2


# ============================================================
# DISTRICT MAPPING
# ============================================================

features = roads.merge(
    district_map[
        [
            "segment_id",
            "district",
            "mapping_method",
            "confidence"
        ]
    ],
    on="segment_id",
    how="left",
    validate="one_to_one"
)


if features["district"].isna().any():

    missing = features[
        features["district"].isna()
    ]["segment_id"].tolist()

    raise ValueError(
        f"Missing district mapping for segments: {missing}"
    )


# ============================================================
# NCRB DISTRICT BASELINE
# ============================================================

baseline_columns = [
    "district",
    "population",
    "population_density",
    "total_reported_cases",
    "cases_per_100k",
    "severity_weighted_cases_per_100k",
    "recent_cases_per_100k",
    "recent_severity_per_100k",
    "crime_trend_slope",
    "historical_baseline"
]


features = features.merge(
    baseline[
        baseline_columns
    ],
    on="district",
    how="left",
    validate="many_to_one"
)


if features["historical_baseline"].isna().any():

    missing_districts = (
        features[
            features["historical_baseline"].isna()
        ]["district"]
        .unique()
        .tolist()
    )

    raise ValueError(
        "Districts missing NCRB baseline: "
        + str(missing_districts)
    )


# ============================================================
# DIRECT SEGMENT FEATURES
# ============================================================

# Lighting

lighting_columns = [
    "segment_id",
    "lighting_score"
]

features = features.merge(
    lighting[
        lighting_columns
    ],
    on="segment_id",
    how="left",
    validate="one_to_one"
)


# CCTV

cctv_columns = [
    "segment_id",
    "coverage_score"
]

features = features.merge(
    cctv[
        cctv_columns
    ],
    on="segment_id",
    how="left",
    validate="one_to_one"
)

features = features.rename(
    columns={
        "coverage_score":
        "cctv_coverage_score"
    }
)


# Mobility

mobility_columns = [
    "segment_id",
    "footfall_proxy"
]

features = features.merge(
    mobility[
        mobility_columns
    ],
    on="segment_id",
    how="left",
    validate="one_to_one"
)


# ============================================================
# DISTANCE TO NEAREST POINT
# ============================================================

def add_nearest_distance(
    feature_df,
    points_df,
    output_column
):

    required = [
        "latitude",
        "longitude"
    ]

    for column in required:

        if column not in points_df.columns:

            raise ValueError(
                f"Missing column '{column}'"
            )

    values = []

    point_lat = points_df[
        "latitude"
    ].to_numpy()

    point_lon = points_df[
        "longitude"
    ].to_numpy()

    for _, row in feature_df.iterrows():

        distances = haversine_distance(
            row["midpoint_latitude"],
            row["midpoint_longitude"],
            point_lat,
            point_lon
        )

        values.append(
            float(np.min(distances))
        )

    feature_df[
        output_column
    ] = values

    return feature_df


# ============================================================
# POLICE PROXIMITY
# ============================================================

features = add_nearest_distance(
    features,
    police,
    "distance_to_police_m"
)


# ============================================================
# HOSPITAL PROXIMITY
# ============================================================

features = add_nearest_distance(
    features,
    hospitals,
    "distance_to_hospital_m"
)


# ============================================================
# MEDICAL FACILITY PROXIMITY
# ============================================================

features = add_nearest_distance(
    features,
    medical,
    "distance_to_medical_facility_m"
)


# ============================================================
# PUBLIC TOILET PROXIMITY
# ============================================================

public_toilets = amenities[
    amenities["type"]
    .astype(str)
    .str.contains(
        "toilet|washroom",
        case=False,
        na=False
    )
].copy()


if len(public_toilets) > 0:

    features = add_nearest_distance(
        features,
        public_toilets,
        "distance_to_public_toilet_m"
    )

else:

    features[
        "distance_to_public_toilet_m"
    ] = np.nan


# ============================================================
# NEAREST PUBLIC AMENITY
# ============================================================

features = add_nearest_distance(
    features,
    amenities,
    "distance_to_nearest_amenity_m"
)


# ============================================================
# CRIME HOTSPOT PROXIMITY
# ============================================================

hotspot_lat = hotspots[
    "latitude"
].to_numpy()

hotspot_lon = hotspots[
    "longitude"
].to_numpy()

hotspot_intensity = hotspots[
    "intensity"
].to_numpy()


nearest_hotspot_distance = []

nearest_hotspot_intensity = []


for _, row in features.iterrows():

    distances = haversine_distance(
        row["midpoint_latitude"],
        row["midpoint_longitude"],
        hotspot_lat,
        hotspot_lon
    )

    nearest_index = np.argmin(
        distances
    )

    nearest_hotspot_distance.append(
        float(
            distances[
                nearest_index
            ]
        )
    )

    nearest_hotspot_intensity.append(
        float(
            hotspot_intensity[
                nearest_index
            ]
        )
    )


features[
    "nearest_hotspot_distance_m"
] = nearest_hotspot_distance


features[
    "nearest_hotspot_intensity"
] = nearest_hotspot_intensity


# ============================================================
# SYNTHETIC DATA FLAGS
# ============================================================

features[
    "lighting_data_synthetic"
] = True

features[
    "cctv_data_synthetic"
] = True

features[
    "mobility_data_synthetic"
] = True

features[
    "hotspot_data_synthetic"
] = True


# ============================================================
# FEATURE AVAILABILITY FLAGS
# ============================================================

features[
    "has_police_nearby"
] = (
    features[
        "distance_to_police_m"
    ]
    <= 1000
)


features[
    "has_hospital_nearby"
] = (
    features[
        "distance_to_hospital_m"
    ]
    <= 2000
)


features[
    "has_public_toilet_nearby"
] = (
    features[
        "distance_to_public_toilet_m"
    ]
    <= 1000
)


# ============================================================
# CLEAN OUTPUT COLUMNS
# ============================================================

output_columns = [
    "segment_id",
    "segment_name",

    "district",
    "mapping_method",
    "confidence",

    "midpoint_latitude",
    "midpoint_longitude",

    "distance_m",
    "estimated_travel_time_s",
    "road_type",
    "walkable",

    "population",
    "population_density",

    "total_reported_cases",
    "cases_per_100k",
    "severity_weighted_cases_per_100k",
    "recent_cases_per_100k",
    "recent_severity_per_100k",
    "crime_trend_slope",
    "historical_baseline",

    "lighting_score",
    "cctv_coverage_score",
    "footfall_proxy",

    "distance_to_police_m",
    "distance_to_hospital_m",
    "distance_to_medical_facility_m",

    "distance_to_public_toilet_m",
    "distance_to_nearest_amenity_m",

    "nearest_hotspot_distance_m",
    "nearest_hotspot_intensity",

    "has_police_nearby",
    "has_hospital_nearby",
    "has_public_toilet_nearby",

    "lighting_data_synthetic",
    "cctv_data_synthetic",
    "mobility_data_synthetic",
    "hotspot_data_synthetic"
]


features = features[
    output_columns
]


# ============================================================
# FINAL VALIDATION
# ============================================================

if len(features) != 30:

    raise ValueError(
        f"Expected 30 feature rows, got {len(features)}"
    )


if features["segment_id"].nunique() != 30:

    raise ValueError(
        "Segment IDs are not unique."
    )


# ============================================================
# SAVE
# ============================================================

features.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("SEGMENT CONTEXT FEATURE TABLE CREATED")
print("=" * 70)

print(
    f"\nOutput:\n{OUTPUT_FILE}"
)

print(
    f"\nSegments processed: {len(features)}"
)

print(
    f"\nFeature count: "
    f"{len(output_columns)}"
)

print("\nDistrict distribution:")

print(
    features[
        "district"
    ].value_counts().to_string()
)


print("\nSelected features:")

print(
    features[
        [
            "segment_id",
            "district",
            "historical_baseline",
            "lighting_score",
            "cctv_coverage_score",
            "footfall_proxy",
            "distance_to_police_m",
            "distance_to_hospital_m",
            "distance_to_public_toilet_m",
            "nearest_hotspot_distance_m",
            "nearest_hotspot_intensity"
        ]
    ].to_string(
        index=False
    )
)