from pathlib import Path
import pandas as pd


# =========================================================
# PATHS
# =========================================================

# Project root = SAKHI/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw"
SYNTHETIC_DIR = PROJECT_ROOT / "ml" / "data" / "synthetic"

OUTPUT_DIR = PROJECT_ROOT / "ml" / "data" / "processed"

# Create processed directory if it doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# DATASETS
# =========================================================

# REAL / SOURCE DATA
REAL_DATASETS = [
    "crime_records.csv",
    "population.csv",
    "road_segments.csv",
    "police_stations.csv",
    "hospitals.csv",
    "medical_facilities.csv",
    "public_amenities.csv",
]


# SYNTHETIC / PROXY DATA
SYNTHETIC_DATASETS = [
    "synthetic_lighting.csv",
    "synthetic_cctv.csv",
    "synthetic_mobility.csv",
    "synthetic_crime_hotspots.csv",
    "synthetic_contextual_segments.csv",
]


# =========================================================
# DATASET INSPECTION
# =========================================================

def inspect_dataset(path, dataset_type):

    if not path.exists():
        print(f"\n[WARNING] Dataset not found:")
        print(path)
        return None

    try:
        df = pd.read_csv(path)

    except Exception as error:
        print(f"\n[ERROR] Could not read {path.name}")
        print(error)
        return None

    result = {
        "dataset": path.name,
        "type": dataset_type,

        "rows": len(df),
        "columns": len(df.columns),

        "missing_values": int(
            df.isna().sum().sum()
        ),

        "missing_percent": round(
            df.isna().mean().mean() * 100,
            2
        ),

        "duplicate_rows": int(
            df.duplicated().sum()
        ),

        "has_latitude": "latitude" in df.columns,
        "has_longitude": "longitude" in df.columns,

        "has_start_latitude": "start_latitude" in df.columns,
        "has_start_longitude": "start_longitude" in df.columns,

        "has_end_latitude": "end_latitude" in df.columns,
        "has_end_longitude": "end_longitude" in df.columns,

        "has_segment_id": "segment_id" in df.columns,

        "has_district": "district" in df.columns,

        "has_year": "year" in df.columns,

        "has_synthetic_flag": "is_synthetic" in df.columns,
    }


    # =====================================================
    # YEAR INFORMATION
    # =====================================================

    if "year" in df.columns:

        result["year_min"] = df["year"].min()
        result["year_max"] = df["year"].max()

    else:

        result["year_min"] = None
        result["year_max"] = None


    # =====================================================
    # SYNTHETIC FLAG
    # =====================================================

    if "is_synthetic" in df.columns:

        synthetic_values = (
            df["is_synthetic"]
            .fillna(False)
            .astype(bool)
        )

        result["synthetic_rows"] = int(
            synthetic_values.sum()
        )

    else:

        result["synthetic_rows"] = None


    # =====================================================
    # PRINT DATASET INFORMATION
    # =====================================================

    print("\n")
    print("=" * 70)

    print(f"DATASET: {path.name}")
    print(f"TYPE:    {dataset_type}")

    print("=" * 70)

    print(f"Rows:                  {result['rows']}")
    print(f"Columns:               {result['columns']}")
    print(f"Missing values:        {result['missing_values']}")
    print(f"Missing percentage:    {result['missing_percent']}%")
    print(f"Duplicate rows:        {result['duplicate_rows']}")

    print()

    print(f"Latitude:              {result['has_latitude']}")
    print(f"Longitude:             {result['has_longitude']}")

    print(
        f"Start coordinates:     "
        f"{result['has_start_latitude'] and result['has_start_longitude']}"
    )

    print(
        f"End coordinates:       "
        f"{result['has_end_latitude'] and result['has_end_longitude']}"
    )

    print(f"Segment ID:            {result['has_segment_id']}")
    print(f"District:              {result['has_district']}")

    print(
        f"Year range:            "
        f"{result['year_min']} - {result['year_max']}"
    )

    print(
        f"Synthetic flag:        "
        f"{result['has_synthetic_flag']}"
    )

    print(
        f"Synthetic rows:        "
        f"{result['synthetic_rows']}"
    )

    print("\nColumns:")

    for column in df.columns:
        print(f"  - {column}")


    # =====================================================
    # BASIC DATA TYPES
    # =====================================================

    print("\nData types:")

    for column, dtype in df.dtypes.items():
        print(f"  - {column}: {dtype}")


    return result


# =========================================================
# MAIN AUDIT
# =========================================================

def main():

    print("\n")
    print("=" * 70)
    print("SAKHI DATASET AUDIT")
    print("=" * 70)

    print("\nProject root:")
    print(PROJECT_ROOT)

    print("\nReal data directory:")
    print(RAW_DIR)

    print("\nSynthetic data directory:")
    print(SYNTHETIC_DIR)


    results = []


    # =====================================================
    # REAL DATA
    # =====================================================

    print("\n\n")
    print("#" * 70)
    print("# REAL / SOURCE DATASETS")
    print("#" * 70)

    for filename in REAL_DATASETS:

        path = RAW_DIR / filename

        result = inspect_dataset(
            path,
            "real/source"
        )

        if result is not None:
            results.append(result)


    # =====================================================
    # SYNTHETIC DATA
    # =====================================================

    print("\n\n")
    print("#" * 70)
    print("# SYNTHETIC / PROXY DATASETS")
    print("#" * 70)

    for filename in SYNTHETIC_DATASETS:

        path = SYNTHETIC_DIR / filename

        result = inspect_dataset(
            path,
            "synthetic/proxy"
        )

        if result is not None:
            results.append(result)


    # =====================================================
    # SAVE AUDIT REPORT
    # =====================================================

    if not results:

        print("\n[ERROR] No datasets were successfully inspected.")
        return


    audit = pd.DataFrame(results)

    output_file = (
        OUTPUT_DIR /
        "dataset_audit.csv"
    )

    audit.to_csv(
        output_file,
        index=False
    )


    # =====================================================
    # FINAL SUMMARY
    # =====================================================

    print("\n\n")
    print("=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

    print(
        f"\nDatasets successfully inspected: "
        f"{len(results)}"
    )

    print(
        f"\nAudit report created at:"
    )

    print(output_file)

    print("\nDataset summary:")

    print(
        audit[
            [
                "dataset",
                "type",
                "rows",
                "columns",
                "missing_values",
                "duplicate_rows"
            ]
        ].to_string(index=False)
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()