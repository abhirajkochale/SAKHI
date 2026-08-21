from pathlib import Path

import json
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ROAD_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "road_segments.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "road_network_graph.json"
)


# ============================================================
# LOAD ROAD SEGMENTS
# ============================================================

print("\nLoading road segments...")

roads = pd.read_csv(
    ROAD_FILE
)

print(
    f"Road segments loaded: {len(roads)}"
)


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [
    "segment_id",
    "start_latitude",
    "start_longitude",
    "end_latitude",
    "end_longitude",
    "distance_m",
    "estimated_travel_time_s",
    "road_type",
    "walkable",
    "segment_name",
]


missing = [
    column
    for column in required_columns
    if column not in roads.columns
]


if missing:

    raise ValueError(
        "Missing required columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# NODE ID
# ============================================================
#
# Coordinates are used as the physical identity of a node.
#
# Rounding avoids floating-point differences creating duplicate
# nodes for coordinates that should represent the same junction.
#

def node_id(latitude, longitude):

    return (
        f"{float(latitude):.5f},"
        f"{float(longitude):.5f}"
    )


# ============================================================
# BUILD GRAPH
# ============================================================

nodes = {}

edges = []


for _, row in roads.iterrows():

    segment_id = int(
        row["segment_id"]
    )

    start_lat = float(
        row["start_latitude"]
    )

    start_lon = float(
        row["start_longitude"]
    )

    end_lat = float(
        row["end_latitude"]
    )

    end_lon = float(
        row["end_longitude"]
    )


    start_node = node_id(
        start_lat,
        start_lon
    )

    end_node = node_id(
        end_lat,
        end_lon
    )


    # --------------------------------------------------------
    # Register nodes
    # --------------------------------------------------------

    nodes[
        start_node
    ] = {
        "latitude": start_lat,
        "longitude": start_lon,
    }


    nodes[
        end_node
    ] = {
        "latitude": end_lat,
        "longitude": end_lon,
    }


    # --------------------------------------------------------
    # Register directed edge
    # --------------------------------------------------------

    edge = {
        "segment_id": segment_id,

        "from_node": start_node,

        "to_node": end_node,

        "distance_m": float(
            row["distance_m"]
        ),

        "travel_time_s": float(
            row["estimated_travel_time_s"]
        ),

        "road_type": str(
            row["road_type"]
        ),

        "walkable": bool(
            row["walkable"]
        ),

        "segment_name": str(
            row["segment_name"]
        ),
    }


    edges.append(
        edge
    )


# ============================================================
# BUILD ADJACENCY LIST
# ============================================================

adjacency = {}


for node in nodes:

    adjacency[node] = []


for edge in edges:

    adjacency[
        edge["from_node"]
    ].append(
        {
            "to_node": edge["to_node"],
            "segment_id": edge["segment_id"],
        }
    )


# ============================================================
# GRAPH OBJECT
# ============================================================

graph = {
    "metadata": {
        "source": "road_segments.csv",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "directed": True,
    },

    "nodes": nodes,

    "edges": edges,

    "adjacency": adjacency,
}


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        graph,
        file,
        indent=2
    )


# ============================================================
# REPORT
# ============================================================

print("\n")
print("=" * 70)
print("ROAD NETWORK GRAPH CREATED")
print("=" * 70)


print(
    f"\nOutput:\n{OUTPUT_FILE}"
)


print(
    f"\nNodes: "
    f"{len(nodes)}"
)


print(
    f"Edges: "
    f"{len(edges)}"
)


print("\nSample nodes:")

for node, data in list(
    nodes.items()
)[:5]:

    print(
        f"{node} → "
        f"({data['latitude']}, "
        f"{data['longitude']})"
    )


print("\nSample edges:")

for edge in edges[:10]:

    print(
        f"{edge['segment_id']}: "
        f"{edge['from_node']} → "
        f"{edge['to_node']} "
        f"({edge['segment_name']})"
    )


print("\n")
print("=" * 70)
print("STEP 2B COMPLETE")
print("=" * 70)

print(
    "\nRoad segments are now represented as a routing graph."
)

print(
    "\nNext stage:"
)

print(
    "Step 2C → Safety-aware Dijkstra/A* routing"
)