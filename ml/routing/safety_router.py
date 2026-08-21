from pathlib import Path
import json
import heapq

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GRAPH_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "road_network_graph.json"
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
    / "route_test_results.csv"
)


# ============================================================
# LOAD GRAPH
# ============================================================

print("\nLoading road network graph...")

with open(
    GRAPH_FILE,
    "r",
    encoding="utf-8"
) as file:

    graph = json.load(file)


nodes = graph["nodes"]
edges = graph["edges"]
adjacency = graph["adjacency"]

print(
    f"Nodes: {len(nodes)}"
)

print(
    f"Edges: {len(edges)}"
)


# ============================================================
# LOAD RISK DATA
# ============================================================

print("\nLoading route-ready risk data...")

risk_df = pd.read_csv(
    RISK_FILE
)

print(
    f"Risk rows: {len(risk_df)}"
)


# ============================================================
# PREPARE RISK LOOKUP
# ============================================================

# For each:
#
# segment + time period + weekend
#
# we store the model risk and routing cost.

risk_lookup = {}


for _, row in risk_df.iterrows():

    key = (
        int(row["segment_id"]),
        str(row["time_period"]),
        int(row["is_weekend"]),
    )

    risk_lookup[key] = {
        "risk_score": float(
            row["model_risk_score"]
        ),

        "risk_band": str(
            row["model_risk_band"]
        ),

        "routing_cost": float(
            row["routing_cost"]
        ),

        "confidence_score": float(
            row.get(
                "confidence_score",
                0
            )
        ),
    }


# ============================================================
# BUILD EDGE LOOKUP
# ============================================================

edge_lookup = {}


for edge in edges:

    edge_lookup[
        int(edge["segment_id"])
    ] = edge


# ============================================================
# FIND NEAREST NODE
# ============================================================

def nearest_node(
    latitude,
    longitude
):

    best_node = None
    best_distance = float(
        "inf"
    )

    for node_id, data in nodes.items():

        d_lat = (
            data["latitude"]
            - latitude
        )

        d_lon = (
            data["longitude"]
            - longitude
        )

        distance = (
            d_lat ** 2
            +
            d_lon ** 2
        )

        if distance < best_distance:

            best_distance = distance
            best_node = node_id

    return best_node


# ============================================================
# GET EDGE COST
# ============================================================

def get_edge_cost(
    segment_id,
    time_period,
    is_weekend,
    mode
):

    key = (
        int(segment_id),
        str(time_period),
        int(is_weekend),
    )

    risk_info = risk_lookup.get(
        key
    )

    edge = edge_lookup[
        int(segment_id)
    ]

    travel_time = float(
        edge["travel_time_s"]
    )

    if risk_info is None:

        # Conservative fallback
        risk_score = 50.0
        routing_cost = (
            travel_time * 2
        )

    else:

        risk_score = (
            risk_info[
                "risk_score"
            ]
        )

        routing_cost = (
            risk_info[
                "routing_cost"
            ]
        )


    # --------------------------------------------------------
    # ROUTING MODES
    # --------------------------------------------------------

    if mode == "fastest":

        cost = travel_time

    elif mode == "safest":

        # Safety dominates.
        #
        # Risk penalty is weighted strongly.

        risk_penalty = (
            routing_cost
            -
            travel_time
        )

        cost = (
            travel_time
            +
            2.5
            *
            risk_penalty
        )

    elif mode == "balanced":

        # Balanced between travel time
        # and contextual safety.

        risk_penalty = (
            routing_cost
            -
            travel_time
        )

        cost = (
            travel_time
            +
            1.25
            *
            risk_penalty
        )

    else:

        raise ValueError(
            f"Unknown routing mode: {mode}"
        )


    return cost, risk_score


# ============================================================
# DIJKSTRA
# ============================================================

def dijkstra(
    start_node,
    destination_node,
    time_period="Evening",
    is_weekend=0,
    mode="balanced"
):

    # Priority queue:
    #
    # (total_cost, node)

    queue = [
        (
            0.0,
            start_node
        )
    ]


    distances = {
        start_node: 0.0
    }


    previous = {}


    while queue:

        current_cost, current_node = (
            heapq.heappop(queue)
        )


        # Skip outdated queue entry

        if (
            current_cost
            >
            distances.get(
                current_node,
                float("inf")
            )
        ):

            continue


        # Destination reached

        if (
            current_node
            ==
            destination_node
        ):

            break


        # Explore neighbors

        for connection in adjacency.get(
            current_node,
            []
        ):

            next_node = (
                connection["to_node"]
            )

            segment_id = int(
                connection["segment_id"]
            )


            edge_cost, risk_score = (
                get_edge_cost(
                    segment_id,
                    time_period,
                    is_weekend,
                    mode
                )
            )


            new_cost = (
                current_cost
                +
                edge_cost
            )


            if new_cost < distances.get(
                next_node,
                float("inf")
            ):

                distances[
                    next_node
                ] = new_cost


                previous[
                    next_node
                ] = {
                    "node": current_node,
                    "segment_id": segment_id,
                    "edge_cost": edge_cost,
                    "risk_score": risk_score,
                }


                heapq.heappush(
                    queue,
                    (
                        new_cost,
                        next_node
                    )
                )


    # ========================================================
    # NO ROUTE
    # ========================================================

    if destination_node not in distances:

        return None


    # ========================================================
    # RECONSTRUCT ROUTE
    # ========================================================

    route_nodes = []
    route_segments = []

    current = destination_node


    while current != start_node:

        route_nodes.append(
            current
        )


        step = previous[
            current
        ]


        route_segments.append(
            {
                "segment_id":
                    step[
                        "segment_id"
                    ],

                "edge_cost":
                    step[
                        "edge_cost"
                    ],

                "risk_score":
                    step[
                        "risk_score"
                    ],
            }
        )


        current = step[
            "node"
        ]


    route_nodes.append(
        start_node
    )


    route_nodes.reverse()
    route_segments.reverse()


    return {
        "mode": mode,

        "start_node":
            start_node,

        "destination_node":
            destination_node,

        "nodes":
            route_nodes,

        "segments":
            route_segments,

        "total_cost":
            distances[
                destination_node
            ],
    }


# ============================================================
# ROUTE SUMMARY
# ============================================================

def summarize_route(
    route,
    time_period,
    is_weekend
):

    if route is None:

        return None


    segment_ids = [
        segment[
            "segment_id"
        ]

        for segment
        in route[
            "segments"
        ]
    ]


    total_distance = 0.0
    total_time = 0.0
    risk_scores = []


    for segment_id in segment_ids:

        edge = edge_lookup[
            segment_id
        ]


        total_distance += float(
            edge[
                "distance_m"
            ]
        )


        total_time += float(
            edge[
                "travel_time_s"
            ]
        )


        key = (
            segment_id,
            time_period,
            is_weekend
        )


        if key in risk_lookup:

            risk_scores.append(
                risk_lookup[
                    key
                ][
                    "risk_score"
                ]
            )


    average_risk = (
        sum(risk_scores)
        /
        len(risk_scores)
        if risk_scores
        else 0
    )


    maximum_risk = (
        max(risk_scores)
        if risk_scores
        else 0
    )


    return {
        "mode":
            route["mode"],

        "segments":
            " → ".join(
                map(
                    str,
                    segment_ids
                )
            ),

        "segment_count":
            len(segment_ids),

        "distance_m":
            round(
                total_distance,
                2
            ),

        "travel_time_s":
            round(
                total_time,
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

        "routing_cost":
            round(
                route[
                    "total_cost"
                ],
                2
            ),
    }


# ============================================================
# TEST ROUTING
# ============================================================

print("\n")
print("=" * 70)
print("TESTING SAFETY-AWARE ROUTING")
print("=" * 70)


# ------------------------------------------------------------
# Test location
# ------------------------------------------------------------
#
# Connaught Place
#
# → Dwarka Sector 23
#
# using the coordinates already present in your road data.
#

start_lat = 28.6327
start_lon = 77.2195

destination_lat = 28.5562
destination_lon = 77.0543


start_node = nearest_node(
    start_lat,
    start_lon
)

destination_node = nearest_node(
    destination_lat,
    destination_lon
)


print(
    f"\nStart node:"
    f"\n{start_node}"
)


print(
    f"\nDestination node:"
    f"\n{destination_node}"
)


# ============================================================
# TEST ALL MODES
# ============================================================

results = []


for mode in [
    "fastest",
    "balanced",
    "safest",
]:

    print(
        f"\nCalculating "
        f"{mode} route..."
    )


    route = dijkstra(
        start_node,
        destination_node,
        time_period="Evening",
        is_weekend=0,
        mode=mode
    )


    if route is None:

        print(
            f"No {mode} route found."
        )

        continue


    summary = summarize_route(
        route,
        time_period="Evening",
        is_weekend=0
    )


    results.append(
        summary
    )


    print(
        "\nRoute:"
    )

    print(
        summary[
            "segments"
        ]
    )


    print(
        f"Distance: "
        f"{summary['distance_m']} m"
    )


    print(
        f"Travel time: "
        f"{summary['travel_time_s']} s"
    )


    print(
        f"Average risk: "
        f"{summary['average_risk']}"
    )


    print(
        f"Maximum risk: "
        f"{summary['maximum_risk']}"
    )


    print(
        f"Routing cost: "
        f"{summary['routing_cost']}"
    )


# ============================================================
# SAVE RESULTS
# ============================================================

if results:

    results_df = pd.DataFrame(
        results
    )


    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


# ============================================================
# FINAL REPORT
# ============================================================

print("\n")
print("=" * 70)
print("STEP 2C COMPLETE")
print("=" * 70)


print(
    "\nSAKHI can now calculate:"
)


print(
    "• Fastest route"
)


print(
    "• Balanced route"
)


print(
    "• Safest route"
)


print(
    "\nNext stage:"
)


print(
    "Step 2D → Route comparison and recommendation"
)