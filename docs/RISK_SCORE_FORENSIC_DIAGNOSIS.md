CURRENT SEGMENT RISK FORMULA:
There are **two conflicting formulas** currently active depending on the execution context (Offline vs. Real-Time API).

1. **Real-Time API (`risk_service.py`)**:
```math
raw\_prediction = f_{\text{XGBoost}}(\mathbf{X}_{13})
```Inspect the current real crime datasets and determine whether we can construct a genuine ground-truth safety target for Connaught Place.

DO NOT modify code.
DO NOT retrain.
DO NOT change the existing model.

Inspect:
- ml/data/raw/crime_records.csv
- ml/data/normalized/delhi_crime_historical_normalized.csv
- ml/data/processed/ml_training_dataset.csv
- all preprocessing scripts responsible for crime processing

Determine:

1. Exact columns available in the real crime data.
2. Exact date/time coverage.
3. Exact latitude/longitude availability.
4. Exact spatial resolution.
5. Number of real incidents that fall inside Connaught Place.
6. Number of incidents per road segment if mapping is possible.
7. Number of incidents by time-of-day if possible.
8. Number of incidents by crime category.
9. Whether the data supports a segment-level target.
10. Whether the data supports a segment + time target.
11. Any missing/invalid coordinates.
12. Any duplicate incidents.
13. Any temporal gaps.
14. Any spatial gaps.

Then determine the strongest REAL target we can construct without using:
- synthetic data
- manually invented risk formulas
- district-average proxies
- target leakage

Possible target forms may include:
- incident count per segment/time window
- incident rate per segment/time window
- binary occurrence/no-occurrence
- severity-weighted incident outcome

BUT DO NOT choose one yet.

Create:

docs/CONNAUGHT_PLACE_GROUND_TRUTH_AUDIT.md

The report must conclude with:

A. What real target(s) are feasible
B. What target is statistically defensible
C. What data is insufficient
D. What additional real data would most improve the target
E. Recommended target — DO NOT IMPLEMENT YET

All findings must come from the actual repository data.

Do not invent coordinates, observations, or accuracy.
```math
\text{final\_risk\_score} = \text{round}(\max(0.0, \min(100.0, raw\_prediction)), 2)
```

2. **Offline Pipeline (`risk_engine.py`)**:
```math
raw\_prediction = f_{\text{XGBoost}}(\mathbf{X}_{13})
```
```math
\text{confidence\_factor} = \frac{\text{confidence\_score}}{100.0}
```
```math
\text{confidence\_adjusted\_risk} = \text{raw\_prediction} \times (0.75 + 0.25 \times \text{confidence\_factor})
```

CODE LOCATION (API):
`C:\GitHub\SAKHI\backend\app\services\risk\risk_service.py`
`RiskService.calculate_risk()`
Lines 61-105

CODE LOCATION (Offline ML):
`C:\GitHub\SAKHI\ml\routing\risk_engine.py`
`_ (global pipeline scope)`
Lines 411-434

---

CURRENT ROUTE RISK FORMULA:
Again, there are **two completely disjoint formulas** depending on whether the route is calculated by the ML pipeline or the Backend API.

1. **Offline Pipeline Formula (`route_safety_metrics.py`)** (Used to generate `route_recommendation.csv`):
```math
\text{risk\_safety\_comp} = \max(0, 100 - \text{average\_risk})
```
```math
\text{route\_safety\_score} = (0.40 \times \text{risk\_safety\_comp}) + (0.15 \times \text{avg\_lighting}) + (0.15 \times \text{avg\_cctv}) + (0.10 \times \text{police\_comp}) + (0.05 \times \text{hospital\_comp}) + (0.10 \times \text{hotspot\_dist\_comp}) + (0.05 \times \text{hotspot\_intensity\_comp})
```
*(Note: `average_risk` is the arithmetic mean of the segment XGBoost outputs).*

2. **Backend API Formula (`route_ranking_service.py`)**:
```math
\text{route\_risk\_score} = \frac{\sum (\text{segment\_risk}_i \times \text{duration}_i)}{\sum \text{duration}_i}
```

CODE LOCATION (Offline ML):
`C:\GitHub\SAKHI\ml\routing\route_safety_metrics.py`
`_ (global pipeline scope)`
Lines 437-497

CODE LOCATION (API):
`C:\GitHub\SAKHI\backend\app\services\routing\route_ranking_service.py`
`RouteRankingService.aggregate_metrics()`
Lines 36-48

---

CURRENT CONFIDENCE FORMULA:
```math
\text{Confidence Score} = (0.45 \times \text{data\_quality}) + (0.35 \times \text{mapping\_quality}) + (0.20 \times \text{infra\_quality})
```

CODE LOCATION:
`C:\GitHub\SAKHI\backend\app\services\risk\confidence_service.py`
`ConfidenceService.calculate_confidence()`
Lines 30-99

---

CURRENT MODEL ACCURACY:
**NO VALID HELD-OUT ACCURACY CURRENTLY AVAILABLE.** 
The XGBoost script (`train_xgboost.py`) reports evaluation metrics (Train MAE: 0.128, Validation MAE: ~0.15), but it explicitly states: `(all metrics vs. engineered proxy target, not real crime events)`. The model has never been empirically evaluated against actual, observed historical street-level incidents.

---

# 1. One real route traced end-to-end

**Route Selected**: Route ID 1 from `ml/data/processed/route_recommendation.csv`
**Context**: Evening, Weekday (`is_weekend = 0`)
**Origin**: Connaught Place
**Destination**: Dwarka Sec 23
**Distance**: 22.8 km (22,800 meters)
**Travel Time**: 30.4 minutes (1824 seconds)
**Segment Count**: 4
**Segments Included**:
- 1015: Connaught Place to Karol Bagh
- 1016: Karol Bagh to Rajouri Garden
- 1017: Rajouri Garden to Janakpuri
- 1018: Janakpuri to Dwarka Sec 23

---

# 2. Every segment traced

| Segment ID | Path | District | Features (Lighting/CCTV) | Model Output (Risk) | Confidence | Offline Adjusted Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1015** | CP to Karol Bagh | Central | 95 / 51 | 25.23 (Moderate) | 35.47 | 21.16 |
| **1016** | Karol Bagh to Rajouri Garden | West | 81 / 58 | 20.28 (Low) | 0.00 | 15.21 |
| **1017** | Rajouri Garden to Janakpuri | West | 98 / 55 | 12.80 (Low) | 0.00 | 9.60 |
| **1018** | Janakpuri to Dwarka Sec 23 | South West | 97 / 65 | 16.39 (Low) | 0.00 | 12.29 |

---

# 3. Segment-level data

**Segment 1015 (`route_ready_segments.csv`)**:
- Coordinates: `28.6421, 77.20485`
- Distance: `3300m`, Travel Time: `264s`
- Lighting: `95`, CCTV: `51`
- Contextual Footfall: `2192.0`
- Distance to Police: `920.6m`
- Distance to Hospital: `1550.5m`
- Hotspot Distance: `920.6m`, Intensity: `88.0`
- Raw Prediction: `25.23`
- Confidence: `35.47`
- Routing Cost (Time + Penalties): `375.74`

---

# 4. Route-level calculation

Let's manually reproduce the "Route 1 Safety Score" of **68.47** calculated by the ML pipeline to prove how the metric is constructed.

**1. Calculate Arithmetic Means of the 4 Segments**:
- `average_risk` = (25.23 + 20.28 + 12.80 + 16.39) / 4 = **18.68**
- `average_lighting` = (95 + 81 + 98 + 97) / 4 = **92.75**
- `average_cctv` = (51 + 58 + 55 + 65) / 4 = **57.25**
- `avg_police_dist` = (920.6 + 3315.89 + 824.4 + 3968.7) / 4 = **2257.41 m**
- `avg_hospital_dist` = (1550.56 + 2290.38 + 1102.04 + 1342.16) / 4 = **1571.29 m**
- `avg_hotspot_dist` = (920.6 + 5736.96 + 8086.28 + 12210.53) / 4 = **6738.6 m**
- `avg_hotspot_int` = (88 + 88 + 85 + 85) / 4 = **86.5**

**2. Component Normalization (`route_safety_metrics.py`)**:
- `risk_comp` = max(0, 100 - 18.68) = **81.32**
- `police_comp` = (1 - (2257.41 / 5000)) * 100 = **54.85**
- `hospital_comp` = (1 - (1571.29 / 8000)) * 100 = **80.36**
- `hotspot_dist_comp` = (1 - (6738.6 / 10000)) * 100 = **32.61**
- `hotspot_int_comp` = 100 - 86.5 = **13.5**

**3. Final Weighted Sum**:
`Score = (0.40 * 81.32) + (0.15 * 92.75) + (0.15 * 57.25) + (0.10 * 54.85) + (0.05 * 80.36) + (0.10 * 32.61) + (0.05 * 13.5)`
`Score = 32.528 + 13.9125 + 8.5875 + 5.485 + 4.018 + 3.261 + 0.675 = 68.467`
`Rounded = 68.47`

**Matches application value EXACTLY.**

---

# 5. Confidence interpretation

**CONFIDENCE DOES NOT REPRESENT PREDICTION ACCURACY.** 

It is entirely a **heuristic penalty metric** grading the quality of the input data sources.
If data is synthetic, if geo-coordinates are far from known references, or if the time field is missing, it docks points using a linear equation. It has zero statistical relationship with whether the XGBoost model's prediction correctly reflects historical crime probability.

**"Does this confidence number represent actual empirical prediction accuracy?"**
**NO.** It represents the integrity of the data stream, not the certainty of the model.

---

# 6. Actual validation metrics

There is no valid hold-out test accuracy. The script `train_xgboost.py` outputs a Mean Absolute Error (MAE) of ~0.15 on its validation set. However, this MAE is testing the model's ability to recalculate the `crime_grounded_risk_index` proxy, not to predict real crimes. 

---

# 7. Three detailed segment explanations

**1. Segment 1015 (CP to Karol Bagh, Evening, Weekday)**
- **Raw features**: Distance: 3300m, Police dist: 920.6m, Lighting: 95.
- **Model Output**: 25.23
- **SHAP Explanation**: `distance_to_police` decreases risk (negative $\phi$), `lighting_score` decreases risk (negative $\phi$). `hotspot_intensity` (88.0) increases risk (positive $\phi$).
- **Source**: Real road geometry, synthetic infrastructure proxy.

**2. Segment 1017 (Rajouri Garden to Janakpuri, Evening, Weekday)**
- **Raw features**: Distance: 4300m, Police dist: 824m, Hospital: 1102m.
- **Model Output**: 12.80
- **SHAP Explanation**: Close proximity to Police (824m) and high lighting (98) act as the strongest suppressors of risk score.
- **Source**: Real road geometry, synthetic infrastructure proxy.

**3. Segment 1001 (Connaught Place to Janpath, Night, Weekday)**
- **Raw features**: Distance: 950m, Footfall: 1673, Hotspot Intensity: 88.0.
- **Model Output**: 53.02
- **SHAP Explanation**: The drop in `contextual_footfall_proxy` (from 4782 in the evening to 1673 at night) triggers the temporal penalty learned from the target array, driving the risk output high.
- **Source**: Target proxy logic.

---

# 8. SHAP verification

**SHAP explains the raw `predict()` regression margin.**
It does **NOT** explain the `confidence_adjusted_risk` computed in `risk_engine.py`, nor does it account for the route-level inflation formulas in `route_safety_metrics.py`. 
For instance, on Segment 1016, SHAP will explain why the XGBoost model arrived at `20.28`. It will completely ignore that the system then multiplies this by `0.75` (because `confidence` = 0), lowering it arbitrarily to `15.21`. The user-facing explanation thus defends a score different from what is actually used to route them.

---

# 9. Training coverage

The ML training spatial bounding box spans:
- Min Lat: 28.5252, Max Lat: 28.7258
- Min Lon: 77.0709, Max Lon: 77.2918

Route 1 segments (1015-1018) sit entirely within this bounding box. However, because the dataset utilizes purely district-level baseline averages assigned generically to proxy polygons, true sub-meter spatial coverage interpolation is an illusion. The model sees no geographical difference between two segments in the same district other than their distance to static GIS nodes (like a hospital).

---

# 10. Target construction

**What is the model actually being trained to predict?**
It is trained to predict `crime_grounded_risk_index`.
This index is **synthetic and circular**. It is explicitly constructed in `build_training_target.py` using temporal hours and generic geographical modifiers. Because the target is derived from the same domain logic as the input features (e.g., night hours penalize the target, low footfall identifies night), the XGBoost model simply functions as a slow, computationally expensive memory bank that interpolates the heuristic formula written in python. 

---

# 11. Data quality

A review of `dataset_audit.csv` reveals the following critical data weaknesses for the selected route:
- `synthetic_lighting.csv`: 100% Synthetic / Proxy
- `synthetic_cctv.csv`: 100% Synthetic / Proxy
- `synthetic_mobility.csv`: 100% Synthetic / Proxy
- `crime_records.csv`: Real, but aggregated entirely at the district level. 

There is **no street-level observational safety data** being fed into the XGBoost model. The model calculates local variation based entirely on distances to OSM features (Police, Hospital).

---

# 12. Score sanity tests

- **A. Missing Confidence (`risk_engine.py`)**: If confidence data is missing (0.0), the model risk score is immediately multiplied by 0.75. **A lack of data literally makes the segment safer by 25%.**
- **B. Double Counting (`route_safety_metrics.py`)**: A segment with fantastic lighting (95/100) will receive a low risk score from the ML model. Then, the Route Ranker will see the low risk, convert it to a high "safety component", and **add** another 15 points because lighting is 95/100. Good infrastructure is rewarded twice.

---

# 13. Root causes of inaccurate scores

The combination of the following issues renders the scores scientifically invalid:
1. **Target Circularity**: The model trains on a proxy formula, not ground truth.
2. **Double-Counting (Inflation)**: The offline routing algorithm adds feature scores on top of an ML prediction that already consumed those features.
3. **Negative Uncertainty**: The confidence adjustment lowers risk when data is missing.
4. **Proxy Saturation**: 100% of local infrastructure variables (lighting, CCTV) are generated synthetically.

---

# 14. CRITICAL/HIGH/MEDIUM/LOW findings

- **CRITICAL**: The Offline Pipeline `route_safety_score` double-counts input features, causing severe, mathematically indefensible safety score inflation.
- **CRITICAL**: The `confidence_adjusted_risk` formula (`model_risk_score * (0.75 + 0.25*conf)`) fundamentally violates basic safety principles by interpreting missing data (0% confidence) as a 25% risk reduction.
- **HIGH**: The training target is a synthetic heuristic formula; the ML model operates strictly as an interpolator of that formula rather than a discoverer of real crime patterns.
- **HIGH**: Discrepancy between Offline routing (uses heuristic inflation + confidence penalty) vs API routing (uses exact duration-weighted ML output). 

---

# 15. Exact evidence for every finding

- **Double-Counting**: Line 437-497 in `ml/routing/route_safety_metrics.py` explicitly constructs the weighted sum using `lighting_component`, `cctv_component`, etc.
- **Negative Uncertainty**: Line 411-434 in `ml/routing/risk_engine.py` executes the 0.75 multiplication scalar.
- **Proxy Saturation**: `dataset_audit.csv` lines 9-11 show 100% synthetic ratio.
- **Target Circularity**: `ml/preprocessing/build_training_target.py` mathematically forces temporal and spatial relationships into the target label prior to training.

---

# 16. Recommended next step — DO NOT IMPLEMENT IT YET

The most immediate requirement is to **dismantle the score inflation and double-counting formulas** in `route_safety_metrics.py` and `risk_engine.py`. The routing offline pipeline should unify with the backend API `aggregate_metrics` logic, utilizing pure duration-weighted ML model output without heuristic re-addition of features or negative-uncertainty scaling. Following this, the XGBoost target generation pipeline must be overhauled to use empirical incident data rather than proxy index approximations.
