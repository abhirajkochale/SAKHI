# Connaught Place Ground-Truth Audit

This report details an exhaustive inspection of the real crime datasets currently available in the SAKHI repository (`crime_records.csv`, `delhi_crime_historical_normalized.csv`, and preprocessing scripts) to determine whether a genuine, segment-level ground-truth safety target can be constructed.

## Data Inspection Results

### 1. Exact columns available in the real crime data
- `ml/data/raw/crime_records.csv`: `id`, `district`, `police_station`, `crime_category`, `crime_subcategory`, `reported_cases`, `severity`, `year`, `month`, `source`, `source_url`, `data_precision`, `is_synthetic`
- `ml/data/normalized/delhi_crime_historical_normalized.csv`: `district`, `year`, `rape_cases`, `assault_women`, `kidnapping`, `source_file`, `source_type`, `source_date_range`, `normalization_notes`

### 2. Exact date/time coverage
- **Years**: 2018 to 2023
- **Months**: 1 through 12
- **Time of Day**: Not recorded. There is zero hourly or temporal resolution beyond the month.

### 3. Exact latitude/longitude availability
- **None**. The raw crime data contains absolutely no coordinate fields.

### 4. Exact spatial resolution
- **District-Level Aggregate**. The data is grouped into 11 broad Delhi districts (e.g., "Central", "New Delhi", "South"). 

### 5. Number of real incidents that fall inside Connaught Place
- **Impossible to isolate**. Police station mappings are generic (e.g., "New Delhi Central PS") and represent entire district aggregates rather than individual local stations.

### 6. Number of incidents per road segment
- **0**. Mapping to road segments is completely impossible because there are no coordinates, addresses, or sub-district geographic identifiers.

### 7. Number of incidents by time-of-day
- **0**. Time-of-day is fundamentally missing from all real datasets.

### 8. Number of incidents by crime category
Across all districts and years (2018-2023):
- Assault on Women with Intent to Outrage Modesty: 8,264
- Cruelty by Husband or Relatives: 12,514
- Dowry Deaths: 802
- Kidnapping & Abduction of Women: 8,235
- Rape: 8,073
- Stalking: 6,573
- Voyeurism: 8,667

### 9. Whether the data supports a segment-level target
- **No.** The spatial resolution is locked at the district level.

### 10. Whether the data supports a segment + time target
- **No.** The temporal resolution is locked at the month level, and spatial at the district level.

### 11. Any missing/invalid coordinates
- 100% of the dataset lacks coordinates.

### 12. Any duplicate incidents
- No direct duplicates found, but the data exists purely as macro-level sums, meaning incident-level duplication analysis is inapplicable.

### 13. Any temporal gaps
- The data completely lacks day-of-week, day-of-month, and time-of-day (hourly) data. 

### 14. Any spatial gaps
- The data completely lacks street-level, ward-level, or neighborhood-level granularity.

---

## Conclusion & Target Feasibility

### A. What real target(s) are feasible
Given the raw data currently in the repository, **no segment-level or time-specific target is feasible**. The only feasible "real" target we can extract is a **District-Year-Month Aggregated Crime Rate** or **Severity-Weighted District Burden**. It cannot be localized to a specific road segment, and it cannot vary by time-of-day.

### B. What target is statistically defensible
Using the existing data, the only statistically defensible construction is a macroscopic `District Crime Baseline` (which the pipeline already computes as a prior). 

However, using this district-level aggregate as the *predictive target* for a segment-level XGBoost model is **not statistically defensible**. Because the target variable has zero variance within the same district, the ML model is forced to hallucinate false correlations with segment-specific features (like distance to a hospital or lighting) in an attempt to minimize error against a flat district average. This is the root cause of the arbitrary risk scores observed during inference.

### C. What data is insufficient
The entire historical dataset is grossly insufficient for predicting segment-level safety. The lack of geocoordinates, exact timestamps, and individual incident records prevents the creation of an empirical, localized ground truth.

### D. What additional real data would most improve the target
To construct a genuine segment-level ground-truth target, SAKHI requires:
1. **Incident-level records** (individual FIRs, emergency calls, or localized reports).
2. **Exact latitude/longitude** or geocoded street intersections for each incident.
3. **Precise timestamps** (Date and exact Time of Day) for temporal pattern matching.

### E. Recommended target — DO NOT IMPLEMENT YET
**Recommended Target Construction (with proper data):**
*Segment-Time Incident Rate (Incidents per 100 meters per time-period)*

**Logic**: 
Map individual incident coordinates to the nearest road segment (using a 50m spatial join radius). Group the counts by Segment ID and Time-of-Day (Morning, Day, Evening, Night). Finally, normalize the incident count by the segment's length (e.g., incidents per 100m) so that physically longer segments do not falsely appear disproportionately dangerous compared to shorter, denser segments. This target should be trained using a Poisson or Negative Binomial regression objective rather than arbitrary 0-100 regression.
