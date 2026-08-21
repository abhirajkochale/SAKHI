from pathlib import Path
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "ml" / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "delhi_district_boundaries.geojson"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# NIC BharatMap district layer
BASE_URL = (
    "https://webgis3.nic.in/"
    "bharatmaps/rest/services/"
    "BharatMapService/"
    "Admin_Boundary_District/"
    "MapServer/1/query"
)


params = {
    "where": "stcode11='07'",
    "outFields": "dtname,stname,dtcode11,year_stat",
    "returnGeometry": "true",
    "outSR": "4326",
    "f": "geojson",
}


print("Downloading Delhi district boundaries...")
print(BASE_URL)


try:

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=60
    )

    print(f"HTTP status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

except Exception as error:

    print("\nDOWNLOAD FAILED")
    print(error)
    raise SystemExit(1)


# ---------------------------------------------------------
# BASIC VALIDATION
# ---------------------------------------------------------

if data.get("type") != "FeatureCollection":

    print("\nERROR: Response is not a GeoJSON FeatureCollection.")

    print(data)

    raise SystemExit(1)


features = data.get("features", [])

print(f"\nFeatures received: {len(features)}")


if len(features) == 0:

    print("\nERROR: No Delhi district features returned.")

    raise SystemExit(1)


# ---------------------------------------------------------
# SHOW DISTRICTS
# ---------------------------------------------------------

districts = []

for feature in features:

    properties = feature.get("properties", {})

    district = properties.get("dtname")

    if district:
        districts.append(district)


districts = sorted(set(districts))


print("\nDistricts found:")

for district in districts:
    print(f"  - {district}")


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

OUTPUT_FILE.write_text(
    response.text,
    encoding="utf-8"
)


print("\nSUCCESS")
print(f"Saved to:")
print(OUTPUT_FILE)